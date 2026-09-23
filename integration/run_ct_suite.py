"""integration/run_ct_suite.py — the CONTAINER (hermeticity) suite + its artifact.

THE PLAN: .trident/ct-plan.md (5,325 chars, 8 SCENARIO markers, 7 sections).
THE CLAIM: the circuit's OFFLINE code runs in a clean python:3.12-slim container
with NOTHING but the standard library. The host has satisfied this suite
silently for the whole build; the container exposes every environment dependency
the host was hiding — and it DID: 16 of the 31 tests embedded the absolute host
path, and classify_38 required a tree the container does not have.

WHAT IS NOT CLAIMED: the two MODEL-DEPENDENT tests (the live Decider on :8008,
the live Limite on :8100) are NOT hermetic by construction. They are excluded by
name, and that exclusion is stated, not hidden.

THE EVIDENCE CHANNEL: each scenario's passToken must appear IN THE CONTAINER'S
COMMAND OUTPUT. This runner records the container exec result verbatim.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

R = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
OUT = R / ".trident/ct-results.json"
CT_DIR = "/work/p3/plutus-ct"

# THE ADVERSARIAL SCENARIOS RUN FIRST (the pin's ADVERSARIAL LOOP).
ADV = [
    ("ADV-1", "a sub-floor RRR must be refused",
     "cd %s && python3 -c \"import sys\\n"
     "for s in ('gates','limite','state'): sys.path.insert(0,s)\\n"
     "from gates import TradeCandidate, evaluate\\n"
     "c=TradeCandidate(pair='EUR/USD',direction='long',entry=1.14110,sl=1.13925,"
     "tp=1.14395,rrr=1.54,zone_width_pips=10.0,sl_distance_pips=18.5,confidence=0.72,"
     "session_utc='LONDON 02:00',dedup_key='X',limite_rrr=1.54)\\n"
     "v=evaluate(c); print('ADV1','REJECTED' if not v.accepted else 'ACCEPTED_BADLY')\"",
     "G-RRR_REJECT", "ACCEPTED_BADLY"),
    ("ADV-2", "a bar past the temporal anchor must be refused",
     "cd %s && python3 -c \"import sys; sys.path.insert(0,'state')\\n"
     "from state_constructor import parse_bars, FutureBarLeak\\n"
     "try:\\n"
     "    parse_bars([{'ts':1783317600001,'open':1,'high':1,'low':1,'close':1}],1783317600000)"
     "; print('ADV2 LEAK_NOT_CAUGHT')\\n"
     "except FutureBarLeak: print('ADV2 FUTURE_BAR_LEAK')\"",
     "FUTURE_BAR_LEAK", "LEAK_NOT_CAUGHT"),
    ("ADV-3", "an unknown pair must fail closed",
     "cd %s && python3 -c \"import sys; sys.path.insert(0,'limite')\\n"
     "from math_queries import pip_for, UnknownPair\\n"
     "try: print('ADV3 WRONG', pip_for('USD/JPY'))\\n"
     "except UnknownPair: print('ADV3 UNKNOWN_PAIR')\"",
     "UNKNOWN_PAIR", "WRONG"),
]

# THE HAPPY PATH RUNS LAST (the post-debug confirmation).
HAPPY = [
    ("HAPPY-1", "the golden week e2e in the container", "test_golden_week_e2e"),
    ("HAPPY-2", "the fail-closed gate battery", "test_gate_fail_closed"),
    ("HAPPY-3", "determinism in the container", "test_determinism_sha_match"),
    ("HAPPY-4", "the memory store's durability", "test_memory_persistence"),
    ("HAPPY-5", "the TUI pane renders", "test_tui_renders_probabilities"),
    ("HAPPY-6", "the 8-section report", "test_report_golden_check"),
    ("HAPPY-7", "the walk-forward on an unseen week", "test_walkforward_unseen_week"),
    ("HAPPY-8", "the 38 forensic classification", "test_forensic_38_classification"),
    ("HAPPY-9", "the zero-coding source check", "test_zero_coding_surface"),
    ("HAPPY-10", "the 6 math queries + shadows", "test_math_queries_shape"),
    ("HAPPY-11", "the OMS execution", "test_oms_execute_order"),
    ("HAPPY-12", "the commission sensitivity", "test_commission_0_1pct"),
    ("HAPPY-13", "the state constructor + temporal law", "test_state_constructor_golden"),
]


def container_exec(command: str, timeout: int = 900) -> tuple[int, str]:
    """Run a command in the container via the container-testing tool's CLI."""
    p = subprocess.run(
        ["omp", "ct", "exec", "--name", "omp-ct", "--", "bash", "-lc", command],
        capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    results, t0 = [], time.time()

    for sid, name, cmd_tpl, pass_tok, fail_tok in ADV:
        st = time.time()
        try:
            rc, out = container_exec(cmd_tpl % CT_DIR)
        except Exception as e:
            rc, out = -1, f"EXEC_ERROR: {type(e).__name__}: {e}"
        pm, fa = pass_tok in out, fail_tok not in out
        results.append({
            "id": sid, "name": name, "kind": "adversarial",
            "exitCode": rc, "passToken": pass_tok, "passTokenMatch": pm,
            "failToken": fail_tok, "failTokenAbsent": fa,
            "toolResultContext": out[-1500:],
            "durationMs": round((time.time() - st) * 1000, 1),
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})

    for sid, name, test in HAPPY:
        st = time.time()
        try:
            rc, out = container_exec(
                f"cd {CT_DIR} && PLUTUS_PY=python3 bash tests/run.sh {test}")
        except Exception as e:
            rc, out = -1, f"EXEC_ERROR: {type(e).__name__}: {e}"
        pm, fa = f"RESULT: PASS {test}" in out, "[TOKEN-ABSENT]" not in out
        results.append({
            "id": sid, "name": name, "kind": "happy_path",
            "exitCode": rc, "passToken": test, "passTokenMatch": pm,
            "failToken": "[TOKEN-ABSENT]", "failTokenAbsent": fa,
            "toolResultContext": out[-1500:],
            "durationMs": round((time.time() - st) * 1000, 1),
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})

    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    adv = [r for r in results if r["kind"] == "adversarial"]
    happy = [r for r in results if r["kind"] == "happy_path"]
    artifact = {
        "schema": "plutus-v6-ct-results/v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "container": {"image": "python:3.12-slim", "name": "omp-ct",
                      "python": "3.12.14", "packages": ["pip only"],
                      "deployedTo": CT_DIR},
        "plan": ".trident/ct-plan.md",
        "excludedByName": ["test_limite_dual_live", "test_calibration_layer",
                           "test_decider_calibration_ece", "test_decider_load",
                           "test_limite_serves_temp0", "test_pass_e1_questions"],
        "exclusionReason": ("these require the LIVE host services (the Decider on "
                            "127.0.0.1:8008 and Limite on 127.0.0.1:8100) and are "
                            "NOT hermetic by construction"),
        "scenarios": results,
        "summary": {
            "total": len(results), "pass": n_pass, "fail": len(results) - n_pass,
            "adversarial": {"n": len(adv), "pass": sum(1 for r in adv if r["verdict"] == "PASS")},
            "happyPath": {"n": len(happy), "pass": sum(1 for r in happy if r["verdict"] == "PASS")},
        },
        "durationMs": round((time.time() - t0) * 1000, 1),
        "overallVerdict": "PASS" if n_pass == len(results) else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2))
    print(json.dumps(artifact["summary"], indent=2))
    print("overallVerdict:", artifact["overallVerdict"])
    for r in results:
        print(f"  {r['verdict']:4} {r['id']:9} {r['kind']:11} {r['name'][:52]}")
    return 0 if artifact["overallVerdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
