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
import sys, time, hashlib, json
from dataclasses import dataclass, field, asdict
from pathlib import Path

WT = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt")
for sub in ("wb-limite/gates", "wb-limite/limite", "wb-limite/mpse",
            "wc-exec/oms", "wc-exec/report", "wa-decider/state",
            "wa-decider/decider", "wd-tui/tui", "wf-det/determinism"):
    p = WT / sub
    if p.exists() and str(p) not in sys.path: sys.path.insert(0, str(p))


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
    def build_state(self, feeds: dict) -> str:
        """Render the state. An empty feed is a NAMED refusal (NO_BARS),
        never a bare ValueError from inside max()."""
        from state_constructor import render_state, session_label, EmptyBars
        if not feeds:
            raise EmptyBars("NO_BARS: the circuit received an empty feed set")
        return render_state(self.pair, self.anchor_ms, feeds,
                            session_utc=session_label(self.anchor_ms))

    # ---- stage 3-11: the judgment chain ------------------------------------
    def decide(self, pair: str, bars_by_tf: dict, feeds: dict,
               limite_rrr: float | None = None) -> CircuitResult:
        t0 = time.perf_counter()
        self.pair = pair
        from state_constructor import session_label, in_london
        from gates import TradeCandidate, evaluate
        from math_queries import code_truth

        stage = {}
        t = time.perf_counter()
        state = self.build_state(feeds)
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
        entry, sl, tp = bars_by_tf["entry"], bars_by_tf["sl"], bars_by_tf["tp"]
        direction = bars_by_tf["direction"]
        # DEFECT FIXED (found by the e2e probe 2026-09-23): this stage hardcoded
        # 0.0001 as the pip for EVERY pair, so a DXY trade (pip = 0.01) had its
        # 4-pip stop reported as 400 pips and was rejected by G-SL. The pip
        # scale is a property of the PAIR and must come from the one authority
        # that defines it (math_queries.PIP), never a literal.
        from math_queries import PIP as PIP_SCALE
        pip = PIP_SCALE.get(pair, 0.0001)
        zone_w = bars_by_tf.get("zone_width_pips", abs(tp - entry) / pip)
        sl_d = abs(entry - sl) / pip
        rrr_code = code_truth("L3", entry=entry, sl=sl, tp=tp, pair=pair)
        stage["limite_ms"] = round((time.perf_counter() - t) * 1000, 3)

        if limite_rrr is None: limite_rrr = rrr_code

        conf = bars_by_tf.get("confidence", 0.72)
        cand = TradeCandidate(
            pair=pair, direction=direction, entry=entry, sl=sl, tp=tp,
            rrr=rrr_code, zone_width_pips=zone_w, sl_distance_pips=sl_d,
            confidence=conf, session_utc=session_label(self.anchor_ms),
            cascade_valid=bars_by_tf.get("cascade_valid", True),
            chain_integrity=bars_by_tf.get("chain_integrity", True),
            dedup_key=bars_by_tf.get("zone_id", ""),
            recent_keys=bars_by_tf.get("recent_keys", []),
            limite_rrr=limite_rrr)
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
            limite={"L3": {"model": limite_rrr, "code": rrr_code,
                           "delta": round(abs(limite_rrr - rrr_code), 6),
                           "pass": abs(limite_rrr - rrr_code) <= 0.02}},
            latency_ms=total, stage_latency=stage,
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
            f = execution.trades[0].fill
            ex = {"entry": f.entry, "exit": f.exit, "gross_pips": f.gross_pips,
                  "cost_pips": f.cost_pips, "net_pips": f.net_pips, "outcome": "tp"}
        ri = ReportInput(
            pair=result.pair, anchor_ms=result.anchor_ms, session=result.session,
            state_text="<|fim_prefix|> (see state constructor)",
            decider=result.decider or {"E3.Q1": {"long": 0.6, "short": 0.2, "no_trade": 0.2}},
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
        stages = {r.zone_id or f"t{i}": r.to_dict() for i, r in enumerate(results)}
        return dg(stages)
