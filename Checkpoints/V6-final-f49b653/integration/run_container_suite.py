"""integration/run_container_suite.py — the runtime suite + the results artifact.

THE PROOF CONTRACT (pin): every pass token MUST appear in a tool-result context;
the results artifact at .trident/container-test-results.json records per-scenario
passTokenMatch / failTokenAbsent / toolResultContext / verdict. WITHOUT THIS
FILE THERE IS NO TEST.

ADVERSARIAL FIRST: the five probes run BEFORE the happy path. The happy path
runs LAST, as the post-debugging confirmation.
"""
from __future__ import annotations
import json, subprocess, sys, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

R = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
OUT = R/".trident/container-test-results.json"
PY = "/home/leviathan/venvs/plutus-v6/bin/python"

SCENARIOS = [
    # --- ADVERSARIAL (run first) ------------------------------------------
    {"id": "ADV-1", "name": "empty bars -> circuit must refuse with NO_BARS",
     "kind": "adversarial",
     "cmd": [PY, "-c", """
import sys, pathlib
B=pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
for s in ("integration","state","gates","limite","oms","determinism"):
    sys.path.insert(0,str(B/s))
from state_constructor import parse_bars, EmptyBars
try:
    parse_bars([], 1783317600000); print("NO_REFUSAL")
except EmptyBars as e:
    print(f"REFUSED {e}")
"""],
     "passToken": "NO_BARS", "failToken": "NO_REFUSAL"},

    {"id": "ADV-2", "name": "bar past the anchor -> FUTURE_BAR_LEAK must fire",
     "kind": "adversarial",
     "cmd": [PY, "-c", """
import sys, pathlib
B=pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0,str(B/"state"))
from state_constructor import parse_bars, FutureBarLeak
A=1783317600000
try:
    parse_bars([{"ts":A+60000,"open":1,"high":1,"low":1,"close":1}], A); print("LEAK_NOT_CAUGHT")
except FutureBarLeak as e:
    print(f"REFUSED {e}")
"""],
     "passToken": "FUTURE_BAR_LEAK", "failToken": "LEAK_NOT_CAUGHT"},

    {"id": "ADV-3", "name": "RRR below 2.5 -> G-RRR must reject",
     "kind": "adversarial",
     "cmd": [PY, "-c", """
import sys, pathlib
B=pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0,str(B/"gates"))
from gates import TradeCandidate, evaluate
c=TradeCandidate(pair="EUR/USD",direction="long",entry=1.14110,sl=1.13925,tp=1.14395,
  rrr=1.54,zone_width_pips=10.0,sl_distance_pips=18.5,confidence=0.72,
  session_utc="LONDON 02:00",dedup_key="X",limite_rrr=1.54)
v=evaluate(c)
print("REJECTED" if not v.accepted else "ACCEPTED_BADLY", [r.token for r in v.rejections])
"""],
     "passToken": "G-RRR_REJECT", "failToken": "ACCEPTED_BADLY"},

    {"id": "ADV-4", "name": "session outside London -> G-SESSION must reject",
     "kind": "adversarial",
     "cmd": [PY, "-c", """
import sys, pathlib
B=pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0,str(B/"gates"))
from gates import g_session, TradeCandidate
c=TradeCandidate(pair="EUR/USD",direction="long",entry=1.1,sl=1.09,tp=1.13,rrr=4.0,
  zone_width_pips=10.0,sl_distance_pips=11.0,confidence=0.75,
  session_utc="2026-07-06T14:30:00-04:00",limite_rrr=4.0)
r=g_session(c); print(r.token, r.detail)
"""],
     "passToken": "G-SESSION_REJECT", "failToken": "G-SESSION_PASS"},

    {"id": "ADV-5", "name": "wrong Limite output -> G-DUAL must catch divergence",
     "kind": "adversarial",
     "cmd": [PY, "-c", """
import sys, pathlib
B=pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
for s in ("gates","limite"):
    sys.path.insert(0,str(B/s))
from gates import g_dual, TradeCandidate
c=TradeCandidate(pair="EUR/USD",direction="long",entry=1.14110,sl=1.13925,tp=1.14395,
  rrr=1.5405,zone_width_pips=10.0,sl_distance_pips=18.5,confidence=0.72,
  session_utc="LONDON 02:00",limite_rrr=9.99)
r=g_dual(c); print(r.token, r.detail)
"""],
     # the token was renamed G-DUAL_REJECT in audit round 3 (it now follows the
     # G-<NAME>_REJECT convention every other gate uses). The DIVERGENCE is
     # still the thing being caught; only the label changed.
     "passToken": "G-DUAL_REJECT", "failToken": "G-DUAL_PASS"},

    # --- THE HAPPY PATH (runs LAST) ---------------------------------------
    {"id": "HAPPY-1", "name": "golden week e2e: 6/6 Tier-A accepted, canon RRR +-0.02",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_golden_week_e2e"],
     "passToken": "test_golden_week_e2e", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-2", "name": "limite live temp=0 deterministic",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_limite_serves_temp0"],
     "passToken": "test_limite_serves_temp0", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-3", "name": "decider live: 17/17 non-uniform distributions",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_pass_e1_questions"],
     "passToken": "test_pass_e1_questions", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-4", "name": "commission: golden week profitable at 0.1%",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_commission_0_1pct"],
     "passToken": "test_commission_0_1pct", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-5", "name": "determinism: SHA-identical runs",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_determinism_sha_match"],
     "passToken": "test_determinism_sha_match", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-6", "name": "TUI renders every probability",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_tui_renders_probabilities"],
     "passToken": "test_tui_renders_probabilities", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-7", "name": "zero coding surface",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_zero_coding_surface"],
     "passToken": "test_zero_coding_surface", "failToken": "[TOKEN-ABSENT]"},
    {"id": "HAPPY-8", "name": "corpus 1267 records with D13 provenance",
     "kind": "happy_path",
     "cmd": ["bash", str(R/"tests/run.sh"), "test_corpus_record_count"],
     "passToken": "test_corpus_record_count", "failToken": "[TOKEN-ABSENT]"},
]


