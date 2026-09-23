import _boot, sys, re, tempfile, os
from pathlib import Path
from coding_surface import (scan_tree, scan_text, EXEC_FORBIDDEN, WRITE_FORBIDDEN,
                            WRITE_ALLOWED_PATHS, is_write_allowed)

R = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")

# ---- 1. THE AGENT TREE: no code execution, no undeclared writes -------------
# The agent's own modules (the circuit's runtime surface).
agent_modules = ["gates/gates.py", "limite/math_queries.py", "limite/dual_compute.py",
                 "limite/limite_client.py", "decider/decider_client.py",
                 "decider/question_templates.py", "mpse/predicates.py", "oms/oms.py",
                 "oms/golden_decisions.py", "report/report.py", "tui/pane.py",
                 "tui/coding_surface.py", "determinism/determinism.py",
                 "memory/memory_store.py", "state/state_constructor.py",
                 "integration/circuit.py", "corpus/build_corpus.py"]
exec_v, write_v = [], []
for rel in agent_modules:
    f = R/rel
    if not f.exists(): continue
    src = f.read_text(errors="ignore")
    for name, pat in EXEC_FORBIDDEN.items():
        for m in re.finditer(pat, src):
            exec_v.append((rel, src[:m.start()].count("\n")+1, name, m.group(0)))
    if rel not in WRITE_ALLOWED_PATHS:
        for name, pat in WRITE_FORBIDDEN.items():
            for m in re.finditer(pat, src):
                write_v.append((rel, src[:m.start()].count("\n")+1, name, m.group(0)))

# ---- 2. THE NEGATIVE CONTROL: the scanner MUST fire on a known-bad sample ---
canary = ("import subprocess\nsubprocess.run(['bash','-c','rm -rf /'])\n"
          "os.system('id')\nfrom subprocess import Popen\nPopen(['id'])\n"
          "builtins.eval('1+1')\n")
caught = {v["capability"] for v in scan_text(canary)}
control_ok = {"subprocess","os.system","popen","eval"} <= caught

# ---- 3. THE CRITICAL BYPASS IS CLOSED (the audit's finding) ----------------
# a file NAMED like an allowlisted artifact, hiding exec, in a foreign dir
d = tempfile.mkdtemp()
os.makedirs(f"{d}/evil", exist_ok=True)
for nm, body in [("report.py", "import subprocess\nsubprocess.run(['id'])\n"),
                 ("oms.py", "from subprocess import Popen\nPopen(['id'])\n"),
                 ("state_constructor.py", "builtins.exec('x=1')\n")]:
    open(f"{d}/evil/{nm}","w").write(body)
bypass_v = scan_tree(d)
bypass_closed = len(bypass_v) >= 3

# ---- 4. the allowlist is PATH-keyed, not basename-keyed --------------------
basename_only = all("/" in p for p in WRITE_ALLOWED_PATHS)
not_allowlisted = not is_write_allowed("evil/report.py")

# ---- 5. the scanner scans ITSELF with no exemption -------------------------
# (its own source must contain no literal trigger word — the fragments fix)
self_src = (R/"tui/coding_surface.py").read_text()
self_v = []
for name, pat in EXEC_FORBIDDEN.items():
    for m in re.finditer(pat, self_src):
        self_v.append((name, m.group(0)))
self_clean = not self_v

ok = (not exec_v) and (not write_v) and control_ok and bypass_closed \
     and basename_only and not_allowlisted and self_clean
print(f"[TOKEN] test_zero_coding_surface" if ok else "[TOKEN-ABSENT] test_zero_coding_surface")
print(f"[DETAIL] agent modules scanned = {len(agent_modules)}")
print(f"[DETAIL] code-execution violations = {len(exec_v)}")
for v in exec_v[:6]: print(f"[DETAIL]   {v}")
print(f"[DETAIL] undeclared write violations = {len(write_v)}")
for v in write_v[:6]: print(f"[DETAIL]   {v}")
print(f"[DETAIL] negative control fires = {control_ok} caught={sorted(caught)}")
print(f"[DETAIL] CRITICAL bypass closed (3 planted files) = {bypass_closed} found={len(bypass_v)}")
print(f"[DETAIL] allowlist is path-keyed = {basename_only} | evil/report.py allowed = {not not_allowlisted}")
print(f"[DETAIL] the scanner scans itself clean (no exemption) = {self_clean}")
print(f"[DETAIL] lexicons: exec={len(EXEC_FORBIDDEN)} write={len(WRITE_FORBIDDEN)} allowed_paths={len(WRITE_ALLOWED_PATHS)}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_zero_coding_surface")
sys.exit(0 if ok else 1)
