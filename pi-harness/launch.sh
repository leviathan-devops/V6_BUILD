#!/usr/bin/env bash
# launch.sh — start the Plutus V6 trading agent on the pi TUI harness.
#
# THE ZERO-CODING LAW IS MECHANICAL HERE, not a promise:
#   --no-builtin-tools   removes pi's read, bash, powershell, edit, write,
#                        grep, find and ls. The agent cannot touch the disk or
#                        spawn a process.
#   -e <the extension>   adds ONLY the circuit's trading tools.
# A launch with any built-in tool present is a FAILED launch (gate.sh proves it).
#
# NOT HEADLESS: pi's TUI is the seat. There is no --print, no --mode json.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export PLUTUS_ROOT="${PLUTUS_ROOT:-$ROOT}"
export PLUTUS_PY="${PLUTUS_PY:-/home/leviathan/venvs/plutus-v6/bin/python}"

SYSTEM_PROMPT="$(cat "$HERE/plutus-system-prompt.txt")"

exec pi \
  --no-builtin-tools \
  -e "$HERE/plutus-circuit.ts" \
  --system-prompt "$SYSTEM_PROMPT" \
  --session-dir "$HERE/sessions" \
  "$@"
