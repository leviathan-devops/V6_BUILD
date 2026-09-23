#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WF1 determinism SHA match" "bash tests/run.sh test_determinism_sha_match"
  run "D-WF2 memory persistence across restart" "bash tests/run.sh test_memory_persistence"
  run "D-WF3 no sampling path" "bash tests/run.sh test_no_sampling_path"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
