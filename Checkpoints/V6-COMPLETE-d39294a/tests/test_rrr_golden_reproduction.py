import _boot, sys
from math_queries import code_truth

# THE 6 TIER-A TRADES — DXY, documented exact.
# SOURCE: MASTER_CONTEXT/PLUTUS_MASTER_CONTEXT_INJECTOR.md:1049
#   "Tier A (8 DXY, documented exact): #1 Mon SS LONG 100.945/100.905/101.115 4.25
#    #2 Mon BS SHORT 101.14/101.200/100.845 4.92 #3 Tue R LONG 100.845/100.77/101.190 4.60
#    #4 Wed SS SHORT 101.19/101.25/100.975 3.58 #5 Wed RWL LONG 100.975/100.905/101.240 3.79
#    #6 Wed BS SHORT 101.235/101.330/100.680 5.84"
# format: (name, entry, SL, TP, documented RRR)
TIER_A = [
    ("#1 Mon SS LONG",   100.945, 100.905, 101.115, 4.25),
    ("#2 Mon BS SHORT",  101.140, 101.200, 100.845, 4.92),
    ("#3 Tue R LONG",    100.845, 100.770, 101.190, 4.60),
    ("#4 Wed SS SHORT",  101.190, 101.250, 100.975, 3.58),
    ("#5 Wed RWL LONG",  100.975, 100.905, 101.240, 3.79),
    ("#6 Wed BS SHORT",  101.235, 101.330, 100.680, 5.84),
]
TOL = 0.02
rows, fails = [], []
for name, entry, sl, tp, expect in TIER_A:
    got = code_truth("L3", entry=entry, sl=sl, tp=tp, pair="DXY")
    delta = abs(got - expect)
    rows.append((name, expect, got, delta))
    if delta > TOL: fails.append((name, expect, got, delta))

ok = not fails
print(f"[TOKEN] test_rrr_golden_reproduction" if ok else "[TOKEN-ABSENT] test_rrr_golden_reproduction")
for name, expect, got, delta in rows:
    print(f"[DETAIL] {'OK ' if delta<=TOL else 'BAD'} {name}: canon {expect:.2f} computed {got:.4f} delta {delta:.4f} (tol {TOL})")
print(f"[DETAIL] {len(rows)-len(fails)}/{len(rows)} within +/-{TOL}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_rrr_golden_reproduction")
sys.exit(0 if ok else 1)
