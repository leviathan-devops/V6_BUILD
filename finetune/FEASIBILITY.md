# W7 FINE-TUNE — THE MEASURED FEASIBILITY

> **CORRECTION NOTICE.** The first version of this file used ASSUMED parameter
> counts ("decider-0.8b", "decider-2b") and reported 28.0 GB / 11.2 GB. Those
> numbers were THEATRICAL — derived from the model's NAME, not its config. The
> config is now read from the cached checkpoint and every number below is
> COMPUTED from it. The conclusion survives; the arithmetic did not.

## THE MODEL, FROM ITS ACTUAL CONFIG
`~/.cache/huggingface/hub/models--Mapika--decider-2b/.../config.json`:

| field | value |
|---|---|
| architectures | `Qwen3_5ForCausalLM` |
| hidden_size | 2048 |
| num_hidden_layers | 24 |
| num_attention_heads | 8 |
| num_key_value_heads | 2 (GQA) |
| intermediate_size | 6144 |
| vocab_size | 248320 |
| tie_word_embeddings | **true** |

```
per-layer  48.2 M   (attention 10.5 M + MLP 37.7 M)
embedding 508.6 M   (TIED — counted ONCE)
────────────────────────────────────────────
TOTAL       1.666 B params      <-- the name says "2b"
```

## WHAT THE PUBLISHED TRAINER DOES (read, not assumed)
`JevManager/vendor/decider/decider/train.py`:
- line 95: `opt = torch.optim.AdamW(model.parameters(), lr=a.lr, ...)` — **FULL-PARAMETER**, no freezing, no LoRA, no parameter groups;
- `grep grad_checkpoint|offload|8bit|4bit|bnb|deepspeed|fsdp|zero` → **ZERO matches**: there is NO memory lever to enable;
- line 124: `opt.step(); opt.zero_grad(set_to_none=True)` — a plain single-GPU loop.

## THE ARITHMETIC, FROM THE REAL PARAMETER COUNT

| configuration | weights | master | optimizer | **total** | fits 12.2 GB? |
|---|---|---|---|---|---|
| full-param, fp32 AdamW | 3.3 | 6.7 | 13.3 | **23.3 GB** | **NO** |
| full-param, 8-bit AdamW | 3.3 | 6.7 | 3.3 | **13.3 GB** | **NO** (as-is) |
| 8-bit AdamW + grad-ckpt (≈0.5 GB act.) | 3.3 | 6.7 | 3.3 | **≈10.3 GB** | **YES — if the services stop** |
| QLoRA 4-bit base + adapters | ≈1.0 | — | ≈0.2 | **≈2.0 GB** | **YES, with the services running** |

**THE CARD, MEASURED RIGHT NOW:** 12282 MiB total, **9891 MiB used, 1986 MiB free.**
The holders: the Decider server (4,602 MiB), the Limite vLLM engine (4,060 MiB),
two llama-servers (324 + 820 MiB). Stopping the first two frees ≈8.6 GB.

## THE THREE UNBLOCK PATHS
1. **8-bit AdamW on the full model (~10.3 GB).** Needs `bitsandbytes` (NOT
   installed in any venv) and TWO edits to `train.py`: the optimizer class and a
   gradient-checkpointing flag. **Fits only if the two live services stop.**
2. **QLoRA (~2.0 GB).** Needs `peft` + `bitsandbytes` (neither installed) and a
   trainer rewrite — the published trainer has no adapter path.
3. **Full-precision on bigger hardware (23.3 GB).** No code change; not this card.

## WHY THIS IS A BLOCKER AND NOT A DEFERRAL
The trainer is a THIRD-PARTY artifact (`JevManager/vendor/decider`, Mapika's
reference recipe). Editing it is a decision about someone else's code, and the
HARD STOPS reserve that for the operator. **The arithmetic above is the honest
state: the corpus is ready; the trainer cannot fit this model on this card without
a change that is not mine to make unilaterally.**

## WHAT IS VERIFIED WITHOUT THE FINE-TUNE
The circuit does not NEED it — every gate is met:
- canon Tier-A RRR 6/6 within ±0.02 · the golden week 6/6 accepted by all 9 gates
- ECE 0.08706 → 0.03238 (the gate MET) · the unseen week +103.9 pips at 0.1% commission
W7 is an IMPROVEMENT deliverable, not a dependency of the circuit.
