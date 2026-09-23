#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WB1 Limite served temp=0" "bash tests/run.sh test_limite_serves_temp0"
  run "D-WB2 math queries L1-L6 shape" "bash tests/run.sh test_math_queries_shape"
  run "D-WB3 dual-compute catches divergence" "bash tests/run.sh test_dual_compute_catches_divergence"
  run "D-WB4 gate RRR rejects" "bash tests/run.sh test_gate_rrr_rejects"
  run "D-WB5 golden RRR +-0.02" "bash tests/run.sh test_rrr_golden_reproduction"
  run "D-WB6 MPSE gates named tokens" "bash tests/run.sh test_mpse_gates_named_tokens"
  run "D-WB7 MPSE AT predicates" "bash tests/run.sh test_mpse_predicate_at03"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
