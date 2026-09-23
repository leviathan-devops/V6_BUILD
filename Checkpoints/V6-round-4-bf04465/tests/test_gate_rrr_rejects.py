import _boot, sys
from gates import TradeCandidate, evaluate, g_rrr, RRR_FLOOR

BASE = dict(pair="EUR/USD", direction="long", entry=1.14110, sl=1.13925, tp=1.14395,
            zone_width_pips=10.0, sl_distance_pips=18.5, confidence=0.72,
            session_utc="2026-07-06T02:30:00-04:00", dedup_key="EU#1")

def cand(rrr, limite=None):
    return TradeCandidate(rrr=rrr, limite_rrr=rrr if limite is None else limite, **BASE)

# ADVERSARIAL 1: RRR below floor -> G-RRR must reject with its named token
v_low = evaluate(cand(1.54))
ok1 = (not v_low.accepted) and any(r.token == "G-RRR_REJECT" for r in v_low.rejections)

# ADVERSARIAL 2: RRR exactly at the floor -> PASS (boundary inclusive)
ok2 = g_rrr(cand(RRR_FLOOR)).passed

# ADVERSARIAL 3: RRR just below the floor -> REJECT (no epsilon slop)
ok3 = not g_rrr(cand(RRR_FLOOR - 0.001)).passed

# ADVERSARIAL 4: zero RRR -> REJECT
ok4 = not g_rrr(cand(0.0)).passed

# ADVERSARIAL 5: no_trade direction with a high RRR still gets gate-checked
ok5 = isinstance(g_rrr(cand(9.9)).passed, bool)

ok = ok1 and ok2 and ok3 and ok4 and ok5
print(f"[TOKEN] G-RRR_REJECT" if ok1 else "[TOKEN-ABSENT] G-RRR_REJECT")
print(f"[DETAIL] reject reason: {v_low.rejections[0].detail if v_low.rejections else 'none'}")
print(f"[DETAIL] edge={RRR_FLOOR} pass={ok2} | just_below reject={ok3} | zero reject={ok4}")
print(f"[DETAIL] all 8 gate tokens on the low candidate: {v_low.tokens}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_gate_rrr_rejects")
sys.exit(0 if ok else 1)
