"""mpse/predicates.py — the 10 AT predicates + the 3-way trust engine.

MPSE law: mathematics is the spec, the code is the implementation, the tests
are the proof. Each predicate is a NAMED decision with an executable body and
a machine-readable verdict token — never a prose rule.

THE 3-WAY TRUST ENGINE: a predicate's verdict is trusted only when the three
independent witnesses agree:
  1. LIMITE  — the math model's own computation
  2. CODE    — the deterministic python shadow
  3. GEOMETRY— the structural consistency check (signs, ordering, magnitude)
When all three agree -> TRUSTED. When they disagree -> DIVERGENT (named).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

TRUSTED, DIVERGENT, INCONCLUSIVE = "TRUSTED", "DIVERGENT", "INCONCLUSIVE"

PIP = {"EUR/USD": 0.0001, "GBP/USD": 0.0001, "DXY": 0.01}
RRR_FLOOR = 2.5
SL_MAX_PIPS = 55.0


@dataclass(frozen=True)
class Verdict:
    name: str
    passed: bool
    token: str
    detail: str

    def __bool__(self) -> bool: return self.passed


def _v(name, ok, token, detail): return Verdict(name, ok, token, detail)


# ---- AT-01 .. AT-10 ---------------------------------------------------------
def at_01_rrr_floor(c) -> Verdict:
    ok = c["rrr"] >= RRR_FLOOR
    return _v("AT-01", ok, "AT01_PASS" if ok else "AT01_RRR_BELOW_FLOOR",
              f"rrr {c['rrr']:.3f} vs floor {RRR_FLOOR}")

def at_02_sl_envelope(c) -> Verdict:
    ok = c["sl_distance_pips"] <= SL_MAX_PIPS
    return _v("AT-02", ok, "AT02_PASS" if ok else "AT02_SL_OUTSIDE_ENVELOPE",
              f"sl {c['sl_distance_pips']:.2f}p vs max {SL_MAX_PIPS}p")

def at_03_direction_sign(c) -> Verdict:
    """Long: TP above entry, SL below. Short: the mirror. A wrong-signed
    geometry is a SIDE INVERSION — the V5 class the mutants target."""
    d, e, sl, tp = c["direction"], c["entry"], c["sl"], c["tp"]
    ok = (tp > e > sl) if d == "long" else (sl > e > tp)
    return _v("AT-03", ok, "AT03_PASS" if ok else "AT03_SIDE_INVERSION",
              f"{d}: e={e} sl={sl} tp={tp}")

def at_04_zone_positive(c) -> Verdict:
    ok = c["zone_width_pips"] > 0
    return _v("AT-04", ok, "AT04_PASS" if ok else "AT04_ZERO_ZONE",
              f"zone width {c['zone_width_pips']}")

def at_05_confidence_in_range(c) -> Verdict:
    ok = 0.0 <= c["confidence"] <= 1.0
    return _v("AT-05", ok, "AT05_PASS" if ok else "AT05_CONF_OUT_OF_RANGE",
              f"confidence {c['confidence']}")

def at_06_dual_consistency(c) -> Verdict:
    """|model - code| <= eps on the RRR path."""
    m, k = c.get("limite_rrr"), c["rrr"]
    if m is None:
        return _v("AT-06", False, "AT06_NO_MODEL_VALUE", "no Limite value to compare")
    delta = abs(m - k)
    ok = delta <= 0.02
    return _v("AT-06", ok, "AT06_PASS" if ok else "LIMITE_CODE_DIVERGENCE",
              f"|{m:.4f}-{k:.4f}|={delta:.4f} vs eps 0.02")

def at_07_pip_scale(c) -> Verdict:
    """The pair's pip scale must be the one its price magnitude implies —
    a DXY level treated as FX destroys every downstream pip count."""
    pair, entry = c["pair"], c["entry"]
    expect = 0.01 if entry > 10 else 0.0001
    ok = PIP.get(pair, 0.0001) == expect
    return _v("AT-07", ok, "AT07_PASS" if ok else "AT07_PIP_SCALE_MISMATCH",
              f"{pair} entry={entry} expects pip {expect}")

def at_08_monotone_levels(c) -> Verdict:
    """All three levels must be distinct (a collapsed level is a degenerate trade)."""
    ok = len({c["entry"], c["sl"], c["tp"]}) == 3
    return _v("AT-08", ok, "AT08_PASS" if ok else "AT08_COLLAPSED_LEVELS",
              f"distinct levels={len({c['entry'], c['sl'], c['tp']})}")

def at_09_rrr_recompute(c) -> Verdict:
    """The stated RRR must equal the geometry's RRR — a stated/derived mismatch
    is the single most dangerous silent-arithmetic defect."""
    pip = PIP.get(c["pair"], 0.0001)
    sl_d, tp_d = abs(c["entry"]-c["sl"])/pip, abs(c["tp"]-c["entry"])/pip
    if sl_d == 0:
        return _v("AT-09", False, "AT09_ZERO_SL", "SL distance 0 -> RRR undefined")
    recomputed = round(tp_d/sl_d, 4)
    ok = abs(recomputed - c["rrr"]) <= 0.02
    return _v("AT-09", ok, "AT09_PASS" if ok else "AT09_RRR_MISMATCH",
              f"stated {c['rrr']:.4f} vs recomputed {recomputed:.4f}")

def at_10_session_valid(c) -> Verdict:
    s = c.get("session_utc", "")
    ok = bool(s) and "02:00" <= s[-5:] <= "05:00"
    return _v("AT-10", ok, "AT10_PASS" if ok else "AT10_SESSION_INVALID",
              f"session {s[-5:] if s else '<none>'}")

PREDICATES = (at_01_rrr_floor, at_02_sl_envelope, at_03_direction_sign,
              at_04_zone_positive, at_05_confidence_in_range, at_06_dual_consistency,
              at_07_pip_scale, at_08_monotone_levels, at_09_rrr_recompute,
              at_10_session_valid)


# ---- THE 3-WAY TRUST ENGINE -------------------------------------------------
@dataclass(frozen=True)
class TrustVerdict:
    status: str
    predicate: str
    witnesses: dict[str, bool]
    detail: str


def geometry_witness(c) -> bool:
    """Structural consistency: signs, ordering, magnitude coherent."""
    d, e, sl, tp = c["direction"], c["entry"], c["sl"], c["tp"]
    sign_ok = (tp > e > sl) if d == "long" else (sl > e > tp)
    dist_ok = abs(e-sl) > 0 and abs(tp-e) > 0
    scale_ok = c["entry"] > 10 if c["pair"] == "DXY" else c["entry"] < 10
    return bool(sign_ok and dist_ok and scale_ok)


def trust(predicate: Callable, c: dict) -> TrustVerdict:
    """Adjudicate ONE predicate across the three witnesses."""
    v = predicate(c)
    code_ok = v.passed
    model_ok = (abs(c.get("limite_rrr", c["rrr"]) - c["rrr"]) <= 0.02
                if c.get("limite_rrr") is not None else False)
    geom_ok = geometry_witness(c)
    w = {"LIMITE": model_ok, "CODE": code_ok, "GEOMETRY": geom_ok}
    if all(w.values()):
        status = TRUSTED
    elif sum(w.values()) == 0:
        status = INCONCLUSIVE
    else:
        status = DIVERGENT
    return TrustVerdict(status, v.name, w, v.detail)


def trust_all(c: dict) -> list[TrustVerdict]:
    return [trust(p, c) for p in PREDICATES]