def run() -> dict:
    results, t0 = [], time.time()
    for sc in SCENARIOS:
        st = time.time()
        try:
            p = subprocess.run(sc["cmd"], capture_output=True, text=True, timeout=900)
            out = (p.stdout or "") + (p.stderr or "")
            code = p.returncode
        except subprocess.TimeoutExpired:
            out, code = "TIMEOUT", -1
        pass_match = sc["passToken"] in out
        fail_absent = sc["failToken"] not in out
        verdict = "PASS" if (pass_match and fail_absent and code == 0) else "FAIL"
        results.append({
            "id": sc["id"], "name": sc["name"], "kind": sc["kind"],
            "exitCode": code,
            "passToken": sc["passToken"], "passTokenMatch": pass_match,
            "failToken": sc["failToken"], "failTokenAbsent": fail_absent,
            "toolResultContext": out[-1200:],
            "durationMs": round((time.time()-st)*1000, 1),
            "verdict": verdict})
    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    adv = [r for r in results if r["kind"] == "adversarial"]
    happy = [r for r in results if r["kind"] == "happy_path"]
    return {
        "schema": "plutus-v6-container-test-results/v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "durationMs": round((time.time()-t0)*1000, 1),
        "scenarios": results,
        "summary": {
            "total": len(results), "pass": n_pass, "fail": len(results)-n_pass,
            "adversarial": {"n": len(adv), "pass": sum(1 for r in adv if r["verdict"]=="PASS")},
            "happyPath": {"n": len(happy), "pass": sum(1 for r in happy if r["verdict"]=="PASS")},
        },
        "overallVerdict": "PASS" if n_pass == len(results) else "FAIL",
    }


if __name__ == "__main__":
    res = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res["summary"], indent=2))
    print("overallVerdict:", res["overallVerdict"])
    for r in res["scenarios"]:
        print(f"  {r['verdict']:4} {r['id']:8} {r['kind']:11} {r['name'][:60]}")
    sys.exit(0 if res["overallVerdict"] == "PASS" else 1)
