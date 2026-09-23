from pathlib import Path
import _boot, sys, json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "decider"))
from question_templates import ALL_QUESTIONS, CALLS, E1, E2, E3, PVE, expected_level
from decider_client import Decider, choice, noul, score

# ---- PART 1: the template contract (17 questions in 4 calls) ----------------
ok_shape = (len(ALL_QUESTIONS) == 17 and len(E1) == 5 and len(E2) == 4
            and len(E3) == 5 and len(PVE) == 3)
bad = []
for q in ALL_QUESTIONS:
    r = q.render()
    if not r.startswith("<|fim_middle|>"): bad.append(f"{q.id} no question delim")
    if r.count("<|box_start|>") != q.n_options: bad.append(f"{q.id} option count")
    if q.kind not in ("choice","noul","score"): bad.append(f"{q.id} bad kind")
exp = expected_level({"F":0.02,"C":0.08,"B":0.25,"A":0.45,"Aplus":0.20}, ("F","C","B","A","Aplus"))
ok_exp = 3.5 < exp < 4.0

# ---- PART 2: THE LIVE DECIDER on the golden-week state, 17 questions --------
# "Decider returns non-trivial distributions (all 17 questions have argmax != uniform)"
STATE = ("EUR/USD 30m zone 1.14300-1.14400 (width 10p), body 45p, range 60p, ATR 35p. "
         "Session London 02:30. Entry 1.14395, SL 1.14510, TP 1.14110, RRR 2.48. "
         "4 prior holds at the zone edge. DXY 100.945 1H LQZ. Day element: SS.")

WIRE = {
 "E1.Q1": choice("What is the zone type at this level?",
    {"BoM":"balance of momentum","MoM":"mitigation of momentum","PHANTOM":"no true mitigation","LQZ":"liquidity zone"}),
 "E1.Q2": choice("Does this zone pass the OBCV displacement gate?",
    {"pass":"body >= 1.5x avg AND range >= 1.5x ATR","fail":"below the displacement threshold"}),
 "E1.Q3": choice("What is the mitigation state?",
    {"unmitigated":"never tested","1x":"tested once","2x":"tested twice","3x_deployed":"tested 3+ times"}),
 "E1.Q4": choice("What is the pressure classification?",
    {"strong_demand":"multiple holds","weak_demand":"partial holds","neutral":"no clear bias",
     "weak_supply":"partial absorption","strong_supply":"multiple rejections"}),
 "E1.Q5": noul("Is this a FORTRESS zone with 4 or more defense events?"),
 "E2.Q1": choice("What shape is forming on the day element?",
    {"BS":"buy side","WL":"weekly level","RWL":"refined weekly level","R":"range","SS":"sell side","consolidation":"no direction"}),
 "E2.Q2": choice("What is the day element designation?",
    {"BS_day":"buy-side day","WL_day":"weekly-level day","R_day":"range day"}),
 "E2.Q3": choice("Is the cascade valid?",
    {"valid":"chain unbroken","invalid":"chain broken","partial":"chain partially broken"}),
 "E2.Q4": choice("What is the freshness state?",
    {"unmitigated":"fresh","1x_80":"one test, 80% strength","2x_50":"two tests, 50%","3x_deployed":"spent"}),
 "E3.Q1": choice("What is the trade direction?",
    {"long":"buy","short":"sell","no_trade":"stand aside"}),
 "E3.Q2": score("What is the quality grade?",
    ["F: below 0.50","C: 0.50-0.59","B: 0.60-0.69","A: 0.70-0.79","Aplus: 0.80 or above"]),
 "E3.Q3": noul("Is the session valid for entry?"),
 "E3.Q4": noul("Is the SL inside the envelope?"),
 "E3.Q5": noul("Is there shield coverage on the entry path?"),
 "PVE.Q1": score("What is the TP hit probability?",
    ["very_low","low","medium","high","very_high"]),
 "PVE.Q2": noul("Is the entry reachable from here?"),
 "PVE.Q3": score("What is the confidence grade?",
    ["F: below 0.50","C: 0.50-0.59","B: 0.60-0.69","A: 0.70-0.79","Aplus: 0.80 or above"]),
}

live_ok, uniform, results = True, [], {}
try:
    d = Decider()
    ans = d.decide(STATE, WIRE)
    for qid, a in ans.items():
        if qid not in WIRE: continue
        probs = a.get("probabilities") or {}
        if a.get("type") == "noul":
            p = a.get("noul", 0.5)
            results[qid] = {"noul": round(p, 4)}
            if abs(p - 0.5) < 1e-9: uniform.append(qid)
        else:
            top = max(probs, key=probs.get) if probs else None
            results[qid] = {"argmax": top, "p": round(probs.get(top, 0), 4)}
            if probs and abs(max(probs.values()) - 1.0/len(probs)) < 1e-6:
                uniform.append(qid)
    n_answered = len(results)
except Exception as e:
    live_ok, n_answered = False, 0
    results = {"error": f"{type(e).__name__}: {e}"}

ok_live = live_ok and n_answered >= 17 and not uniform
ok = ok_shape and not bad and ok_exp and ok_live

print(f"[TOKEN] test_pass_e1_questions" if ok else "[TOKEN-ABSENT] test_pass_e1_questions")
print(f"[DETAIL] template shape: 17 questions (E1={len(E1)} E2={len(E2)} E3={len(E3)} PVE={len(PVE)}) render_errors={bad}")
print(f"[DETAIL] expected_level = {exp} (blueprint §1.4 says 3.73)")
print(f"[DETAIL] LIVE Decider answered {n_answered}/17 questions")
for qid in sorted(results):
    r = results[qid]
    if "error" in r: print(f"[DETAIL]   ERROR {r['error']}")
    elif "noul" in r: print(f"[DETAIL]   {qid}: noul={r['noul']}")
    else: print(f"[DETAIL]   {qid}: argmax={r['argmax']} p={r['p']}")
print(f"[DETAIL] uniform (trivial) distributions = {uniform}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_pass_e1_questions")
sys.exit(0 if ok else 1)
