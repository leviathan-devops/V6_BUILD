import _boot, sys
from predicates import (trust, trust_all, geometry_witness, at_01_rrr_floor,
                        at_03_direction_sign, at_04_zone_positive, PREDICATE_WITNESSES)

BASE = dict(pair="EUR/USD", direction="long", entry=1.14110, sl=1.13925, tp=1.14395,
            rrr=4.25, zone_width_pips=18.5, sl_distance_pips=18.5, confidence=0.72,
            session_utc="LONDON 02:00", limite_rrr=4.25)

# 1) all applicable witnesses agree -> TRUSTED
t_ok = trust(at_01_rrr_floor, BASE)
ok1 = t_ok.status == "TRUSTED" and all(v for v in t_ok.witnesses.values() if v is not None)

# 2) CODE agrees, LIMITE disagrees -> DIVERGENT
t_div = trust(at_01_rrr_floor, {**BASE, "limite_rrr": 9.99})
ok2 = t_div.status == "DIVERGENT" and t_div.witnesses["LIMITE"] is False

# 3) an inverted geometry -> AT-03 (a GEOMETRY-subject predicate) rejects
geom_bad = geometry_witness({**BASE, "sl": 1.14510, "tp": 1.14100})
ok3 = geom_bad is False
t_inv = trust(at_03_direction_sign, {**BASE, "sl": 1.14510, "tp": 1.14100})
# CODE and GEOMETRY both fail -> unanimous rejection -> TRUSTED_REJECT
ok4 = t_inv.status == "TRUSTED_REJECT"

# 4) a predicate whose subject is CODE only: no LIMITE/GEOMETRY vote
t_zone = trust(at_04_zone_positive, {**BASE, "zone_width_pips": 0.0})
ok5 = t_zone.status == "TRUSTED_REJECT" and "LIMITE" not in t_zone.witnesses

# 5) the witness PANEL is predicate-aware (audit rounds 8 and 13)
#    AUDIT ROUND 13: the map became a PANEL (a tuple of witnesses) because the
#    old single-subject form made the documented 3-way panel unreachable — every
#    predicate had a subject, so the "draw all three" branch never fired.
w = PREDICATE_WITNESSES
ok6 = (w.get("AT-03") == ("GEOMETRY",)            # side inversion IS geometry
       and w.get("AT-01") == ("LIMITE",)           # the floor is ABOUT the model
       and "GEOMETRY" in w.get("AT-09", ())        # the RRR recompute is BOTH
       and w.get("AT-04") == ()                    # zone width: no witness BEARS
       and w.get("AT-05") == () and w.get("AT-10") == ())

# 6) trust_all returns one verdict per predicate
allv = trust_all(BASE)
ok7 = len(allv) == 10 and all(v.predicate.startswith("AT-") for v in allv)

# 7) an invalid direction is refused by the geometry witness
ok8 = geometry_witness({**BASE, "direction": "no_trade"}) is False

ok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8])
print(f"[TOKEN] test_trust_engine_verdicts" if ok else "[TOKEN-ABSENT] test_trust_engine_verdicts")
print(f"[DETAIL] unanimous pass -> {t_ok.status} witnesses={t_ok.witnesses} (pass={ok1})")
print(f"[DETAIL] LIMITE disagrees -> {t_div.status} witnesses={t_div.witnesses} (pass={ok2})")
print(f"[DETAIL] inverted geometry: witness false={ok3} predicate -> {t_inv.status} (pass={ok4})")
print(f"[DETAIL] CODE-only predicate (AT-04 zero zone) -> {t_zone.status} witnesses={t_zone.witnesses} (pass={ok5})")
print(f"[DETAIL] predicate-aware subjects = {ok6} | trust_all -> {len(allv)} verdicts (pass={ok7})")
print(f"[DETAIL] invalid direction refused = {ok8}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_trust_engine_verdicts")
sys.exit(0 if ok else 1)
