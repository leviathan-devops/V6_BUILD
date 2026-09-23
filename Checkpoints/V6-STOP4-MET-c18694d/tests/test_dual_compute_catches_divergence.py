import _boot, sys
from dual_compute import verify, verify_strict, DualComputeDivergence

# ADVERSARIAL: a deliberately wrong Limite output must be CAUGHT
wrong = 3.99   # true RRR is ~1.5405
r_bad = verify("L3", wrong, entry=1.14110, sl=1.13925, tp=1.14395, pair="EUR/USD")
caught = (not r_bad.passed) and r_bad.token == "LIMITE_CODE_DIVERGENCE"

# STRICT path must RAISE, never silently continue
raised = False
try:
    verify_strict("L3", wrong, entry=1.14110, sl=1.13925, tp=1.14395, pair="EUR/USD")
except DualComputeDivergence as e:
    raised = "LIMITE_CODE_DIVERGENCE" in str(e)

# the honest answer must PASS
r_good = verify("L3", 1.5405, entry=1.14110, sl=1.13925, tp=1.14395, pair="EUR/USD")
good = r_good.passed and r_good.token == "G-DUAL_PASS"

ok = caught and raised and good
print(f"[TOKEN] LIMITE_CODE_DIVERGENCE" if caught else "[TOKEN-ABSENT] LIMITE_CODE_DIVERGENCE")
print(f"[DETAIL] wrong={wrong} code={r_bad.code:.4f} delta={r_bad.delta:.4f} eps={r_bad.eps} passed={r_bad.passed}")
print(f"[DETAIL] strict path raised={raised}")
print(f"[DETAIL] honest={r_good.model} delta={r_good.delta:.4f} passed={good}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_dual_compute_catches_divergence")
sys.exit(0 if ok else 1)
