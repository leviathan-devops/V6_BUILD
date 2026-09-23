import _boot, sys
from oms import simulate, TradeDecision, PIP, PIP_VALUE_PER_UNIT

# ADVERSARIAL 1: a LONG that hits TP must be profitable
d_tp = TradeDecision("EUR/USD","long",1.14110,1.13925,1.14395,1.54,0.72,zone_id="A")
pf = simulate([d_tp], 0.0, {"A":"tp"})
ok1 = pf.net_pips_total > 0

# ADVERSARIAL 2: the SAME long hitting SL must be negative
pf_sl = simulate([d_tp], 0.0, {"A":"sl"})
ok2 = pf_sl.net_pips_total < 0

# ADVERSARIAL 3: a SHORT trades the opposite sign
d_sh = TradeDecision("EUR/USD","short",1.14395,1.14510,1.14110,1.54,0.72,zone_id="B")
pf_sh = simulate([d_sh], 0.0, {"B":"tp"})
ok3 = pf_sh.net_pips_total > 0

# ADVERSARIAL 4: DXY uses pip=0.01, not 0.0001
d_dxy = TradeDecision("DXY","long",100.945,100.905,101.115,4.25,0.78,zone_id="C")
pf_dxy = simulate([d_dxy], 0.0, {"C":"tp"})
expected_dxy = round((101.115-100.945)/0.01, 4)   # 17.0 pips
ok4 = abs(pf_dxy.gross_pips_total - expected_dxy) < 1e-6
ok5 = abs(pf.gross_pips_total - round((1.14395-1.14110)/0.0001,4)) < 1e-6   # 28.5

# ADVERSARIAL 5: the blueprint's worked example — 0.1% => 20.0 pips cost on FX
from oms import Fill
f = Fill("EUR/USD","long",1.14110,1.14395,100000,0.001)
ok6 = abs(f.cost_pips - 20.0) < 1e-6
ok7 = abs(f.net_pips - 8.5) < 0.01    # blueprint §2.3: 28.5 - 20.0 = 8.5

ok = all([ok1,ok2,ok3,ok4,ok5,ok6,ok7])
print(f"[TOKEN] test_oms_execute_order" if ok else "[TOKEN-ABSENT] test_oms_execute_order")
print(f"[DETAIL] long@TP={pf.net_pips_total:+.1f}p (pass={ok1}) | long@SL={pf_sl.net_pips_total:+.1f}p (pass={ok2})")
print(f"[DETAIL] short@TP={pf_sh.net_pips_total:+.1f}p (pass={ok3})")
print(f"[DETAIL] DXY gross={pf_dxy.gross_pips_total:.1f}p expect {expected_dxy} (pass={ok4})")
print(f"[DETAIL] FX gross={pf.gross_pips_total:.1f}p expect 28.5 (pass={ok5})")
print(f"[DETAIL] blueprint worked example: cost={f.cost_pips}p expect 20.0 (pass={ok6}) net={f.net_pips}p expect 8.5 (pass={ok7})")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_oms_execute_order")
sys.exit(0 if ok else 1)
