import _boot, sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "determinism"))
from determinism import digest

R = Path(__file__).resolve().parent.parent

# THE LAW: no SAMPLING on the decision/math path.
# A seeded weight INITIALISATION is not sampling — it is deterministic by
# construction (torch.randn(n, generator=g) with g manually seeded produces
# the same tensor every process). The discriminator is therefore the
# PRESENCE OF A SEEDED GENERATOR, not the function name.
UNSEEDED = {
    "torch.multinomial": r"multinomial\s*\(",
    "torch.bernoulli":   r"bernoulli\s*\(",
    "np.random":         r"np\.random|numpy\.random",
    "random.choice":     r"\brandom\.choice\s*\(",
    "random.sample":     r"\brandom\.sample\s*\(",
    "random.random":     r"\brandom\.random\s*\(",
    "temperature>0":     r"temperature\s*=\s*0?\.[1-9]",
    "top_p<1":           r"top_p\s*=\s*0?\.\d*[1-9]",
}
SEEDED_ALLOWED = r"generator\s*=\s*\w+"      # an explicitly seeded generator

roots = [R/".wt/wa-decider/decider", R/".wt/wa-decider/state", R/".wt/wb-limite/gates",
         R/".wt/wb-limite/limite", R/".wt/wb-limite/mpse", R/".wt/wc-exec/oms",
         R/".wt/wc-exec/report", R/".wt/wd-tui/tui", R/".wt/wf-det/determinism"]
hits, seeded_ok = [], []
for root in roots:
    if not root.exists(): continue
    for f in root.rglob("*.py"):
        if "tests" in f.parts: continue
        for ln, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            for name, pat in UNSEEDED.items():
                if re.search(pat, line):
                    if name.startswith("torch.rand") and re.search(SEEDED_ALLOWED, line):
                        seeded_ok.append((f.name, ln, line.strip()[:80])); continue
                    hits.append((f.name, ln, name, line.strip()[:80]))
            if re.search(r"torch\.rand\w*\s*\(", line):
                if re.search(SEEDED_ALLOWED, line): seeded_ok.append((f.name, ln, line.strip()[:80]))
                elif not any(h[1] == ln for h in hits): hits.append((f.name, ln, "torch.rand* unseeded", line.strip()[:80]))

# the negative control MUST fire on genuinely unseeded sampling
ctrl = "import torch, random\nx = torch.multinomial(p, 1)\ny = random.random()\ntemperature = 0.6\n"
caught = {n for n, p in UNSEEDED.items() if re.search(p, ctrl)}
control_ok = {"torch.multinomial", "random.random", "temperature>0"} <= caught

# and the seeded control must be ALLOWED
seeded_ctrl = "g = torch.Generator().manual_seed(0)\nW = torch.randn(8, 1, generator=g)"
seeded_allowed = bool(re.search(SEEDED_ALLOWED, seeded_ctrl))

client = (R/".wt/wb-limite/limite/client.py").read_text()
temp_law = "TEMPERATURE = 0.0" in client

ok = (not hits) and control_ok and seeded_allowed and temp_law
print(f"[TOKEN] test_no_sampling_path" if ok else "[TOKEN-ABSENT] test_no_sampling_path")
print(f"[DETAIL] UNSEEDED sampling primitives in the circuit = {len(hits)}")
for h in hits[:6]: print(f"[DETAIL]   {h}")
print(f"[DETAIL] seeded-deterministic init sites (allowed) = {len(seeded_ok)}")
for s in seeded_ok[:3]: print(f"[DETAIL]   {s[0]}:{s[1]} {s[2]}")
print(f"[DETAIL] negative control fires on unseeded sampling={control_ok} caught={sorted(caught)}")
print(f"[DETAIL] seeded control allowed={seeded_allowed}")
print(f"[DETAIL] client declares TEMPERATURE = 0.0 = {temp_law}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_no_sampling_path")
sys.exit(0 if ok else 1)
