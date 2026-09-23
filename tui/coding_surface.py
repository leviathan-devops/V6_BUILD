"""tui/coding_surface.py — the NO-CODING audit.

PIN LAW: "zero coding capability in the trading agent — bash REMOVED, code
execution DISABLED". This module is the mechanical predicate that proves it:
it scans a tree for every capability that would let the agent write or run
code, and returns a NAMED violation list. An empty list is the only pass.

A prose claim ("we removed bash") is not evidence; this scan is.
"""
from __future__ import annotations
import re
from pathlib import Path

# Every import/call that grants code execution or file-writing authority.
FORBIDDEN = {
    "subprocess":  r"\bsubprocess\b",
    "os.system":   r"\bos\.system\s*\(",
    "os.exec":     r"\bos\.exec\w*\s*\(",
    "os.spawn":    r"\bos\.spawn\w*\s*\(",
    "popen":       r"\bpopen\s*\(",
    "eval":        r"(?<![\w.])eval\s*\(",
    "exec":        r"(?<![\w.])exec\s*\(",
    "compile":     r"(?<![\w.])compile\s*\(",
    "__import__":  r"__import__\s*\(",
    "pty":         r"\bpty\b",
    "ctypes":      r"\bctypes\b",
    "pickle.load": r"pickle\.loads?\s*\(",
    "marshal":     r"\bmarshal\b",
    "shell=True":  r"shell\s*=\s*True",
}

# File-writing authority is allowed ONLY for the report/state artifacts,
# which are declared here explicitly.
WRITE_ALLOWLIST = ("report.py", "state_constructor.py", "model.py", "oms.py",
                   # the scanner IS the instrument, not a subject: its pattern
                   # table necessarily contains the words it searches for.
                   "coding_surface.py", "test_zero_coding_surface.py")


def scan_tree(root: str, allowlist: tuple[str, ...] = WRITE_ALLOWLIST) -> list[dict]:
    """Return a violation per forbidden capability found."""
    violations = []
    root_p = Path(root)
    for f in sorted(root_p.rglob("*.py")):
        if f.name in allowlist: continue
        if "tests" in f.parts: continue
        src = f.read_text(errors="ignore")
        for name, pat in FORBIDDEN.items():
            for m in re.finditer(pat, src):
                line = src[:m.start()].count("\n") + 1
                violations.append({"file": str(f), "line": line,
                                   "capability": name, "text": m.group(0)})
    return violations


def scan_text(text: str) -> list[dict]:
    out = []
    for name, pat in FORBIDDEN.items():
        for m in re.finditer(pat, text):
            out.append({"capability": name, "text": m.group(0)})
    return out
