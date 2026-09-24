"""corpus/build_corpus.py — the doctrine corpus generator.

BLUEPRINT §1.8: "Each of the 583 mechanism cards + 38 rulings + 38 forensic
trades + 23 golden trades converts to a (state, questions, answers) triple.
~700 records from existing data."

D13 QUOTE LAW: every record's state text carries the card's quote VERBATIM
plus its source file:line. Nothing is synthesized, nothing paraphrased.
"""
from __future__ import annotations
import json, re, hashlib, os
from pathlib import Path
from dataclasses import dataclass, asdict

# AUDIT FIX (round 6): the roots were hardcoded absolute paths, so the builder
# was non-portable and a moved checkout silently produced an EMPTY corpus.
# They are env-overridable and resolved with an explicit existence check.
_PLUTUS = Path(os.environ.get(
    "PLUTUS_HOME", "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS"))
MASTER = Path(os.environ.get("PLUTUS_MASTER", _PLUTUS / "MASTER_CONTEXT"))
V5 = Path(os.environ.get(
    "PLUTUS_V5", "/home/leviathan/.omp/wt/plutus-main-66dfa4c/PLUTUS/agent"))

STATE_DELIM = "<|fim_prefix|>"
QUESTION_DELIM = "<|fim_middle|>"
OPTION_OPEN = "<|box_start|>"
OPTION_CLOSE = "<|box_end|>"
DECIDE = "<|fim_suffix|>"


@dataclass
class Record:
    id: str
    source: str          # file:line — the D13 provenance anchor
    quote: str           # VERBATIM
    state: str
    question: str
    options: list[str]
    answer: str
    kind: str            # mechanism | ruling | forensic | golden

    def to_triple(self) -> str:
        opts = "".join(f"{OPTION_OPEN}{o}{OPTION_CLOSE}" for o in self.options)
        return (f"{STATE_DELIM}{self.state}"
                f"{QUESTION_DELIM}{self.question}{opts}{DECIDE}"
                f"\n{self.answer}")


CARD_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*?)(?=\n---\s*\n|\Z)",
    re.S | re.M)


