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
    bars, leaks, bad_ts, bad_ohlc = [], [], [], []
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
        # AUDIT FIX (round 12): an EXPLICIT ts of 0 / -1 / "0" passed the anchor
        # check and sorted to the FRONT of the state — re-introducing the exact
        # silent-epoch pollution the missing-key fix closed (a 0 sentinel is a
        # missing timestamp wearing a value). A real epoch is POSITIVE.
        if ts <= 0:
            bad_ts.append(f"bar ts={raw_ts!r} is not a positive epoch")
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
            bad_ohlc.append(f"bar ts={ts} has no {e}")
            continue
        except (TypeError, ValueError) as e:
            bad_ohlc.append(f"bar ts={ts} has a non-numeric OHLC — {e}")
            continue
        if not all(v == v and abs(v) != float("inf") for v in (o, h, l, cl)):
            bad_ohlc.append(f"bar ts={ts} has a non-finite OHLC")
            continue
        if h < l:
            bad_ohlc.append(f"bar ts={ts} high={h} < low={l}")
            continue
        bars.append(Bar(ts, o, h, l, cl, v))
    # AUDIT FIX (round 9): OHLC problems raised IMMEDIATELY inside the loop, so a
    # feed carrying a future bar AND a bad-OHLC bar reported the OHLC error — the
    # FUTURE_BAR_LEAK (the temporal law's named violation) was masked a SECOND
    # time. Every per-bar problem is now COLLECTED, and the precedence is:
    #   the LEAK (the law) > the timestamp > the OHLC (hygiene).
    if leaks:
        raise FutureBarLeak(
            f"FUTURE_BAR_LEAK: {len(leaks)} bar(s) past anchor {anchor_ms} "
            f"(first leaked ts={min(leaks)})"
            + (f"; {len(bad_ts)} bar(s) also lacked a timestamp" if bad_ts else ""))
    if bad_ts:
        raise ValueError(
            f"BAR_MISSING_TIMESTAMP: {len(bad_ts)} bar(s) carry no usable ts/time")
    if bad_ohlc:
        raise ValueError(
            f"BAR_BAD_OHLC: {len(bad_ohlc)} bar(s) — first: {bad_ohlc[0]}")
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


# THE BAR COUNT IS THE LATENCY LEVER. The blueprint (1.7) fixes the state's
# TIMEFRAMES ("30m/1H/4H bars") but NOT how many bars of each. The measured
# latency is ~0.127 ms per request token, so the state size IS the budget:
#   12 bars x 3 feeds -> 3047 tokens -> 505ms median  (over the 500ms budget)
#    8 bars x 3 feeds -> ~2400 tokens -> ~400ms       (comfortable margin)
# Eight recent bars per timeframe (24 across the three) is the context the
# decision needs; the ATR(14) and swing levels in the header carry the longer
# lookback. THE TRADE IS NAMED: context breadth for latency headroom.
BARS_PER_FEED = 8


def render_feed_block(pair: str, tf: str, bars: list[Bar], n: int = BARS_PER_FEED) -> str:
    """The compact OHLC block for one (pair, timeframe)."""
    recent = bars[-n:]
    pip = PIP.get(pair, 0.0001)
    # DEFECT FIXED (2026-09-24): the precision was HARDCODED at 5 decimals for
    # every pair, so a DXY bar (pip=0.01) rendered `100.93600` — three digits of
    # pure noise, on every number, in every bar, in every block. The precision
    # now follows the instrument's own pip scale: pip decimals + 1 (the
    # blueprint's own example renders EUR/USD at 5). A pip of 0.01 gives 3.
    _dec = max(2, len(str(pip).split(".")[-1]) + 1) if "." in str(pip) else 3
    lines = [f"{pair} {tf} ({len(bars)} bars, last {len(recent)} shown, pip={pip}):"]
    for b in recent:
        lines.append(f"  t={b.ts} O={b.open:.{_dec}f} H={b.high:.{_dec}f} "
                     f"L={b.low:.{_dec}f} C={b.close:.{_dec}f}")
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
        # AUDIT FIX (round 15): the render path ASSUMED ascending order and only
        # checked the anchor — and my round-14 edit silently no-op'd (its anchor
        # did not match this code), so nothing sorted. `atr()`,
        # `render_feed_block()` and `swing_levels()` all slice the TAIL, so an
        # unsorted or mutated feed silently described the WRONG era. The feed is
        # now sorted here (a total, stable fix) and each bar is revalidated, so
        # every downstream slice is chronological by construction.
        bars = sorted(bars, key=lambda b: b.ts)
        for b in bars:
            if b.ts <= 0:
                raise ValueError(
                    f"BAR_NON_POSITIVE_TS: {p} {tf} has ts={b.ts} — not a positive epoch")
            if not all(v == v and abs(v) != float("inf")
                       for v in (b.open, b.high, b.low, b.close)):
                raise ValueError(
                    f"BAR_NON_FINITE: {p} {tf} bar ts={b.ts} carries a non-finite OHLC")
            if b.high < b.low:
                raise ValueError(
                    f"BAR_INVERTED: {p} {tf} bar ts={b.ts} high={b.high} < low={b.low}")
        over = [b for b in bars if b.ts > anchor_ms]
        if over:
            raise FutureBarLeak(
                f"FUTURE_BAR_LEAK: {p} {tf} has {len(over)} bar(s) past anchor "
                f"{anchor_ms} at RENDER time (first ts={over[0].ts})")
        feeds[(p, tf)] = bars
    # THE STATE CONTRACT (blueprint 1.7, verbatim for CALL 1 / E1):
    #     "State: 30m/1H/4H bars + pair + session + DXY ctx"
    #
    # DEFECT FIXED (2026-09-24): the first version rendered EVERY feed in the
    # dict — all three pairs x FOUR timeframes (15m included) = 12 blocks, 9452
    # chars, ~9242 REAL tokens. That is 4x the specified state, it exceeds the
    # blueprint's own 8,192-token limit, and it is the direct cause of the
    # measured 1259ms decision latency (the budget is 500ms).
    #
    # The state is now the TARGET PAIR's 30m/1H/4H (the spec's three timeframes)
    # plus the DXY CONTEXT the spec names. A pair with no 30m/1H/4H falls back to
    # whatever it does have, so a thinner feed is still renderable.
    SPEC_TFS = ("30m", "1H", "4H")
    own = [(tf, feeds[(pair, tf)]) for tf in SPEC_TFS
           if (pair, tf) in feeds and feeds[(pair, tf)]]
    if not own:
        own = [(tf, b) for (p, tf), b in sorted(feeds.items())
               if p == pair and b]
    blocks = [render_feed_block(pair, tf, b) for tf, b in own]
    # "+ DXY ctx": the dollar index as CONTEXT when the target is not DXY itself.
    if pair != "DXY":
        for tf in SPEC_TFS:
            ctx = feeds.get(("DXY", tf))
            if ctx:
                blocks.append("DXY CONTEXT " + render_feed_block("DXY", tf, ctx))
                break
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
    doc = f"{STATE_DELIM}\n{body}\n"
    # AUDIT FIX (round 22): the limit was enforced only if the CALLER remembered
    # `assert_state_fits` — so an oversize state (many feeds, a large `extra`)
    # reached the Decider, and an oversize state is exactly what OOM'd the served
    # model and blew the latency budget. The guard is now at the return boundary,
    # which is the only place every caller passes through.
    assert_state_fits(doc)
    return doc


