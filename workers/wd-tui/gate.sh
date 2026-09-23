#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WD1 TUI renders probabilities" "bash tests/run.sh test_tui_renders_probabilities"
  run "D-WD2 zero coding surface" "bash tests/run.sh test_zero_coding_surface"
  run "D-WD3 rejection log tokens" "bash tests/run.sh test_rejection_log_tokens"
  run "D-WD4 not headless" "bash tests/run.sh test_not_headless"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
