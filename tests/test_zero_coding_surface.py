import _boot, sys, re
from pathlib import Path
from coding_surface import scan_tree, scan_text, FORBIDDEN

R = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")

# 1) the AGENT tree (the trading runtime) must be free of every capability
agent_roots = [R/".wt/wa-decider/decider", R/".wt/wa-decider/state",
               R/".wt/wb-limite/gates", R/".wt/wb-limite/limite", R/".wt/wb-limite/mpse",
               R/".wt/wc-exec/oms", R/".wt/wc-exec/report", R/".wt/wd-tui/tui"]
all_v = []
for root in agent_roots:
    if root.exists(): all_v += scan_tree(str(root))

# 2) the negative control: the scanner MUST fire on a known-bad sample
canary = "import subprocess\nsubprocess.run(['bash','-c','rm -rf /'])\nos.system('id')\n"
caught = {v["capability"] for v in scan_text(canary)}
control_ok = {"subprocess", "os.system"} <= caught

# 3) no pi-harness bash tool registration
harness = R/".wt/wa-decider/pi-harness"
harness_hits = []
if harness.exists():
    for f in harness.rglob("*"):
        if f.is_file() and f.suffix in (".ts",".js",".py",".json"):
            harness_hits += scan_text(f.read_text(errors="ignore"))

ok = (not all_v) and control_ok and (not harness_hits)
print(f"[TOKEN] test_zero_coding_surface" if ok else "[TOKEN-ABSENT] test_zero_coding_surface")
print(f"[DETAIL] scanned {len(agent_roots)} agent roots")
print(f"[DETAIL] violations in the agent tree = {len(all_v)}")
for v in all_v[:8]: print(f"[DETAIL]   {v['file']}:{v['line']} {v['capability']} {v['text']!r}")
print(f"[DETAIL] negative control fires on canary={control_ok} caught={sorted(caught)}")
print(f"[DETAIL] pi-harness bash hits = {len(harness_hits)}")
print(f"[DETAIL] forbidden capability lexicon = {len(FORBIDDEN)} entries")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_zero_coding_surface")
sys.exit(0 if ok else 1)
