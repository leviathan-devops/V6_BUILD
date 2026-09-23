import _boot, sys
from pathlib import Path
from pane import render, PaneModel, WIDTH

# NOT HEADLESS: the pane must be a renderable, operator-visible surface —
# not a log line, not a JSON blob, not a headless print of a status code.
m = PaneModel(pair="DXY", session="LONDON 02:00", pnl_pips=12.5, open_positions=1,
              decider={"E1.Q4": {"strong_supply":0.83,"neutral":0.12,"strong_demand":0.05}},
              gates=[{"gate":"G-RRR","passed":True,"token":"G-RRR_PASS","detail":"rrr 4.25 >= 2.5"}])
text = render(m)
lines = text.splitlines()

ok_framed  = text.startswith("=") and "PLUTUS V6" in text
ok_width   = all(len(l) <= WIDTH for l in lines)
ok_visual  = "|" in text and "#" in text          # bars = a visual surface
ok_notjson = not text.strip().startswith("{")
ok_multiline = len(lines) > 12
ok_noprompt = ">>>" not in text and "$ " not in text

ok = ok_framed and ok_width and ok_visual and ok_notjson and ok_multiline and ok_noprompt
print(f"[TOKEN] test_not_headless" if ok else "[TOKEN-ABSENT] test_not_headless")
print(f"[DETAIL] framed header={ok_framed} | all lines <= {WIDTH}={ok_width}")
print(f"[DETAIL] visual bars={ok_visual} | not a json blob={ok_notjson}")
print(f"[DETAIL] multi-line pane={ok_multiline} ({len(lines)} lines) | no shell prompt={ok_noprompt}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_not_headless")
sys.exit(0 if ok else 1)
