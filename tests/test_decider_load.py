import _boot, sys, json, pathlib
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/decider")
from client import Decider, health, choice, noul, score, DeciderUnavailable

# THE PUBLISHED DECIDER (not a hand-built head).
# Probe evidence (2026-09-23):
#   Mapika/decider-0.8b -> the family's smallest, base Qwen3.5-0.8B-Base, 1.4GB
#   Mapika/decider-2b   -> the default, base Qwen3.5-2B-Base, 3.5GB
#   served: uvicorn decider.serve:app on 127.0.0.1:8008
# The hand-built head in model.py is SUPERSEDED (see decider/SUPERSEDED.md).

h = health()
model = h.get("model", "")
device = h.get("device", "")

d = Decider()
info = d.info()

# the three primitives must each return their documented shape
ans = d.decide(
    {"zone": "EUR/USD 30m 1.14300-1.14400 body 45p range 60p ATR 35p",
     "session": "London 02:30"},
    {"obcv": choice("Does this zone pass the OBCV displacement gate?",
                    {"pass": "body >= 1.5x avg AND range >= 1.5x ATR",
                     "fail": "below the displacement threshold"}),
     "fortress": noul("Is this a FORTRESS zone with 4 or more defense events?"),
     "grade": score("What is the confidence grade?",
                    ["F: below 0.50", "C: 0.50-0.59", "B: 0.60-0.69",
                     "A: 0.70-0.79", "Aplus: 0.80 or above"])})

ok_health = bool(h.get("ok"))
ok_model = "decider" in model.lower()
ok_cuda = device == "cuda"
ok_choice = ("choice" in ans.get("obcv", {})
             and abs(sum(ans["obcv"]["probabilities"].values()) - 1.0) < 0.01)
ok_noul = "noul" in ans.get("fortress", {}) and 0.0 <= ans["fortress"]["noul"] <= 1.0
ok_score = "score" in ans.get("grade", {}) and "probabilities" in ans["grade"]

# the corpus-derived OBCV case: body 45 / ATR 35 = 1.29 < 1.5 -> FAIL
obcv_choice = ans["obcv"]["choice"]
ok_reasoning = obcv_choice == "fail"

ok = all([ok_health, ok_model, ok_cuda, ok_choice, ok_noul, ok_score, ok_reasoning])
print(f"[TOKEN] test_decider_load" if ok else "[TOKEN-ABSENT] test_decider_load")
print(f"[DETAIL] health: ok={h.get('ok')} model={model} device={device}")
print(f"[DETAIL] client info: {info}")
print(f"[DETAIL] choice -> {ans['obcv']['choice']} conf={ans['obcv']['confidence']} probs={ans['obcv']['probabilities']}")
print(f"[DETAIL] noul   -> {ans['fortress']['noul']}")
print(f"[DETAIL] score  -> {ans['grade']['score']} probs={ans['grade']['probabilities']}")
print(f"[DETAIL] OBCV reasoning: body 45p / ATR 35p = 1.29 < 1.5 -> {obcv_choice} (correct={ok_reasoning})")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_decider_load")
sys.exit(0 if ok else 1)
