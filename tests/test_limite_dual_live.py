import _boot, sys, re
"""The LIVE dual-compute: Limite-1B computes, the python shadow verifies.

This is the ONLY test that requires the Limite engine to be up. It is separate
from the golden-week e2e so that a down engine reports BLOCKED here rather than
turning the circuit's geometry test red.
"""
from math_queries import render, code_truth, QUERIES
from dual_compute import verify, DualComputeDivergence

try:
    from limite_client import complete
    complete("Compute 2 + 2. ANSWER: 4", max_tokens=64)
    live = True
except Exception as e:
    live, err = False, f"{type(e).__name__}: {e}"

if not live:
    print(f"[BLOCKED] test_limite_dual_live — the Limite engine is down: {err}")
    print(f"[DETAIL] the dual-compute mechanism is still verified by "
          f"test_dual_compute_catches_divergence and container ADV-5")
    print(f"RESULT: BLOCKED test_limite_dual_live (not a pass)")
    sys.exit(2)

# the 6 Tier-A RRRs, computed BY THE MODEL and verified by the shadow
TIER_A = [("DXY",100.945,100.905,101.115,4.25), ("DXY",101.140,101.200,100.845,4.92),
          ("DXY",100.845,100.770,101.190,4.60), ("DXY",101.190,101.250,100.975,3.58),
          ("DXY",100.975,100.905,101.240,3.79), ("DXY",101.235,101.330,100.680,5.84)]

rows, fails = [], []
for pair, e, sl, tp, canon in TIER_A:
    prompt = render("L3", entry=e, sl=sl, tp=tp, pair=pair)
    raw = complete(prompt, max_tokens=3000)
    m = (re.search(r"ANSWER\s*:\s*(-?\d+(?:\.\d+)?)", raw, re.I)
         or re.search(r"boxed\{(-?\d+(?:\.\d+)?)\}", raw)
         or re.search(r"(-?\d+(?:\.\d+)?)\s*$", raw.strip()))
    got = float(m.group(1)) if m else None
    truth = code_truth("L3", entry=e, sl=sl, tp=tp, pair=pair)
    delta = abs(got - truth) if got is not None else None
    rows.append((pair, e, sl, tp, canon, truth, got, delta))
    if got is None or delta is None or delta > 0.02:
        fails.append((pair, e, sl, tp, canon, truth, got, delta))

ok = not fails
print(f"[TOKEN] test_limite_dual_live" if ok else "[TOKEN-ABSENT] test_limite_dual_live")
for p_,e,sl,tp,canon,truth,got,delta in rows:
    print(f"[DETAIL] {p_} e={e} sl={sl} tp={tp}: canon={canon} shadow={truth} "
          f"limite={got} delta={delta}")
print(f"[DETAIL] {len(rows)-len(fails)}/{len(rows)} within 0.02 of the shadow")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_limite_dual_live")
sys.exit(0 if ok else 1)
