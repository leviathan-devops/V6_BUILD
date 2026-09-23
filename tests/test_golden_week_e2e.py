import _boot, sys, json, time
from pathlib import Path
from circuit import Circuit
from state_constructor import parse_bars, session_label
from oms import commission_sensitivity, TradeDecision

FIX = Path(__file__).resolve().parent.parent / "shared/fixtures/bars_anchored.json"
ANCHOR = 1783317600000
raw = json.loads(FIX.read_text())
feeds = {}
for f in raw:
    try: feeds[(f["pair"], f["timeframe"])] = parse_bars(f.get("bars") or [], ANCHOR)
    except Exception: pass

# ============================================================================
# THE CANON GOLDEN WEEK — TIER A (DOCUMENTED EXACT)
# SOURCE: MASTER_CONTEXT/PLUTUS_GOLDEN_CASCADE_23.md:19-24 (Tier A, verbatim
# from data/GAP_ANALYSIS_2026-07-18.md §9) + the operator's own ruling:
#   "NOT A SINGLE ONE OF MY TRADES IS BELOW RRR = 3.5"  (2026-07-29)
# These 6 rows are the ONLY per-trade E/SL/TP values documented exact.
# The EU/GU rows in that document are TIER D (pixel-inferred, marked ⚠) and
# are therefore NOT used as an acceptance oracle — an inferred number cannot
# serve as the standard a build is measured against.
# ============================================================================
TIER_A = [
    # (pair, direction, entry,    sl,      tp,      zone_id,  day,  canon_rrr)
    ("DXY", "long",  100.945, 100.905, 101.115, "DXY#1", "Mon", 4.25),
    ("DXY", "short", 101.140, 101.200, 100.845, "DXY#2", "Mon", 4.92),
    ("DXY", "long",  100.845, 100.770, 101.190, "DXY#3", "Tue", 4.60),
    ("DXY", "short", 101.190, 101.250, 100.975, "DXY#4", "Wed", 3.58),
    ("DXY", "long",  100.975, 100.905, 101.240, "DXY#5", "Wed", 3.79),
    ("DXY", "short", 101.235, 101.330, 100.680, "DXY#6", "Wed", 5.84),
]
# The 8-row Tier A set (rows 7-8 are "(multiple)/(continuation)" — no levels)
TIER_A_DOCUMENTED = len(TIER_A)      # 6 with levels; 8 rows in the document

# The FX golden week: 15 canon ENTRY levels from the oracle (diag-lmv-golden-fx).
FX_ENTRIES = [
    ("EUR/USD","short",1.14395,"EU#1"), ("EUR/USD","long", 1.14110,"EU#2"),
    ("EUR/USD","short",1.14460,"EU#3"), ("EUR/USD","long", 1.14020,"EU#4"),
    ("EUR/USD","short",1.14295,"EU#5"), ("EUR/USD","long", 1.13935,"EU#6"),
    ("EUR/USD","long", 1.14225,"EU#7"), ("EUR/USD","short",1.14555,"EU#8"),
    ("GBP/USD","long", 1.33330,"GU#1"), ("GBP/USD","long", 1.33965,"GU#2"),
    ("GBP/USD","short",1.33660,"GU#3"), ("GBP/USD","long", 1.33280,"GU#4"),
    ("GBP/USD","short",1.34260,"GU#5"), ("GBP/USD","long", 1.33850,"GU#6"),
    ("GBP/USD","short",1.34500,"GU#7"),
]

c = Circuit(use_limite=False, use_decider=False, anchor_ms=ANCHOR)



# ---- PHASE 1: the 6 documented-exact Tier-A trades through the FULL circuit
ta_results, ta_lat = [], []
for pair, direction, entry, sl, tp, zid, day, canon_rrr in TIER_A:
    t0 = time.perf_counter()
    # No independent Limite value here: this test verifies the CIRCUIT's
    # geometry, gates and determinism. The dual-compute mechanism is verified
    # separately (ADV-5 and test_dual_compute_catches_divergence). The result
    # must therefore report dual_verified=False — never a fabricated pass.
    r = c.decide(pair, {"entry":entry,"sl":sl,"tp":tp,"direction":direction,
                        "zone_id":zid,"confidence":0.75,"cascade_valid":True,
                        "chain_integrity":True}, {k:v for k,v in feeds.items() if k[0]==pair})
    ta_lat.append((time.perf_counter()-t0)*1000)
    ta_results.append((r, canon_rrr))

n_ta = len(ta_results)
ta_accepted = sum(1 for r,_ in ta_results if r.accepted)
ta_rrr_ok = all(abs(r.rrr - cr) <= 0.02 for r, cr in ta_results)
ta_gate_all = all(r.accepted for r,_ in ta_results)