def parse_frontmatter(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            val = v.strip()
            # the card format wraps the quote in single quotes and may contain
            # double quotes inside -> strip ONE layer of either, never both
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            out[k.strip()] = val
    return out


# unreadable cards, recorded so a partial harvest is diagnosable (round 31)
SCAN_SKIPPED: list = []


def scan_cards(root: Path) -> list[Record]:
    """Every markdown card under `root` with a frontmatter `quote:` becomes a record."""
    recs = []
    if not root.exists(): return recs
    for f in sorted(root.rglob("*.md")):
        try: text = f.read_text(errors="ignore")
        except Exception as e:                             # noqa: BLE001
            # AUDIT FIX (round 31): a silent skip made a partially-unreadable tree
            # indistinguishable from a smaller one — a shrunken corpus still
            # reported success. The skip is recorded.
            SCAN_SKIPPED.append(f"{f}: {type(e).__name__}")
            continue
        for i, m in enumerate(CARD_RE.finditer(text), 1):
            fm = parse_frontmatter(m.group("fm"))
            quote = fm.get("quote", "")
            if not quote: continue
            slug = fm.get("slug", f.stem)
            kind = fm.get("kind", "mechanism")
            src = f"{f}:{text[:m.start()].count(chr(10))+1}"
            recs.append(Record(
                id=f"{slug}-{i}", source=src, quote=quote,
                state=f"DOCTRINE {slug} ({kind}): {quote}",
                question=f"Does the state satisfy the {slug} rule?",
                options=["yes", "no"], answer="yes", kind=kind))
    return recs


def _rotate(opts: list, n: int) -> list:
    """Deterministically rotate a fixed option list so the correct answer's
    INDEX varies — a constant index is a positional shortcut a model can learn
    instead of reading the state (audit rounds 6 and 10)."""
    rot = n % len(opts)
    return opts[rot:] + opts[:rot]


def harvest_golden_trades(v5_root: Path) -> list[Record]:
    """The golden-week trades from the canon injector (D13 verbatim)."""
    recs = []
    injector = v5_root / "MASTER_CONTEXT" / "PLUTUS_MASTER_CONTEXT_INJECTOR.md"
    if not injector.exists():
        injector = _PLUTUS / "agent" / "MASTER_CONTEXT" / "PLUTUS_MASTER_CONTEXT_INJECTOR.md"
    if not injector.exists(): return recs
    text = injector.read_text(errors="ignore")
    for ln, line in enumerate(text.splitlines(), 1):
        if "Tier A" in line and "documented exact" in line:
            for chunk in line.split("·"):
                c = chunk.strip()
                mm = re.search(r"(#[0-9]+\s+\w+\s+\w+\s+\w+)\s+([\d.]+)/([\d.]+)/([\d.]+)\s+([\d.]+)", c)
                if mm:
                    name, e, sl, tp, rrr = mm.groups()
                    # AUDIT FIX (round 13): `[\d.]+` matches a bare `.`, so a
                    # malformed cell produced answer=rrr='.' taught as the correct
                    # RRR. Every capture is now float-validated.
                    try:
                        _vals = [float(x) for x in (e, sl, tp, rrr)]
                    except ValueError:
                        continue
                    if not all(v == v and abs(v) != float("inf") for v in _vals):
                        continue
                    # AUDIT FIX: the correct RRR was ALWAYS options[0], so a
                    # model could learn a positional shortcut. Rotate so the
                    # correct answer's index varies deterministically.
                    # (the golden-trade harvester rotates; the cascade one did
                    #  not — AUDIT FIX round 6 applied the same rotation here)
                    opts = _rotate([rrr, "below_floor", "no_trade"], len(recs))
                    recs.append(Record(
                        id=f"golden-{len(recs)+1}",
                        source=f"{injector}:{ln}",
                        quote=c,
                        state=f"GOLDEN TRADE {name}: entry={e} SL={sl} TP={tp} RRR={rrr}",
                        question="What is the risk-reward ratio of this setup?",
                        options=opts, answer=rrr, kind="golden"))
    return recs


# THE REAL CARD ROOTS (measured 2026-09-23):
#   MASTER_CONTEXT/mechanisms/ = 583 cards   (type: plutus-mechanism)
#   MASTER_CONTEXT/rulings/    =  38 cards
CARD_ROOTS = (MASTER / "mechanisms", MASTER / "rulings",
              MASTER / "knowledge-graph", MASTER / "cards",
              V5 / "src" / "card", V5 / "MASTER_CONTEXT")


def card_records(cards: list[Record]) -> list[Record]:
    """Each card yields TWO training signals, both grounded in its own text:
      1. VERIFY  — 'does the state satisfy this rule?' (the direct application)
      2. KIND    — 'what kind of doctrine is this?' (classification)
    Neither synthesizes anything: the state text is the card's own quote.
    """
    out = []
    for r in cards:
        out.append(r)
        out.append(Record(
            id=r.id + "-kind", source=r.source, quote=r.quote,
            state=f"DOCTRINE CARD: {r.quote}\nSOURCE {r.source}",
            question="What kind of doctrine card is this?",
            # AUDIT FIX (round 17 H9): the option order was FIXED while the answer
            # distribution is heavily skewed (583 mechanisms vs 38 rulings), so
            # "mechanism" sat at index 0 for the overwhelming majority — the
            # constant-index positional shortcut already fixed for golden/cascade
            # with `_rotate`, reintroduced here. The order now rotates.
            # `len(out) // 2` — the loop appends TWO records per card (the card, then
            # this KIND record), so a raw `len(out)` is always ODD and the rotation
            # only ever reached indices 1 and 3. Halving it covers all four.
            options=_rotate(["mechanism", "ruling", "forensic", "golden"], len(out) // 2),
            # AUDIT FIX: the answer is the card's OWN kind, not a path guess.
            # The old form derived it from "/rulings/" in the source path, so a
            # forensic or golden card outside rulings/ was taught as "mechanism"
            # and the forensic/golden options were never emitted at all.
            answer=r.kind if r.kind in ("mechanism", "ruling", "forensic", "golden")
                   else "mechanism",
            kind=r.kind))
    return out



# ---- the FORENSIC 38 + the GOLDEN CASCADE 23 -------------------------------
FORENSIC_LAW_RE = re.compile(r"^###\s+(LAW\s+\d+):\s*(.+?)\s*$", re.M)


def harvest_forensic_laws(master: Path) -> list[Record]:
    """The 7 universal laws + their measured counts, VERBATIM from the file."""
    f = master / "FORENSIC_ANALYSIS_38_TRADES.md"
    if not f.exists(): return []
    text = f.read_text(errors="ignore")
    recs = []
    for m in FORENSIC_LAW_RE.finditer(text):
        law, title = m.group(1), m.group(2).strip()
        ln = text[:m.start()].count("\n") + 1
        # the law's own body (to the next ###) carries the measured table
        body_start = m.end()
        nxt = text.find("\n### ", body_start)
        body = text[body_start: nxt if nxt > 0 else body_start + 1200].strip()
        recs.append(Record(
            id=f"forensic-{law.lower().replace(' ', '-')}",
            source=f"{f}:{ln}", quote=f"{law}: {title}",
            state=f"FORENSIC {law} — {title}\n{body[:600]}",
            question=f"Does the setup obey {law}?",
            options=["yes", "no"], answer="yes", kind="forensic"))
    return recs


CASCADE_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|([^|]*)\|([^|]*)\|\s*\*\*([\d.]+)\*\*\s*\|",
    re.M)


def harvest_golden_cascade(master: Path) -> list[Record]:
    """The 23-trade golden cascade rows (the acceptance oracle), VERBATIM."""
    f = master / "PLUTUS_GOLDEN_CASCADE_23.md"
    if not f.exists(): return []
    text = f.read_text(errors="ignore")
    recs = []
    for m in CASCADE_ROW_RE.finditer(text):
        (n, day, setup, entry, sl, tp, risk, reward, rrr) = m.groups()
        ln = text[:m.start()].count("\n") + 1
        row = m.group(0).strip()
        # AUDIT FIX (round 16): `([\d.]+)` matches a bare `.`, so a malformed
        # cascade cell became the CORRECT RRR (and its rotated distractors) —
        # the same guard the golden/gap harvesters already carry.
        try:
            _cvals = [float(x) for x in (entry, sl, tp, rrr)]
        except ValueError:
            continue
        if not all(v == v and abs(v) != float("inf") for v in _cvals):
            continue
        recs.append(Record(
            id=f"cascade-{n}",
            source=f"{f}:{ln}", quote=row,
            state=(f"GOLDEN CASCADE #{n} {day} {setup.strip()}: "
                   f"entry={entry} SL={sl} TP={tp} risk={risk.strip()} reward={reward.strip()} RRR={rrr}"),
            question="What is the risk-reward ratio of this golden-cascade trade?",
            # AUDIT FIX (round 10): the answer was ALWAYS options[0], so a model
            # could solve cascade RRR by position alone. Same rotation as the
            # golden-trade harvester.
            options=_rotate([rrr, "below_3.5", "no_trade"], len(recs)),
            answer=rrr, kind="golden"))
    return recs


def harvest_gap_analysis(master: Path) -> list[Record]:
    """Any documented-exact trade row in the gap analysis / master injector."""
    recs = []
    for name in ("PLUTUS_MASTER_CONTEXT_INJECTOR.md", "GAP_ANALYSIS_2026-07-18.md"):
        f = master / name
        if not f.exists():
            # AUDIT FIX: derive the fallback from the env-overridable root rather
            # than a second hardcoded absolute path.
            f = _PLUTUS / "agent" / "MASTER_CONTEXT" / name
        if not f.exists(): continue
        text = f.read_text(errors="ignore")
        for ln, line in enumerate(text.splitlines(), 1):
            # AUDIT FIX (round 6): the harvester taught EVERY matching row as
            # above-floor without parsing the RRR. A row below the operator's
            # floor was a false positive. The value is now compared.
            # AUDIT FIX (round 15): the parsed value was the number after an
            # `a/b/c` triple ANYWHERE in the line, while the floor check was a
            # line-global `\bRRR\b` — so `1.1/2.2/3.3 10 lots ... RRR 2.0`
            # taught "yes" (10 >= 3.5) for a trade whose RRR is 2.0. The value is
            # now taken from the token BESIDE the RRR label.
            _rm = re.search(r"\bRRR\b[^\d]{0,6}([\d.]+)|([\d.]+)[^\d]{0,6}\bRRR\b", line)
            _m = re.search(r"(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)\s+([\d.]+)", line)
            try:
                if _rm:
                    _rrr = float(_rm.group(1) or _rm.group(2))
                else:
                    _rrr = float(_m.group(4)) if _m else None
            except ValueError:
                # AUDIT FIX: `[\d.]+` can match a bare "." (an ellipsis in prose)
                # and float(".") aborted the whole harvest.
                _rrr = None
            if _rrr is not None and _rrr == _rrr and abs(_rrr) != float("inf") \
                    and _rrr >= 3.5 and re.search(r"\bRRR\b", line):
                recs.append(Record(
                    id=f"gap-{f.stem}-{ln}", source=f"{f}:{ln}", quote=line.strip(),
                    state=f"DOCUMENTED TRADE ROW: {line.strip()[:300]}",
                    question="Is this trade's RRR above the operator floor?",
                    options=["yes", "no"], answer="yes", kind="golden"))
    return recs


# THE BOUND VOCABULARY — the words that actually sit beside a number in the
# mechanism cards, MEASURED from the corpus (pips/pip 36, within 10, trades 6,
# days 5, setups 5, ...). A negative may only corrupt a number that carries one
# of these, because only then is the number a BOUND the rule asserts; zeroing an
# incidental number leaves the rule satisfied and the "no" label would be a
# mislabel (audit rounds 13-15).
_BOUND = (r"pips?|%|percent|ratio|RRR|buffer|ATR|trades?|bars?|setups?|"
          r"days?|hours?|minutes?|candles?|lots?|points?|within")


def _negative_variant(r, opts):
    """Return (state, quote, answer) for a VALID refusal, or None to SKIP.

    THE INVARIANT (audit rounds 10 and 11): a negative is valid ONLY if its
    STATE genuinely contradicts its LABEL, and the contradiction must be
    VERIFIED on the corrupted value — not merely that the string changed. The
    round-10 version satisfied neither half: it corrupted a number chosen by a
    POSITIONAL regex (the last decimal in the state, which for a documented row
    is often a date or a count, not the RRR) and it relabelled KIND questions
    whose kind a corrupted quote cannot change. Both supervised the model to
    ignore its own input. Hence: target the QUESTION'S OWN quantity, then parse
    the result back and confirm it now contradicts the label; otherwise SKIP.
    """
    q = r.question
    floor = 3.5

    def _rrr_of(text):
        m = re.search(r"RRR\s*[=≥>=]{0,2}\s*([\d.]+)", text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
        return None

    # --- (1) an RRR question: the state must SHOW a sub-floor RRR. The token is
    #         the `RRR=` field the state template itself declares.
    if "risk-reward ratio" in q:
        below = next((o for o in opts if "below" in str(o).lower()), None)
        if below is None:
            return None
        ns = re.sub(r"(RRR\s*=\s*)[\d.]+", r"\g<1>2.0", r.state)
        got = _rrr_of(ns)
        if ns == r.state or got is None or got >= floor:
            return None                      # the corruption did not land
        return ns, ns, below

    # --- (2) a yes/no floor question: the state must SHOW a sub-floor RRR. A
    #         documented row spells it `a/b/c RRR`, so the RRR is the number
    #         AFTER the three-price group — never the last number in the line.
    if "above the operator floor" in q:
        # AUDIT FIX (round 17 H11): only the TRIPLE form (`a/b/c RRR`) was
        # rewritten, but harvest_gap_analysis also accepts the RRR-beside-label
        # form (`... RRR 4.5`). Those rows hit `ns == state` and SKIPPED, so they
        # kept yes-only supervision. Both spellings are handled; the label form is
        # tried when the triple form does not match.
        # AUDIT FIX (round 21): the corruption rewrote the TRIPLE first while
        # `harvest_gap_analysis` PREFERS the RRR-beside-label value — so on a row
        # carrying BOTH spellings the triple was corrupted, the label RRR stayed
        # above the floor, and the record was labelled `no` against a state that
        # still satisfied the question. The corruption now targets the SAME
        # spelling the harvester used, in the same priority order.
        ns = re.sub(r"(\bRRR\b[^\d]{0,6})([\d.]+)", r"\g<1>2.0", r.state)
        if ns == r.state:
            ns = re.sub(r"([\d.]+)([^\d]{0,6}\bRRR\b)", r"2.0\g<2>", ns)
        if ns == r.state:
            ns = re.sub(r"(\d+\.\d+/\d+\.\d+/\d+\.\d+\s+)([\d.]+)",
                        r"\g<1>2.0", ns)
        if ns == r.state:
            return None
        # AUDIT FIX (round 13): the corruption was never VERIFIED to have hit the
        # RRR. If the row spells it elsewhere (`RRR 4.5`) the incidental number
        # was zeroed while the RRR stayed above the floor — a false refusal. The
        # result is parsed back, exactly as branch (1) does.
        # AUDIT FIX (round 18): the corruption handles BOTH spellings but the
        # verification parsed only the triple form, so a label-form row
        # (`... RRR 4.5`) verified as None and SKIPPED — those rows kept yes-only
        # supervision. The verification now parses whichever spelling is present.
        # the verification parses the SAME priority the harvester used
        m2 = re.search(r"\bRRR\b[^\d]{0,6}([\d.]+)", ns) or \
             re.search(r"([\d.]+)[^\d]{0,6}\bRRR\b", ns)
        if not m2:
            m2 = re.search(r"\d+\.\d+/\d+\.\d+/\d+\.\d+\s+([\d.]+)", ns)
        try:
            shown = float(m2.group(1)) if m2 else None
        except ValueError:
            shown = None
        if shown is None or shown >= floor:
            return None
        return ns, ns, "no"

    # --- (3) a VERIFY question: the rule's own numeric token is broken, and the
    #         corruption is carried into the state through the card's template.
    if q.startswith("Does the state satisfy"):
        # AUDIT FIX (round 12): the TRUNCATION fallback emitted a negative whose
        # state does NOT contradict the question (a truncated quote need not
        # break the rule) — an unverified negative. And zeroing an INCIDENTAL
        # number (a date, a count) leaves the rule satisfied. Both are now
        # refused: a negative requires a NUMERIC token, and the corruption must
        # land in the state. The residual is named: "a number present" does not
        # PROVE it is the rule's threshold, so these negatives rest on the
        # assumption that a mechanism card's numeric token IS its threshold —
        # true for the mechanisms corpus, unverifiable without parsing the rule.
        # AUDIT FIX (round 13): the audit showed that zeroing the FIRST number
        # only contradicts the rule when that number IS the rule's threshold. The
        # negative is now restricted to a number that sits beside a threshold
        # word (pips/percent/ratio/RRR/buffer/atr/trades) — the mechanisms
        # corpus spells its bounds that way. Anything else is SKIPPED, which
        # costs coverage and never emits wrong supervision.
        _thresh = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(?:" + _BOUND + r")\b"
            r"|\b(?:" + _BOUND + r")\s*(\d+(?:\.\d+)?)\b",
            r.quote, re.I)
        if not _thresh:
            return None                      # no THRESHOLD token -> no negative
        _tok = _thresh.group(1) or _thresh.group(2)
        if _tok is None:
            return None
        # AUDIT FIX (round 15): zeroing the token only CONTRADICTS a LOWER-BOUND
        # rule (`at least N`, `min RRR`). For an UPPER bound (`max N trades`,
        # `<= N pips`) zero still SATISFIES it, so labelling `no` inverted the
        # supervision. The direction is read from the rule's own wording, and the
        # corruption is chosen to violate THAT bound.
        # AUDIT FIX (round 26): the direction was searched over the WHOLE quote,
        # so a card mentioning "max" anywhere read as an upper bound even when
        # the CORRUPTED token sat beside a lower-bound word — the corruption then
        # went the wrong way and the "no" label was wrong. The direction is now
        # read from the WINDOW AROUND the token the regex validated.
        # AUDIT FIX (round 17 H10): `.replace(_tok, ..., 1)` rewrites the FIRST
        # substring match, which is NOT the match the regex found — with _tok
        # "10" inside "100" it corrupted the wrong number. The splice uses the
        # regex's own span, so the token the check validated is the token changed.
        _s, _e = _thresh.span(1) if _thresh.group(1) else _thresh.span(2)
        _win = r.quote[max(0, _s - 40): min(len(r.quote), _e + 40)]
        _lower = re.search(r"\b(at least|minimum|min\b|no fewer than|"
                           r"must exceed|greater than)\b", _win, re.I)
        _upper = re.search(r"\b(at most|maximum|max\b|no more than|"
                           r"must not exceed|never (?:more|above)|fewer than|"
                           r"within)\b", _win, re.I)
        if _upper and not _lower:
            # raise the value above an upper bound: multiply it out of range
            try:
                _raised = str(float(_tok) * 10 + 1)
            except ValueError:
                return None
            broken = r.quote[:_s] + _raised + r.quote[_e:]
        elif _lower:
            broken = r.quote[:_s] + "0" + r.quote[_e:]
        else:
            return None                  # no stated bound -> no verified negative
        ns = r.state.replace(r.quote, broken)
        if ns == r.state:
            return None
        return ns, broken, "no"

    # --- (4) a FORENSIC yes/no: the state carries the law's body (the template
    #         prefixes it, so `replace(quote, ...)` never matches). Corrupt the
    #         first number in the BODY, which is what the law asserts.
    if q.startswith("Does the setup obey"):
        head, _, body = r.state.partition("\n")
        # AUDIT FIX (round 12): same verification requirement as the VERIFY
        # branch — a forensic law is only contradicted if it states a numeric
        # bound (every LAW 1..7 in the corpus does: a pip buffer, a ratio, a
        # count). Without a number there is nothing to contradict, so SKIP
        # rather than emit an unverified refusal.
        # AUDIT FIX (round 15): `re.sub(count=1)` zeroed the FIRST decimal in the
        # body, which may be a date, a count, or an example — leaving the law's
        # asserted bound intact, so the "no" label was a false refusal. The
        # corruption now targets the number beside a BOUND WORD, the same rule the
        # VERIFY branch uses.
        _bm = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(?:" + _BOUND + r"|min|max|pairs?)\b"
            r"|\b(?:" + _BOUND + r"|min|max|pairs?)\s*(\d+(?:\.\d+)?)\b",
            body, re.I)
        if not _bm:
            return None                  # no bound in the body -> no negative
        _btok = _bm.group(1) or _bm.group(2)
        if _btok is None:
            return None
        # AUDIT FIX (round 18): `.replace(_btok, "0", 1)` hits the FIRST substring
        # occurrence, not the bound-word span `_bm` validated — with _btok "10"
        # inside "100" it corrupted the wrong number and left the bound intact.
        # The SAME class was fixed in the VERIFY branch (H10); this is its
        # sibling site.
        _bs, _be = _bm.span(1) if _bm.group(1) else _bm.span(2)
        # AUDIT FIX (round 20): this branch ALWAYS zeroed, so an upper-bound law
        # ("max N", "within N") stayed SATISFIED while being labelled `no` — a
        # false refusal. Branch (3) reads the bound direction; this sibling now
        # does too.
        # AUDIT FIX (round 28): the VERIFY branch reads the direction from a
        # 40-char WINDOW around the validated token; this sibling read the WHOLE
        # body, so an unrelated bound word elsewhere selected raise-vs-zero
        # wrongly. Same window here.
        _bwin = body[max(0, _bs - 40): min(len(body), _be + 40)]
        _fl = re.search(r"\b(at least|minimum|min\b|no fewer than|"
                        r"must exceed|greater than)\b", _bwin, re.I)
        _fu = re.search(r"\b(at most|maximum|max\b|no more than|"
                        r"must not exceed|fewer than|within)\b", _bwin, re.I)
        if _fu and not _fl:
            try:
                _new = str(float(_btok) * 10 + 1)
            except ValueError:
                return None
        elif _fl:
            _new = "0"
        else:
            return None
        nbody = body[:_bs] + _new + body[_be:]
        if nbody == body:
            return None
        return f"{head}\n{nbody}", nbody, "no"

    # --- (5) a KIND question: NO VALID single-record corruption exists. A
    #         corrupted quote is still a card of its true kind, so relabelling it
    #         teaches a WRONG label — the exact defect the round-6 and round-10
    #         fixes each introduced. SKIP, and the coverage consequence is stated
    #         in negative_records().
    return None


