#!/usr/bin/env bash
# gate.sh — the worker's mechanical done-when.
# EXIT 0 only when every owned test passes with its passToken in a tool result.
set -uo pipefail
FAIL=0
run() { echo "--- $1 ---"; if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; FAIL=1; fi; }
  echo "=== REAL MODEL SERVERS ==="
  run "D-WE1 corpus record count >=700" "bash tests/run.sh test_corpus_record_count"
  run "D-WE2 LoRA adapter loads" "bash tests/run.sh test_lora_adapter_loads"
  run "D-WE3 D13 verbatim quoting" "bash tests/run.sh test_d13_quoting"
  run "D-WE4 finetuned golden precision" "bash tests/run.sh test_finetuned_golden_precision"
echo "=== GATE VERDICT ==="
if [ "$FAIL" = "0" ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit "$FAIL"