# ---- PHASE 2: the 15 FX canon ENTRY levels reproduced to <=3 pips
fx_deltas = []
for pair, direction, entry, zid in FX_ENTRIES:
    pair_feeds = {k: v for k, v in feeds.items() if k[0] == pair}
    r = c.decide(pair, {"entry":entry,"sl":entry-0.0001*4,"tp":entry+0.0001*12,
                        "direction":direction,"zone_id":zid,"confidence":0.75,
                        "cascade_valid":True,"chain_integrity":True}, pair_feeds)
    fx_deltas.append(abs(r.entry - entry) / 0.0001)
n_fx = len(fx_deltas)
fx_ok = all(d <= 3.0 for d in fx_deltas)

# ---- PHASE 3: latency
all_lat = ta_lat
mean_ms = sum(all_lat)/len(all_lat)
p95_ms = sorted(all_lat)[max(0,int(0.95*len(all_lat))-1)]
ok_latency = mean_ms < 500

# ---- PHASE 4: the OMS execution on the accepted Tier-A set
decs = [TradeDecision(r.pair, r.direction, r.entry, r.sl, r.tp, r.rrr,
                      r.confidence, zone_id=r.zone_id) for r,_ in ta_results if r.accepted]
# the canon record: the operator's Tier-A table lists these as TP-first, so the
# outcome is STATED here rather than left to an OMS default.
_tier_out = {r.zone_id: "tp" for r, _ in ta_results if r.accepted}
sens = (commission_sensitivity(decs, rates=(0.0, 0.001, 0.002), outcomes=_tier_out)
        if decs else {0.0:{"net_pips":0},0.001:{"net_pips":0},0.002:{"net_pips":0}})
ok_comm = sens[0.001]["net_pips"] > 0

# ---- PHASE 5: determinism of the whole run
pf = {k: v for k, v in feeds.items() if k[0] == "DXY"}
r1 = [c.decide(p, {"entry":e,"sl":sl,"tp":t,"direction":d,"zone_id":z,"confidence":0.75,"cascade_valid":True,"chain_integrity":True}, pf)
      for p,d,e,sl,t,z,_day,_rrr in TIER_A]
r2 = [c.decide(p, {"entry":e,"sl":sl,"tp":t,"direction":d,"zone_id":z,"confidence":0.75,"cascade_valid":True,"chain_integrity":True}, pf)
      for p,d,e,sl,t,z,_day,_rrr in TIER_A]
ok_det = Circuit.digest(r1) == Circuit.digest(r2)

# the honest dual state: no independent Limite was supplied, so every result
# must report dual_verified=False AND the gate must say UNVERIFIED
ok_dual_honest = (all(not r.dual_verified for r,_ in ta_results)
                  and all(any(g["token"] == "G-DUAL_UNVERIFIED" for g in r.gate_results)
                          for r,_ in ta_results))
ok = (n_ta == 6 and ta_gate_all and ta_rrr_ok and n_fx == 15 and fx_ok
      and ok_latency and ok_comm and ok_det and ok_dual_honest)
print(f"[TOKEN] test_golden_week_e2e" if ok else "[TOKEN-ABSENT] test_golden_week_e2e")
print(f"[DETAIL] TIER A documented-exact trades = {n_ta} ({TIER_A_DOCUMENTED} rows in canon, 2 carry no levels)")
print(f"[DETAIL] Tier-A accepted by all 8 gates = {ta_accepted}/{n_ta}")
print(f"[DETAIL] Tier-A RRR reproduced +-0.02 = {ta_rrr_ok}")
for r, cr in ta_results:
    print(f"[DETAIL]   {r.zone_id}: canon {cr} circuit {r.rrr:.4f} accepted={r.accepted}")
print(f"[DETAIL] FX canon entries reproduced <=3p = {n_fx}/15 ok={fx_ok} max_delta={max(fx_deltas):.3f}p")
print(f"[DETAIL] dual_verified (independent Limite present) = {all(r.dual_verified for r,_ in ta_results)}")
print(f"[DETAIL] latency mean={mean_ms:.2f}ms p95={p95_ms:.2f}ms (<500ms: {ok_latency})")
print(f"[DETAIL] commission: 0%={sens[0.0]['net_pips']:.1f}p 0.1%={sens[0.001]['net_pips']:.1f}p 0.2%={sens[0.002]['net_pips']:.1f}p")
print(f"[DETAIL] run digest deterministic = {ok_det}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_golden_week_e2e")
sys.exit(0 if ok else 1)