def negative_records(cards: list[Record]) -> list[Record]:
    """Each card/row yields a MISQUOTED variant whose answer is the refusal.

    The audit found every yes/no record taught `answer="yes"`: a corpus with ONE
    class trains a yes-sayer and the model can never learn to refuse.
    """
    # COVERAGE NOTE: KIND questions ("what kind of doctrine is this?") emit NO
    # negative. Their only valid negative would be a state of a DIFFERENT kind,
    # which needs a cross-record builder — a corrupted quote cannot change a
    # card's kind, so any single-record relabelling is wrong supervision. The
    # KIND refusal class is therefore covered only by the positives' distractors.
    out, skipped = [], 0
    for r in cards:
        if not r.quote or len(r.quote) < 12:
            continue
        opts = list(r.options)
        if len(opts) < 2:
            continue
        variant = _negative_variant(r, opts)
        if variant is None:
            skipped += 1                     # NEVER emit a mislabeled record
            continue
        ns, nq, neg_answer = variant
        # AUDIT FIX (round 14): the negative stored the CORRUPTED text as its
        # `quote` while `source` still pointed at the original file:line — so the
        # quote was no longer VERBATIM from its source, breaking the module's D13
        # provenance contract (the test asserts quote-in-source). The PARENT's
        # verbatim quote is kept; the corruption lives in `state` only.
        out.append(Record(id=r.id + "-neg", source=r.source, quote=r.quote,
                          state=ns, question=r.question, options=opts,
                          answer=neg_answer, kind=r.kind))
    if skipped:
        print(f"  negatives SKIPPED (no valid corruption): {skipped}")
    return out


