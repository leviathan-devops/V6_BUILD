#!/usr/bin/env bash
# tests/run.sh <test_name> — runs one V6 test from the INTEGRATED master tree.
set -uo pipefail
WT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: run.sh <test_name>}"
F="$WT/tests/${NAME}.py"
[ -f "$F" ] || { echo "BLOCKED: $NAME — $F does not exist"; exit 2; }
PY="${PLUTUS_PY:-/home/leviathan/venvs/plutus-v6/bin/python}"
cd "$WT/tests"
"$PY" "$F"
exit $?
