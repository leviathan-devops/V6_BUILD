#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WC1 OMS execute order" "bash tests/run.sh test_oms_execute_order"
  run "D-WC2 commission 0.1pct profitable" "bash tests/run.sh test_commission_0_1pct"
  run "D-WC3 walk-forward unseen week" "bash tests/run.sh test_walkforward_unseen_week"
  run "D-WC4 report golden check" "bash tests/run.sh test_report_golden_check"
  run "D-WC5 mutant RRR drift fires" "bash tests/run.sh test_mutant_8_rrr_drift"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
