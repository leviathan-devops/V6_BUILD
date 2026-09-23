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


def _num(v):
    """A probability, or None when the value is not usable.

    AUDIT FIX: the pane assumed every value was numeric, so a None/str in a
    distribution raised TypeError out of max()/sorted()/format and CRASHED the
    seat. A malformed entry now renders as a placeholder.
    """
    try:
        f = float(v)
    except (TypeError, ValueError, OverflowError):
        # AUDIT FIX (round 7): float(10**1000) raises OverflowError, which
        # (TypeError, ValueError) does not catch — the seat still crashed.
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def render_probabilities(decider: dict) -> list[str]:
    out = [rule("="), " DECIDER PROBABILITIES (every question, every option)", rule("=")]
    for qid in sorted(decider):
        dist = decider[qid]
        # AUDIT FIX: a non-dict DISTRIBUTION (None/list/str/float) crashed
        # .items() and took the seat down — the same class _num fixed for values.
        if not isinstance(dist, dict):
            out.append(f" {qid}: <malformed distribution {type(dist).__name__}>")
            continue
        if not dist:
            out.append(f" {qid}: <no distribution>")
            continue
        clean = {k: _num(v) for k, v in dist.items()}
        bad = [k for k, v in clean.items() if v is None]
        clean = {k: v for k, v in clean.items() if v is not None}
        if not clean:
            out.append(f" {qid}: <no numeric distribution> (unusable: {bad})")
            continue
        if bad:
            out.append(f" {qid}: WARNING non-numeric entries {bad} rendered as omitted")
        dist = clean
        top = max(dist, key=dist.get)
        out.append(f" {qid}  argmax={top} p={dist[top]:.3f}")
        for opt, p in sorted(dist.items(), key=lambda kv: -kv[1]):
            out.append(f"    {opt:<18} {p:6.3f} |{_bar(p)}|")
    return out


def render_gates(gates: list) -> list[str]:
    out = [rule("="), " GATE DECISIONS (deterministic layer)", rule("=")]
    for g in gates:
        # AUDIT FIX: a non-dict gate entry crashed g.get().
        if not isinstance(g, dict):
            out.append(f" [????  ] <malformed gate entry {type(g).__name__}>")
            continue
        mark = "PASS  " if g.get("passed") else "REJECT"
        out.append(f" [{mark}] {g.get('gate','?'):<10} {g.get('token','')}")
        out.append(f"            {g.get('detail','')}")
    return out


def render_pnl(pnl_pips, open_positions) -> list[str]:
    """AUDIT FIX (round 7): `:+.2f` raised on None/str, so a malformed P&L feed
    took the seat down. The same _num guard the probabilities use."""
    p = _num(pnl_pips)
    o = _num(open_positions)
    p_s = f"{p:+.2f}" if p is not None else f"<malformed {type(pnl_pips).__name__}>"
    o_s = f"{int(o)}" if o is not None else f"<malformed {type(open_positions).__name__}>"
    return [rule("="), " LIVE P&L", rule("="),
            f" net_pips={p_s}   open_positions={o_s}"]


def render_rejections(rejections) -> list[str]:
    # AUDIT FIX: `len(None)` and `r.get` on a non-dict both crashed the pane.
    if not isinstance(rejections, (list, tuple)):
        return [rule("="), f" REJECTION LOG (malformed: {type(rejections).__name__})",
                rule("=")]
    out = [rule("="), f" REJECTION LOG ({len(rejections)} entries)", rule("=")]
    if not rejections:
        out.append(" (none)")
    for r in rejections:
        if not isinstance(r, dict):
            out.append(f" <malformed entry {type(r).__name__}>")
            continue
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
