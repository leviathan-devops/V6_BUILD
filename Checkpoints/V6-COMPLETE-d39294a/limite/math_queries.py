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


# AUDIT FIX: the first pattern was `-?\d+(?:\.\d+)?`, which SILENTLY TRUNCATED:
#   "ANSWER: 1.23e-4" -> 1.23     (drops the exponent: a 10000x error)
#   "ANSWER: .618"    -> 618      (the leading-dot form matched the digits only)
#   "ANSWER: -.5"     -> 5        (drops the sign)
# The pattern now accepts an optional sign, a leading dot, and an exponent.
ANSWER_RE = re.compile(
    r"ANSWER\s*:\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)", re.I)


def _last_number(text: str) -> float:
    """The value from the response's `ANSWER: <value>` tag.

    AUDIT FIX: the first version returned the LAST bare number anywhere in the
    response, so any trailing number (a unit, a parenthetical, a date, a
    reasoning aside) silently won — `ANSWER: 12.34 (~12.5 with spread)` parsed
    as 12.5. The ANSWER tag is the contract; parse THAT, and refuse if absent.
    """
    m = ANSWER_RE.search(text.replace(",", ""))
    if not m:
        raise ValueError(
            f"LIMITE_NO_ANSWER_TAG: no 'ANSWER: <value>' in {text[:200]!r}")
    return float(m.group(1))


# ---- L1: zone width in pips -------------------------------------------------
def _shadow_zone_width(top: float, bottom: float, pair: str) -> float:
    return round(abs(top - bottom) / pip_for(pair), 4)


# ---- L2: SL distance = zone width + buffer ----------------------------------
def _shadow_sl_distance(zone_width_pips: float, buffer_pips: float) -> float:
    return round(zone_width_pips + buffer_pips, 4)


# ---- L3: RRR = TP_dist / SL_dist --------------------------------------------
def _shadow_rrr(entry: float, sl: float, tp: float, pair: str) -> float:
    pip = pip_for(pair)
    sl_d = abs(entry - sl) / pip
    tp_d = abs(tp - entry) / pip
    # AUDIT FIX: an exact `== 0` check missed a NEAR-ZERO denominator, which
    # produced an RRR in the thousands that still passed dual-compute (both
    # sides agreed on the nonsense). A sub-pip SL is economically invalid.
    if sl_d < 0.1:
        raise ZeroDivisionError(
            f"RRR_SL_TOO_TIGHT: SL distance {sl_d:.6f} pips is below the 0.1-pip "
            f"minimum (a sub-pip stop is not a trade)")
    return round(tp_d / sl_d, 4)


# ---- L4: Fibonacci levels ---------------------------------------------------
FIB_RATIOS = (0.382, 0.5, 0.618, 0.786, 1.272, 1.618)


def _shadow_fib(swing_high: float, swing_low: float) -> dict[str, float]:
    rng = swing_high - swing_low
    return {f"{r}": round(swing_high - rng * r, 5) for r in FIB_RATIOS}


# ---- L5: commission impact --------------------------------------------------
def _shadow_commission(gross_pips: float, units: float, rate: float, pair: str) -> float:
    """`units` is retained for signature compatibility only: the pip cost
    (rate*2/pip) is units-independent, since units cancel in
    (units*rate*2) / (units*pip)."""
    """Commission cost in pips. cost_$ = units * rate * 2 (round trip)."""
    # AUDIT FIX: the first assignment was dead (immediately overwritten) and
    # made `units` look load-bearing when the pip-cost formula is
    # units-independent: cost_pips = (units*rate*2) / (units*pip) = rate*2/pip.
    cost_pips = (rate * 2) / pip_for(pair)
    return round(gross_pips - cost_pips, 4)


