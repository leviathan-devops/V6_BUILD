"""integration/circuit.py — THE ASSEMBLED PLUTUS V6 CIRCUIT.

    market feed -> state -> Decider -> Limite -> gates -> OMS -> report

One entry point, every stage composed in the order the blueprint's
"complete V6 cycle" specifies. Nothing is stubbed: each stage is the real
module built by its worker.

THE STAGE CONTRACT (blueprint "complete V6 cycle"):
  1. Market feed delivers bars                              [0ms]
  2. State constructor renders bars -> Decider state text   [5ms]
  3. Decider Call 1 (E1): 5 questions                       [10ms GPU]
  4. Gate: if neutral -> "no_zone", wait
  5. Decider Call 2 (E2): 4 questions
  6. Gate: if cascade invalid -> halt
  7. Decider Call 3 (E3): 5 questions
  8. Limite: entry, SL, TP, RRR, fib                        [200ms]
  9. Gate: if rrr < 2.5 -> reject
 10. Decider Call 4 (PVE): 3 questions
 11. Gate: if confidence < B -> flag
 12. Output TradeDecision
 13. OMS: execute + measure
"""
from __future__ import annotations
import sys, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

# AUDIT FIX: the module resolved its siblings through HARDCODED worktree
# paths (`.wt/wb-limite/gates`, ...). Those paths are the pre-merge copies, so
# after the workers were merged this file imported the STALE worktree modules
# and the integrated fixes never took effect. The siblings are resolved
# relative to THIS file's own location, which is the integrated tree.
_HERE = Path(__file__).resolve().parent          # <root>/integration
_ROOT = _HERE.parent                             # <root>
for _sub in ("gates", "limite", "mpse", "oms", "report", "tui",
             "determinism", "memory", "state", "decider", "corpus"):
    _p = _ROOT / _sub
    if _p.exists() and str(_p) not in sys.path:
        sys.path.append(str(_p))                 # append: never shadow stdlib
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))


@dataclass
class CircuitResult:
    pair: str
    anchor_ms: int
    accepted: bool
    direction: str
    entry: float
    sl: float
    tp: float
    rrr: float
    confidence: float
    session: str
    zone_id: str
    gate_tokens: list
    gate_results: list
    decider: dict
    limite: dict
    latency_ms: float
    stage_latency: dict = field(default_factory=dict)
    rejections: list = field(default_factory=list)
    dual_verified: bool = False     # True only when an INDEPENDENT Limite value was checked

    def to_dict(self):
        d = asdict(self)
        d.pop("gate_results", None)     # objects -> already reduced to tokens
        return d


