import _boot, sys, json, re
from pathlib import Path
from report import ReportInput, render, run_id, section_count

# Build a report from the REAL modules in this tree.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "limite"))
from gates import TradeCandidate, evaluate
from math_queries import code_truth
from oms import simulate, TradeDecision

cand = TradeCandidate(pair="DXY", direction="long", entry=100.945, sl=100.905,
                      tp=101.115, rrr=4.25, zone_width_pips=10.0, sl_distance_pips=4.0,
                      confidence=0.78, session_utc="2026-07-06T02:30:00-04:00",
                      dedup_key="DXY#1", limite_rrr=4.25)
v = evaluate(cand)
dec = TradeDecision("DXY","long",100.945,100.905,101.115,4.25,0.78,zone_id="DXY#1")
pf = simulate([dec], 0.001, {"DXY#1":"tp"})
fill = pf.trades[0].fill

ri = ReportInput(
    pair="DXY", anchor_ms=1783317600000, session="LONDON 02:00",
    state_text="<|fim_prefix|>\nPAIR DXY ANCHOR 1783317600000\nATR(14) 0.043",
    decider={"E1.Q4": {"strong_demand":0.05,"neutral":0.12,"strong_supply":0.83},
             "E3.Q2": {"F":0.02,"C":0.08,"B":0.25,"A":0.45,"Aplus":0.20}},
    limite={"L3": {"model":4.25,"code":4.25,"delta":0.0,"pass":True}},
    gates=[{"gate":r.gate,"passed":r.passed,"token":r.token,"detail":r.detail} for r in v.results],
    decision={"accepted":v.accepted,"direction":"long","reason":"all 8 gates pass"},
    execution={"entry":fill.entry,"exit":fill.exit,"gross_pips":fill.gross_pips,
               "cost_pips":fill.cost_pips,"net_pips":fill.net_pips,"outcome":"tp"},
)
out = render(ri)

secs = re.findall(r"^## (\d)\. ", out, flags=re.M)
ok_secs = len(secs) >= 8 and sorted(int(s) for s in secs) == list(range(1, len(secs)+1))
ok_prob = "|#" in out and "argmax=" in out          # probability bars rendered
ok_gates = all(t in out for t in ("G-RRR","G-SESSION","G-DUAL"))
ok_pips = f"{fill.net_pips}" in out
ok_id = run_id(ri) in out

# determinism of the report itself
out2 = render(ri)
ok_det = out == out2

ok = ok_secs and ok_prob and ok_gates and ok_pips and ok_id and ok_det
print(f"[TOKEN] test_report_golden_check" if ok else "[TOKEN-ABSENT] test_report_golden_check")
print(f"[DETAIL] sections found={secs} (>=8 contiguous = {ok_secs})")
print(f"[DETAIL] probability bars rendered={ok_prob}")
print(f"[DETAIL] gate tokens present (G-RRR/G-SESSION/G-DUAL)={ok_gates}")
print(f"[DETAIL] net pips {fill.net_pips} present={ok_pips} | run_id {run_id(ri)} present={ok_id}")
print(f"[DETAIL] report deterministic across renders={ok_det}")
print(f"[DETAIL] section_count()={section_count()} lines={len(out.splitlines())}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_report_golden_check")
sys.exit(0 if ok else 1)
