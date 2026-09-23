"""integration/ct_run_inside.py — the CONTAINER-SIDE driver (RUNS INSIDE).

WHY THIS FILE EXISTS. The host-side runner shelled out to
`omp ct exec --name omp-ct -- ...`. That is NOT a real CLI: `omp` parses `ct` as
a launch MESSAGE and then rejects `--name` as an unknown flag, so every scenario
returned exit 2 with the extension log as its output. The suite's verdicts could
therefore NOT be reproduced by the runner that claimed them — the artifact was
true but the reproduction path was decorative.

THE SANCTIONED PATH is the container-testing AGENT TOOL. This script is what that
tool EXECUTES; because it already runs INSIDE the container, it invokes the
scenarios with plain `subprocess` and needs no docker and no CLI indirection.

THE SCENARIO AUTHORITY is `run_ct_suite.ADV` / `.HAPPY` — imported, never
duplicated, so the list cannot drift between the runner and the driver.

THE OUTPUT is /work/p3/ct-capture.json (the raw per-scenario records), which the
host-side assembler folds into .trident/ct-results.json.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ct_suite import ADV, HAPPY, EXCLUDED, EXCLUSION_REASON  # noqa: E402

CT_DIR = "/work/p3/plutus-ct"
CAPTURE = Path("/work/p3/ct-capture.json")


def run(cmd: str, timeout: int = 900) -> tuple[int, str, float]:
    t0 = time.time()
    try:
        p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True,
                           timeout=timeout)
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:                                     # noqa: BLE001
        rc, out = -1, f"EXEC_ERROR: {type(e).__name__}: {e}"
    return rc, out, round((time.time() - t0) * 1000, 1)


def main() -> int:
    results = []
    # THE ADVERSARIAL SCENARIOS RUN FIRST (the pin's ADVERSARIAL LOOP).
    for sid, name, cmd_tpl, pass_tok, fail_tok in ADV:
        rc, out, ms = run(cmd_tpl % CT_DIR)
        pm, fa = pass_tok in out, fail_tok not in out
        results.append({
            "id": sid, "name": name, "kind": "adversarial",
            "exitCode": rc, "passToken": pass_tok, "passTokenMatch": pm,
            "failToken": fail_tok, "failTokenAbsent": fa,
            "toolResultContext": out[-1500:], "durationMs": ms,
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})
    # THE HAPPY PATH RUNS LAST (the post-debug confirmation).
    for sid, name, test in HAPPY:
        rc, out, ms = run(f"cd {CT_DIR} && PLUTUS_PY=python3 bash tests/run.sh {test}")
        pm = f"RESULT: PASS {test}" in out
        fa = "[TOKEN-ABSENT]" not in out
        results.append({
            "id": sid, "name": name, "kind": "happy_path",
            "exitCode": rc, "passToken": test, "passTokenMatch": pm,
            "failToken": "[TOKEN-ABSENT]", "failTokenAbsent": fa,
            "toolResultContext": out[-1500:], "durationMs": ms,
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})

    CAPTURE.parent.mkdir(parents=True, exist_ok=True)
    CAPTURE.write_text(json.dumps({
        "scenarios": results,
        "excludedByName": EXCLUDED,
        "exclusionReason": EXCLUSION_REASON,
    }, indent=2))
    n = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"CT-INSIDE: {n}/{len(results)} PASS -> {CAPTURE}")
    for r in results:
        print(f"  {r['verdict']:4} {r['id']:9} {r['kind']:11} {r['name'][:52]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
