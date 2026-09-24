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


def _safe(v, width: int = 60) -> str:
    """A rendered field: control chars stripped, length bounded.

    AUDIT FIX (round 24): gate/rejection text was interpolated VERBATIM, so a
    multiline value injected extra rows and could MIMIC a `[PASS  ]` verdict that
    `has_gate_decisions` then believed. Newlines and control chars are removed and
    the field is bounded to the pane width.
    """
    s = v if isinstance(v, str) else repr(v)
    s = "".join(ch if ch.isprintable() else " " for ch in s)
    return s if len(s) <= width else s[: width - 1] + "\u2026"


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
            out.append(f" {_safe(qid, 20)}: <malformed distribution {type(dist).__name__}>")
            continue
        if not dist:
            out.append(f" {_safe(qid, 20)}: <no distribution>")
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
            out.append(f" {_safe(qid, 20)}: <no numeric distribution> (unusable: {_safe(bad, 24)})")
            continue
        if bad:
            out.append(f" {_safe(qid, 20)}: WARNING non-numeric entries {_safe(bad, 20)} rendered as omitted")
        dist = clean
        top = max(dist, key=dist.get)
        out.append(f" {_safe(qid, 20)}  argmax={_safe(top, 18)} p={dist[top]:.3f}")
        for opt, p in sorted(dist.items(), key=lambda kv: -kv[1]):
            # a non-str option name rejects a non-empty format spec -> coerce
            out.append(f"    {_safe(opt, 18):<18} {p:6.3f} |{_bar(p)}|")
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
        # AUDIT FIX (round 26, completing round 24): this sanitizer was WRITTEN in
        # round 24 but never applied — a batch aborted at an earlier anchor miss,
        # so only render_rejections got `_safe`. Gate text was still interpolated
        # verbatim, so a multiline value injected rows and could MIMIC the
        # `[PASS  ]`/`[REJECT]` markers that has_gate_decisions trusts.
        out.append(f" [{mark}] {_safe(g.get('gate','?'), 10):<10} {_safe(g.get('token',''), 24)}")
        out.append(f"            {_safe(g.get('detail',''))}")
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
        # AUDIT FIX (round 24): the rejection fields were interpolated verbatim,
        # so a multiline value injected rows and could mimic a verdict marker.
        out.append(f" {_safe(r.get('when',''), 20)} {_safe(r.get('token',''), 20)} "
                   f"— {_safe(r.get('detail',''))}")
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
    # AUDIT FIX (round 26): pair/session were interpolated verbatim, so a newline
    # broke the grid and a literal marker in either forged a gate verdict.
    lines = [rule("="), f" PLUTUS V6 — {_safe(pair, 24)}  {_safe(sess, 24)}", rule("=")]
    lines += render_pnl(m.pnl_pips, m.open_positions)
    lines += render_probabilities(m.decider)
    lines += render_gates(m.gates)
    lines += render_rejections(m.rejections)
    return "\n".join(lines)


def has_probability_bars(text: str) -> bool:
    """A real probability BAR row exists.

    AUDIT FIX (round 34): this was a whole-pane substring check for `|`, `#` and
    `argmax=`, all of which `_safe` PRESERVES (they are printable) — so a single
    rejection detail containing those characters forged it. The scan is now
    scoped to the DECIDER PROBABILITIES section and requires the renderer's own
    row shape: an `argmax=` header followed by a bar line at the option column.
    """
    if not isinstance(text, str):
        return False
    _in = False
    _saw_argmax = False
    for ln in text.splitlines():
        if ln.startswith(" DECIDER PROBABILITIES"):
            _in = True
            continue
        # AUDIT FIX (round 35, twice): the first version required both
        # `startswith(" ")` AND `not startswith(" ")` — always False, so the scan
        # never terminated. The second exited on the `argmax=` row itself, which
        # is ALSO at the one-space column. The section's own one-space rows are
        # the `argmax=` headers; anything else at that column is a NEW section.
        # AUDIT FIX (round 38): the exit fired on the renderer's OWN in-section
        # rows (`<malformed distribution>`, `WARNING non-numeric entries`, ...),
        # which sit at the one-space column WITHOUT `argmax=` — so the scan
        # aborted before any later bar row. The section's own rows are now
        # RECOGNIZED (argmax headers and the `<...>`/WARNING notices) and only a
        # genuinely different one-space line exits.
        if _in and ln.startswith(" ") and not ln.startswith("  ") and ln.strip() \
                and "argmax=" not in ln and not ln.lstrip().startswith("<") \
                and "WARNING non-numeric" not in ln:
            _in = False
            continue
        if not _in:
            continue
        if "argmax=" in ln:
            _saw_argmax = True
            continue
        # the option row: FOUR spaces, a label, a probability, then a bar
        if _saw_argmax and ln.startswith("    ") and "|" in ln and "#" in ln:
            return True
    return False


