#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WA1 zero coding tools in the harness" "test \$(grep -rEl 'child_process|execSync|spawn\(' pi-harness/ 2>/dev/null | wc -l) -eq 0"
  run "D-WA2 memory round-trip" "bash tests/run.sh test_memory_roundtrip"
  run "D-WA3 Decider loads" "bash tests/run.sh test_decider_load"
  run "D-WA4 17 question distributions non-uniform" "bash tests/run.sh test_pass_e1_questions"
  run "D-WA5 state constructor golden" "bash tests/run.sh test_state_constructor_golden"
  run "D-WA6 session London window" "bash tests/run.sh test_session_london_window"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
