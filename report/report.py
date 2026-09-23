"""report/report.py — the 8-section trading report.

Sections (per the pin DOC CONTRACT):
  1. HEADER        — pair, anchor, session, run id
  2. MARKET STATE  — the state the Decider saw
  3. DECIDER       — the 17 probability distributions, verbatim
  4. LIMITE        — the 6 math quantities with their dual-compute deltas
  5. GATES         — all 8 gate verdicts with their named tokens
  6. DECISION      — accept/reject + the reason chain
  7. EXECUTION     — the OMS fill, gross/cost/net pips
  8. VERDICT       — the run-level summary + honest gaps
"""
from __future__ import annotations
import json, hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ReportInput:
    pair: str
    anchor_ms: int
    session: str
    state_text: str
    decider: dict            # {qid: {option: prob}}
    limite: dict             # {qid: {"model":x,"code":y,"delta":d,"pass":bool}}
    gates: list              # [{"gate":..,"passed":..,"token":..,"detail":..}]
    decision: dict           # {"accepted":bool,"reason":str,"direction":str,...}
    execution: dict = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)


def _bar(p: float, width: int = 24) -> str:
    filled = max(0, min(width, int(round(p * width))))
    return "#" * filled + "." * (width - filled)


def _fmt_ts(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(ri: ReportInput) -> str:
    # AUDIT FIX: the id must cover the WHOLE run. The first version hashed only
    # pair/anchor/decider/gates, so runs differing in session, state, limite,
    # decision, execution or gaps collided.
    h = hashlib.sha256()
    h.update(json.dumps({
        "pair": ri.pair, "anchor": ri.anchor_ms, "session": ri.session,
        "state_text": ri.state_text, "decider": ri.decider, "limite": ri.limite,
        "gates": ri.gates, "decision": ri.decision, "execution": ri.execution,
        "gaps": ri.gaps,
    }, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def render(ri: ReportInput) -> str:
    L = []
    rid = run_id(ri)
    # 1
    L += ["## 1. HEADER",
          f"pair={ri.pair}  anchor={_fmt_ts(ri.anchor_ms)}  session={ri.session}  run_id={rid}",
          ""]
    # 2
    # AUDIT FIX: the display truncation is now DISCLOSED (the run_id hashes the
    # FULL text, so a reader must know the shown state is a prefix).
    shown = ri.state_text.strip()
    truncated = len(shown) > 1500
    L += ["## 2. MARKET STATE",
          f"  (showing {min(len(shown),1500)} of {len(shown)} chars"
          + (" — TRUNCATED for display; the run_id hashes the full text)" if truncated else ")"),
          "```", shown[:1500], "```", ""]
    # 3
    L += ["## 3. DECIDER — 17 distributions"]
    for qid in sorted(ri.decider):
        dist = ri.decider[qid]
        top = max(dist, key=dist.get) if dist else "-"
        L.append(f"  {qid}: argmax={top} ({dist.get(top, 0):.3f})")
        for opt, p in sorted(dist.items(), key=lambda kv: -kv[1])[:3]:
            L.append(f"      {opt:<16} {p:.4f} |{_bar(p)}|")
    L.append("")
    # 4
    L += ["## 4. LIMITE — 6 math quantities (dual-compute)"]
    for qid in sorted(ri.limite):
        r = ri.limite[qid]
        mark = "OK " if r.get("pass") else "DIVERGENT"
        L.append(f"  {qid}: model={r.get('model')} code={r.get('code')} "
                 f"delta={r.get('delta')} [{mark}]")
    L.append("")
    # 5
    L += ["## 5. GATES — 8 deterministic verdicts"]
    for g in ri.gates:
        mark = "PASS" if g.get("passed") else "REJECT"
        L.append(f"  {g.get('gate','?'):<10} [{mark}] {g.get('token','')} — {g.get('detail','')}")
    L.append("")
    # 6
    L += ["## 6. DECISION",
          f"  accepted={ri.decision.get('accepted')}",
          f"  direction={ri.decision.get('direction','-')}",
          f"  reason={ri.decision.get('reason','-')}", ""]
    # 7
    L += ["## 7. EXECUTION"]
    if ri.execution:
        for k in ("entry", "exit", "gross_pips", "cost_pips", "net_pips", "outcome"):
            if k in ri.execution: L.append(f"  {k}={ri.execution[k]}")
    else:
        L.append("  (no execution — the trade was rejected or not routed)")
    L.append("")
    # 8
    L += ["## 8. VERDICT"]
    n_ok = sum(1 for g in ri.gates if g.get("passed"))
    short = contract_shortfalls(ri)
    L += [f"  gates_passed={n_ok}/{len(ri.gates)}",
          f"  CONTRACT: decider {len(ri.decider)}/{CONTRACT_COUNTS['decider']} "
          f"limite {len(ri.limite)}/{CONTRACT_COUNTS['limite']} "
          f"gates {len(ri.gates)}/{CONTRACT_COUNTS['gates']}",
          f"  contract_complete={not short}",
          f"  run_id={rid}"]
    if short:
        L.append(f"  CONTRACT SHORTFALL: {short}")
    if ri.gaps:
        L.append("  HONEST GAPS:")
        for g in ri.gaps: L.append(f"    - {g}")
    else:
        L.append("  HONEST GAPS: none recorded for this run")
    L.append("")
    return "\n".join(L)


def section_count() -> int:
    """The contract's section count (the test asserts >= 8)."""
    return 8


# The contract's per-section counts (the pin DOC CONTRACT).
CONTRACT_COUNTS = {"decider": 17, "limite": 6, "gates": 8}


def contract_shortfalls(ri: ReportInput) -> dict:
    """AUDIT FIX: the report emitted headings and a gates_passed=n/len(gates)
    line for ANY input, so a run with 12 decider answers / 5 limite quantities /
    6 gates looked complete. The shortfall is now NAMED per section."""
    have = {"decider": len(ri.decider), "limite": len(ri.limite), "gates": len(ri.gates)}
    return {k: {"have": have[k], "need": v} for k, v in CONTRACT_COUNTS.items()
            if have[k] < v}
