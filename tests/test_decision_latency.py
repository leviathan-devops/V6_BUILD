import _boot, sys, json, time, statistics
from pathlib import Path
from circuit import Circuit
from state_constructor import parse_bars

FIX = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/shared/fixtures/bars_raw.json")
ANCHOR = 1783317600000
raw = json.loads(FIX.read_text())
feeds = {}
for f in raw:
    try: feeds[(f["pair"], f["timeframe"])] = parse_bars(f.get("bars") or [], ANCHOR)
    except Exception: pass

TIER_A = [
    ("DXY","long",100.945,100.905,101.115,"DXY#1"), ("DXY","short",101.140,101.200,100.845,"DXY#2"),
    ("DXY","long",100.845,100.770,101.190,"DXY#3"), ("DXY","short",101.190,101.250,100.975,"DXY#4"),
    ("DXY","long",100.975,100.905,101.240,"DXY#5"), ("DXY","short",101.235,101.330,100.680,"DXY#6"),
]
c = Circuit(anchor_ms=ANCHOR)
pf = {k: v for k, v in feeds.items() if k[0] == "DXY"}

# warm up (first call builds the state from 6,500 bars)
c.decide("DXY", {"entry":100.945,"sl":100.905,"tp":101.115,"direction":"long",
                 "zone_id":"warm","confidence":0.75}, pf)

lat = []
for _ in range(20):
    for pair, d, e, sl, tp, z in TIER_A:
        t0 = time.perf_counter()
        c.decide(pair, {"entry":e,"sl":sl,"tp":tp,"direction":d,"zone_id":z,"confidence":0.75}, pf)
        lat.append((time.perf_counter()-t0)*1000)

mean = statistics.mean(lat); p50 = statistics.median(lat)
p95 = sorted(lat)[int(0.95*len(lat))-1]; worst = max(lat)
GATE = 500.0
ok = mean < GATE and p95 < GATE and worst < GATE
print(f"[TOKEN] test_decision_latency" if ok else "[TOKEN-ABSENT] test_decision_latency")
print(f"[DETAIL] n={len(lat)} decisions on the golden-week state")
print(f"[DETAIL] mean={mean:.3f}ms p50={p50:.3f}ms p95={p95:.3f}ms worst={worst:.3f}ms (gate < {GATE}ms)")
print(f"[DETAIL] headroom vs gate: {GATE/mean:.0f}x on the mean")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_decision_latency")
sys.exit(0 if ok else 1)
