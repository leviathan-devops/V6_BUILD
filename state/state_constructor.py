"""state/state_constructor.py — bars -> Decider state text.

The Decider reads ONE document (the state) plus typed questions. This module
renders the golden-week bars into that document.

THE TEMPORAL LAW: only bars with ts <= anchor_ms may enter the state. A bar
past the anchor is a FUTURE_BAR_LEAK and MUST be rejected, never silently
dropped — the leak is a named error.

Source: Plutus_V6_Master_Blueprint_v1.md — the packing grammar:
  <|fim_prefix|> STATE   <|fim_middle|> QUESTION   <|box_start|> OPTION ...
"""
from __future__ import annotations
from dataclasses import dataclass

STATE_DELIM = "<|fim_prefix|>"
QUESTION_DELIM = "<|fim_middle|>"
OPTION_OPEN = "<|box_start|>"
OPTION_CLOSE = "<|box_end|>"
DECIDE = "<|fim_suffix|>"

STATE_TOKEN_LIMIT = 8192      # the Decider's state limit (blueprint §1.6)

PIP = {"EUR/USD": 0.0001, "GBP/USD": 0.0001, "DXY": 0.01}

LONDON_OPEN_ET = "02:00"
LONDON_CLOSE_ET = "05:00"


class FutureBarLeak(RuntimeError):
    """A bar strictly after the analysis anchor entered the state."""


class EmptyBars(RuntimeError):
    """NO_BARS: the feed delivered nothing. Loud, named, never a silent skip."""


