import _boot, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "corpus"))
from build_corpus import build, scan_cards, harvest_golden_trades, MASTER, V5

OUT = Path(__file__).resolve().parent.parent / ".wt/we-train/corpus/records.jsonl"
stats = build(OUT)
n = sum(1 for _ in OUT.open()) if OUT.exists() else 0

# every record carries its D13 provenance + a VERBATIM quote
bad = []
with OUT.open() as fh:
    for line in fh:
        r = json.loads(line)
        if not r.get("source") or ":" not in r["source"]: bad.append(f"{r['id']} no file:line")
        if not r.get("quote"): bad.append(f"{r['id']} empty quote")
        if not r.get("triple", "").startswith("<|fim_prefix|>"): bad.append(f"{r['id']} bad triple")

ok = n >= 700 and not bad
print(f"[TOKEN] test_corpus_record_count" if ok else "[TOKEN-ABSENT] test_corpus_record_count")
print(f"[DETAIL] records written = {n} (gate: >= 700 -> {n>=700})")
print(f"[DETAIL] stats = {stats}")
print(f"[DETAIL] provenance/quote/triple violations = {len(bad)}")
for b in bad[:5]: print(f"[DETAIL]   {b}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_corpus_record_count")
sys.exit(0 if ok else 1)
