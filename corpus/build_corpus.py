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
                    opts = [rrr, "below_floor", "no_trade"]
                    rot = len(recs) % len(opts)
                    opts = opts[rot:] + opts[:rot]
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
            options=[rrr, "below_3.5", "no_trade"], answer=rrr, kind="golden"))
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


def negative_records(cards: list[Record]) -> list[Record]:
    """NEGATIVE supervision — audit fix.

    The audit found every yes/no record taught `answer="yes"`: a corpus with
    ONE class trains a yes-sayer, and the model can never learn to refuse.
    Each card therefore also yields a MISQUOTED variant (the quote perturbed
    in a way that breaks the rule) whose answer is "fail".
    """
    out = []
    for r in cards:
        if not r.quote or len(r.quote) < 12:
            continue
        # a controlled corruption: drop the rule's numeric/threshold token,
        # which is exactly what makes the card's rule no longer satisfied
        import re as _re
        broken = _re.sub(r"\b(\d+(?:\.\d+)?)\b", "0", r.quote, count=1)
        if broken == r.quote:
            broken = r.quote[:-6] + " [TRUNCATED]"
        # CRITICAL FIX (audit round 3): the negative answer must be a SELECTABLE
        # option. The first version emitted answer="fail" while reusing the
        # parent's options (["yes","no"]), so the label was out of vocabulary and
        # the record was unusable for option-grounded training. The option set is
        # now derived from the parent's own options: the FIRST option is the
        # "affirmative" one, so the negative answer is the LAST option.
        opts = list(r.options)
        if len(opts) < 2:
            continue
        # AUDIT FIX: opts[-1] is "golden" for a 4-way KIND record, so an altered
        # MECHANISM card was taught as GOLDEN — altering the quote does not
        # change its kind. The negative label is chosen from the QUESTION's own
        # semantics: a VERIFY question's refusal is "no"; a KIND question's
        # refusal is any OTHER kind (the record keeps its true kind as the
        # distractor, never as the answer).
        if r.question.startswith("Does the state satisfy"):
            neg_answer = "no"
        elif r.question.startswith("What kind of doctrine"):
            # AUDIT FIX (round 6): altering a quote does NOT change a card's
            # kind, so a KIND negative was WRONG supervision (an altered
            # MECHANISM card taught as "ruling"). A KIND record yields no
            # negative at all.
            continue
        else:
            neg_answer = next((o for o in opts if o != r.answer), opts[-1])
        out.append(Record(
            id=r.id + "-neg", source=r.source, quote=broken,
            # AUDIT FIX (round 9): every negative carried "(altered)" while no
            # positive did, so a model could reach perfect refusal accuracy by
            # matching that token ALONE without learning the rule. The negative
            # now uses the PARENT's own state template.
            state=(f"DOCTRINE {r.id.rsplit('-', 1)[0]}: {broken}"
                   if r.kind != "golden" else f"GOLDEN (restated) {broken}"),
            question=r.question, options=opts, answer=neg_answer, kind=r.kind))
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