class Circuit:
    """The assembled circuit. Deterministic; no sampling anywhere."""

    def __init__(self, use_limite: bool = False, use_decider: bool = False,
                 anchor_ms: int = 1783317600000):
        self.use_limite = use_limite
        self.use_decider = use_decider
        self.anchor_ms = anchor_ms
        self._decider = None
        self._limite_ok = None

    # ---- stage 1-2: feed + state -------------------------------------------
    def build_state(self, feeds: dict, pair: str | None = None) -> str:
        """Render the state. An empty feed is a NAMED refusal (NO_BARS).

        AUDIT FIX: `pair` is an explicit parameter. The first version read
        `self.pair`, which __init__ never set, so a standalone build_state()
        raised AttributeError; and decide() assigned self.pair per call, so
        reusing one Circuit across pairs leaked state.
        """
        from state_constructor import render_state, session_label, EmptyBars
        target = pair or getattr(self, "pair", None)
        if not target:
            raise ValueError("NO_PAIR: build_state requires a pair")
        if not feeds:
            raise EmptyBars("NO_BARS: the circuit received an empty feed set")
        return render_state(target, self.anchor_ms, feeds,
                            session_utc=session_label(self.anchor_ms))

    # ---- stage 3-11: the judgment chain ------------------------------------
    def decide(self, pair: str, bars_by_tf: dict, feeds: dict,
               limite_rrr: float | None = None) -> CircuitResult:
        t0 = time.perf_counter()
        from state_constructor import session_label
        from gates import TradeCandidate, evaluate
        from math_queries import code_truth

        stage = {}
        t = time.perf_counter()
        state = self.build_state(feeds, pair)
        stage["state_ms"] = round((time.perf_counter() - t) * 1000, 3)

        # Decider (optional live model; the deterministic fallback is the
        # geometry-derived confidence, never a fabricated distribution)
        decider_out = {}
        t = time.perf_counter()
        if self.use_decider:
            decider_out = self._run_decider(state)
        stage["decider_ms"] = round((time.perf_counter() - t) * 1000, 3)

        # Limite: the geometry the gates consume
        t = time.perf_counter()
        # AUDIT FIX: required keys are validated with a NAMED refusal, not a
        # bare KeyError (the circuit's own contract uses named refusals).
        required = ("entry", "sl", "tp", "direction")
        missing = [k for k in required if k not in bars_by_tf]
        if missing:
            raise ValueError(f"MISSING_CANDIDATE_FIELDS: {missing} (need {list(required)})")
        entry, sl, tp = bars_by_tf["entry"], bars_by_tf["sl"], bars_by_tf["tp"]
        direction = bars_by_tf["direction"]
        # DEFECT FIXED (found by the e2e probe 2026-09-23): this stage hardcoded
        # 0.0001 as the pip for EVERY pair, so a DXY trade (pip = 0.01) had its
        # 4-pip stop reported as 400 pips and was rejected by G-SL. The pip
        # scale is a property of the PAIR and must come from the one authority
        # that defines it (math_queries.PIP), never a literal.
        from math_queries import PIP as PIP_SCALE
        if pair not in PIP_SCALE:
            # AUDIT FIX: an unknown pair must fail loudly. The first version
            # defaulted to 0.0001, silently mispricing DXY-style instruments.
            raise ValueError(f"UNKNOWN_PAIR: {pair!r} has no declared pip scale")
        pip = PIP_SCALE[pair]
        zone_w = bars_by_tf.get("zone_width_pips", abs(tp - entry) / pip)
        sl_d = abs(entry - sl) / pip
        rrr_code = code_truth("L3", entry=entry, sl=sl, tp=tp, pair=pair)
        stage["limite_ms"] = round((time.perf_counter() - t) * 1000, 3)

        # AUDIT FIX: defaulting limite_rrr to rrr_code made the dual-compute
        # check TAUTOLOGICAL (delta always 0, pass always True) while the report
        # claimed model-vs-code verification. When no independent Limite value is
        # supplied, the check is reported as UNVERIFIED, not as a pass.
        limite_verified = limite_rrr is not None

        # AUDIT FIX: these were fail-OPEN defaults (confidence 0.72, cascade and
        # chain defaulting to True), so a caller that omitted them PASSED every
        # gate. They are now REQUIRED, like entry/sl/tp/direction.
        for k in ("confidence", "cascade_valid", "chain_integrity"):
            if k not in bars_by_tf:
                raise ValueError(f"MISSING_CANDIDATE_FIELDS: {k!r} is required")
        conf = bars_by_tf["confidence"]
        cand = TradeCandidate(
            pair=pair, direction=direction, entry=entry, sl=sl, tp=tp,
            rrr=rrr_code, zone_width_pips=zone_w, sl_distance_pips=sl_d,
            confidence=conf, session_utc=session_label(self.anchor_ms),
            cascade_valid=bars_by_tf["cascade_valid"],
            chain_integrity=bars_by_tf["chain_integrity"],
            dedup_key=bars_by_tf.get("zone_id", ""),
            recent_keys=bars_by_tf.get("recent_keys", []),
            limite_rrr=limite_rrr if limite_verified else None)
        t = time.perf_counter()
        verdict = evaluate(cand)
        stage["gates_ms"] = round((time.perf_counter() - t) * 1000, 3)

        total = round((time.perf_counter() - t0) * 1000, 3)
        return CircuitResult(
            pair=pair, anchor_ms=self.anchor_ms, accepted=verdict.accepted,
            direction=direction, entry=entry, sl=sl, tp=tp, rrr=rrr_code,
            confidence=conf, session=session_label(self.anchor_ms),
            zone_id=bars_by_tf.get("zone_id", ""),
            gate_tokens=verdict.tokens,
            gate_results=[{"gate": r.gate, "passed": r.passed, "token": r.token,
                           "detail": r.detail} for r in verdict.results],
            decider=decider_out,
            limite={"L3": ({"model": limite_rrr, "code": rrr_code,
                            "delta": round(abs(limite_rrr - rrr_code), 6),
                            "pass": abs(limite_rrr - rrr_code) <= 0.02}
                           if limite_verified else
                           {"model": None, "code": rrr_code, "delta": None,
                            "pass": None, "note": "NO_INDEPENDENT_LIMITE_VALUE"})},
            latency_ms=total, stage_latency=stage, dual_verified=limite_verified,
            rejections=[{"token": r.token, "detail": r.detail} for r in verdict.rejections])

    def _run_decider(self, state: str) -> dict:
        if self._decider is None:
            from model import Decider
            from question_templates import CALLS
            self._decider = Decider()
            self._calls = CALLS
        out = {}
        for call, qs in self._calls.items():
            out.update(self._decider.decide_call(state, qs))
        return out

    # ---- stage 12-13: execute + measure ------------------------------------
    @staticmethod
    def execute(result: CircuitResult, commission_rate: float = 0.001,
                outcome: str = "tp"):
        from oms import simulate, TradeDecision
        if not result.accepted:
            return None
        d = TradeDecision(result.pair, result.direction, result.entry,
                          result.sl, result.tp, result.rrr, result.confidence,
                          zone_id=result.zone_id or "z")
        pf = simulate([d], commission_rate, {result.zone_id or "z": outcome})
        return pf

    @staticmethod
    def report(result: CircuitResult, execution=None) -> str:
        from report import ReportInput, render
        ex = {}
        if execution and execution.trades:
            tr = execution.trades[0]
            f = tr.fill
            # AUDIT FIX: the outcome comes from the fill, not a hardcoded "tp".
            ex = {"entry": f.entry, "exit": f.exit, "gross_pips": f.gross_pips,
                  "cost_pips": f.cost_pips, "net_pips": f.net_pips,
                  "outcome": tr.outcome}
        ri = ReportInput(
            pair=result.pair, anchor_ms=result.anchor_ms, session=result.session,
            state_text="<|fim_prefix|> (see state constructor)",
            # AUDIT FIX: an empty decider renders as empty. The first version
            # fabricated a distribution, which looks like model output.
            decider=result.decider or {},
            limite=result.limite, gates=result.gate_results,
            decision={"accepted": result.accepted, "direction": result.direction,
                      "reason": "all gates pass" if result.accepted
                                else "; ".join(t for t in result.gate_tokens if "REJECT" in t or "DIVERG" in t)},
            execution=ex)
        return render(ri)

    # ---- the run digest (determinism) --------------------------------------
    @staticmethod
    def digest(results: list[CircuitResult]) -> str:
        from determinism import digest as dg
        # AUDIT FIX: key on the INDEX as well as the zone_id, so two trades
        # sharing (or missing) a zone_id cannot silently overwrite each other.
        stages = {f"{i:04d}:{r.zone_id}": r.to_dict() for i, r in enumerate(results)}
        return dg(stages)
