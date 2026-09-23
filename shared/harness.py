"""shared/harness.py — the V6 test harness.
Every test prints a machine-readable PASS/FAIL line + a passToken in a tool result.
Usage:  python3 harness.py <test_name>
Exit 0 = PASS, exit 1 = FAIL, exit 2 = BLOCKED (named reason).
A pass is VALID only when the passToken appears in THIS stdout.
"""
import sys, json, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "shared" / "fixtures"

def emit(name, ok, passtoken, detail):
    print(f"[TOKEN] {passtoken}" if ok else f"[TOKEN-ABSENT] {passtoken}")
    print(f"[DETAIL] {detail}")
    print(f"RESULT: {'PASS' if ok else 'FAIL'} {name}")
    return 0 if ok else 1

def blocked(name, reason):
    print(f"BLOCKED: {name} — {reason}")
    return 2

def golden_bars():
    p = FIXTURES / "bars_raw.json"
    if not p.exists(): return None
    return json.loads(p.read_text())

def golden_entries():
    """The 15 canon entries from the V5 oracle (OR-1)."""
    return [
        ("EU","#1 Mon SHORT E",1.14395),("EU","#1 TP",1.14110),("EU","#2 Mon LONG E",1.14110),
        ("EU","#2 TP",1.14460),("EU","#3 Tue SHORT E",1.14460),("EU","#4 Wed LONG E",1.14020),
        ("EU","#5 Wed SHORT E",1.14295),("EU","#6 Wed LONG E",1.13935),("EU","#7 Thu LONG E",1.14225),
        ("EU","#8 Fri SHORT E",1.14555),("GU","#1 Mon LONG E",1.33330),("GU","#2 (chained)",1.33965),
        ("GU","#3 Wed SHORT E",1.33660),("GU","#4 Wed LONG E",1.33280),("GU","#5 Thu SHORT E",1.34260),
        ("GU","#6 Thu LONG E",1.33850),("GU","#7 Fri SHORT E",1.34500),
    ]

def tier_a_rrr():
    """The 6 Tier-A RRRs (OR-6)."""
    return {"EU#1":4.25,"EU#2":4.92,"GU#1":4.60,"GU#3":3.58,"GU#4":3.79,"GU#7":5.84}

def sha(path):
    h = hashlib.sha256()
    h.update(pathlib.Path(path).read_bytes())
    return h.hexdigest()[:16]
