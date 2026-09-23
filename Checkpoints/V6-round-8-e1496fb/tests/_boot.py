"""tests/_boot.py — path bootstrap for the integrated V6 tree."""
import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
for sub in ("gates","limite","mpse","oms","report","tui","determinism","memory",
            "state","decider","integration","corpus"):
    p = WT / sub
    if p.exists(): sys.path.insert(0, str(p))
sys.path.insert(0, str(WT))