_TOKENIZER = None
_TOKENIZER_TRIED = False


def _tokenizer():
    """The DECIDER's real tokenizer, or None.

    DEFECT FIXED (2026-09-24): the guard below counted WHITESPACE WORDS, which
    undercounts numeric-dense text badly — the real state measured 2238 by
    estimate and **9242 by the served tokenizer (a 4.13x undershoot)**. The guard
    therefore PASSED a state 4x over the blueprint's documented 8,192-token
    limit, and that oversize is what OOM'd the server and blew the latency
    budget. An estimate that cannot see the real tokenizer cannot enforce a
    token limit.
    """
    global _TOKENIZER, _TOKENIZER_TRIED
    if _TOKENIZER_TRIED:
        return _TOKENIZER
    _last = None
    # AUDIT FIX (round 23): the failure was silent, and the fallback estimate is
    # documented in this very file as a ~4x UNDERCOUNT — so a missing tokenizer
    # silently defeated the 8192-token OOM guard. The reason is recorded.
    import glob, os
    cands = [os.environ.get("DECIDER_TOKENIZER"),
             *glob.glob("/home/leviathan/.cache/huggingface/hub/"
                        "models--Mapika--decider-2b/snapshots/*"),
             os.environ.get("DECIDER_BASE", "/home/leviathan/models/qwen3-0.6b-base")]
    try:
        from transformers import AutoTokenizer
        for c in cands:
            if not c:
                continue
            try:
                _TOKENIZER = AutoTokenizer.from_pretrained(c)
                # AUDIT FIX (round 23b, MY OWN REGRESSION): `_TOKENIZER_TRIED` was
                # set only on the FAILURE path, so the SUCCESS path returned
                # without caching — every count_tokens call re-ran
                # from_pretrained (~900ms), which took the offline golden week
                # from 5ms to 948ms and broke four tests. Marked here, and the
                # load happens exactly once.
                _TOKENIZER_TRIED = True
                return _TOKENIZER
            except Exception as e:                     # noqa: BLE001
                _last = f"{type(e).__name__}: {e}"
                continue
    except Exception as e:                                 # noqa: BLE001
        _last = f"{type(e).__name__}: {e}"
    _TOKENIZER_TRIED = True
    globals()["_TOKENIZER_FAIL"] = _last or "no candidate loaded"
    return None


def warm_tokenizer():
    """Load the real tokenizer NOW, so no measured path pays for it.

    Returns the tokenizer, or None when it is unavailable (the estimate then
    stands in — and `count_tokens` records why, per the round-23 fix).
    """
    return _tokenizer()


def count_tokens(text: str) -> int:
    r"""A conservative token estimate: whitespace words PLUS the punctuation
    attached to them.

    AUDIT FIX: `\S+` already consumes attached punctuation, so the `|[^\w\s]`
    branch was UNREACHABLE and the count was whitespace-tokens only — the
    docstring promised a conservative over-count and delivered an under-count,
    so assert_state_fits could admit an oversized state.
    """
    # THE REAL TOKENIZER FIRST; the estimate is only a fallback.
    _t = _tokenizer()
    if _t is not None:
        try:
            return len(_t.encode(text, add_special_tokens=False))
        except Exception:
            pass
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
