#!/usr/bin/env bash
# tests/run.sh <test_name>
# The Decider tests need torch+transformers+peft -> the vendor venv (torch 2.11, cu130).
set -uo pipefail
WT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?usage: run.sh <test_name>}"
F="$WT/tests/${NAME}.py"
[ -f "$F" ] || { echo "BLOCKED: $NAME — test file $F does not exist yet"; exit 2; }
PY="${DECIDER_PY:-/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/vendor/limite-violetto/.venv/bin/python}"
cd "$WT/tests"
"$PY" "$F"
exit $?
