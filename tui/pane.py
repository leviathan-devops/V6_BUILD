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
    # AUDIT FIX (round 13): `bool` is a subclass of `int`, so `float(True)` is
    # 1.0 and `float(False)` is 0.0 — a boolean feed rendered as an authoritative
    # probability ("1.000") and as a position count. A bool is not a number here.
    if isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError, OverflowError):
        # AUDIT FIX (round 7): float(10**1000) raises OverflowError, which
        # (TypeError, ValueError) does not catch — the seat still crashed.
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def render_probabilities(decider) -> list[str]:
    # AUDIT FIX: a None/non-dict TOP-LEVEL decider crashed sorted().
    if not isinstance(decider, dict):
        return [rule("="), f" DECIDER PROBABILITIES (malformed: {type(decider).__name__})",
                rule("=")]
    out = [rule("="), " DECIDER PROBABILITIES (every question, every option)", rule("=")]
    # AUDIT FIX (round 9): sorted() on heterogeneous qids ({1:..., 'a':...})
    # raised TypeError and crashed the seat. The key is the STRING form.
    for qid in sorted(decider, key=str):
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
        # AUDIT FIX (round 10): a probability outside [0,1] passed _num (which
        # only rejects NaN/Inf), printed as authoritative ("1.500") while _bar
        # silently CLAMPED — so the text and the bar disagreed and the seat
        # presented an impossible number as a real one. Out-of-range is
        # malformed, not rendered.
        bad = [k for k, v in clean.items() if v is None or not (0.0 <= v <= 1.0)]
        clean = {k: v for k, v in clean.items()
                 if v is not None and 0.0 <= v <= 1.0}
        if not clean:
            out.append(f" {qid}: <no numeric distribution> (unusable: {bad})")
            continue
        if bad:
            out.append(f" {qid}: WARNING non-numeric entries {bad} rendered as omitted")
        dist = clean
        top = max(dist, key=dist.get)
        out.append(f" {qid}  argmax={top} p={dist[top]:.3f}")
        for opt, p in sorted(dist.items(), key=lambda kv: -kv[1]):
            # a non-str option name rejects a non-empty format spec -> coerce
            out.append(f"    {str(opt):<18} {p:6.3f} |{_bar(p)}|")
    return out


def render_gates(gates) -> list[str]:
    # AUDIT FIX: a None/non-list gates argument crashed the iteration.
    if not isinstance(gates, (list, tuple)):
        return [rule("="), f" GATE DECISIONS (malformed: {type(gates).__name__})", rule("=")]
    out = [rule("="), " GATE DECISIONS (deterministic layer)", rule("=")]
    for g in gates:
        # AUDIT FIX: a non-dict gate entry crashed g.get().
        if not isinstance(g, dict):
            out.append(f" [????  ] <malformed gate entry {type(g).__name__}>")
            continue
        # AUDIT FIX (round 12): truthiness misreports a malformed feed as an
        # authoritative decision — `"false"` and `"0"` are TRUTHY (rendered
        # PASS) while 0/""/None render REJECT. A gate verdict must be a real
        # bool; anything else is flagged as malformed, never decided.
        _p = g.get("passed")
        if _p is True:
            mark = "PASS  "
        elif _p is False:
            mark = "REJECT"
        else:
            mark = "????  "
        out.append(f" [{mark}] {str(g.get('gate','?')):<10} {g.get('token','')}")
        out.append(f"            {g.get('detail','')}")
    return out


def render_pnl(pnl_pips, open_positions) -> list[str]:
    """AUDIT FIX (round 7): `:+.2f` raised on None/str, so a malformed P&L feed
    took the seat down. The same _num guard the probabilities use."""
    p = _num(pnl_pips)
    o = _num(open_positions)
    p_s = f"{p:+.2f}" if p is not None else f"<malformed {type(pnl_pips).__name__}>"
    # AUDIT FIX (round 10): sharing the FLOAT guard let `int(o)` silently
    # truncate a fractional count (2.9 -> 2) and accept negatives, misreporting
    # the position count instead of flagging a malformed feed. A count must be a
    # non-negative integer; P&L may be any finite float. Separate validation.
    if o is not None and (o < 0 or o != int(o)):
        o_s = f"<malformed count {open_positions!r}>"
    else:
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
    # AUDIT FIX (round 9): render() dereferenced the model's fields with no
    # guard, so a None/wrong-type field raised AttributeError while every
    # sub-renderer handled malformed input. The top level is guarded too.
    if not isinstance(m, PaneModel):
        return "\n".join([rule("="),
                           f" PANE (malformed model: {type(m).__name__})",
                           rule("=")])
    pair = m.pair if isinstance(m.pair, str) else f"<{type(m.pair).__name__}>"
    sess = m.session if isinstance(m.session, str) else f"<{type(m.session).__name__}>"
    lines = [rule("="), f" PLUTUS V6 — {pair}  {sess}", rule("=")]
    lines += render_pnl(m.pnl_pips, m.open_positions)
    lines += render_probabilities(m.decider)
    lines += render_gates(m.gates)
    lines += render_rejections(m.rejections)
    return "\n".join(lines)


def has_probability_bars(text: str) -> bool:
    return "|" in text and "#" in text and "argmax=" in text


def has_gate_decisions(text: str) -> bool:
    # AUDIT FIX (round 16): the REJECTION LOG header (always emitted by
    # render_rejections) contains the substring "REJECT", so this returned True
    # for ANY rendered pane — even one whose gate section had zero verdicts. It
    # matches the rendered MARKER the gate renderer actually emits.
    if not isinstance(text, str):
        return False
    return "[PASS  ]" in text or "[REJECT]" in text
