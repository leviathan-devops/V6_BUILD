import _boot, sys, json, random
from pathlib import Path
B = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(B/"decider"))
from calibration import fit, ece, split, apply_T, nll
from decider_client import Decider, choice

# ---- 1. the instrument controls --------------------------------------------
perfect  = [(k/10, i < round(k/10*100)) for k in range(1,10) for i in range(100)]
overconf = [(0.95, False)]*100 + [(0.05, True)]*100
instrument_ok = ece(perfect,1.0) < 0.05 < ece(overconf,1.0)

# ---- 2. the layer is monotone and bounded ----------------------------------
# p=0.5 is the FIXED POINT of temperature scaling (logit 0 / T = 0), so it
# must be excluded from the monotonicity check, not asserted to move.
mono = all(apply_T(p, 0.5) > p for p in (0.6, 0.7, 0.9)) and \
       all(apply_T(p, 2.0) < p for p in (0.6, 0.7, 0.9)) and \
       abs(apply_T(0.5, 3.0) - 0.5) < 1e-12
bounded = all(0.0 <= apply_T(p, t) <= 1.0
              for p in (0.01, 0.5, 0.99) for t in (0.1, 1.0, 5.0))
try:
    apply_T(0.5, 0.0); rejects_bad_T = False
except ValueError as e:
    rejects_bad_T = "INVALID_TEMPERATURE" in str(e)

# ---- 3. the layer IMPROVES held-out ECE on the real task -------------------
recs = [json.loads(l) for l in open(B/".wt/we-train/corpus/records.jsonl")]
kind = [r for r in recs if r.get("question","").startswith("What kind of doctrine")]
random.Random(7).shuffle(kind)
fit_rows, eval_rows = split(kind[:120], seed=11, fit_frac=0.5)

d = Decider()
def ask(rows):
    out=[]
    for r in rows:
        a = d.decide({"card": r["quote"], "source": r["source"]},
                     {"kind": choice("What kind of doctrine card is this?",
                        {"mechanism":"a mechanism rule","ruling":"an operator ruling",
                         "forensic":"a forensic trade finding","golden":"a golden trade"})})
        ans=a.get("kind",{}); probs=ans.get("probabilities",{}); ch=ans.get("choice")
        out.append((float(ans.get("confidence", probs.get(ch,0.5))), ch==r["answer"]))
    return out

try:
    fr, er = ask(fit_rows), ask(eval_rows)
except Exception as e:
    print(f"[BLOCKED] test_calibration_layer — live Decider unavailable: {type(e).__name__}: {e}")
    print(f"RESULT: BLOCKED test_calibration_layer (not a pass)")
    sys.exit(2)

f = fit(fr)
ece_raw = ece(er, 1.0)
ece_cal = ece(er, f.T)
improves = ece_cal < ece_raw
# the improvement must hold on data the fit did NOT see
ok = instrument_ok and mono and bounded and rejects_bad_T and f.improves and improves

print(f"[TOKEN] test_calibration_layer" if ok else "[TOKEN-ABSENT] test_calibration_layer")
print(f"[DETAIL] controls: perfect={ece(perfect,1.0):.5f} overconfident={ece(overconf,1.0):.5f} ok={instrument_ok}")
print(f"[DETAIL] monotone (T<1 sharpens, T>1 softens)={mono} | bounded={bounded} | rejects T<=0={rejects_bad_T}")
print(f"[DETAIL] fit n={len(fr)} eval n={len(er)} (HELD OUT — the fit never sees the eval rows)")
print(f"[DETAIL] fitted T={f.T:.3f} (fit NLL {f.fit_nll:.4f} vs baseline {f.baseline_nll:.4f}) improves={f.improves}")
print(f"[DETAIL] ECE on the HELD-OUT set: raw={ece_raw:.5f} -> calibrated={ece_cal:.5f} "
      f"({(1-ece_cal/max(ece_raw,1e-9))*100:.0f}% reduction)")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_calibration_layer")
sys.exit(0 if ok else 1)
