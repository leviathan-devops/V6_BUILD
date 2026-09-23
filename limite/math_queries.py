"""limite/math_queries.py — the 6 math queries (L1-L6).

The Limite math engine computes HOW MUCH; the caller decides WHAT.
Every query is a (prompt_template, parser, python_shadow) triple:
  - the prompt goes to Limite at temperature=0
  - the python_shadow recomputes the same quantity in pure code
  - the dual-compute verifier compares the two

Source: Plutus_V6_Master_Blueprint_v1.md §2.3 (the 5 math calls) + the
pipeline's 6th (TP distance), giving L1..L6.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import re

PIP = {"EUR/USD": 0.0001, "GBP/USD": 0.0001, "DXY": 0.01}


@dataclass(frozen=True)
class MathQuery:
    id: str
    name: str
    template: str
    parse: Callable[[str], float]
    shadow: Callable[..., float]
    unit: str
    tolerance: float   # the dual-compute epsilon for this quantity


def _last_number(text: str) -> float:
    """Extract the final numeric literal from a Limite response."""
    nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not nums:
        raise ValueError(f"LIMITE_NO_NUMBER: no numeric literal in {text[:200]!r}")
    return float(nums[-1])


# ---- L1: zone width in pips -------------------------------------------------
def _shadow_zone_width(top: float, bottom: float, pair: str) -> float:
    return round(abs(top - bottom) / PIP[pair], 4)


# ---- L2: SL distance = zone width + buffer ----------------------------------
def _shadow_sl_distance(zone_width_pips: float, buffer_pips: float) -> float:
    return round(zone_width_pips + buffer_pips, 4)


# ---- L3: RRR = TP_dist / SL_dist --------------------------------------------
def _shadow_rrr(entry: float, sl: float, tp: float, pair: str) -> float:
    sl_d = abs(entry - sl) / PIP[pair]
    tp_d = abs(tp - entry) / PIP[pair]
    if sl_d == 0:
        raise ZeroDivisionError("RRR_SL_ZERO: SL distance is 0 pips")
    return round(tp_d / sl_d, 4)


# ---- L4: Fibonacci levels ---------------------------------------------------
FIB_RATIOS = (0.382, 0.5, 0.618, 0.786, 1.272, 1.618)


def _shadow_fib(swing_high: float, swing_low: float) -> dict[str, float]:
    rng = swing_high - swing_low
    return {f"{r}": round(swing_high - rng * r, 5) for r in FIB_RATIOS}


# ---- L5: commission impact --------------------------------------------------
def _shadow_commission(gross_pips: float, units: float, rate: float, pair: str) -> float:
    """Commission cost in pips. cost_$ = units * rate * 2 (round trip)."""
    pip_value_per_unit = PIP[pair]
    cost_pips = (units * rate * 2) / (units * pip_value_per_unit / PIP[pair]) if units else 0.0
    # the shadow is expressed in PIPS of the pair directly:
    cost_pips = (rate * 2) / PIP[pair]
    return round(gross_pips - cost_pips, 4)


# ---- L6: TP distance --------------------------------------------------------
def _shadow_tp_distance(entry: float, tp: float, pair: str) -> float:
    return round(abs(tp - entry) / PIP[pair], 4)


QUERIES: dict[str, MathQuery] = {
    "L1": MathQuery(
        id="L1", name="zone_width",
        template=("Zone top={top}, zone bottom={bottom}, pair={pair}, pip={pip}.\n"
                  "Compute the zone width in pips: |top - bottom| / pip.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number, shadow=_shadow_zone_width, unit="pips", tolerance=0.01),
    "L2": MathQuery(
        id="L2", name="sl_distance",
        template=("Zone width = {zone_width_pips} pips. Buffer = {buffer_pips} pips.\n"
                  "Compute the stop-loss distance = zone width + buffer.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number, shadow=_shadow_sl_distance, unit="pips", tolerance=0.01),
    "L3": MathQuery(
        id="L3", name="rrr",
        template=("Entry={entry}, SL={sl}, TP={tp}, pair={pair}, pip={pip}.\n"
                  "SL distance = |entry - sl| / pip.\n"
                  "TP distance = |tp - entry| / pip.\n"
                  "Compute RRR = TP distance / SL distance.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number, shadow=_shadow_rrr, unit="ratio", tolerance=0.02),
    "L4": MathQuery(
        id="L4", name="fib_levels",
        template=("Swing high wick={swing_high}, swing low reaction wick={swing_low}.\n"
                  "Compute the 0.618 retracement level = high - (high - low) * 0.618.\n"
                  "Give the final value to 5 decimals as: ANSWER: <value>"),
        parse=_last_number,
        shadow=lambda swing_high, swing_low: _shadow_fib(swing_high, swing_low)["0.618"],
        unit="price", tolerance=0.00002),
    "L5": MathQuery(
        id="L5", name="commission_impact",
        template=("Gross profit = {gross_pips} pips. Round-trip commission rate = {rate} "
                  "(i.e. {rate} of notional charged each way). pair={pair}, pip={pip}.\n"
                  "Commission cost in pips = (rate * 2) / pip.\n"
                  "Compute net profit = gross profit - commission cost.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number,
        shadow=lambda gross_pips, units, rate, pair: _shadow_commission(gross_pips, units, rate, pair),
        unit="pips", tolerance=0.05),
    "L6": MathQuery(
        id="L6", name="tp_distance",
        template=("Entry={entry}, TP={tp}, pair={pair}, pip={pip}.\n"
                  "Compute the TP distance in pips = |tp - entry| / pip.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number, shadow=_shadow_tp_distance, unit="pips", tolerance=0.01),
}


def render(query_id: str, **kw) -> str:
    q = QUERIES[query_id]
    kw.setdefault("pip", PIP.get(kw.get("pair", "EUR/USD"), 0.0001))
    return q.template.format(**kw)


def code_truth(query_id: str, **kw) -> float:
    """The python shadow — the deterministic ground truth for dual-compute."""
    return QUERIES[query_id].shadow(**kw)
