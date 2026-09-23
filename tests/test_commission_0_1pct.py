import _boot, sys, json
from oms import commission_sensitivity, TradeDecision
from golden_decisions import ALL_GOLDEN, DXY_TIER_A, fx_golden_week

# MEASURE at the three canon levels (0% / 0.1% / 0.2% round trip)
from golden_decisions import GOLDEN_OUTCOMES
DXY_OUT = {d.zone_id: "tp" for d in DXY_TIER_A}
FX_OUT  = {d.zone_id: "tp" for d in fx_golden_week()}
dxy  = commission_sensitivity(DXY_TIER_A, outcomes=DXY_OUT)
fx   = commission_sensitivity(fx_golden_week(), outcomes=FX_OUT)
allg = commission_sensitivity(ALL_GOLDEN, outcomes=GOLDEN_OUTCOMES)

print("[DETAIL] === DXY TIER-A (6 documented-exact trades) ===")
for r, row in sorted(dxy.items()):
    print(f"[DETAIL]   {r*100:.1f}%: gross={row['gross_pips']:.1f}p cost={row['costs_pips']:.1f}p net={row['net_pips']:.1f}p win={row['win_rate']:.2f} profitable={row['profitable']}")
print("[DETAIL] === FX GOLDEN WEEK (15 entries) ===")
for r, row in sorted(fx.items()):
    print(f"[DETAIL]   {r*100:.1f}%: gross={row['gross_pips']:.1f}p cost={row['costs_pips']:.1f}p net={row['net_pips']:.1f}p win={row['win_rate']:.2f} profitable={row['profitable']}")
print("[DETAIL] === ALL 21 ===")
for r, row in sorted(allg.items()):
    print(f"[DETAIL]   {r*100:.1f}%: gross={row['gross_pips']:.1f}p cost={row['costs_pips']:.1f}p net={row['net_pips']:.1f}p profitable={row['profitable']}")

# THE GATE (pin): golden-week profitable at 0.1% commission
net_01 = allg[0.001]["net_pips"]
ok = net_01 > 0
print(f"[TOKEN] test_commission_0_1pct" if ok else f"[TOKEN-ABSENT] test_commission_0_1pct")
print(f"[DETAIL] golden-week net at 0.1% = {net_01:.1f} pips (gate: > 0)")
print(f"[DETAIL] cost per FX trade at 0.1% = {fx[0.001]['costs_pips']/max(fx[0.001]['n_trades'],1):.2f} pips")
print(f"[DETAIL] cost per DXY trade at 0.1% = {dxy[0.001]['costs_pips']/max(dxy[0.001]['n_trades'],1):.2f} pips")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_commission_0_1pct")
sys.exit(0 if ok else 1)
