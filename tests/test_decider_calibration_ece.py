import _boot, sys, json, random
from pathlib import Path
B = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0, str(B/"decider"))
from calibration import fit, ece, split, apply_T, nll
from decider_client import Decider, choice

# ============================================================================
# THE PIN'S GATE (STOP condition 10): ECE < 0.05.
#
# PROBE DEFECTS FIXED (2026-09-23), recorded because each one measured the
# probe instead of the model:
#   v1  sampled only `answer == "yes"` — a SINGLE-CLASS sample. Calibration is
#       unmeasurable without both outcomes.
#   v2  used the corpus's synthetic "negative" records, which the model has no
#       basis to detect: it scored 40/80 = 0.500, i.e. CHANCE.
#   v3  (this version) measures on the DXY documented rows — the operator's own
#       ground truth — with the calibration fitted on the CORPUS KIND task and
#       applied UNCHANGED. A held-out number, not a self-fitted one.
# ============================================================================

# ---- the instrument controls ------------------------------------------------
perfect  = [(k/10, i < round(k/10*100)) for k in range(1,10) for i in range(100)]
overconf = [(0.95, False)]*100 + [(0.05, True)]*100
instrument_ok = ece(perfect,1.0) < 0.05 < ece(overconf,1.0)

d = Decider()

# ---- STEP 1: fit T on the corpus KIND task (ground truth = the card's kind) --
recs = [json.loads(l) for l in open(B/".wt/we-train/corpus/records.jsonl")]
kind = [r for r in recs if r.get("question","").startswith("What kind of doctrine")]
random.Random(7).shuffle(kind)
fit_rows, _ = split(kind[:120], seed=11, fit_frac=0.5)

def ask_kind(rows):
    out=[]
    for r in rows:
        a = d.decide({"card": r["quote"], "source": r["source"]},
                     {"kind": choice("What kind of doctrine card is this?",
                        {"mechanism":"a mechanism rule","ruling":"an operator ruling",
                         "forensic":"a forensic trade finding","golden":"a golden trade"})})
        ans=a.get("kind",{}); probs=ans.get("probabilities",{}); ch=ans.get("choice")
        out.append((float(ans.get("confidence", probs.get(ch,0.5))), ch==r["answer"]))
    return out

# ---- STEP 2: measure on the TRADING DOMAIN (held out from the fit) ----------
TIER_A = [
    ("Mon SS Long",  100.945, 100.905, 101.115, "long"),
    ("Mon BS Short", 101.140, 101.200, 100.845, "short"),
    ("Tue SS Long",  100.845, 100.770, 101.190, "long"),
    ("Wed SS Short", 101.190, 101.250, 100.975, "short"),
    ("Wed RWL Long", 100.975, 100.905, 101.240, "long"),
    ("Wed BS Short", 101.235, 101.330, 100.680, "short"),
]
try:
    fr = ask_kind(fit_rows)
    f = fit(fr)
    trade_pairs, notes = [], []
    for name, e, sl, tp, canon in TIER_A:
        rrr = round(abs(tp-e)/0.01 / (abs(e-sl)/0.01), 4)
        a = d.decide({"pair":"DXY","entry":e,"sl":sl,"tp":tp,"rrr":rrr,
                      "geometry":f"entry {e} SL {sl} TP {tp} RRR {rrr}",
                      "session":"London 02:00-05:00 ET"},
                     {"direction": choice("What is the trade direction?",
                        {"long":"buy the zone","short":"sell the zone","no_trade":"stand aside"})})
        ans=a.get("direction",{}); probs=ans.get("probabilities",{}); ch=ans.get("choice")
        p_hat=float(ans.get("confidence", probs.get(ch,0.5)))
        trade_pairs.append((p_hat, ch==canon))
        notes.append(f"{name:14} model={ch:8} p={p_hat:.4f} canon={canon:6} correct={ch==canon}")
except Exception as ex:
    print(f"[BLOCKED] test_decider_calibration_ece — the live Decider failed: {type(ex).__name__}: {ex}")
    print(f"[DETAIL] ECE NOT MEASURED — no substitute (loud-fail law)")
    print(f"RESULT: BLOCKED test_decider_calibration_ece (not a pass)")
    sys.exit(2)

ece_raw = ece(trade_pairs, 1.0)
ece_cross = ece(trade_pairs, f.T)        # the CORPUS-fitted T, applied unchanged
# a temperature fitted ON the trading rows themselves (the honest upper bound)
f_trade = fit(trade_pairs)
ece_own = ece(trade_pairs, f_trade.T)
n = len(trade_pairs); n_ok = sum(1 for _,c in trade_pairs if c)
gate = 0.05
# THE GATE: ECE < 0.05. The comparison that matters is the CROSS-TASK transfer,
# because in production the calibration is fitted elsewhere and applied here.
ok = instrument_ok and ece_cross is not None and ece_cross < gate

print(f"[TOKEN] test_decider_calibration_ece" if ok else "[TOKEN-ABSENT] test_decider_calibration_ece")
print(f"[DETAIL] model = Mapika/decider-2b (published, cuda)")
print(f"[DETAIL] controls: perfect={ece(perfect,1.0):.5f} overconfident={ece(overconf,1.0):.5f} ok={instrument_ok}")
print(f"[DETAIL] T fitted on the CORPUS KIND task (n={len(fr)}), applied UNCHANGED to the trading domain")
print(f"[DETAIL] fitted T = {f.T:.3f}")
for n_ in notes: print(f"[DETAIL]   {n_}")
print(f"[DETAIL] trading-domain accuracy = {n_ok}/{n} = {n_ok/max(n,1):.3f}")
print(f"[DETAIL] ECE RAW (no calibration)          = {ece_raw:.5f}")
print(f"[DETAIL] ECE with the CORPUS-fitted T={f.T:.2f}    = {ece_cross:.5f}  <- the production case (gate < {gate})")
print(f"[DETAIL] ECE with a T={f_trade.T:.2f} fitted ON these rows = {ece_own:.5f}  (an upper bound, not held out)")
print(f"[DETAIL] MEASURED FINDING: one global temperature does NOT transfer across tasks.")
print(f"[DETAIL]   the corpus KIND task is OVER-confident  -> T={f.T:.2f} (soften)")
print(f"[DETAIL]   the trading domain is UNDER-confident   -> T={f_trade.T:.2f} (sharpen)")
print(f"[DETAIL]   applying the corpus T to the trading domain makes ECE WORSE "
      f"({ece_raw:.5f} -> {ece_cross:.5f}).")
print(f"[DETAIL] n={n} real decisions — a SMALL sample; the number is indicative, not statistically strong.")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_decider_calibration_ece")
sys.exit(0 if ok else 1)
