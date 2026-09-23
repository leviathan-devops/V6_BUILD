"""gates/gates.py — the 8 deterministic gates.

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
SL_BUFFER_PIPS = 3.0
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


def _ok(token: str, detail: str, gate: str) -> GateResult:
    return GateResult(True, token, detail, gate)


def _no(token: str, detail: str, gate: str) -> GateResult:
    return GateResult(False, token, detail, gate)


def g_rrr(t: TradeCandidate) -> GateResult:
    """G-RRR: the risk-reward floor. The single most load-bearing gate."""
    if t.rrr < RRR_FLOOR:
        return _no("G-RRR_REJECT", f"rrr {t.rrr:.2f} < floor {RRR_FLOOR}", "G-RRR")
    return _ok("G-RRR_PASS", f"rrr {t.rrr:.2f} >= {RRR_FLOOR}", "G-RRR")


SESSION_LABEL_RE = None   # set below (compiled once)


def _local_hhmm(session_utc: str) -> str | None:
    """Extract the LOCAL wall-clock HH:MM from an ISO timestamp.

    DEFECT FIXED (found by the adversarial probe 2026-09-23):
    the previous implementation used `s[-5:]`, which on
    "2026-07-06T14:30:00-04:00" returns "-04:00" -> "04:00" — i.e. it read the
    UTC OFFSET SUFFIX as if it were the local time, so EVERY EDT timestamp
    silently passed the London window. The local time is the component
    AFTER the 'T' and BEFORE the offset, and nothing else.
    """
    if not session_utc:
        return None
    # FORM 1: the state constructor's human label, e.g. "LONDON 02:00".
    # INTERFACE DEFECT FIXED (2026-09-23): the state constructor emits a LABEL
    # while this gate originally parsed only ISO timestamps, so every candidate
    # the circuit produced was rejected as "no parseable session timestamp".
    # The gate now accepts BOTH forms — the label and the ISO timestamp.
    m = re.search(r"\b(\d{2}:\d{2})\b", session_utc)
    if m and "T" not in session_utc:
        return m.group(1)
    # FORM 2: an ISO timestamp — the local time is between 'T' and the offset.
    if "T" in session_utc:
        after_t = session_utc.split("T", 1)[1]
        hhmm = after_t[:5]                  # "14:30" — never the offset tail
        if len(hhmm) == 5 and hhmm[2] == ":":
            return hhmm
    return m.group(1) if m else None


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
    if d > SL_MAX_PIPS:
        return _no("G-SL_REJECT", f"sl distance {d:.1f}p > envelope {SL_MAX_PIPS}p", "G-SL")
    return _ok("G-SL_PASS", f"sl distance {d:.1f}p within envelope", "G-SL")


def g_conf(t: TradeCandidate) -> GateResult:
    """G-CONF: the confidence floor. Below F = reject; F..C = flag for review."""
    if t.confidence < CONF_FLOOR:
        return _no("G-CONF_REJECT", f"confidence {t.confidence:.2f} < {CONF_FLOOR}", "G-CONF")
    return _ok("G-CONF_PASS", f"confidence {t.confidence:.2f} >= {CONF_FLOOR}", "G-CONF")


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
        return _no("LIMITE_CODE_DIVERGENCE", "no Limite RRR to verify against", "G-DUAL")
    delta = abs(t.limite_rrr - t.rrr)
    if delta > DUAL_EPS:
        return _no("LIMITE_CODE_DIVERGENCE",
                   f"|limite {t.limite_rrr:.4f} - code {t.rrr:.4f}| = {delta:.4f} > eps {DUAL_EPS}", "G-DUAL")
    return _ok("G-DUAL_PASS", f"|limite - code| = {delta:.4f} <= eps {DUAL_EPS}", "G-DUAL")


GATES = (g_rrr, g_session, g_sl, g_conf, g_cascade, g_chain, g_dedup, g_dual)
GATE_NAMES = ("G-RRR", "G-SESSION", "G-SL", "G-CONF", "G-CASCADE", "G-CHAIN", "G-DEDUP", "G-DUAL")


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
    """Run all 8 gates. ALL must pass — a single named rejection blocks the trade."""
    results = [g(t) for g in GATES]
    return GateVerdict(all(r.passed for r in results), results)
