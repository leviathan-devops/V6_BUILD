#!/usr/bin/env bash
# tests/run_all.sh — every V6 test; the honest tally.
# Exit 0 when nothing FAILED (BLOCKED is not a failure; it is reported).
cd "$(dirname "$0")/.." || exit 1

PASS=0
FAIL=0
BLOCKED=0
FAILED=""
BLOCKEDL=""

for t in $(ls tests/test_*.py | xargs -n1 basename | sed 's/\.py$//'); do
  timeout 900 bash tests/run.sh "$t" >"/tmp/v6_${t}.out" 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    PASS=$((PASS + 1))
  elif [ "$rc" -eq 2 ]; then
    BLOCKED=$((BLOCKED + 1))
    BLOCKEDL="$BLOCKEDL $t"
  else
    FAIL=$((FAIL + 1))
    FAILED="$FAILED $t"
  fi
done

echo "PASS=$PASS FAIL=$FAIL BLOCKED=$BLOCKED"
if [ -n "$FAILED" ]; then echo "FAILED:$FAILED"; fi
if [ -n "$BLOCKEDL" ]; then echo "BLOCKED:$BLOCKEDL"; fi
exit "$FAIL"
