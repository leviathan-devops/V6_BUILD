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
    bars, leaks = [], []
    for r in raw:
        ts = int(r.get("ts") or r.get("time") or 0)
        if ts > anchor_ms:
            leaks.append(ts)
            continue
        bars.append(Bar(ts, float(r["open"]), float(r["high"]),
                        float(r["low"]), float(r["close"]),
                        float(r.get("volume", 0.0))))
    if leaks:
        raise FutureBarLeak(
            f"FUTURE_BAR_LEAK: {len(leaks)} bar(s) past anchor {anchor_ms} "
            f"(first leaked ts={min(leaks)})")
    return sorted(bars, key=lambda b: b.ts)


def atr(bars: list[Bar], period: int = 14) -> float:
    if len(bars) < 2: return 0.0
    trs = [abs(bars[i].high - bars[i].low) for i in range(1, min(len(bars), period + 1))]
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
    """Render the full Decider state document."""
    blocks = []
    for (p, tf), bars in sorted(feeds.items()):
        if not bars: continue
        blocks.append(render_feed_block(p, tf, bars))
    main = feeds.get((pair, "30m")) or feeds.get((pair, "1H")) or []
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
    """A conservative token estimate (whitespace + punctuation split)."""
    import re
    return len(re.findall(r"\S+|[^\w\s]", text))


def assert_state_fits(state: str) -> int:
    n = count_tokens(state)
    if n > STATE_TOKEN_LIMIT:
        raise ValueError(f"STATE_TOO_LARGE: {n} tokens > limit {STATE_TOKEN_LIMIT}")
    return n


# ---- session detection (the London window) ---------------------------------
def et_offset_hours(ts_ms: int) -> int:
    """US Eastern offset: -4 (EDT) Mar-Nov, -5 (EST) otherwise."""
    import datetime as dt
    d = dt.datetime.fromtimestamp(ts_ms / 1000, dt.timezone.utc)
    return -4 if 3 <= d.month <= 11 else -5


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
