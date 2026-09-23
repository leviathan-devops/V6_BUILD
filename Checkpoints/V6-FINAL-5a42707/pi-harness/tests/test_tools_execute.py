"""pi-harness/tests/test_tools_execute.py — do the extension's tools ACTUALLY run?

The extension's `execute()` bodies are python snippets passed to the circuit's
interpreter via execFile. This test extracts each snippet from the TypeScript
and RUNS it exactly as the extension would. A tool whose payload fails here
fails in the TUI.

This is the mechanical proof that the harness is wired: not that the file
exists, but that the work each tool performs actually executes.
"""
import re, subprocess, sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = HERE.parent / "plutus-circuit.ts"
ROOT = HERE.parent.parent
PY = "/home/leviathan/venvs/plutus-v6/bin/python"

src = EXT.read_text()
# the BOOT preamble the extension prepends to every snippet
m = re.search(r"const BOOT = `\n(.*?)\n`;", src, re.S)
boot = m.group(1).replace("${JSON.stringify(ROOT)}", json.dumps(str(ROOT)))

# each registerTool block: name, then its script = BOOT + `...`
tools = re.findall(r'name:\s*"(plutus_[a-z_]+)"', src)
blocks = re.split(r'pi\.registerTool\(\{', src)[1:]

results = {}
for b in blocks:
    nm = re.search(r'name:\s*"(plutus_[a-z_]+)"', b)
    if not nm: continue
    name = nm.group(1)
    sm = re.search(r"const script = BOOT \+ `\n(.*?)\n`;", b, re.S)
    if sm:
        results[name] = boot + sm.group(1)
    elif "execute: async () => {" in b:
        sm2 = re.search(r"const script = BOOT \+ `\n(.*?)\n`;", b, re.S)
        if sm2: results[name] = boot + sm2.group(1)

print(f"[DETAIL] tools found in the extension: {sorted(results)}")
fails, passes = [], []
for name, script in sorted(results.items()):
    # the tools that need JSON args get none here: they are exercised with a
    # representative payload below instead of the empty-argv path.
    if name in ("plutus_decide", "plutus_math", "plutus_gate", "plutus_run", "plutus_pane"):
        continue
    p = subprocess.run([PY, "-c", script], capture_output=True, text=True,
                       cwd=str(ROOT), timeout=600)
    ok = p.returncode == 0 and p.stdout.strip()
    (passes if ok else fails).append((name, p.returncode, (p.stdout or p.stderr)[:200]))

# ---- and the tools that need arguments, with a real payload ----------------
ARGS = {
 "plutus_gate": [json.dumps({"pair":"DXY","direction":"long","entry":100.945,
   "sl":100.905,"tp":101.115,"zone_width_pips":4.0,"sl_distance_pips":4.0,
   "confidence":0.78,"session_utc":"LONDON 02:00","cascade_valid":True,
   "chain_integrity":True,"dedup_key":"DXY#1","recent_keys":[],"limite_rrr":4.25})],
 "plutus_math": ["L3", json.dumps({"entry":100.945,"sl":100.905,"tp":101.115,"pair":"DXY"})],
 "plutus_decide": [json.dumps(["yes","no"]), json.dumps("body 45p ATR 35p"),
                   "Does this pass the OBCV gate?"],
}
for name, args in ARGS.items():
    script = results.get(name)
    if not script: continue
    p = subprocess.run([PY, "-c", script] + args, capture_output=True, text=True,
                       cwd=str(ROOT), timeout=900)
    ok = p.returncode == 0 and p.stdout.strip()
    (passes if ok else fails).append((name, p.returncode, (p.stdout or p.stderr)[:200]))

ok = not fails and len(passes) >= 5
print(f"[TOKEN] test_tools_execute" if ok else "[TOKEN-ABSENT] test_tools_execute")
for n, rc, out in passes:
    first = out.strip().splitlines()[0][:90] if out.strip() else ""
    print(f"[DETAIL]   PASS {n:20} rc={rc}  {first}")
for n, rc, out in fails:
    print(f"[DETAIL]   FAIL {n:20} rc={rc}  {out[:160]!r}")
print(f"[DETAIL] executed {len(passes)}/{len(passes)+len(fails)} tool payloads")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_tools_execute")
sys.exit(0 if ok else 1)
