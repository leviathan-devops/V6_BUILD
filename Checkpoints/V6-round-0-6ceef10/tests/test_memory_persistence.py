import _boot, sys, tempfile, os, pathlib
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det/memory")
from memory_store import MemoryStore, Row

tmp = tempfile.mkdtemp()
p = os.path.join(tmp, "m.sqlite")

# 1) write rows, close, REOPEN from a fresh handle -> every row survives
s1 = MemoryStore(p, writer="plutus-v6")
s1.append("doctrine", "obcv-displacement-gate", "body >=1.5x avg AND range >=1.5x ATR", 1783317600000, "MACRO.md:57")
s1.append("doctrine", "rrr-floor", "NOT A SINGLE ONE OF MY TRADES IS BELOW RRR = 3.5", 1783317600001, "OPERATOR:2026-07-29")
n1 = s1.count()
s1.close()

s2 = MemoryStore(p, writer="plutus-v6")
n2 = s2.count()
rows = s2.rows("doctrine")
survived = n2 == n1 == 2 and len(rows) == 2

# 2) APPEND-ONLY: a correction is a NEW row, the old row is untouched
before = [r.digest for r in s2.rows("doctrine")]
s2.append("doctrine", "rrr-floor", "CORRECTION: floor is 2.5 on the FX path", 1783317600002, "OPERATOR:2026-09-23")
after = s2.rows("doctrine")
append_only = len(after) == 3 and [r.digest for r in after[:2]] == before

# 3) one-writer-per-bank: a foreign writer is REFUSED, loudly
refused = False
try:
    MemoryStore(p, writer="some-other-agent").append("doctrine", "x", "y", 1, "src")
except PermissionError as e:
    refused = "BANK_OWNED_BY_OTHER" in str(e)

# 4) a different bank is free for a different writer
ok_other = True
try:
    MemoryStore(p, writer="reports-writer").append("reports", "k", "v", 2, "src")
except Exception:
    ok_other = False

# 5) the digest is stable for identical content
s3 = MemoryStore(p, writer="plutus-v6")
r = s3.append("doctrine", "k2", "v2", 99, "src")
r2 = s3.append("doctrine", "k2", "v2", 99, "src")
stable_digest = (r.digest == r2.digest)
total = s3.count()
s3.close()

ok = survived and append_only and refused and ok_other and stable_digest
print(f"[TOKEN] test_memory_persistence" if ok else "[TOKEN-ABSENT] test_memory_persistence")
print(f"[DETAIL] rows before close={n1} after reopen={n2} survived={survived}")
print(f"[DETAIL] append-only: 2 -> 3 rows, prior digests untouched={append_only}")
print(f"[DETAIL] foreign writer refused with BANK_OWNED_BY_OTHER={refused}")
print(f"[DETAIL] a different bank admits a different writer={ok_other}")
print(f"[DETAIL] identical content -> identical digest={stable_digest}")
print(f"[DETAIL] final row count={total}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_memory_persistence")
sys.exit(0 if ok else 1)