# ---- L6: TP distance --------------------------------------------------------
def _shadow_tp_distance(entry: float, tp: float, pair: str) -> float:
    return round(abs(tp - entry) / pip_for(pair), 4)


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
        # AUDIT FIX: the template never interpolates {units} and the pip-cost
        # formula is units-independent, so `units` is not a parameter here.
        shadow=lambda gross_pips, rate, pair: _shadow_commission(gross_pips, 0, rate, pair),
        unit="pips", tolerance=0.05),
    "L6": MathQuery(
        id="L6", name="tp_distance",
        template=("Entry={entry}, TP={tp}, pair={pair}, pip={pip}.\n"
                  "Compute the TP distance in pips = |tp - entry| / pip.\n"
                  "Give the final value to 4 decimals as: ANSWER: <value>"),
        parse=_last_number, shadow=_shadow_tp_distance, unit="pips", tolerance=0.01),
}


class UnknownPair(ValueError):
    """A pair with no declared pip scale. Loud, never defaulted."""


def pip_for(pair: str) -> float:
    """THE single pip authority. Every path resolves the pip through here.

    AUDIT FIX: render() used to default an unknown pair to 0.0001 while the
    shadows raised KeyError on the same input — the prompt and the python side
    could compute with DIFFERENT pip assumptions. One function, one answer.
    """
    if pair not in PIP:
        raise UnknownPair(f"UNKNOWN_PAIR: {pair!r} has no declared pip scale "
                          f"(known: {sorted(PIP)})")
    return PIP[pair]


def render(query_id: str, **kw) -> str:
    q = QUERIES[query_id]
    # AUDIT FIX: `kw.get("pair", "EUR/USD")` silently assumed FX scale for a
    # caller that forgot the pair, contradicting pip_for()'s loud UnknownPair.
    # The requirement is EXACTLY the queries whose template interpolates {pip}:
    # L2 (width + buffer, both already in pips) and L4 (a fib PRICE level) do
    # not convert a price to pips, so they legitimately carry no pair.
    if "pair" not in kw and "{pip}" in q.template:
        raise UnknownPair(
            f"MISSING_PAIR: query {query_id} needs its pair (its template "
            f"converts a price to pips; known: {sorted(PIP)})")
    # AUDIT FIX: the pip is ALWAYS the authority's value. A caller-supplied pip
    # was kept by setdefault, so the prompt could compute with pip=999 while the
    # shadow used the real one — a silent divergence.
    if "pip" in kw and abs(float(kw["pip"]) - pip_for(kw.get("pair", "EUR/USD"))) > 1e-12:
        raise ValueError(
            f"PIP_CONFLICT: caller passed pip={kw['pip']} but {kw.get('pair')} has "
            f"pip={pip_for(kw.get('pair', 'EUR/USD'))}")
    if "pair" in kw:
        kw["pip"] = pip_for(kw["pair"])
    return q.template.format(**kw)


def code_truth(query_id: str, **kw) -> float:
    """The python shadow — the deterministic ground truth for dual-compute.

    AUDIT FIX: the template and the shadow must accept the SAME kwargs. The
    templates interpolate {pip} while the shadows derive it from `pair`, so a
    caller passing both made the shadow raise TypeError. `pip` is now consumed
    by this wrapper (it is derived, not passed).
    """
    # AUDIT FIX: an explicitly passed pip is VALIDATED against the authority
    # before it is dropped, so a divergence cannot be silently discarded.
    # AUDIT FIX: the conflict check was skipped when `pair` was absent/unknown,
    # so a divergent pip was silently DISCARDED. Any explicit pip is now
    # validated, and its removal is reported.
    if "pip" in kw:
        pair = kw.get("pair")
        if pair is None:
            raise UnknownPair(
                "PIP_WITHOUT_PAIR: an explicit pip cannot be validated without "
                "the pair it belongs to")
        if abs(float(kw["pip"]) - pip_for(pair)) > 1e-12:
            raise ValueError(
                f"PIP_CONFLICT: passed pip={kw['pip']} vs authority "
                f"pip={pip_for(pair)} for {pair}")
        kw.pop("pip")
    return QUERIES[query_id].shadow(**kw)
