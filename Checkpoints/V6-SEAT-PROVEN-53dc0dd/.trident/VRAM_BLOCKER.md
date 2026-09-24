# RESOLVED — VRAM OVERFLOW (was BLOCKED; the hard stop is cleared)

> **STATUS UPDATE (2026-09-24, later the same session): RESOLVED — and NO MODEL
> SUBSTITUTION WAS NEEDED.** The blocker was NOT actually a model-size problem.
> Three real defects were found and fixed instead, and the numbers below are the
> ORIGINAL report, kept for the record.
>
> | | before | after |
> |---|---|---|
> | the state rendered | 12 blocks, 9452 chars, **9242 tok** | the spec's 30m/1H/4H + DXY ctx, 2350 chars, ~1400 tok |
> | the token guard | 2238 by ESTIMATE (4.13x undershoot) | the real tokenizer, ratio **0.97** |
> | `DECIDER_MAX_STATE_TOKENS` | unset -> 32768 | **8192** (the documented limit) |
> | the server's footprint | 6587 MiB | **3827 MiB** (2.76 GB freed) |
> | the real state | **OOM** | 17/17 answers |
> | decision latency | OOM / 1259ms | **402ms** (budget 500ms) — **STOP 4 MET** |
>
> THE ROOT CAUSE WAS THE STATE, NOT THE MODEL: `render_state` rendered EVERY feed
> (3 pairs x 4 timeframes = 12 blocks), 4x the blueprint's spec ("State: 30m/1H/4H
> bars + pair + session + DXY ctx") and 13% OVER the blueprint's own 8,192-token
> limit. The state size IS the VRAM AND the latency budget.
>
> THE MODEL-DOWNGRADE RECOMMENDATION BELOW IS THEREFORE **NOT NEEDED** and is
> retained only as the option the hard stop asked for. The one remaining use for
> it: if `DECIDER_WARMUP=1` (CUDA-graph capture, measured to OOM at the current
> footprint) is wanted, a smaller model would give it room.

---

## THE ORIGINAL REPORT (BLOCKED, 2026-09-24)

## THE HARD STOP, QUOTED
> "VRAM overflow: if the 3-model stack exceeds 12GB, BLOCKED + report which model
> to downgrade"

**STATE: BLOCKED.** The 3-model stack does not fit. This is not a pass.

## THE MEASURED ACCOUNTING (nvidia-smi, this session)
```
GPU 0: 12282 MiB total | 11871 MiB used | 6 MiB free
```
| pid | MiB | process | in the pin's stack? |
|---|---|---|---|
| 548969 | **6582** | `decider.serve` — **Mapika/decider-2b** | **YES — the decision model** |
| 615164 | 4060 | `VLLM::EngineCore` — Limite-1B | YES — the math model |
| 6076 | 820 | `llama.cpp/build/bin/llama-server` | **NO — another project's** |
| 2817 | 324 | `buun-llama-cpp/build/bin/llama-server` | **NO — another project's** |
| | **11786** | | |

## THE ROOT CAUSE (a server traceback, not a guess)
`/tmp/decider-serve.log`, from the served Decider on the real state:
```
transformers/integrations/sdpa_attention.py:24 in repeat_kv
    return hidden_states.reshape(batch, num_key_value_heads * n_rep, slen, head_dim)
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 366.00 MiB.
GPU 0 has a total capacity of 11.60 GiB of which 11.38 MiB is free.
```
**The state LENGTH correlates with the activation size, and there is no room left.**
Measured: a 3000-char state scores (17 answers); the REAL 9452-char state OOMs.
Pure filler of 9452 chars succeeds — the filler is a handful of tokens, the real
state is ~2400 — which is why the failure is content-correlated, not length-correlated.

## THE PIN'S CONFIG vs WHAT IS DEPLOYED — THE MISMATCH
| | pin says | deployed |
|---|---|---|
| decision model | **Decider-0.6B bf16** | **Mapika/decider-2b** (3.5 GB bf16, **6582 MiB resident**) |

The decision model is **~3.3x larger than the pin budgets**, and it is the single
largest VRAM consumer. `/health` reports `{"model":"Mapika/decider-2b"}`.

## WHICH MODEL TO DOWNGRADE — THE REPORT
`decider/SUPERSEDED.md` documents the published family:
```
Mapika/decider-0.8b   base Qwen3.5-0.8B-Base, 1.4 GB bf16   (smallest)
Mapika/decider-2b     base Qwen3.5-2B-Base,   3.5 GB bf16   (the default, DEPLOYED)
Mapika/decider-4b     base Qwen3.5-4B-Base,   8.4 GB bf16
```
**RECOMMENDATION: downgrade the decision model to `Mapika/decider-0.8b`.**
- it is the smallest PUBLISHED member (not a substitute model — the same family,
  same wire format, same recipe);
- it would free an estimated **~3.5-4 GiB** of the 6582 MiB the 2b holds;
- that is the same order as the ~1.5 GB the pin reserves as headroom, and it is
  the difference between a 9452-char state scoring and OOMing.

**SECONDARY (free, no model change):** the two `llama-server` processes
(820 + 324 = **1144 MiB**) are NOT in the pin's 3-model stack — they belong to
other projects. Stopping them frees ~1.1 GiB with no substitution at all.

**WHAT I DID NOT DO:** I did not swap the model. The pin's ANTI-DERAIL says
"MODEL SUBSTITUTION: Decider-0.6B is the confirmed decision model — do not swap
for Kev/other without the operator." A downgrade within the published family is
still a substitution decision, and the hard stop asks me to REPORT it, not make it.

## THE RESUME CONDITION
This unblocks when EITHER:
1. the operator authorizes `Mapika/decider-0.8b` (or another family member) as the
   served decision model; OR
2. the two non-stack llama-servers are stopped AND that is measured sufficient; OR
3. the state is rendered smaller (a state-constructor change — a design decision,
   not a workaround: it trades context for fit).

**Until then, STOP condition 4 (`decision latency <500ms` with the model in the
loop) is UNMET and UNMEASURABLE**, and `test_golden_week_e2e` passes only because
it runs `use_decider=False` (the offline path). That is stated in the test itself
and is now recorded here so it cannot be mistaken for a live-model pass.
