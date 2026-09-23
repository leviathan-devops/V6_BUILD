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
import re
from dataclasses import dataclass
from typing import Callable

TRUSTED, DIVERGENT, INCONCLUSIVE = "TRUSTED", "DIVERGENT", "INCONCLUSIVE"
# AUDIT FIX: TRUSTED_REJECT was used as a status but never exported, so a
# consumer matching on the constants mishandled it. It is now part of the
# vocabulary: a unanimous FAIL is a TRUSTED rejection (the witnesses AGREE).
TRUSTED_REJECT = "TRUSTED_REJECT"
ALL_STATUSES = (TRUSTED, TRUSTED_REJECT, DIVERGENT, INCONCLUSIVE)

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


# AUDIT FIX: every predicate indexed c[...] unconditionally, so one missing key
# raised a raw KeyError out of trust()/trust_all() instead of yielding a failed
# verdict. The required keys are checked once, up front.
REQUIRED_KEYS = ("pair", "direction", "entry", "sl", "tp", "rrr",
                 "zone_width_pips", "sl_distance_pips", "confidence")


def _missing(c: dict) -> list:
    """Fields that are ABSENT **or** not usable numbers.

    AUDIT FIX (round 10): the first version checked only KEY PRESENCE, so a
    candidate carrying `rrr=None` or `entry="abc"` passed the guard and then
    raised TypeError out of the predicates (`c['rrr'] >= ...`, `abs(e-sl)/pip`)
    instead of yielding a fail-closed verdict. A guard that lets a bad value
    through is not a guard.
    """
    bad = []
    for k in REQUIRED_KEYS:
        if k not in c or c[k] is None:
            bad.append(k)
        elif k == "pair":
            # AUDIT FIX (round 12): `pair not in PIP` requires HASHING, so a list
            # or dict raised TypeError out of AT-07/AT-09/geometry_witness
            # instead of failing closed.
            if not isinstance(c[k], str):
                bad.append(k)
        elif k == "direction":
            if not isinstance(c[k], str):
                bad.append(k)
        else:
            v = c[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                bad.append(k)
            elif v != v or abs(v) == float("inf"):
                bad.append(k)
    return bad


def _guard(c: dict, name: str):
    """Return a MISSING-FIELDS verdict, or None when the candidate is complete.

    CRITICAL FIX (audit round 7): `_guard` returned `Verdict(passed=False)`, and
    `Verdict.__bool__` returns `passed` — so the guard's own return value was
    FALSY and every `if g: return g` never fired. The guard was dead code and
    direct predicate calls still raised KeyError. The guard's verdict is now
    returned as a TUPLE so truthiness cannot swallow it.
    """
    miss = _missing(c)
    if miss:
        return (_v(name, False, f"{name.replace('-','')}_MISSING_FIELDS",
                   f"candidate is missing {miss}"),)
    return None


# ---- AT-01 .. AT-10 ---------------------------------------------------------
def at_01_rrr_floor(c) -> Verdict:
    g = _guard(c, 'AT-01')
    if g: return g[0]
    ok = c["rrr"] >= RRR_FLOOR
    return _v("AT-01", ok, "AT01_PASS" if ok else "AT01_RRR_BELOW_FLOOR",
              f"rrr {c['rrr']:.3f} vs floor {RRR_FLOOR}")

def at_02_sl_envelope(c) -> Verdict:
    g = _guard(c, 'AT-02')
    if g: return g[0]
    ok = c["sl_distance_pips"] <= SL_MAX_PIPS
    return _v("AT-02", ok, "AT02_PASS" if ok else "AT02_SL_OUTSIDE_ENVELOPE",
              f"sl {c['sl_distance_pips']:.2f}p vs max {SL_MAX_PIPS}p")

def at_03_direction_sign(c) -> Verdict:
    g = _guard(c, 'AT-03')
    if g: return g[0]
    """Long: TP above entry, SL below. Short: the mirror. A wrong-signed
    geometry is a SIDE INVERSION — the V5 class the mutants target."""
    d, e, sl, tp = c["direction"], c["entry"], c["sl"], c["tp"]
    # AUDIT FIX: an invalid direction was silently treated as short, so a typo
    # could PASS. Validate membership.
    if d not in ("long", "short"):
        return _v("AT-03", False, "AT03_INVALID_DIRECTION",
                  f"direction {d!r} is not one of ('long','short')")
    ok = (tp > e > sl) if d == "long" else (sl > e > tp)
    return _v("AT-03", ok, "AT03_PASS" if ok else "AT03_SIDE_INVERSION",
              f"{d}: e={e} sl={sl} tp={tp}")

def at_04_zone_positive(c) -> Verdict:
    g = _guard(c, 'AT-04')
    if g: return g[0]
    ok = c["zone_width_pips"] > 0
    return _v("AT-04", ok, "AT04_PASS" if ok else "AT04_ZERO_ZONE",
              f"zone width {c['zone_width_pips']}")

def at_05_confidence_in_range(c) -> Verdict:
    g = _guard(c, 'AT-05')
    if g: return g[0]
    ok = 0.0 <= c["confidence"] <= 1.0
    return _v("AT-05", ok, "AT05_PASS" if ok else "AT05_CONF_OUT_OF_RANGE",
              f"confidence {c['confidence']}")

def at_06_dual_consistency(c) -> Verdict:
    g = _guard(c, 'AT-06')
    if g: return g[0]
    """|model - code| <= eps on the RRR path."""
    m, k = c.get("limite_rrr"), c["rrr"]
    # AUDIT FIX (round 11): only None was handled, so a non-numeric `limite_rrr`
    # ('abc', a bool, a list) raised TypeError out of `abs(m - k)` instead of
    # yielding a fail-closed verdict — and NaN silently produced a meaningless
    # delta (NaN <= 0.02 is False, i.e. a "divergence" from nothing).
    if m is None:
        return _v("AT-06", False, "AT06_NO_MODEL_VALUE", "no Limite value to compare")
    if isinstance(m, bool) or not isinstance(m, (int, float)) or m != m \
            or abs(m) == float("inf"):
        return _v("AT-06", False, "AT06_NO_MODEL_VALUE",
                  f"limite_rrr is not a usable number: {m!r}")
    delta = abs(m - k)
    ok = delta <= 0.02
    return _v("AT-06", ok, "AT06_PASS" if ok else "LIMITE_CODE_DIVERGENCE",
              f"|{m:.4f}-{k:.4f}|={delta:.4f} vs eps 0.02")

def at_07_pip_scale(c) -> Verdict:
    g = _guard(c, 'AT-07')
    if g: return g[0]
    """The pair's pip scale must be the one its price magnitude implies —
    a DXY level treated as FX destroys every downstream pip count."""
    pair, entry = c["pair"], c["entry"]
    expect = 0.01 if entry > 10 else 0.0001
    # AUDIT FIX: PIP.get(pair, 0.0001) FAILED OPEN — an unconfigured pair was
    # assumed to be FX scale and could pass. An unknown pair is now a failure.
    if pair not in PIP:
        return _v("AT-07", False, "AT07_UNKNOWN_PAIR",
                  f"pair {pair!r} has no declared pip scale")
    ok = PIP[pair] == expect
    return _v("AT-07", ok, "AT07_PASS" if ok else "AT07_PIP_SCALE_MISMATCH",
              f"{pair} entry={entry} expects pip {expect}")

def at_08_monotone_levels(c) -> Verdict:
    g = _guard(c, 'AT-08')
    if g: return g[0]
    """All three levels must be distinct (a collapsed level is a degenerate trade)."""
    ok = len({c["entry"], c["sl"], c["tp"]}) == 3
    return _v("AT-08", ok, "AT08_PASS" if ok else "AT08_COLLAPSED_LEVELS",
              f"distinct levels={len({c['entry'], c['sl'], c['tp']})}")

def at_09_rrr_recompute(c) -> Verdict:
    g = _guard(c, 'AT-09')
    if g: return g[0]
    """The stated RRR must equal the geometry's RRR — a stated/derived mismatch
    is the single most dangerous silent-arithmetic defect."""
    if c["pair"] not in PIP:
        return _v("AT-09", False, "AT09_UNKNOWN_PAIR",
                  f"pair {c['pair']!r} has no declared pip scale")
    pip = PIP[c["pair"]]
    sl_d, tp_d = abs(c["entry"]-c["sl"])/pip, abs(c["tp"]-c["entry"])/pip
    if sl_d == 0:
        return _v("AT-09", False, "AT09_ZERO_SL", "SL distance 0 -> RRR undefined")
    recomputed = round(tp_d/sl_d, 4)
    ok = abs(recomputed - c["rrr"]) <= 0.02
    return _v("AT-09", ok, "AT09_PASS" if ok else "AT09_RRR_MISMATCH",
              f"stated {c['rrr']:.4f} vs recomputed {recomputed:.4f}")

def _session_hhmm(s: str):
    """(hour, minute) from a session stamp, or None. Handles a bare `HH:MM`, a
    label carrying one (`LONDON 02:00`), an ISO stamp (`...T02:30:00-04:00`) and
    an unpadded hour (`3:00`) — compared NUMERICALLY, never as strings."""
    m = re.search(r"(\d{1,2}):(\d{2})(?::\d{2})?", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return None
    return (h, mi)


def at_10_session_valid(c) -> Verdict:
    g = _guard(c, 'AT-10')
    if g: return g[0]
    s = c.get("session_utc", "")
    # AUDIT FIX (round 12): the round-11 edit targeted `c.get("session_utc")` but
    # the code reads `c.get("session_utc", "")`, so the replace MISSED and a
    # truthy non-string (int/list/dict) still crashed on `s[-5:]`. A missing or
    # non-string session is a fail-closed verdict.
    if not isinstance(s, str):
        return _v("AT-10", False, "AT10_SESSION_INVALID",
                  f"session_utc is not a string: {type(s).__name__}")
    hhmm = _session_hhmm(s)
    # AUDIT FIX (round 13): `s[-5:]` assumed exactly a zero-padded `HH:MM` tail.
    # `02:00:00` sliced to `00:00` (a wrong FAIL), `3:00` compared
    # LEXICOGRAPHICALLY ('3:00' > '05:00'), and an ISO stamp with a zone sliced
    # to garbage. The time is now PARSED and compared NUMERICALLY.
    if hhmm is None:
        return _v("AT-10", False, "AT10_SESSION_INVALID",
                  f"session {s!r} carries no HH:MM")
    ok = (2, 0) <= hhmm <= (5, 0)
    return _v("AT-10", ok, "AT10_PASS" if ok else "AT10_SESSION_INVALID",
              f"session {hhmm[0]:02d}:{hhmm[1]:02d}")

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
    """Structural consistency: signs, ordering, magnitude coherent.

    AUDIT FIX: an invalid direction was silently treated as short. Validate.
    """
    d = c.get("direction")
    if d not in ("long", "short"):
        return False
    # AUDIT FIX (round 15): the witness indexed entry/sl/tp directly, so a
    # DIRECT call (not via _guard) raised KeyError/TypeError instead of returning
    # the fail-closed False the module's contract promises. `pair` also needs a
    # hashable check before `not in PIP`.
    try:
        e, sl, tp = c["entry"], c["sl"], c["tp"]
    except (KeyError, TypeError):
        return False
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and v == v and abs(v) != float("inf") for v in (e, sl, tp)):
        return False
    if not isinstance(c.get("pair"), str):
        return False
    sign_ok = (tp > e > sl) if d == "long" else (sl > e > tp)
    dist_ok = abs(e-sl) > 0 and abs(tp-e) > 0
    # AUDIT FIX (round 9): an UNKNOWN pair fell into the `else` branch and got
    # scale_ok=True — FAIL OPEN, undoing AT-07's fail-closed fix. The pip scale
    # comes from the single authority; an unknown pair is not a pass.
    if c.get("pair") not in PIP:
        return False
    pip = PIP[c["pair"]]
    scale_ok = abs(e - round(e / pip) * pip) < pip / 2      # a whole number of pips
    return bool(sign_ok and dist_ok and scale_ok)


# THE WITNESS PANEL — which INDEPENDENT witnesses corroborate each predicate.
#
# AUDIT FIX (round 13): the previous single-subject map made the documented
# "three-witness panel" UNREACHABLE. Every predicate had a subject, so the
# `subject is None` branch (which drew all three) never fired; a CODE-subject
# predicate drew ONE vote and a LIMITE/GEOMETRY one drew TWO. The docstring
# described a panel the code could not build.
#
# The panel is now the predicate's own CODE verdict PLUS every witness that
# BEARS on its subject — 2 or 3 votes, and the two 1-witness predicates are
# named as such rather than implied. The CODE vote is always present; the
# LIMITE vote is the independent model RRR; the GEOMETRY vote is the
# sign/scale witness.
# A witness is listed ONLY when it BEARS ON THE PREDICATE'S OWN QUANTITY.
# The geometry witness tests the sign/scale of entry/sl/tp — it says nothing
# about the zone width, the SL envelope, or the confidence range, so it ABSTAINS
# there. Listing it anyway would manufacture a disagreement (measured: AT-04
# flipped from TRUSTED_REJECT to DIVERGENT purely from an irrelevant vote).
PREDICATE_WITNESSES = {
    "AT-01": ("LIMITE",),              # the floor is a claim ABOUT the model RRR
    "AT-02": (),                       # the SL envelope has no second source
    "AT-03": ("GEOMETRY",),            # side inversion IS the geometry sign
    "AT-04": (),                       # zone width has no second source
    "AT-05": (),                       # the confidence range has no second source
    "AT-06": ("LIMITE",),              # dual consistency IS the model-vs-code
    "AT-07": ("GEOMETRY",),            # the pip scale IS the geometry scale
    "AT-08": ("GEOMETRY",),            # monotone levels IS the geometry sign
    "AT-09": ("LIMITE", "GEOMETRY"),   # the RRR recompute is BOTH
    "AT-10": (),                       # the session window has no second source
}


def trust(predicate: Callable, c: dict) -> TrustVerdict:
    """AUDIT FIX: a candidate missing a required key now yields an INCONCLUSIVE
    verdict naming the field, instead of raising KeyError out of the caller."""
    miss = _missing(c)
    if miss:
        return TrustVerdict("INCONCLUSIVE", getattr(predicate, "__name__", "?"),
                            {}, f"candidate is missing {miss}")
    """Adjudicate ONE predicate across the three witnesses.

    AUDIT FIX: the LIMITE and GEOMETRY witnesses were computed identically for
    EVERY predicate (always the RRR delta and always the geometry), so a
    non-RRR predicate like AT-04 (zone width) spuriously reported DIVERGENT
    whenever the RRR delta happened to be non-zero. A witness now VOTES only
    when it bears on the predicate's subject; otherwise it ABSTAINS (None),
    and abstention is not counted as agreement or disagreement.
    """
    v = predicate(c)
    code_ok = v.passed
    witnesses = PREDICATE_WITNESSES.get(v.name, ("LIMITE", "GEOMETRY"))
    votes = {"CODE": code_ok}
    if "LIMITE" in witnesses:
        # AUDIT FIX (round 11): `limite_rrr` bypassed _missing's type guard (it is
        # not a REQUIRED_KEY), so a string/bool raised TypeError out of `abs()`.
        _m = c.get("limite_rrr")
        votes["LIMITE"] = (abs(_m - c["rrr"]) <= 0.02
                           if isinstance(_m, (int, float)) and not isinstance(_m, bool)
                           and _m == _m and abs(_m) != float("inf") else None)
    if "GEOMETRY" in witnesses:
        votes["GEOMETRY"] = geometry_witness(c)
    voting = [x for x in votes.values() if x is not None]
    # AUDIT FIX (round 6): the PASS path required a FULL panel while the FAIL
    # path did not, so an abstained witness gave TRUSTED_REJECT on a failure but
    # INCONCLUSIVE on a pass. Abstention is now symmetric: any abstention means
    # the panel is incomplete and the verdict is INCONCLUSIVE either way.
    if not voting:
        status = INCONCLUSIVE
    elif len(voting) < len(votes):
        status = INCONCLUSIVE
    elif all(voting):
        status = TRUSTED
    elif not any(voting):
        # unanimous FAIL: the witnesses AGREE that the predicate fails. That is
        # a TRUSTED rejection, not an inconclusive one (audit fix: the first
        # version classified it INCONCLUSIVE, losing the distinction).
        status = TRUSTED_REJECT
    else:
        status = DIVERGENT
    return TrustVerdict(status, v.name, votes, v.detail)


def trust_all(c: dict) -> list[TrustVerdict]:
    return [trust(p, c) for p in PREDICATES]
