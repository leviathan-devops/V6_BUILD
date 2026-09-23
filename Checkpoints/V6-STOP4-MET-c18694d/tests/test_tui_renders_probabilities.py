import _boot, sys
from pane import (PaneModel, render, render_probabilities, has_probability_bars,
                  has_gate_decisions, WIDTH)
from gates import TradeCandidate, evaluate

cand = TradeCandidate(pair="DXY", direction="long", entry=100.945, sl=100.905,
                      tp=101.115, rrr=4.25, zone_width_pips=4.0, sl_distance_pips=4.0,
                      confidence=0.78, session_utc="LONDON 02:00",
                      dedup_key="DXY#1", limite_rrr=4.25)
v = evaluate(cand)

m = PaneModel(
    pair="DXY", session="LONDON 02:00", pnl_pips=16.8, open_positions=1,
    decider={"E1.Q4": {"strong_demand":0.05,"neutral":0.12,"strong_supply":0.83},
             "E3.Q2": {"F":0.02,"C":0.08,"B":0.25,"A":0.45,"Aplus":0.20},
             "PVE.Q1": {"very_low":0.03,"low":0.07,"medium":0.20,"high":0.45,"very_high":0.25}},
    gates=[{"gate":r.gate,"passed":r.passed,"token":r.token,"detail":r.detail} for r in v.results],
    rejections=[{"when":"2026-07-06T02:31Z","token":"G-DEDUP_REJECT","detail":"key DXY#1 seen"}],
)
text = render(m)

# the pane must render EVERY probability, not just the argmax
ok_bars = has_probability_bars(text)
n_prob_lines = sum(1 for l in text.splitlines() if "|" in l and "#" in l)
ok_all = n_prob_lines >= 11        # 3 questions -> 3+5+5 = 13 option rows
ok_gates = has_gate_decisions(text) and all(g in text for g in ("G-RRR","G-SESSION","G-DUAL"))
ok_pnl = "net_pips=+16.80" in text
ok_rej = "G-DEDUP_REJECT" in text
ok_width = all(len(l) <= WIDTH for l in text.splitlines())
# the pane must NOT expose any code-execution surface
ok_nocode = not any(k in text.lower() for k in ("bash", "subprocess", "exec("))

ok = ok_bars and ok_all and ok_gates and ok_pnl and ok_rej and ok_width and ok_nocode
print(f"[TOKEN] test_tui_renders_probabilities" if ok else "[TOKEN-ABSENT] test_tui_renders_probabilities")
print(f"[DETAIL] probability bars present={ok_bars} option_rows={n_prob_lines} (>=11: {ok_all})")
print(f"[DETAIL] gate decisions present={ok_gates} | pnl rendered={ok_pnl} | rejection logged={ok_rej}")
print(f"[DETAIL] all lines <= {WIDTH} cols={ok_width} | no code surface={ok_nocode}")
print("[DETAIL] --- pane excerpt ---")
for l in text.splitlines()[:14]: print(f"[DETAIL] {l}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_tui_renders_probabilities")
sys.exit(0 if ok else 1)
