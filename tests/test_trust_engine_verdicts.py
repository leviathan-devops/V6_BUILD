import _boot, sys
from predicates import trust, trust_all, geometry_witness, at_01_rrr_floor, at_03_direction_sign

BASE = dict(pair="EUR/USD", direction="long", entry=1.14110, sl=1.13925, tp=1.14395,
            rrr=4.25, zone_width_pips=10.0, sl_distance_pips=18.5, confidence=0.72,
            session_utc="2026-07-06T02:30:00-04:00", limite_rrr=4.25)

# 1) all three witnesses agree -> TRUSTED
t_ok = trust(at_01_rrr_floor, BASE)
ok1 = t_ok.status == "TRUSTED" and all(t_ok.witnesses.values())

# 2) CODE and GEOMETRY agree, LIMITE disagrees -> DIVERGENT
t_div = trust(at_01_rrr_floor, {**BASE, "limite_rrr": 9.99})
ok2 = t_div.status == "DIVERGENT" and (not t_div.witnesses["LIMITE"])

# 3) an inverted geometry -> the geometry witness is FALSE
geom_bad = geometry_witness({**BASE, "sl": 1.14510, "tp": 1.14100})
ok3 = geom_bad is False
t_inv = trust(at_03_direction_sign, {**BASE, "sl": 1.14510, "tp": 1.14100})
ok4 = t_inv.status == "DIVERGENT" and not t_inv.witnesses["GEOMETRY"]

# 4) an rrr below floor with a matching model value -> all agree it FAILS,
#    so CODE=False but witnesses agree -> DIVERGENT (a real rejection, not noise)
t_low = trust(at_01_rrr_floor, {**BASE, "rrr": 1.0, "limite_rrr": 1.0})
ok5 = t_low.status in ("DIVERGENT", "INCONCLUSIVE")

# 5) trust_all returns one verdict per predicate
allv = trust_all(BASE)
ok6 = len(allv) == 10 and all(v.predicate.startswith("AT-") for v in allv)

ok = ok1 and ok2 and ok3 and ok4 and ok5 and ok6
print(f"[TOKEN] test_trust_engine_verdicts" if ok else "[TOKEN-ABSENT] test_trust_engine_verdicts")
print(f"[DETAIL] 3-way agreement -> {t_ok.status} witnesses={t_ok.witnesses} (pass={ok1})")
print(f"[DETAIL] LIMITE disagrees -> {t_div.status} witnesses={t_div.witnesses} (pass={ok2})")
print(f"[DETAIL] geometry witness false on inversion={ok3} | predicate DIVERGENT={ok4}")
print(f"[DETAIL] rrr below floor -> {t_low.status} (pass={ok5})")
print(f"[DETAIL] trust_all -> {len(allv)} verdicts (pass={ok6})")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_trust_engine_verdicts")
sys.exit(0 if ok else 1)
