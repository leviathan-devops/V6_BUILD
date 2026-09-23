"""gates/gates.py — the 9 deterministic gates.

THE LAW (pin LAWS): DECIDER SCORES, NEVER EDITS. Model outputs are INPUTS;
only this layer — pure Python if/else — accepts or rejects. No model call
appears in any path through this module.

Each gate returns GateResult(passed, token, detail). A rejected trade carries
its NAMED token so the TUI can show the operator exactly why.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

RRR_FLOOR = 2.5
SL_MAX_PIPS = 55.0
CONF_FLOOR = 0.50          # grade F
LONDON_SESSIONS = ("02:00", "05:00")   # ET, per the pin ADVERSARIAL LOOP item 4
# NOTE: no SL_BUFFER_PIPS constant — the buffer is not a gate; the zone width
# IS the SL distance (LAW 2), so a separate buffer would be a second authority.
DEDUP_WINDOW_MINUTES = 60
SL_BUFFER_MAX_PIPS = 5.0     # LAW 2: the SL is the zone edge + 0..5 pips
DUAL_EPS = 0.02            # |limite - code| epsilon on the RRR path


@dataclass(frozen=True)
class GateResult:
    passed: bool
    token: str
    detail: str
    gate: str = ""

    def __bool__(self) -> bool:
        return self.passed


@dataclass
class TradeCandidate:
    """The typed input the gates consume. No model appears here."""
    pair: str
    direction: str            # "long" | "short" | "no_trade"
    entry: float
    sl: float
    tp: float
    rrr: float
    zone_width_pips: float
    sl_distance_pips: float
    confidence: float
    session_utc: str = ""
    cascade_valid: bool = True
    chain_integrity: bool = True
    dedup_key: str = ""
    limite_rrr: float | None = None   # the model's own RRR, for G-DUAL
    recent_keys: list[str] = field(default_factory=list)


import math

# THE PIP AUTHORITY. `limite/math_queries.py` defines the single pip table for
# the whole circuit; the gate layer IMPORTS it rather than declaring a second
# one (two authorities for one quantity is the defect class the audit named).
import sys as _sys
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
if str(_HERE.parent / "limite") not in _sys.path:
    _sys.path.append(str(_HERE.parent / "limite"))
try:
    from math_queries import PIP as PIP
except Exception as _e:                      # a loud, named failure
    raise ImportError(
        f"GATES_NO_PIP_AUTHORITY: cannot import PIP from math_queries — {_e}. "
        f"The pip table is the circuit's single authority; the gate layer "
        f"refuses to run without it.") from _e

VALID_DIRECTIONS = ("long", "short")


def _finite(x) -> bool:
    """A value is usable only if it is a real, finite number.

    AUDIT FIX (round 6): `float(x)` coerced a NUMERIC STRING ("3.0") to a pass,
    but the gates then compared the ORIGINAL value — `"3.0" < 2.5` raised
    TypeError instead of failing closed. A string is not a number here.
    """
    if isinstance(x, bool) or isinstance(x, str):
        return False
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError, OverflowError):
        # AUDIT FIX: a huge int (10**1000) raised OverflowError out of _finite,
        # crashing evaluate() instead of failing closed.
        return False


def _geometry_ok(t: TradeCandidate) -> tuple[bool, str]:
    """Direction + price geometry must be coherent BEFORE any threshold gate.

    DEFECT FIXED (audit 2026-09-23): `direction`, `entry`, `sl`, `tp` were
    stored on the candidate but NO gate read them, so `evaluate()` returned
    accepted=True for `direction="no_trade"`, for an inverted SL/TP, and for a
    zero-width zone. This is the SIDE_INVERSION class the MPSE predicates
    caught while the gates let it through.
    """
    if t.direction not in VALID_DIRECTIONS:
        return False, f"direction {t.direction!r} is not one of {VALID_DIRECTIONS}"
    for name, v in (("entry", t.entry), ("sl", t.sl), ("tp", t.tp)):
        if not _finite(v):
            return False, f"{name}={v!r} is not a finite price"
    if t.direction == "long" and not (t.tp > t.entry > t.sl):
        return False, f"long geometry violated: need tp > entry > sl, got {t.tp} {t.entry} {t.sl}"
    if t.direction == "short" and not (t.sl > t.entry > t.tp):
        return False, f"short geometry violated: need sl > entry > tp, got {t.sl} {t.entry} {t.tp}"
    if len({t.entry, t.sl, t.tp}) != 3:
        return False, f"collapsed levels: {t.entry} {t.sl} {t.tp}"
    # AUDIT FIX: zone_width_pips was stored but NO gate read it, so a 0 /
    # negative / NaN zone width passed. mpse/predicates.py checks it, proving
    # the invariant matters — the gate layer must enforce it too.
    if not _finite(t.zone_width_pips) or t.zone_width_pips <= 0:
        return False, f"zone_width_pips={t.zone_width_pips!r} must be a positive finite number"
    return True, "geometry coherent"


def _ok(token: str, detail: str, gate: str) -> GateResult:
    return GateResult(True, token, detail, gate)


def _no(token: str, detail: str, gate: str) -> GateResult:
    return GateResult(False, token, detail, gate)


def recompute_rrr(t: TradeCandidate) -> float | None:
    """The RRR implied by the GEOMETRY. None when it cannot be computed.

    AUDIT FIX (round 9): G-RRR trusted `t.rrr` — a value the CALLER supplied.
    A candidate with coherent prices but an inflated `rrr` passed the floor
    check, which is a GATE BYPASS: the floor was being compared against a
    claim, not against the trade. The geometry is already validated as finite
    by G-GEOMETRY, so the RRR is recomputable and MUST be recomputed.
    """
    pip = PIP.get(t.pair)
    if pip is None:
        return None
    sl_d = abs(t.entry - t.sl) / pip
    tp_d = abs(t.tp - t.entry) / pip
    if sl_d <= 0:
        return None
    return round(tp_d / sl_d, 4)


def g_rrr(t: TradeCandidate) -> GateResult:
    """G-RRR: the risk-reward floor. The single most load-bearing gate.

    The floor is applied to the RRR the GEOMETRY implies, never to the value the
    caller passed. A stated RRR that disagrees with the geometry is itself a
    rejection (a stated/derived mismatch is the dangerous silent-arithmetic
    class the MPSE AT-09 predicate also checks).
    """
    # FAIL-CLOSED: a NaN rrr makes `nan < floor` False, so the original form
    # PASSED a corrupt value. Non-finite must reject.
    if not _finite(t.rrr):
        return _no("G-RRR_REJECT", f"rrr {t.rrr!r} is not a finite number", "G-RRR")
    # THE BYPASS FIX: compare the GEOMETRY's RRR, and treat a stated value that
    # disagrees with the geometry as its own rejection.
    derived = recompute_rrr(t)
    if derived is None:
        return _no("G-RRR_REJECT",
                   f"rrr cannot be derived from the geometry (pair={t.pair!r}, "
                   f"entry={t.entry} sl={t.sl} tp={t.tp})", "G-RRR")
    if abs(t.rrr - derived) > DUAL_EPS:
        return _no("G-RRR_REJECT",
                   f"stated rrr {t.rrr:.4f} disagrees with the geometry's "
                   f"{derived:.4f} (delta {abs(t.rrr-derived):.4f} > {DUAL_EPS})",
                   "G-RRR")
    if derived < RRR_FLOOR:
        return _no("G-RRR_REJECT", f"rrr {derived:.2f} < floor {RRR_FLOOR}", "G-RRR")
    return _ok("G-RRR_PASS", f"rrr {derived:.2f} >= {RRR_FLOOR} (recomputed)", "G-RRR")


def _local_hhmm(session_utc: str) -> str | None:
    """Extract the LOCAL wall-clock HH:MM from an ISO timestamp.

    DEFECT FIXED (found by the adversarial probe 2026-09-23):
    the previous implementation used `s[-5:]`, which on
    "2026-07-06T14:30:00-04:00" returns "-04:00" -> "04:00" — i.e. it read the
    UTC OFFSET SUFFIX as if it were the local time, so EVERY EDT timestamp
    silently passed the London window. The local time is the component
    AFTER the 'T' and BEFORE the offset, and nothing else.
    """
    # AUDIT FIX: a non-str session (an int/list from a corrupt candidate) raised
    # TypeError from `"T" in session_utc` and crashed evaluate(), breaking this
    # module's fail-closed law.
    if not isinstance(session_utc, str):
        return None
    if not session_utc:
        return None
    # FORM 1: the state constructor's human label, e.g. "LONDON 02:00".
    # INTERFACE DEFECT FIXED (2026-09-23): the state constructor emits a LABEL
    # while this gate originally parsed only ISO timestamps, so every candidate
    # the circuit produced was rejected as "no parseable session timestamp".
    # The gate now accepts BOTH forms — the label and the ISO timestamp.
    # FORM 2 FIRST (the more structured form): an ISO timestamp. The local time
    # is strictly between 'T' and the offset — never the offset tail.
    # AUDIT FIX: the previous version fell through to `m.group(1)`, the FIRST
    # HH:MM in the string, which on a malformed local time could pick the
    # offset. The fallback is removed; an unparseable stamp returns None.
    if "T" in session_utc:
        after_t = session_utc.split("T", 1)[1]
        hhmm = after_t[:5]
        if not (len(hhmm) == 5 and hhmm[2] == ":" and hhmm[:2].isdigit()
                and hhmm[3:].isdigit()):
            return None                      # malformed ISO -> refuse, no guess
        h, m = int(hhmm[:2]), int(hhmm[3:])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        # AUDIT FIX (round 9): the wall-clock was compared to the ET window
        # VERBATIM, so `2026-07-06T03:00:00Z` (23:00 ET — outside the window)
        # PASSED. A UTC/offset-bearing stamp is now CONVERTED to ET.
        off = re.search(r"(Z|[+-]\d{2}:?\d{2})\s*$", session_utc)
        if off:
            tok = off.group(1)
            if tok == "Z":
                off_min = 0
            else:
                sign = 1 if tok[0] == "+" else -1
                oh = int(tok[1:3])
                om = int(tok[-2:])
                off_min = sign * (oh * 60 + om)
            # ET is UTC-4 (EDT) / UTC-5 (EST); the caller's offset is known, so
            # the conversion is exact: ET = UTC + offset_local - offset_ET.
            # Without a date we cannot decide DST, so BOTH windows are tried and
            # the stamp is accepted only if it lands inside one of them.
            for et_off in (-240, -300):
                total = h * 60 + m - off_min + et_off
                total %= 1440
                cand = "%02d:%02d" % (total // 60, total % 60)
                if LONDON_SESSIONS[0] <= cand <= LONDON_SESSIONS[1]:
                    return cand
            # outside both -> return the EDT interpretation so the caller's
            # rejection detail names a concrete time
            total = (h * 60 + m - off_min - 240) % 1440
            return "%02d:%02d" % (total // 60, total % 60)
        return hhmm
    # FORM 1: the state constructor's label, e.g. "LONDON 02:00". Only a label
    # that STARTS with a session word is accepted (no arbitrary HH:MM scrape).
    m = re.match(r"^[A-Z_]+\s+(\d{2}:\d{2})$", session_utc.strip())
    if m:
        h, mi = int(m.group(1)[:2]), int(m.group(1)[3:])
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return m.group(1)
    return None


def g_session(t: TradeCandidate) -> GateResult:
    """G-SESSION: the London window (02:00-05:00 ET) is the only valid entry session."""
    hhmm = _local_hhmm(t.session_utc)
    if hhmm is None:
        return _no("G-SESSION_REJECT",
                   f"no parseable session timestamp on the candidate ({t.session_utc!r})",
                   "G-SESSION")
    if not (LONDON_SESSIONS[0] <= hhmm <= LONDON_SESSIONS[1]):
        return _no("G-SESSION_REJECT",
                   f"session {hhmm} outside London {LONDON_SESSIONS[0]}-{LONDON_SESSIONS[1]}",
                   "G-SESSION")
    return _ok("G-SESSION_PASS", f"session {hhmm} inside London window", "G-SESSION")


def g_sl(t: TradeCandidate) -> GateResult:
    """G-SL: the stop-loss envelope AND the LAW-2 identity.

    LAW 2 (the header): the SL sits at the structural invalidation point, so the
    SL DISTANCE is the ZONE WIDTH (plus the buffer). AUDIT FIX (round 9): the
    zone width and the SL distance were validated INDEPENDENTLY, so a candidate
    claiming zone=10p and sl_distance=50p passed both — two authorities for one
    quantity. They are now required to agree.
    """
    d = t.sl_distance_pips
    # FAIL-CLOSED (audit fix): `d > MAX` is False for NaN, and 0/negative were
    # never rejected. A missing or corrupt SL distance must REJECT.
    if not _finite(d):
        return _no("G-SL_REJECT", f"sl distance {d!r} is not a finite number", "G-SL")
    if d <= 0:
        return _no("G-SL_REJECT", f"sl distance {d:.4f}p is non-positive", "G-SL")
    if d > SL_MAX_PIPS:
        return _no("G-SL_REJECT", f"sl distance {d:.1f}p > envelope {SL_MAX_PIPS}p", "G-SL")
    # LAW 2: the SL distance must equal the zone width + the buffer (0..5 pips).
    # The buffer range is the operator's own documented 2-5 pip rule; 0 is
    # allowed for a zone whose edge IS the invalidation.
    diff = abs(d - t.zone_width_pips)
    if diff > SL_BUFFER_MAX_PIPS:
        return _no("G-SL_REJECT",
                   f"LAW-2 violation: sl distance {d:.2f}p vs zone width "
                   f"{t.zone_width_pips:.2f}p differ by {diff:.2f}p "
                   f"(buffer must be 0..{SL_BUFFER_MAX_PIPS}p)", "G-SL")
    return _ok("G-SL_PASS",
               f"sl {d:.1f}p = zone {t.zone_width_pips:.1f}p + buffer {diff:.1f}p, "
               f"within envelope", "G-SL")


def g_conf(t: TradeCandidate) -> GateResult:
    """G-CONF: the confidence floor. Below F = reject; F..C = flag for review."""
    c = t.confidence
    # FAIL-CLOSED + bounded (audit fix): NaN passed; there was no upper bound,
    # so confidence=5.0 or inf passed as "high confidence".
    if not _finite(c):
        return _no("G-CONF_REJECT", f"confidence {c!r} is not a finite number", "G-CONF")
    if not (0.0 <= c <= 1.0):
        return _no("G-CONF_REJECT", f"confidence {c} outside [0,1]", "G-CONF")
    if c < CONF_FLOOR:
        return _no("G-CONF_REJECT", f"confidence {c:.2f} < {CONF_FLOOR}", "G-CONF")
    return _ok("G-CONF_PASS", f"confidence {c:.2f} >= {CONF_FLOOR}", "G-CONF")


def g_cascade(t: TradeCandidate) -> GateResult:
    """G-CASCADE: the E2 cascade must be valid — E2 designates, E3 obeys."""
    if not t.cascade_valid:
        return _no("G-CASCADE_REJECT", "E2 cascade invalid — no designation for E3", "G-CASCADE")
    return _ok("G-CASCADE_PASS", "E2 cascade valid", "G-CASCADE")


def g_chain(t: TradeCandidate) -> GateResult:
    """G-CHAIN: the shape-chain integrity (sl-lmv / trade-dedup frozen semantics)."""
    if not t.chain_integrity:
        return _no("G-CHAIN_REJECT", "shape chain integrity violated", "G-CHAIN")
    return _ok("G-CHAIN_PASS", "shape chain intact", "G-CHAIN")


def g_dedup(t: TradeCandidate) -> GateResult:
    """G-DEDUP: no re-entry on the same key inside the dedup window."""
    if t.dedup_key and t.dedup_key in t.recent_keys:
        return _no("G-DEDUP_REJECT", f"dedup key {t.dedup_key} seen within {DEDUP_WINDOW_MINUTES}m", "G-DEDUP")
    return _ok("G-DEDUP_PASS", f"dedup key {t.dedup_key or '<none>'} is fresh", "G-DEDUP")


def g_dual(t: TradeCandidate) -> GateResult:
    """G-DUAL: LIMITE COMPUTES, CODE VERIFIES. |model - code| <= eps."""
    if t.limite_rrr is None:
        # The pin's law is "LIMITE COMPUTES, CODE VERIFIES": the python shadow is
        # the authority and the model is a CROSS-CHECK. With no independent value
        # there is nothing to verify, so the gate reports UNVERIFIED — it does
        # NOT fabricate a pass by comparing the code value to itself (which the
        # audit correctly called tautological) and it does NOT block, because a
        # cross-check is optional and its absence is not a contract violation.
        return _ok("G-DUAL_UNVERIFIED",
                   "no independent Limite value supplied — dual-compute NOT performed",
                   "G-DUAL")
    # FAIL-CLOSED (audit fix): NaN on either side made `delta > eps` False.
    if not _finite(t.limite_rrr) or not _finite(t.rrr):
        return _no("G-DUAL_REJECT",
                   f"non-finite pair: limite={t.limite_rrr!r} code={t.rrr!r}", "G-DUAL")
    delta = abs(t.limite_rrr - t.rrr)
    if delta > DUAL_EPS:
        return _no("G-DUAL_REJECT",
                   f"|limite {t.limite_rrr:.4f} - code {t.rrr:.4f}| = {delta:.4f} > eps {DUAL_EPS}", "G-DUAL")
    return _ok("G-DUAL_PASS", f"|limite - code| = {delta:.4f} <= eps {DUAL_EPS}", "G-DUAL")


def g_geometry(t: TradeCandidate) -> GateResult:
    """G-GEOMETRY: direction + price coherence. Runs FIRST (audit fix)."""
    ok, detail = _geometry_ok(t)
    return _ok("G-GEOMETRY_PASS", detail, "G-GEOMETRY") if ok else \
           _no("G-GEOMETRY_REJECT", detail, "G-GEOMETRY")


# G-GEOMETRY leads the chain: nothing downstream is meaningful on incoherent
# geometry, and it is the gate the audit proved was missing entirely.
GATES = (g_geometry, g_rrr, g_session, g_sl, g_conf, g_cascade, g_chain, g_dedup, g_dual)
GATE_NAMES = ("G-GEOMETRY", "G-RRR", "G-SESSION", "G-SL", "G-CONF",
              "G-CASCADE", "G-CHAIN", "G-DEDUP", "G-DUAL")


@dataclass(frozen=True)
class GateVerdict:
    accepted: bool
    results: list[GateResult]

    @property
    def rejections(self) -> list[GateResult]:
        return [r for r in self.results if not r.passed]

    @property
    def tokens(self) -> list[str]:
        return [r.token for r in self.results]


def evaluate(t: TradeCandidate) -> GateVerdict:
    """Run all 9 gates. ALL must pass — a single named rejection blocks the trade.

    (G-GEOMETRY leads the chain; it was added by the audit and the count in the
    earlier docstring said 8.)"""
    results = [g(t) for g in GATES]
    return GateVerdict(all(r.passed for r in results), results)
