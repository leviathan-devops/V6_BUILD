import _boot, sys
from pane import PaneModel, render, render_rejections
from gates import TradeCandidate, evaluate

# an adversarial candidate that trips SEVERAL gates at once
bad = TradeCandidate(pair="EUR/USD", direction="long", entry=1.14110, sl=1.13300,
                     tp=1.14200, rrr=0.9, zone_width_pips=10.0, sl_distance_pips=81.0,
                     confidence=0.30, session_utc="2026-07-06T14:30:00-04:00",
                     cascade_valid=False, chain_integrity=False,
                     dedup_key="EU#9", recent_keys=["EU#9"], limite_rrr=9.99)
v = evaluate(bad)
rejs = [{"when":"2026-07-06T14:31Z","token":r.token,"detail":r.detail} for r in v.rejections]

m = PaneModel(pair="EUR/USD", session="OFF_SESSION 14:30",
              decider={"E3.Q1": {"long":0.6,"short":0.2,"no_trade":0.2}},
              gates=[{"gate":r.gate,"passed":r.passed,"token":r.token,"detail":r.detail} for r in v.results],
              rejections=rejs)
text = render(m)

expected = {"G-RRR_REJECT","G-SESSION_REJECT","G-SL_REJECT","G-CONF_REJECT",
            "G-CASCADE_REJECT","G-CHAIN_REJECT","G-DEDUP_REJECT","LIMITE_CODE_DIVERGENCE"}
present = {r.token for r in v.rejections}
ok_all = expected <= present
ok_text = all(t in text for t in expected)
ok_count = len(v.rejections) == 8
ok_notaccepted = not v.accepted

ok = ok_all and ok_text and ok_count and ok_notaccepted
print(f"[TOKEN] test_rejection_log_tokens" if ok else "[TOKEN-ABSENT] test_rejection_log_tokens")
print(f"[DETAIL] rejections fired = {len(v.rejections)}/8 (all 8 = {ok_count})")
print(f"[DETAIL] named tokens present = {sorted(present)}")
print(f"[DETAIL] every token rendered in the pane = {ok_text}")
print(f"[DETAIL] verdict accepted={v.accepted} (must be False: {ok_notaccepted})")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_rejection_log_tokens")
sys.exit(0 if ok else 1)
