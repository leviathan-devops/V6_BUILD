import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
for sub in ("decider", "state", "pi-harness"):
    p = WT / sub
    if p.exists(): sys.path.insert(0, str(p))
sys.path.insert(0, str(WT))