def has_gate_decisions(text: str) -> bool:
    # AUDIT FIX (round 16): the REJECTION LOG header (always emitted by
    # render_rejections) contains the substring "REJECT", so this returned True
    # for ANY rendered pane — even one whose gate section had zero verdicts. It
    # matches the rendered MARKER the gate renderer actually emits.
    if not isinstance(text, str):
        return False
    # AUDIT FIX (round 29): matching the WHOLE pane let a single-line payload
    # (`[`/`]` are printable, so _safe preserves them) forge a verdict from a
    # rejection detail. Only lines in the GATE DECISIONS section count, and only
    # where the marker sits at the row's start — which is where the renderer
    # emits it.
    # AUDIT FIX (round 30): `ln.strip()` defeated the indent check — a DETAIL row
    # is indented 12 spaces, and stripping it made its content look like a verdict
    # row. The scan is now SECTION-scoped: only lines INSIDE the GATE DECISIONS
    # block count, and the marker must sit at the ROW's own column (no leading
    # whitespace), which is exactly where the renderer emits it.
    if not isinstance(text, str):
        return False
    # THE EXACT COLUMN. The renderer emits a verdict row as `" [{mark}] ..."` —
    # ONE leading space — while a DETAIL row is indented TWELVE. So requiring the
    # one-space prefix distinguishes them exactly, and a marker quoted inside a
    # detail (which sits 12 spaces in) can never match. My first version tracked
    # the section and exited on ANY indented line, which the verdict rows
    # themselves are — it reported False for a pane full of real verdicts.
    # TWO CONDITIONS, both necessary: the line must be INSIDE the GATE DECISIONS
    # section (the renderer delimits sections with a `===` rule) AND the marker
    # must sit at the verdict column (one leading space — details are indented
    # twelve). The column alone is not enough: the REJECTION LOG rows share it.
    import re as _re
    _in = False
    for ln in text.splitlines():
        if ln.startswith(" GATE DECISIONS"):
            _in = True
            continue
        # the section ENDS at the next SECTION HEADER (an all-caps label at the
        # one-space column) — NOT at the `===` rule, which sits BETWEEN the header
        # and its own rows.
        # AUDIT FIX (round 32): the terminator regex required ALL-CAPS, but the
        # real headers are ` LIVE P&L`, ` DECIDER PROBABILITIES (every ...)` and
        # ` REJECTION LOG (N entries)` — lowercase letters and `&`. It never
        # matched, so the GATE scan leaked into the REJECTION LOG, whose rows
        # share the verdict column. Any one-space line that is NOT a verdict row
        # and NOT a rule now ends the section.
        # AUDIT FIX (round 33): the terminator matched DETAIL rows too (they start
        # with a space), so it cleared the section on the first detail and missed
        # every later verdict. A SECTION HEADER sits at the ONE-space column; a
        # detail is indented TWELVE. Only the one-space, non-verdict, non-rule,
        # non-indented line terminates.
        if _in and ln.startswith(" ") and not ln.startswith("  ") \
                and not ln.startswith(" [") and ln.strip() \
                and not set(ln.strip()) <= {"="}:
            _in = False
            continue
        if _in and (ln.startswith(" [PASS  ]") or ln.startswith(" [REJECT]")):
            return True
    return False