@dataclass(frozen=True)
class Bar:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def parse_bars(raw: list[dict], anchor_ms: int) -> list[Bar]:
    """Parse + TEMPORAL-FILTER. Any bar past the anchor raises FutureBarLeak."""
    if not raw:
        raise EmptyBars("NO_BARS: the feed returned an empty bar list")
    bars, leaks, bad_ts = [], [], []
    for r in raw:
        # AUDIT FIX: a missing timestamp became ts=0, which passes the anchor
        # check and sorts to the FRONT of the state, polluting the bar order.
        # accepted key names: ts | time | timestamp (the harvester's key)
        raw_ts = r.get("ts")
        if raw_ts is None: raw_ts = r.get("time")
        if raw_ts is None: raw_ts = r.get("timestamp")
        if raw_ts is None:
            bad_ts.append(r)
            continue
        try:
            ts = int(raw_ts)
        except (TypeError, ValueError):
            bad_ts.append(r)
            continue
        if ts > anchor_ms:
            leaks.append(ts)
            continue
        # AUDIT FIX: a missing OHLC key raised a bare KeyError and a None/non-
        # numeric value a bare TypeError/ValueError, bypassing this module's
        # named loud-fail contract (which ts already had).
        try:
            o = float(r["open"]); h = float(r["high"])
            l = float(r["low"]);  cl = float(r["close"])
            v = float(r.get("volume") or 0.0)
        except KeyError as e:
            raise ValueError(f"BAR_MISSING_FIELD: bar ts={ts} has no {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"BAR_BAD_FIELD: bar ts={ts} has a non-numeric OHLC — {e}") from e
        for nm, val in (("open", o), ("high", h), ("low", l), ("close", cl)):
            if not (val == val and abs(val) != float("inf")):
                raise ValueError(f"BAR_NON_FINITE: bar ts={ts} {nm}={val!r}")
        if h < l:
            raise ValueError(f"BAR_INVERTED: bar ts={ts} high={h} < low={l}")
        bars.append(Bar(ts, o, h, l, cl, v))
    # AUDIT FIX: the leak check ran SECOND, so a feed carrying both a bad
    # timestamp and a future bar reported only the timestamp — the FUTURE_BAR_LEAK
    # (the temporal law's named violation) was masked. The LEAK is reported
    # first: it is the law, the timestamp is hygiene.
    if leaks:
        raise FutureBarLeak(
            f"FUTURE_BAR_LEAK: {len(leaks)} bar(s) past anchor {anchor_ms} "
            f"(first leaked ts={min(leaks)})"
            + (f"; {len(bad_ts)} bar(s) also lacked a timestamp" if bad_ts else ""))
    if bad_ts:
        raise ValueError(
            f"BAR_MISSING_TIMESTAMP: {len(bad_ts)} bar(s) carry no usable ts/time")
    return sorted(bars, key=lambda b: b.ts)


def atr(bars: list[Bar], period: int = 14) -> float:
    """Average True Range over the MOST RECENT `period` bars.

    AUDIT FIX (round 6): the first version sliced `range(1, period+1)` — the
    HEAD of an ascending list — so on a 6,000-bar feed the ATR described bars
    from weeks earlier while the swing levels beside it used the tail. Two
    numbers in the same header described different eras.
    """
    if len(bars) < 2:
        return 0.0
    w = bars[-(period + 1):]              # the trailing window
    # AUDIT FIX (round 8): this was average HIGH-LOW, not TRUE RANGE. The gap
    # terms matter: an overnight/weekend gap shows up only in |high - prevClose|
    # and |low - prevClose|, so the old form understated volatility on exactly
    # the bars that follow a gap. TR = max(H-L, |H-prevC|, |L-prevC|).
    trs = []
    for i in range(1, len(w)):
        prev_c = w[i - 1].close
        trs.append(max(w[i].high - w[i].low,
                       abs(w[i].high - prev_c),
                       abs(w[i].low - prev_c)))
    return round(sum(trs) / len(trs), 5) if trs else 0.0


def swing_levels(bars: list[Bar], lookback: int = 48) -> tuple[float, float]:
    """The swing high/low over the lookback window.

    DEFECT FIXED (found by the e2e probe 2026-09-23): an EMPTY bar list raised
    the bare, unnamed `ValueError: max() iterable argument is empty` from
    inside max(). The empty-feed condition has a NAME in this module — the
    loud-fail law requires it be raised as EmptyBars/NO_BARS, never as a
    generic stdlib error three frames down.
    """
    if not bars:
        raise EmptyBars("NO_BARS: swing_levels called with an empty bar list")
    w = bars[-lookback:] if len(bars) > lookback else bars
    return (round(max(b.high for b in w), 5), round(min(b.low for b in w), 5))


def render_feed_block(pair: str, tf: str, bars: list[Bar], n: int = 12) -> str:
    """The compact OHLC block for one (pair, timeframe)."""
    recent = bars[-n:]
    pip = PIP.get(pair, 0.0001)
    lines = [f"{pair} {tf} ({len(bars)} bars, last {len(recent)} shown, pip={pip}):"]
    for b in recent:
        lines.append(f"  t={b.ts} O={b.open:.5f} H={b.high:.5f} L={b.low:.5f} C={b.close:.5f}")
    return "\n".join(lines)


def render_state(pair: str, anchor_ms: int, feeds: dict[tuple[str, str], list[Bar]],
                 session_utc: str = "", extra: str = "") -> str:
    """Render the full Decider state document.

    AUDIT FIX: the anchor was only INTERPOLATED into the header — no bar was
    checked against it. A `Bar` built by any route other than parse_bars (or a
    feed mutated after parsing) entered the document unchecked, violating the
    module's own TEMPORAL LAW. The check is now enforced at render time too.
    """
    for (p, tf), bars in feeds.items():
        over = [b for b in bars if b.ts > anchor_ms]
        if over:
            raise FutureBarLeak(
                f"FUTURE_BAR_LEAK: {p} {tf} has {len(over)} bar(s) past anchor "
                f"{anchor_ms} at RENDER time (first ts={over[0].ts})")
    blocks = []
    for (p, tf), bars in sorted(feeds.items()):
        if not bars: continue
        blocks.append(render_feed_block(p, tf, bars))
    # AUDIT FIX: a state with neither 30m nor 1H raised EmptyBars from inside
    # swing_levels. The condition is NAMED here.
    main = feeds.get((pair, "30m")) or feeds.get((pair, "1H"))
    if not main:
        raise EmptyBars(
            f"NO_MAIN_TIMEFRAME: {pair!r} has neither a 30m nor a 1H feed "
            f"(available: {sorted(k for k in feeds if k[0] == pair)})")
    atr_v = atr(main)
    hi, lo = swing_levels(main)
    head = [
        f"PAIR {pair} | ANCHOR {anchor_ms} | SESSION {session_utc or 'n/a'}",
        f"ATR(14) {atr_v} | SWING HIGH {hi} | SWING LOW {lo}",
    ]
    body = "\n".join(head + [""] + blocks)
    if extra: body += "\n" + extra
    return f"{STATE_DELIM}\n{body}\n"


def count_tokens(text: str) -> int:
    """A conservative token estimate: whitespace words PLUS the punctuation
    attached to them.

    AUDIT FIX: `\S+` already consumes attached punctuation, so the `|[^\w\s]`
    branch was UNREACHABLE and the count was whitespace-tokens only — the
    docstring promised a conservative over-count and delivered an under-count,
    so assert_state_fits could admit an oversized state.
    """
    import re
    words = re.findall(r"\S+", text)
    punct = re.findall(r"[^\w\s]", text)
    return len(words) + len(punct)


def assert_state_fits(state: str) -> int:
    n = count_tokens(state)
    if n > STATE_TOKEN_LIMIT:
        raise ValueError(f"STATE_TOO_LARGE: {n} tokens > limit {STATE_TOKEN_LIMIT}")
    return n


# ---- session detection (the London window) ---------------------------------
def et_offset_hours(ts_ms: int) -> int:
    """US Eastern offset: -4 (EDT) Mar-Nov, -5 (EST) otherwise."""
    # AUDIT FIX: the coarse `3 <= month <= 11` treated ALL of March and November
    # as EDT, but US DST runs 2nd-Sun-March to 1st-Sun-November. Bars in early
    # March and early November were shifted by an hour and mislabelled.
    import datetime as dt
    d = dt.datetime.fromtimestamp(ts_ms / 1000, dt.timezone.utc)
    if d.month < 3 or d.month > 11:
        return -5
    if d.month == 3:                      # 2nd Sunday of March, 07:00 UTC
        first = dt.datetime(d.year, 3, 1, tzinfo=dt.timezone.utc)
        second_sun = 1 + (6 - first.weekday()) % 7 + 7
        start = dt.datetime(d.year, 3, second_sun, 7, tzinfo=dt.timezone.utc)
        return -4 if d >= start else -5
    if d.month == 11:                     # 1st Sunday of November, 06:00 UTC
        first = dt.datetime(d.year, 11, 1, tzinfo=dt.timezone.utc)
        first_sun = 1 + (6 - first.weekday()) % 7
        end = dt.datetime(d.year, 11, first_sun, 6, tzinfo=dt.timezone.utc)
        return -4 if d < end else -5
    return -4


def session_label(ts_ms: int) -> str:
    import datetime as dt
    off = et_offset_hours(ts_ms)
    et = dt.datetime.fromtimestamp(ts_ms / 1000, dt.timezone.utc) + dt.timedelta(hours=off)
    hhmm = et.strftime("%H:%M")
    if LONDON_OPEN_ET <= hhmm <= LONDON_CLOSE_ET: return f"LONDON {hhmm}"
    if "08:00" <= hhmm <= "11:00": return f"NY_AM {hhmm}"
    if "13:30" <= hhmm <= "16:00": return f"NY_PM {hhmm}"
    return f"OFF_SESSION {hhmm}"


def in_london(ts_ms: int) -> bool:
    return session_label(ts_ms).startswith("LONDON")
