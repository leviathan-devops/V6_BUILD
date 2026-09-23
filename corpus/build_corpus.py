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


def scan_cards(root: Path) -> list[Record]:
    """Every markdown card under `root` with a frontmatter `quote:` becomes a record."""
    recs = []
    if not root.exists(): return recs
    for f in sorted(root.rglob("*.md")):
        try: text = f.read_text(errors="ignore")
        except Exception: continue
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
            options=["mechanism", "ruling", "forensic", "golden"],
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
            _m = re.search(r"(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)\s+([\d.]+)", line)
            try:
                _rrr = float(_m.group(4)) if _m else None
            except ValueError:
                # AUDIT FIX: `[\d.]+` can match a bare "." (an ellipsis in prose)
                # and float(".") aborted the whole harvest.
                _rrr = None
            if _rrr is not None and _rrr >= 3.5 and re.search(r"\bRRR\b", line):
                recs.append(Record(
                    id=f"gap-{f.stem}-{ln}", source=f"{f}:{ln}", quote=line.strip(),
                    state=f"DOCUMENTED TRADE ROW: {line.strip()[:300]}",
                    question="Is this trade's RRR above the operator floor?",
                    options=["yes", "no"], answer="yes", kind="golden"))
    return recs


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
        ns = re.sub(r"(\d+\.\d+/\d+\.\d+/\d+\.\d+\s+)([\d.]+)",
                    r"\g<1>2.0", r.state)
        if ns == r.state:
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
        if not re.search(r"\b\d+(?:\.\d+)?\b", r.quote):
            return None                      # no numeric token -> no negative
        broken = re.sub(r"\b(\d+(?:\.\d+)?)\b", "0", r.quote, count=1)
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
        if not re.search(r"\b\d+(?:\.\d+)?\b", body):
            return None
        nbody = re.sub(r"\b\d+(?:\.\d+)?\b", "0", body, count=1)
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
        out.append(Record(id=r.id + "-neg", source=r.source, quote=nq,
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
    # AUDIT FIX: negatives covered only the card records, so the forensic and
    # golden/gap yes-no questions had ZERO refusal supervision (a yes-sayer
    # bias). Every harvested kind now contributes negatives.
    negatives = negative_records(cards + golden + forensic)
    all_recs = cards + negatives + golden + forensic
    seen, uniq = set(), []
    for r in all_recs:
        # the dedup key is (source, quote, QUESTION): the same card legitimately
        # yields several distinct training signals, but the same card found in
        # two roots yields only one. Keying on source+quote alone would collapse
        # the intentional multi-signal records into one.
        h = hashlib.sha256((r.source + r.quote + r.question).encode()).hexdigest()
        if h in seen: continue
        seen.add(h); uniq.append(r)
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
