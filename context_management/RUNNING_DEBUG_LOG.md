# PLUTUS V6 — RUNNING DEBUG LOG (high frequency, append-only)

## 2026-09-23
- `vllm serve --temperature 0.0` → `unrecognized arguments`. Temperature is a
  REQUEST parameter, not a serve flag. The law is enforced client-side in
  `limite/client.py` (`TEMPERATURE = 0.0`, raises otherwise). The serve command
  was corrected.
- `limite` architecture unresolved → the checkpoint declares
  `LimiteForCausalLM` / model_type `limite`; stock transformers 5.12 cannot
  load it. The official plugin (`VLLM_PLUGINS=limite`) resolves it.
- flashinfer 0.6.14 JIT: `cub::BlockAdjacentDifference<...> has no member
  FlagHeads` → the sampling kernel cannot compile against this CUDA/cub.
  `VLLM_USE_FLASHINFER_SAMPLER=0` selects the native sampler.
- `Mapika/decider-0.6b` → HTTP 401. `Mapika/decider-2b` → 200. The family's
  smallest public member is `decider-0.8b`.
- GPU OOM while the Decider loaded alongside Limite + two embedding servers:
  84 MiB free at the moment of a 740 MiB request. Cause: the host was running
  three model servers at once.
- `test_golden_week_e2e` first reported 15/15 entries at 0.0 pips with 0/15
  accepted → the entry-level check was an identity, not a measurement (T-004).
- `test_decider_calibration_ece` first used a circular fixture (T-003) → then
  measured the live model: 0.2139, a real FAIL.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

## 2026-09-23 · the harness defects
- the extension's python preamble had NO trailing newline -> every tool's first
  statement concatenated onto it -> SyntaxError. Caught by test_tools_execute.
- a pi model entry missing the 'input' field -> "Cannot read properties of
  undefined (reading 'includes')" at send time. Every field is required.
- the 503 was the MODEL's upstream, not the gateway: probed 6 model ids, 3 up
  and 3 down. Registering a down model as the seat default produced a retry loop.
- pi registerProvider needs the session header or the gateway refuses with a
  MissingSessionID error type.
- my own prove_zero_coding regex matched a PROVIDER's model name as a tool name.
- the OMS outcomes default of "tp" was a silent WIN; making it required broke
  3 callers, which is the point — the caller must state the outcome.

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._


## EN-035 · A BATCH EDIT SCRIPT THAT ABORTS SILENTLY SKIPS THE REST (round 26)
- FINDING: my batch-edit helper did `raise SystemExit` on the first ANCHOR MISS.
  Round 24's batch hit one early, so FIVE fixes were WRITTEN BUT NEVER APPLIED —
  and I saw only the `applied: X` lines printed BEFORE the abort, so I believed
  the batch had run.
- CONSEQUENCE: round 25 "found" all five again. I then read that as the reviewer
  inventing new findings and RULED the gate unreachable by iteration. **The ruling
  was based on false data** — the code had simply never changed.
- THE FIX, and it is a standing rule now:
  1. a batch script is NON-ABORTING — it records each outcome and reports at the end;
  2. after every batch, VERIFY each fix by grepping for a unique string it adds;
  3. never infer "applied" from the absence of an error.
- THE GENERAL LAW: a silent no-op is indistinguishable from success. This session
  has now hit that three times (a `str.replace` whose anchor did not match, a
  `git checkout` that reverted an edit, and this aborted batch). Every edit must
  assert it applied.
