"""tests/_boot.py — puts the worker's own modules on sys.path."""
import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
for sub in ("limite", "gates", "mpse"):
    p = WT / sub
    if p.exists(): sys.path.insert(0, str(p))
sys.path.insert(0, str(WT))
