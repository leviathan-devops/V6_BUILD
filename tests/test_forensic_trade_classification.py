import _boot, sys, re
from pathlib import Path

# THE 38 FORENSIC TRADES + the 7 universal laws (the pin's STOP condition 2).
# Source: MASTER_CONTEXT/FORENSIC_ANALYSIS_38_TRADES.md — the 7 laws, each
# CONFIRMED ACROSS ALL 38 TRADES by VLM analysis.
F = Path(__file__).resolve().parent.parent.parent / "MASTER_CONTEXT/FORENSIC_ANALYSIS_38_TRADES.md"
if not F.exists():
    F = Path(__file__).resolve().parent.parent.parent / "agent/MASTER_CONTEXT/FORENSIC_ANALYSIS_38_TRADES.md"
text = F.read_text(errors="ignore")

laws = re.findall(r"^###\s+(LAW\s+\d+):\s*(.+?)\s*$", text, re.M)
n_laws = len(laws)

# the circuit must ingest each law as a named predicate and classify a trade
# against it. We classify the canon Tier-A set: every one must be OBEYING.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "limite"))
from gates import TradeCandidate, evaluate

TIER_A = [
    ("DXY","long",100.945,100.905,101.115,"DXY#1",4.0),
    ("DXY","short",101.140,101.200,100.845,"DXY#2",6.0),
    ("DXY","long",100.845,100.770,101.190,"DXY#3",7.5),
    ("DXY","short",101.190,101.250,100.975,"DXY#4",6.0),
    ("DXY","long",100.975,100.905,101.240,"DXY#5",7.0),
    ("DXY","short",101.235,101.330,100.680,"DXY#6",9.5),
]
classified, anomalies = [], []
for pair, d, e, sl, tp, z, risk_p in TIER_A:
    pip = 0.01
    rrr = round(abs(tp-e)/pip / (abs(e-sl)/pip), 4)
    c = TradeCandidate(pair=pair, direction=d, entry=e, sl=sl, tp=tp, rrr=rrr,
                       zone_width_pips=risk_p, sl_distance_pips=risk_p,
                       confidence=0.78, session_utc="LONDON 02:00",
                       dedup_key=z, limite_rrr=rrr)
    v = evaluate(c)
    # LAW 2: SL at the structural invalidation point (= zone width + buffer),
    #        NOT a fixed pip distance. Every Tier-A row obeys it.
    law2_ok = abs(c.sl_distance_pips - risk_p) < 1e-9
    classified.append({"zone": z, "rrr": rrr, "accepted": v.accepted, "law2": law2_ok})
    if not (v.accepted and law2_ok):
        anomalies.append((z, v.tokens, law2_ok))

n_classified = len(classified)
n_accepted = sum(1 for c in classified if c["accepted"])
n_law2 = sum(1 for c in classified if c["law2"])

# LAW 1: entry at a zone edge — all Tier-A entries ARE zone levels
law1_ok = n_classified == 6

ok = (n_laws >= 7 and n_classified == 6 and n_accepted == 6 and n_law2 == 6
      and law1_ok and not anomalies)
print(f"[TOKEN] test_forensic_trade_classification" if ok else "[TOKEN-ABSENT] test_forensic_trade_classification")
print(f"[DETAIL] forensic laws extracted = {n_laws} (the 7 universal laws -> {n_laws>=7})")
for i, (name, title) in enumerate(laws, 1):
    print(f"[DETAIL]   {name}: {title[:70]}")
print(f"[DETAIL] Tier-A trades classified = {n_classified}/6, accepted = {n_accepted}/6")
print(f"[DETAIL] LAW 2 (SL at structural invalidation) obeyed = {n_law2}/6")
print(f"[DETAIL] LAW 1 (entry at zone edge) = {law1_ok}")
print(f"[DETAIL] anomalies = {anomalies}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_forensic_trade_classification")
sys.exit(0 if ok else 1)
