"""tui/pane.py — the trading pane.

THE RUNTIME SEAT (pin RUNTIME SEAT): the operator sees every probability,
every gate decision, every rejection with its NAMED token. A pane that shows
only "accepted/rejected" is NOT the seat — the distributions ARE the seat.

Renders to a plain character grid so the same code backs both the pi TUI and
the tests. No coding surface: this module reads state and prints; it executes
nothing the operator did not already decide.
"""
from __future__ import annotations
from dataclasses import dataclass

WIDTH = 76


def _bar(p: float, width: int = 30) -> str:
    filled = max(0, min(width, int(round(p * width))))
    return "#" * filled + "." * (width - filled)


def rule(ch: str = "-") -> str:
    return ch * WIDTH


@dataclass
class PaneModel:
    pair: str
    session: str
    decider: dict          # {qid: {option: prob}}
    gates: list            # [{"gate","passed","token","detail"}]
    pnl_pips: float = 0.0
    open_positions: int = 0
    rejections: list = None

    def __post_init__(self):
        if self.rejections is None: self.rejections = []


def render_probabilities(decider: dict) -> list[str]:
    out = [rule("="), " DECIDER PROBABILITIES (every question, every option)", rule("=")]
    for qid in sorted(decider):
        dist = decider[qid]
        if not dist:
            out.append(f" {qid}: <no distribution>")
            continue
        top = max(dist, key=dist.get)
        out.append(f" {qid}  argmax={top} p={dist[top]:.3f}")
        for opt, p in sorted(dist.items(), key=lambda kv: -kv[1]):
            out.append(f"    {opt:<18} {p:6.3f} |{_bar(p)}|")
    return out


def render_gates(gates: list) -> list[str]:
    out = [rule("="), " GATE DECISIONS (deterministic layer)", rule("=")]
    for g in gates:
        mark = "PASS  " if g.get("passed") else "REJECT"
        out.append(f" [{mark}] {g.get('gate','?'):<10} {g.get('token','')}")
        out.append(f"            {g.get('detail','')}")
    return out


def render_pnl(pnl_pips: float, open_positions: int) -> list[str]:
    return [rule("="), " LIVE P&L", rule("="),
            f" net_pips={pnl_pips:+.2f}   open_positions={open_positions}"]


def render_rejections(rejections: list) -> list[str]:
    out = [rule("="), f" REJECTION LOG ({len(rejections)} entries)", rule("=")]
    if not rejections:
        out.append(" (none)")
    for r in rejections:
        out.append(f" {r.get('when','')} {r.get('token','')} — {r.get('detail','')}")
    return out


def render(m: PaneModel) -> str:
    lines = [rule("="), f" PLUTUS V6 — {m.pair}  {m.session}", rule("=")]
    lines += render_pnl(m.pnl_pips, m.open_positions)
    lines += render_probabilities(m.decider)
    lines += render_gates(m.gates)
    lines += render_rejections(m.rejections)
    return "\n".join(lines)


def has_probability_bars(text: str) -> bool:
    return "|" in text and "#" in text and "argmax=" in text


def has_gate_decisions(text: str) -> bool:
    return "PASS" in text or "REJECT" in text
