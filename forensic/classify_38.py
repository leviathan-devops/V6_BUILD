"""forensic/classify_38.py — classify the documented winning trades against the
7 universal laws.

THE SOURCE (all on disk, all text):
  MASTER_CONTEXT/FORENSIC_ANALYSIS_38_TRADES.md
      the 7 UNIVERSAL LAWS, each confirmed across all 38 trades by VLM analysis
  ARCHIVE/agent/Visual_Evals/v4.5.1/SL_vs_ENTRY_ANALYSIS.md
      30 rows: win N | pair DIRECTION day | SL <p> MAE <p> util <x> -> a verdict
  ARCHIVE/agent/Visual_Evals/v4.5.1/OUTCOME_AUDIT.md
      36 setups: per-pair win/loss counts and total R

WHY THIS IS A CLASSIFICATION AND NOT A RE-READING. Each law is a PREDICATE over
a trade's measurable attributes. A trade is CLASSIFIED as OBEYING a law when the
predicate holds, and as VIOLATING it when the predicate fails — and the source's
own verdict is the ground truth to score against. The laws are applied; the
numbers are not restated.

THE HONEST SCOPE. The source data carries SL distance, MAE and the util ratio —
not entry/SL/TP prices. So the laws are classified where the data supports it:
  LAW 1 (entry at a zone edge)      -- not testable from SL/MAE alone
  LAW 2 (SL at the invalidation pt) -- testable via the SL distance vs the zone
  LAW 3 (SL buffer 2-5 pips)        -- not testable (the buffer is not recorded)
  LAW 4 (TP at an opposing zone)    -- not testable
  LAW 5 (the LSZ is a shield)       -- not testable
  LAW 6 (RRR is a consequence)      -- testable via the util ratio's own verdict
  LAW 7 (ladder entries, same zone) -- testable via the repeated identical rows
A law with no testable attribute is reported as NOT CLASSIFIABLE for that trade,
never as a pass.
"""
from __future__ import annotations
import os, re
from pathlib import Path
from dataclasses import dataclass

# AUDIT FIX: env-overridable, and a missing file is a NAMED failure rather than
# a FileNotFoundError from deep inside a parser.
PLUTUS = Path(os.environ.get(
    "PLUTUS_HOME", "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS"))
# PORTABILITY: the three sources are looked up in the PLUTUS tree first, then in
# a `sources/` directory beside this module — so the classifier runs in a
# container where only the circuit plus the three documents were copied.
_HERE = Path(__file__).resolve().parent
_LOCAL = _HERE.parent / "sources"


def _source(rel: str) -> Path:
    """Resolve a source document.

    PLUTUS-relative first (the real tree), then a FLAT `sources/` beside this
    module by BASENAME — a container copy does not reproduce the tree's nested
    directories, so `sources/MASTER_CONTEXT/FORENSIC...md` will not exist while
    `sources/FORENSIC...md` will.
    """
    for cand in (PLUTUS / rel, _LOCAL / rel, _LOCAL / Path(rel).name):
        if cand.exists():
            return cand
    return PLUTUS / rel          # report the PLUTUS path in the error


FORENSIC = _source("MASTER_CONTEXT/FORENSIC_ANALYSIS_38_TRADES.md")
SLDOC = _source("ARCHIVE/agent/Visual_Evals/v4.5.1/SL_vs_ENTRY_ANALYSIS.md")
OUTCOME = _source("ARCHIVE/agent/Visual_Evals/v4.5.1/OUTCOME_AUDIT.md")

LAW_RE = re.compile(r"^###\s+(LAW\s+\d+):\s*(.+?)\s*$", re.M)
ROW_RE = re.compile(
    r"^- win (\d+): ([A-Z/]+) (LONG|SHORT) (\w+)\s*\|\s*SL ([\d.]+)p MAE ([\d.]+)p "
    r"util ([\d.]+) → \*\*(.+?)\*\*", re.M)


@dataclass
class Trade:
    n: int
    pair: str
    direction: str
    day: str
    sl_pips: float
    mae_pips: float
    util: float
    source_verdict: str

    @property
    def sl_too_wide(self) -> bool:
        return "SL TOO WIDE" in self.source_verdict


@dataclass
class LawVerdict:
    law: str
    title: str
    tested: int = 0
    obeyed: int = 0
    violated: int = 0
    not_classifiable: int = 0
    note: str = ""

    @property
    def coverage(self) -> float:
        return self.tested / max(self.tested + self.not_classifiable, 1)


def _read(p: Path) -> str:
    if not p.exists():
        raise FileNotFoundError(f"SOURCE_MISSING: {p} (set PLUTUS_HOME if the tree moved)")
    return p.read_text(errors="ignore")


def parse_laws() -> list[tuple[str, str]]:
    text = _read(FORENSIC)
    laws = [(m.group(1), m.group(2).strip()) for m in LAW_RE.finditer(text)]
    # AUDIT FIX: a format drift silently yielded zero laws and the classification
    # "succeeded" with nothing to classify.
    if not laws:
        raise ValueError(f"NO_LAWS_PARSED: the LAW heading pattern matched nothing in {FORENSIC}")
    return laws


def parse_trades() -> list[Trade]:
    text = _read(SLDOC)
    out = []
    for m in ROW_RE.finditer(text):
        n, pair, direction, day, sl, mae, util, verdict = m.groups()
        out.append(Trade(int(n), pair, direction, day, float(sl), float(mae),
                         float(util), verdict))
    if not out:
        raise ValueError(f"NO_TRADES_PARSED: the row pattern matched nothing in {SLDOC}")
    return out