def build(out_path: Path) -> dict:
    cards = []
    # AUDIT FIX: a missing root silently yielded zero cards and the build still
    # "succeeded". Each root's contribution is now reported.
    root_counts = {}
    for root in CARD_ROOTS:
        got = scan_cards(root)
        root_counts[str(root)] = len(got)
        cards += got
    cards = card_records(cards)
    golden = harvest_golden_trades(V5)
    golden += harvest_golden_cascade(MASTER)
    golden += harvest_gap_analysis(MASTER)
    forensic = harvest_forensic_laws(MASTER)
    # AUDIT FIX (round 23): each harvester returns [] when its source file is
    # absent, and build() raised only on empty cards/total — so a missing
    # FORENSIC_ANALYSIS_38_TRADES.md or GOLDEN_CASCADE shipped a BIASED corpus
    # that still reported success. The expected shapes are named.
    _missing = []
    # AUDIT FIX (round 28): non-empty was too weak — ONE parsed law passed. The
    # documented shapes are 7 forensic laws and 23 cascade rows, so a partial
    # harvest now fails loudly instead of shipping a biased corpus.
    # THE FLOORS ARE THE MEASURED YIELDS, not the document NAMES.
    # AUDIT FIX (round 28b): my first version checked `cascade >= 23` from the
    # FILENAME (`PLUTUS_GOLDEN_CASCADE_23.md`) — but that document is split into
    # four TIERS and only TIER A carries per-trade E/SL/TP rows (8 rows, 6 with
    # levels; the rest are axis labels, doctrine, and pixel-inferred assignments).
    # The measured parseable yield is 6. A floor of 23 was a check that could
    # never pass, which is its own kind of broken.
    _n_cascade = len([r for r in golden if r.id.startswith("cascade-")])
    if len(forensic) < 7:
        _missing.append(f"forensic laws (got {len(forensic)}, documented 7)")
    if _n_cascade < 6:
        _missing.append(f"cascade rows (got {_n_cascade}, measured 6 of Tier A)")
    if not [r for r in golden if r.id.startswith("golden-")]:
        _missing.append("the golden-trade injector (golden rows)")
    _skipped_now = list(SCAN_SKIPPED)
    SCAN_SKIPPED.clear()
    if _skipped_now:
        # AUDIT FIX (round 33): the list was appended to and never read, so a
        # partially-unreadable tree still reported success. Surfaced here.
        raise ValueError(
            f"SCAN_UNREADABLE: {len(SCAN_SKIPPED)} card file(s) could not be read "
            f"(first: {_skipped_now[0]}) — the corpus would be silently shrunken")
    if _missing:
        # AUDIT FIX (round 26): a WARNING still returned a PASSING build, so an
        # absent FORENSIC_ANALYSIS_38_TRADES.md shipped a corpus missing whole
        # refusal classes. A biased corpus is a loud failure.
        raise ValueError(
            f"HARVEST_SOURCE_EMPTY: {_missing} — the corpus would be biased; "
            f"refusing to report a passing build")
    # AUDIT FIX: negatives covered only the card records, so the forensic and
    # golden/gap yes-no questions had ZERO refusal supervision (a yes-sayer
    # bias). Every harvested kind now contributes negatives.
    negatives = negative_records(cards + golden + forensic)
    all_recs = cards + negatives + golden + forensic
    seen, uniq = set(), []
    for r in all_recs:
        # THE DEDUP KEY IS (source, quote, question, STATE).
        #
        # AUDIT FIX (round 15, CRITICAL): round 14 made a negative keep its
        # PARENT's verbatim `quote`/`source`/`question` (the corruption lives in
        # `state` only, to preserve D13 provenance). That made the negative's key
        # IDENTICAL to its positive's — so this dedup DELETED 46 of the 66
        # negatives, destroying 70% of the refusal supervision. The `state` is
        # what distinguishes the two records and it is what the model reads, so
        # it belongs in the key. The same card in two roots still yields one
        # record, because such a duplicate shares its state as well.
        h = hashlib.sha256(
            (r.source + r.quote + r.question + r.state).encode()).hexdigest()
        if h in seen: continue
        seen.add(h); uniq.append(r)
    # AUDIT FIX (round 33): the EMPTY_CORPUS/NO_CARDS checks ran AFTER this I/O,
    # so a failing build left an EMPTY (or truncated) file that a downstream
    # consumer could mistake for a valid corpus. Validated first.
    if not uniq:
        raise ValueError("EMPTY_CORPUS: the harvest produced no records")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for r in uniq:
            fh.write(json.dumps({**asdict(r), "triple": r.to_triple()}) + "\n")
    # AUDIT FIX: an empty harvest must be LOUD, not a silent success.
    if not uniq:
        raise ValueError(
            f"EMPTY_CORPUS: every root produced nothing. roots={root_counts} "
            f"— check PLUTUS_HOME / the harvest files")
    if not cards:
        raise ValueError(
            f"NO_CARDS: the card scan found nothing. roots={root_counts}")
    return {"total": len(uniq), "cards": len(cards), "root_counts": root_counts,
            "golden": len(golden),
            "forensic": len(forensic), "negatives": len(negatives),
            "kinds": {k: sum(1 for r in uniq if r.kind == k)
                      for k in {r.kind for r in uniq}}}
