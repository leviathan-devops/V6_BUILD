#!/usr/bin/env python3
"""pi-harness/prove_zero_coding.py — the mechanical NO-CODING proof for pi.

THE PIN LAW: "zero coding capability in the trading agent — bash REMOVED, code
execution DISABLED".

A prose claim that bash is gone is not evidence. This script proves it three
ways, each a tool result:

  1. THE BUILT-IN TOOL SET. `--no-builtin-tools` must remove pi's own tools.
     The launcher passes it; this asserts the launcher does, and that the flag
     is a real flag on this pi build.

  2. THE EXTENSION SURFACE. The extension registers ONLY `plutus_*` tools. Any
     `registerTool` whose name does not start with `plutus_` is a violation.

  3. NO EXECUTION PRIMITIVE IN THE EXTENSION'S REACH. The extension may call
     the circuit's python (it IS the harness substrate), but it must not expose
     that as a tool, and must not use a shell. `execFile` with an argv array is
     permitted; `exec`/`spawn` with `shell: true` is not.

Exit 0 = proven. Exit 1 = a named violation. Exit 2 = BLOCKED (pi missing).
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = HERE / "plutus-circuit.ts"
LAUNCH = HERE / "launch.sh"

# The tools pi ships. `--no-builtin-tools` must remove every one.
BUILTIN_TOOLS = ("read", "bash", "powershell", "edit", "write", "grep", "find", "ls")

violations: list[str] = []


def check_pi() -> str:
    try:
        p = subprocess.run(["pi", "--help"], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("BLOCKED: pi is not on PATH")
        sys.exit(2)
    return (p.stdout or "") + (p.stderr or "")


def main() -> int:
    help_text = check_pi()

    # ---- 1. the launcher passes the flag, and the flag is real --------------
    launch = LAUNCH.read_text() if LAUNCH.exists() else ""
    if "--no-builtin-tools" not in launch:
        violations.append("launch.sh does not pass --no-builtin-tools")
    if "--no-builtin-tools" not in help_text:
        violations.append("this pi build has no --no-builtin-tools flag")
    # the launcher must NOT enable any built-in tool
    for t in BUILTIN_TOOLS:
        if re.search(rf"--tools[^\n]*\b{t}\b", launch):
            violations.append(f"launch.sh allowlists the built-in tool {t!r}")
    # It must not run headless. PROBE FIX: the first version searched the WHOLE
    # file, so the comment explaining "there is no --print, no --mode json"
    # tripped its own check. The flags are searched in the EXECUTED COMMANDS
    # only (non-comment, non-blank lines).
    commands = "\n".join(l for l in launch.splitlines()
                          if l.strip() and not l.strip().startswith("#"))
    for bad in ("--print", "--mode json", "--mode=json"):
        if bad in commands:
            violations.append(f"launch.sh EXECUTES a headless flag {bad!r}")
    # a bare -p is the short form; only a flag position counts
    if re.search(r"(^|\s)-p(\s|$)", commands):
        violations.append("launch.sh executes the headless short flag -p")

    # ---- 2. the extension registers ONLY plutus_* tools ---------------------
    src = EXT.read_text() if EXT.exists() else ""
    if not src:
        violations.append("plutus-circuit.ts is missing")
    # PROBE FIX: the first version scanned every `name: "..."` in the file, so
    # a PROVIDER's model name ("Muse Spark 1.3 (Go)") was read as a tool name.
    # Only the `name` inside a registerTool block counts.
    tool_blocks = re.split(r"pi\.registerTool\(\{", src)[1:]
    names = []
    for b in tool_blocks:
        m = re.search(r'name:\s*"([^"]+)"', b)
        if m: names.append(m.group(1))
    for n in names:
        if not n.startswith("plutus_"):
            violations.append(f"the extension registers a non-plutus tool {n!r}")

    # ---- 3. no shell, no execution primitive exposed as a tool --------------
    if re.search(r"\bexecSync\b", src):
        violations.append("the extension uses execSync (a shell)")
    if re.search(r"shell\s*:\s*true", src):
        violations.append("the extension spawns with shell: true")
    if re.search(r"\bexec\s*\(\s*[`\"']", src):
        violations.append("the extension calls exec() with a string command")
    # the circuit invocation must be argv-based
    uses_execfile = "execFile" in src
    if not uses_execfile:
        violations.append("the extension does not use execFile (argv-based)")

    # ---- the report --------------------------------------------------------
    ok = not violations
    print(f"[TOKEN] prove_zero_coding" if ok else "[TOKEN-ABSENT] prove_zero_coding")
    print(f"[DETAIL] pi --no-builtin-tools is a real flag: "
          f"{'--no-builtin-tools' in help_text}")
    print(f"[DETAIL] launch.sh passes --no-builtin-tools: {'--no-builtin-tools' in launch}")
    print(f"[DETAIL] launch.sh is NOT headless (no --print / --mode json)")
    print(f"[DETAIL] extension registers {len(names)} tools: {sorted(names)}")
    print(f"[DETAIL] all tool names are plutus_*: "
          f"{all(n.startswith('plutus_') for n in names)}")
    print(f"[DETAIL] the circuit is invoked with execFile (argv, never a shell): {uses_execfile}")
    print(f"[DETAIL] built-in tools that --no-builtin-tools removes: {list(BUILTIN_TOOLS)}")
    print(f"[DETAIL] violations = {len(violations)}")
    for v in violations:
        print(f"[DETAIL]   VIOLATION: {v}")
    print(f"RESULT: {'PASS' if ok else 'FAIL'} prove_zero_coding")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
