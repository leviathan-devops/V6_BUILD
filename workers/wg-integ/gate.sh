#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WG1 golden week e2e >=14/15 <=3p" "bash tests/run.sh test_golden_week_e2e"
  run "D-WG2 decision latency <500ms" "bash tests/run.sh test_decision_latency"
  run "D-WG3 Decider calibration ECE <0.05" "bash tests/run.sh test_decider_calibration_ece"
  run "D-WG4 forensic trade classification (38)" "bash tests/run.sh test_forensic_trade_classification"
  run "D-WG5 container results artifact" "test -s .trident/container-test-results.json"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
