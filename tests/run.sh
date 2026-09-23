#!/usr/bin/env bash
set -uo pipefail
WT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: run.sh <test_name>}"
F="$WT/tests/${NAME}.py"
[ -f "$F" ] || { echo "BLOCKED: $NAME — test file $F does not exist yet"; exit 2; }
cd "$WT/tests"
/home/leviathan/venvs/plutus-v6/bin/python "$F"
exit $?