def parse_outcome() -> dict:
    text = OUTCOME.read_text(errors="ignore")
    d = {}
    m = re.search(r"Setups:\s*(\d+)\s*\|\s*WIN\s*(\d+)\s*\|\s*LOSS\s*(\d+)", text)
    if m:
        d["setups"], d["win"], d["loss"] = (int(x) for x in m.groups())
    per = {}
    for m in re.finditer(r"- ([A-Z/]+): (\d+) setups \| (\d+)W/(\d+)L \| win rate (\d+)% \| total ([+-][\d.]+)R", text):
        per[m.group(1)] = {"setups": int(m.group(2)), "w": int(m.group(3)),
                           "l": int(m.group(4)), "win_rate": int(m.group(5)),
                           "total_R": float(m.group(6))}
    d["per_pair"] = per
    return d


def classify(trades: list[Trade], laws: list[tuple[str, str]]) -> dict[str, LawVerdict]:
    """Apply each law as a PREDICATE over the trades that can test it."""
    out: dict[str, LawVerdict] = {}
    for law, title in laws:
        v = LawVerdict(law, title)
        low = title.lower()

        if "zone edge" in low:
            # LAW 1: the source data carries no entry price -> not testable
            v.not_classifiable = len(trades)
            v.note = ("the row data has SL/MAE/util but no entry price; the law "
                      "is stated as confirmed across all 38 by the source's own "
                      "VLM pass, and is NOT re-derived here")
        elif "structural invalidation" in low or "fixed pip distance" in low:
            # LAW 2: the SL tracks the ZONE, not a fixed pip buffer.
            #
            # PROBE DEFECT FIXED (2026-09-23). The first version called a SHARED
            # SL distance a fixed-buffer violation — which CONTRADICTS LAW 7
            # (ladder entries on ONE zone legitimately share an SL). The two
            # predicates disagreed on the same rows.
            #
            # The sound signal is the SPREAD, not the sharing: a fixed buffer
            # produces a CONSTANT SL across trades, while a structural SL varies
            # with each zone's width. The law is OBEYED when the distances vary.
            # AUDIT FIX (round 7): a single aggregate verdict for all trades
            # contradicted the per-trade model. The per-trade predicate: a
            # FIXED-BUFFER SL is a CONSTANT distance, so a trade whose SL equals
            # the modal (most common) SL is the fixed-buffer case; a trade with
            # its own distance is a structural SL.
            import statistics
            from collections import Counter as _C
            dist = [t.sl_pips for t in trades]
            modal, modal_n = _C(dist).most_common(1)[0]
            spread = statistics.pstdev(dist) if len(dist) > 1 else 0.0
            mean = statistics.mean(dist) if dist else 0.0
            for t in trades:
                v.tested += 1
                if t.sl_pips == modal and modal_n > 1:
                    v.violated += 1      # shares the modal distance = a buffer
                else:
                    v.obeyed += 1        # its own distance = structural
            v.note = (f"per-trade: the modal SL {modal}p recurs {modal_n}x; "
                      f"spread mean {mean:.1f}p sd {spread:.1f}p")
        elif "buffer" in low:
            v.not_classifiable = len(trades)
            v.note = "the buffer is not a recorded column"
        elif "opposing zone" in low or "higher timeframe" in low:
            v.not_classifiable = len(trades)
            v.note = "no TP column in the row data"
        elif "lsz" in low or "shield" in low:
            v.not_classifiable = len(trades)
            v.note = "no shield column in the row data"
        elif "consequence" in low or "target" in low:
            # LAW 6: RRR is a consequence, not a target. The source's util
            # verdict is exactly this test: a util < 0.40 says the SL was set
            # too wide (a target), not derived from the structure.
            for t in trades:
                v.tested += 1
                if t.sl_too_wide:
                    v.violated += 1
                else:
                    v.obeyed += 1
            v.note = ("util < 0.40 (the source's 'SL TOO WIDE') is the signature "
                      "of an SL chosen as a target rather than derived")
        elif "ladder" in low or "same zone" in low:
            # LAW 7: ladder entries share a zone. Identical SL rows on the same
            # pair+day are ladder entries on one zone -> the law holds for them.
            from collections import Counter
            c = Counter((t.pair, t.day) for t in trades)
            for t in trades:
                v.tested += 1
                if c[(t.pair, t.day)] > 1:
                    v.obeyed += 1        # a ladder
                else:
                    v.not_classifiable += 1
            v.tested -= v.not_classifiable
            v.note = "a shared pair+day identifies a ladder"
        else:
            v.not_classifiable = len(trades)
            v.note = "no predicate derived for this law"
        out[law] = v
    return out


def run() -> dict:
    laws = parse_laws()
    trades = parse_trades()
    outcome = parse_outcome()
    verdicts = classify(trades, laws)
    n_obey = sum(1 for v in verdicts.values() if v.tested and v.violated == 0)
    n_viol = sum(1 for v in verdicts.values() if v.tested and v.violated > 0)
    n_unc = sum(1 for v in verdicts.values() if not v.tested)
    return {"laws": laws, "trades": trades, "outcome": outcome,
            "verdicts": verdicts, "n_obeyed_clean": n_obey,
            "n_with_violations": n_viol, "n_unclassifiable": n_unc}
