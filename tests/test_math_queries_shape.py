import _boot, sys
from math_queries import QUERIES, render, code_truth

ARGS = {
    "L1": dict(top=1.14200, bottom=1.14100, pair="EUR/USD"),
    "L2": dict(zone_width_pips=10.0, buffer_pips=3.0),
    "L3": dict(entry=1.14110, sl=1.13925, tp=1.14395, pair="EUR/USD"),
    "L4": dict(swing_high=1.14315, swing_low=1.13925),
    "L5": dict(gross_pips=28.5, units=100000, rate=0.001, pair="EUR/USD"),
    "L6": dict(entry=1.14110, tp=1.14395, pair="EUR/USD"),
}
errors, vals = [], {}
for qid, kw in ARGS.items():
    if qid not in QUERIES: errors.append(f"{qid} missing"); continue
    try:
        prompt = render(qid, **kw)
        v = code_truth(qid, **kw)
        vals[qid] = v
        if not isinstance(v, float): errors.append(f"{qid} non-float {v!r}")
        if "ANSWER:" not in prompt: errors.append(f"{qid} prompt lacks ANSWER anchor")
        if "{" in prompt: errors.append(f"{qid} unformatted placeholder in prompt")
    except Exception as e:
        errors.append(f"{qid}: {type(e).__name__}: {e}")

checks = [
    ("L1", 10.0, 1e-6), ("L2", 13.0, 1e-6), ("L3", 1.5405, 0.01),
    ("L4", 1.14072, 0.0001), ("L6", 28.5, 1e-6),
]
for qid, expect, tol in checks:
    if qid in vals and abs(vals[qid] - expect) > tol:
        errors.append(f"{qid} shadow={vals[qid]} expected~{expect}")

ok = not errors
print(f"[TOKEN] test_math_queries_shape" if ok else "[TOKEN-ABSENT] test_math_queries_shape")
for qid in ("L1","L2","L3","L4","L5","L6"):
    if qid in vals: print(f"[DETAIL] {qid} shadow={vals[qid]}")
print(f"[DETAIL] queries={len(QUERIES)} errors={errors}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_math_queries_shape")
sys.exit(0 if ok else 1)
