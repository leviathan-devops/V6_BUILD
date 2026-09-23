# PLUTUS V6 — DECISION CHAIN

## D-001 · the runtime harness = pi (not MiMoCode/OMP)
- DECISION: the trading agent runs on a pi TUI harness; MiMoCode/OMP is not the
  runtime.
- REASON (operator ruling): "WE DONT NEED A FUCKING CODING AGENT TO RUN A
  FUCKING TRADING AGENT ... THE HARNESS JUST CAN BE BUILT ON VANILLA PI IT NEEDS
  0 CODING CAPABILITIES."
- CONSEQUENCE: the agent has no bash and no code execution; the TUI is the seat.

## D-002 · the decision engine = the PUBLISHED Decider
- DECISION: call \`Mapika/decider-2b\` over \`POST /v1/systemone\`; do not
  reimplement a readout.
- REASON: the published family is present on the host and served on :8008; a
  hand-built head has untrained weights (measured ECE 0.3858).
- DEVIATION REPORTED: the pin names "Decider-0.6B". \`Mapika/decider-0.6b\`
  returns HTTP 401 (not public). The family's smallest public member is
  \`decider-0.8b\` (1.4GB); the documented default is \`decider-2b\` (3.5GB).
  The 2b is used. This is a DEVIATION, logged in SPEC_VIOLATION_LOG SV-10.

## D-003 · the math engine = Limite-1B via its official plugin
- DECISION: run Limite with \`VLLM_PLUGINS=limite\` from the official
  \`paradigma-inc/limite-violetto\` repo (vLLM 0.26.0 + torch 2.11 + cu130).
- REASON: Limite is a custom architecture (\`LimiteForCausalLM\`); stock
  transformers cannot load it. The official plugin is the sanctioned path.
- CONSEQUENCE: a dedicated uv-locked venv (7.5GB) at
  \`vendor/limite-violetto/.venv\`.
- ALSO: \`VLLM_USE_FLASHINFER_SAMPLER=0\` — flashinfer 0.6.14's JIT sampling
  kernel fails to compile against this CUDA/cub version. The native sampler is
  deterministic at temp=0, so the law is unaffected.

## D-004 · the acceptance oracle = the 6 documented-exact Tier-A rows
- DECISION: only the DXY Tier-A rows (canon cascade lines 19-24) serve as the
  acceptance oracle. The EU/GU rows are EXCLUDED.
- REASON: the canon marks every EU/GU per-trade E/SL/TP assignment as TIER D —
  "PIXEL-INFERRED, NEEDS YOUR CONFIRMATION" (⚠). An inferred number cannot be
  the standard a build is measured against.
- CONSEQUENCE: the e2e test asserts 6 Tier-A accepted + their RRR reproduction;
  the 15 FX entries are checked as an entry-level identity only.

## D-005 · gates are pure code, never models
- DECISION: \`gates/gates.py\` contains zero model calls.
- REASON: pin law "DECIDER SCORES, NEVER EDITS". A model in the gate path makes
  accept/reject non-deterministic.
- VERIFICATION: the 8 gates are pure if/else; ADV-3/4/5 prove they reject.

## D-006 · the session gate accepts both the label and the ISO form
- DECISION: \`g_session\` parses \`LONDON 02:00\` AND \`2026-07-06T02:30:00-04:00\`.
- REASON: the state constructor emits a label; the gate originally parsed only
  ISO, so every candidate was rejected (defect EN-003). Two modules must share
  a contract.
