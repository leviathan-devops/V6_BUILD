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


def g_rrr(t: TradeCandidate) -> GateResult:
    """G-RRR: the risk-reward floor. The single most load-bearing gate."""
    # FAIL-CLOSED (audit fix): a NaN rrr makes `nan < floor` False, so the
    # original form PASSED a corrupt value. Non-finite must reject.
    if not _finite(t.rrr):
        return _no("G-RRR_REJECT", f"rrr {t.rrr!r} is not a finite number", "G-RRR")
    if t.rrr < RRR_FLOOR:
        return _no("G-RRR_REJECT", f"rrr {t.rrr:.2f} < floor {RRR_FLOOR}", "G-RRR")
    return _ok("G-RRR_PASS", f"rrr {t.rrr:.2f} >= {RRR_FLOOR}", "G-RRR")


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
        if len(hhmm) == 5 and hhmm[2] == ":" and hhmm[:2].isdigit() and hhmm[3:].isdigit():
            # AUDIT FIX: the shape check accepted impossible times like 02:99,
            # which compared lexicographically INSIDE the London window.
            h, m = int(hhmm[:2]), int(hhmm[3:])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return hhmm
        return None                          # malformed ISO -> refuse, no guess
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
    """G-SL: the stop-loss envelope. A wide SL destroys the RRR at scale."""
    d = t.sl_distance_pips
    # FAIL-CLOSED (audit fix): `d > MAX` is False for NaN, and 0/negative were
    # never rejected. A missing or corrupt SL distance must REJECT.
    if not _finite(d):
        return _no("G-SL_REJECT", f"sl distance {d!r} is not a finite number", "G-SL")
    if d <= 0:
        return _no("G-SL_REJECT", f"sl distance {d:.4f}p is non-positive", "G-SL")
    if d > SL_MAX_PIPS:
        return _no("G-SL_REJECT", f"sl distance {d:.1f}p > envelope {SL_MAX_PIPS}p", "G-SL")
    return _ok("G-SL_PASS", f"sl distance {d:.1f}p within envelope", "G-SL")


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
