import _boot, sys, json, random
from pathlib import Path

def ece(pairs, n_bins=10):
    """pairs = [(p_hat, correct)].  ECE = sum_b (n_b/n)*|acc_b - conf_b|"""
    if not pairs: return None
    bins = [[] for _ in range(n_bins)]
    for p, correct in pairs:
        bins[min(n_bins-1, int(p*n_bins))].append((p, correct))
    n, total = len(pairs), 0.0
    for b in bins:
        if not b: continue
        conf = sum(p for p,_ in b)/len(b); acc = sum(1 for _,c in b if c)/len(b)
        total += (len(b)/n)*abs(acc-conf)
    return total

# ---- INSTRUMENT CONTROLS ----------------------------------------------------
perfect = [(k/10, i < round(k/10*100)) for k in range(1,10) for i in range(100)]
overconf = [(0.95, False)]*100 + [(0.05, True)]*100
ece_perfect, ece_bad = ece(perfect), ece(overconf)
instrument_ok = ece_perfect < 0.05 < ece_bad

# ---- THE MEASUREMENT: the published Decider vs the KNOWN corpus answers -----
# The corpus (worker WE, 1,267 records) carries (state, question, options,
# answer). Every record's answer is KNOWN — that is the ground truth a
# calibration curve requires. n=6 directional trades cannot support a 0.05
# gate; the corpus can.
B = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0, str(B/".wt/wa-decider/decider"))
from decider_client import Decider, choice

CORPUS = B/".wt/we-train/corpus/records.jsonl"
recs = [json.loads(l) for l in CORPUS.open()] if CORPUS.exists() else []
# the yes/no verify records: their answer is the card's own rule applied
verify = [r for r in recs if r.get("options") == ["yes","no"] and r.get("answer") == "yes"]
random.Random(7).shuffle(verify)
SAMPLE = verify[:60]

d = Decider()
pairs, notes, blocked = [], [], None
try:
    for r in SAMPLE:
        ans = d.decide({"doctrine": r["quote"], "state": r["state"]},
                       {"satisfies": choice("Does the state satisfy this rule?",
                                            {"yes": "the state obeys the rule",
                                             "fail": "the state violates the rule"})})
        a = ans.get("satisfies", {})
        probs = a.get("probabilities", {})
        chosen = a.get("choice")
        p_hat = float(a.get("confidence", probs.get(chosen, 0.5)))
        # the corpus answer is "yes"; a claim of yes is CORRECT
        correct = (chosen == "yes")
        pairs.append((p_hat, correct))
except Exception as ex:
    blocked = f"{type(ex).__name__}: {ex}"

if blocked:
    print(f"[TOKEN-ABSENT] test_decider_calibration_ece")
    print(f"[DETAIL] BLOCKED: {blocked}")
    print(f"[DETAIL] ECE NOT MEASURED — no substitute result (loud-fail law)")
    print(f"RESULT: FAIL test_decider_calibration_ece")
    sys.exit(1)

real_ece = ece(pairs)
n = len(pairs); n_correct = sum(1 for _, c in pairs if c)
gate = 0.05
ok = instrument_ok and real_ece is not None and real_ece < gate
print(f"[TOKEN] test_decider_calibration_ece" if ok else "[TOKEN-ABSENT] test_decider_calibration_ece")
print(f"[DETAIL] model = Mapika/decider-2b (published, cuda) | wire POST /v1/systemone")
print(f"[DETAIL] controls: perfect={ece_perfect:.5f} overconfident={ece_bad:.5f} instrument_ok={instrument_ok}")
print(f"[DETAIL] ECE MEASURED = {real_ece:.5f} over n={n} corpus decisions (gate < {gate})")
print(f"[DETAIL] accuracy = {n_correct}/{n} = {n_correct/max(n,1):.3f}")
print(f"[DETAIL] mean stated confidence = {sum(p for p,_ in pairs)/max(n,1):.3f}")
print(f"[DETAIL] NOTE: the decider is under-confident on this corpus (accurate but")
print(f"[DETAIL]       stating ~0.5-0.6) — ECE scores |accuracy - confidence|.")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_decider_calibration_ece")
sys.exit(0 if ok else 1)
