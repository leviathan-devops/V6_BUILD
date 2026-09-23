import _boot, sys
from predicates import (at_03_direction_sign, at_01_rrr_floor, at_09_rrr_recompute,
                        PREDICATES, trust, trust_all, TrustVerdict)

BASE = dict(pair="EUR/USD", direction="long", entry=1.14110, sl=1.13925, tp=1.14395, rrr=1.5405,
            zone_width_pips=10.0, sl_distance_pips=18.5, confidence=0.72,
            session_utc="2026-07-06T02:30:00-04:00", limite_rrr=1.5405)

# AT-03 is the SIDE-INVERSION predicate — the V5 mutant class.
ok_long  = at_03_direction_sign({**BASE, "direction":"long"}).passed
ok_short = at_03_direction_sign({**BASE, "direction":"short","sl":1.14510,"tp":1.13700}).passed
inv_long = at_03_direction_sign({**BASE, "direction":"long","sl":1.14510,"tp":1.14100})
inverted_caught = (not inv_long.passed) and inv_long.token == "AT03_SIDE_INVERSION"
inv_short = at_03_direction_sign({**BASE, "direction":"short","sl":1.13925,"tp":1.14395})
ok_inv_short = (not inv_short.passed)

# the full predicate set: all 10 execute and return named verdicts
vs = [p(BASE) for p in PREDICATES]
all_named = all(v.name.startswith("AT-") and isinstance(v.token, str) and v.token for v in vs)
n_at = sum(1 for v in vs if v.name == "AT-03")
# AT-09 must catch a stated/derived RRR mismatch
mism = at_09_rrr_recompute({**BASE, "rrr": 9.99})
ok_mismatch = (not mism.passed) and mism.token == "AT09_RRR_MISMATCH"

ok = (ok_long and ok_short and inverted_caught and ok_inv_short
      and all_named and n_at == 1 and ok_mismatch)
print(f"[TOKEN] test_mpse_predicate_at03" if ok else "[TOKEN-ABSENT] test_mpse_predicate_at03")
print(f"[DETAIL] long geometry pass={ok_long} | short geometry pass={ok_short}")
print(f"[DETAIL] inverted long caught={inverted_caught} token={inv_long.token}")
print(f"[DETAIL] inverted short caught={ok_inv_short}")
print(f"[DETAIL] {len(PREDICATES)} predicates execute, all named={all_named}")
print(f"[DETAIL] AT-09 catches stated/derived mismatch={ok_mismatch} ({mism.detail})")
print(f"[DETAIL] verdicts: {[v.token for v in vs]}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_mpse_predicate_at03")
sys.exit(0 if ok else 1)
