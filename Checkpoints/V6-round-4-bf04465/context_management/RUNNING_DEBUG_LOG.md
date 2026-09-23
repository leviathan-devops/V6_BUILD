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
- a pi model entry missing  -> "Cannot read properties of undefined
  (reading 'includes')" at send time. Every field is required.
- the 503 was the MODEL's upstream, not the gateway: probed 6 model ids, 3 up
  and 3 down. Registering a down model as the default produced a retry loop.
-  needs the session header or the gateway refuses with
  {"type":"error","error":{"type":"MissingSessionID"}}.
- my own prove_zero_coding regex matched a PROVIDER's model name as a tool name.
- the OMS  default of "tp" was a silent WIN; making it required broke
  3 callers, which is the point — the caller must state the outcome.
