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

# THE MODEL-DEPENDENT TESTS, EXCLUDED BY NAME AND STATED (never hidden).
EXCLUDED = ["test_limite_dual_live", "test_calibration_layer",
            "test_decider_calibration_ece", "test_decider_load",
            "test_limite_serves_temp0", "test_pass_e1_questions"]
EXCLUSION_REASON = ("these require the LIVE host services (the Decider on "
                    "127.0.0.1:8008 and Limite on 127.0.0.1:8100) and are NOT "
                    "hermetic by construction")

# THE ADVERSARIAL SCENARIOS RUN FIRST (the pin's ADVERSARIAL LOOP).
ADV = [
    # AUDIT FIX (round 10): all three probes were BROKEN BY CONSTRUCTION — they
    # embedded `\n` inside `bash -lc "python3 -c \"...\""`, so python received a
    # literal backslash-n and died with "unexpected character after line
    # continuation character". The probe errored, so the scenario reported FAIL
    # and the DEFECT (if any) was never actually tested. Heredocs remove the
    # escaping entirely; a probe that cannot run is not evidence of anything.
    ("ADV-1", "a sub-floor RRR must be refused",
     "cd %s && python3 - <<'PY'\n"
     "import sys\n"
     "for m in ('gates', 'limite', 'state'):\n"
     "    sys.path.insert(0, m)\n"
     "from gates import TradeCandidate, evaluate\n"
     "# the STOP is moved so the DERIVED rrr is 10.0/6.0 = 1.667 < the 2.5 floor\n"
     "c = TradeCandidate(pair='EUR/USD', direction='long', entry=1.14110,\n"
     "                   sl=1.14050, tp=1.14210, rrr=1.667,\n"
     "                   zone_width_pips=6.0, sl_distance_pips=6.0,\n"
     "                   confidence=0.72, session_utc='LONDON 02:00',\n"
     "                   dedup_key='ADV1', limite_rrr=1.667)\n"
     "v = evaluate(c)\n"
     "toks = [r.token for r in v.rejections]\n"
     "print('ADV1', 'REJECTED' if not v.accepted else 'ACCEPTED_BADLY')\n"
     "print('ADV1 tokens', toks)\n"
     "PY",
     "G-RRR_REJECT", "ACCEPTED_BADLY"),
    ("ADV-2", "a bar past the temporal anchor must be refused",
     "cd %s && python3 - <<'PY'\n"
     "import sys\n"
     "sys.path.insert(0, 'state')\n"
     "from state_constructor import parse_bars, FutureBarLeak\n"
     "# one millisecond PAST the anchor\n"
     "try:\n"
     "    parse_bars([{'ts': 1783317600001, 'open': 1, 'high': 1,\n"
     "                 'low': 1, 'close': 1}], 1783317600000)\n"
     "    print('ADV2 LEAK_NOT_CAUGHT')\n"
     "except FutureBarLeak:\n"
     "    print('ADV2 FUTURE_BAR_LEAK')\n"
     "PY",
     "FUTURE_BAR_LEAK", "LEAK_NOT_CAUGHT"),
    ("ADV-3", "an unknown pair must fail closed",
     "cd %s && python3 - <<'PY'\n"
     "import sys\n"
     "sys.path.insert(0, 'limite')\n"
     "from math_queries import pip_for, UnknownPair\n"
     "try:\n"
     "    print('ADV3 WRONG', pip_for('USD/JPY'))\n"
     "except UnknownPair:\n"
     "    print('ADV3 UNKNOWN_PAIR')\n"
     "PY",
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
    """DEPRECATED — DO NOT USE. `omp ct exec` is not a real CLI.

    `omp` parses `ct` as a launch MESSAGE and then rejects `--name` as an unknown
    flag, so this returned exit 2 with the extension log as its output. The
    sanctioned container path is the container-testing AGENT TOOL, which EXECUTES
    `integration/ct_run_inside.py` inside the container. Kept only so the defect
    is visible in the source rather than silently deleted.
    """
    raise RuntimeError(
        "CT_EXEC_UNSANCTIONED: the sanctioned path is the container-testing tool "
        "running integration/ct_run_inside.py inside the container")


def main() -> int:
    """ASSEMBLE the artifact from the container's own capture.

    THE PROCEDURE (the sanctioned path — no docker, no CLI):
      1. deploy this tree into the container with the container-testing AGENT TOOL
      2. exec inside it:  python3 integration/ct_run_inside.py
                          -> writes /work/p3/ct-capture.json
      3. copy that capture back to .trident/ct-capture.json
      4. run THIS script: it folds the capture into .trident/ct-results.json

    The verdicts therefore come from the CONTAINER'S OWN exec output, and the
    scenario list is imported from this same module by the driver — one authority.
    """
    cap_path = R / ".trident/ct-capture.json"
    if not cap_path.exists():
        print("CT_CAPTURE_MISSING:", cap_path)
        print("run integration/ct_run_inside.py inside the container first "
              "(the container-testing tool), then copy its capture back.")
        return 2
    cap = json.loads(cap_path.read_text())
    results = cap["scenarios"]
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
        "capture": ".trident/ct-capture.json",
        "driver": "integration/ct_run_inside.py (executed by the container-testing tool)",
        "excludedByName": cap.get("excludedByName", EXCLUDED),
        "exclusionReason": cap.get("exclusionReason", EXCLUSION_REASON),
        "scenarios": results,
        "summary": {
            "total": len(results), "pass": n_pass, "fail": len(results) - n_pass,
            "adversarial": {"n": len(adv),
                            "pass": sum(1 for r in adv if r["verdict"] == "PASS")},
            "happyPath": {"n": len(happy),
                          "pass": sum(1 for r in happy if r["verdict"] == "PASS")},
        },
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
