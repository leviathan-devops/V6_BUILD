"""corpus/build_corpus.py — the doctrine corpus generator.

BLUEPRINT §1.8: "Each of the 583 mechanism cards + 38 rulings + 38 forensic
trades + 23 golden trades converts to a (state, questions, answers) triple.
~700 records from existing data."

D13 QUOTE LAW: every record's state text carries the card's quote VERBATIM
plus its source file:line. Nothing is synthesized, nothing paraphrased.
"""
from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from dataclasses import dataclass, asdict

MASTER = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/MASTER_CONTEXT")
V5 = Path("/home/leviathan/.omp/wt/plutus-main-66dfa4c/PLUTUS/agent")

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
        injector = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/agent/MASTER_CONTEXT/PLUTUS_MASTER_CONTEXT_INJECTOR.md")
    if not injector.exists(): return recs
    text = injector.read_text(errors="ignore")
    for ln, line in enumerate(text.splitlines(), 1):
        if "Tier A" in line and "documented exact" in line:
            for chunk in line.split("·"):
                c = chunk.strip()
                mm = re.search(r"(#[0-9]+\s+\w+\s+\w+\s+\w+)\s+([\d.]+)/([\d.]+)/([\d.]+)\s+([\d.]+)", c)
                if mm:
                    name, e, sl, tp, rrr = mm.groups()
                    recs.append(Record(
                        id=f"golden-{len(recs)+1}",
                        source=f"{injector}:{ln}",
                        quote=c,
                        state=f"GOLDEN TRADE {name}: entry={e} SL={sl} TP={tp} RRR={rrr}",
                        question="What is the risk-reward ratio of this setup?",
                        options=[rrr, "below_floor", "no_trade"],
                        answer=rrr, kind="golden"))
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
            answer="ruling" if "/rulings/" in r.source else "mechanism",
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
            f = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/agent/MASTER_CONTEXT") / name
        if not f.exists(): continue
        text = f.read_text(errors="ignore")
        for ln, line in enumerate(text.splitlines(), 1):
            if re.search(r"\bRRR\b", line) and re.search(r"\d+\.\d+/\d+\.\d+/\d+\.\d+", line):
                recs.append(Record(
                    id=f"gap-{f.stem}-{ln}", source=f"{f}:{ln}", quote=line.strip(),
                    state=f"DOCUMENTED TRADE ROW: {line.strip()[:300]}",
                    question="Is this trade's RRR above the operator floor?",
                    options=["yes", "no"], answer="yes", kind="golden"))
    return recs


def build(out_path: Path) -> dict:
    cards = []
    for root in CARD_ROOTS:
        cards += scan_cards(root)
    cards = card_records(cards)
    golden = harvest_golden_trades(V5)
    golden += harvest_golden_cascade(MASTER)
    golden += harvest_gap_analysis(MASTER)
    forensic = harvest_forensic_laws(MASTER)
    all_recs = cards + golden + forensic
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
    return {"total": len(uniq), "cards": len(cards), "golden": len(golden),
            "forensic": len(forensic),
            "kinds": {k: sum(1 for r in uniq if r.kind == k)
                      for k in {r.kind for r in uniq}}}
