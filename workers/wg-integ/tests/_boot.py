import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
for sub in ("integration",):
    p = WT / sub
    if p.exists(): sys.path.insert(0, str(p))
sys.path.insert(0, str(WT))
B = pathlib.Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
for sub in ("wb-limite/gates","wb-limite/limite","wb-limite/mpse","wc-exec/oms",
            "wc-exec/report","wa-decider/state","wa-decider/decider","wd-tui/tui",
            "wf-det/determinism","wf-det/memory","we-train/corpus"):
    p = B/".wt"/sub
    if p.exists(): sys.path.insert(0, str(p))
