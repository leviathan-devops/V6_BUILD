#!/usr/bin/env bash
# tests/run_all.sh — run every V6 test; print the honest tally.
cd "$(dirname "$0")/.."
PASS=0; FAIL=0; BLOCKED=0; FAILED=""; BLOCKEDL=""
for t in $(ls tests/test_*.py | xargs -n1 basename | sed 's/.py$//'); do
  timeout 900 bash tests/run.sh "$t" >/tmp/v6_$t.out 2>&1; rc=$?
  case $rc in
    0) PASS=$((PASS+1));;
    2) BLOCKED=$((BLOCKED+1)); BLOCKEDL="$BLOCKEDL $t";;
    *) FAIL=$((FAIL+1)); FAILED="$FAILED $t";;
  esac
done
echo "PASS=$PASS FAIL=$FAIL BLOCKED=$BLOCKED"
[ -n "$FAILED" ] && echo "FAILED:$FAILED"
[ -n "$BLOCKEDL" ] && echo "BLOCKED:$BLOCKEDL"
exit $FAIL
