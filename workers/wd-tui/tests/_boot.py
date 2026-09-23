import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
for sub in ("tui",):
    p = WT / sub
    if p.exists(): sys.path.insert(0, str(p))
sys.path.insert(0, str(WT))
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wb-limite/gates")
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wb-limite/limite")
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wc-exec/oms")
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wc-exec/report")
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/state")
sys.path.insert(0, "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/decider")
