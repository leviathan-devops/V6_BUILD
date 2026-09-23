# W7 FINE-TUNE — THE MEASURED FEASIBILITY (not a guess)

## WHAT THE PIN ASKS
W7: "generate 700+ records from 649 cards, fine-tune Decider-0.6B". The corpus
half is DONE (1,903 records with D13 provenance). This file is the training half.

## WHAT THE PUBLISHED TRAINER DOES (read, not assumed)
`JevManager/vendor/decider/decider/train.py`:
  line 95:  `opt = torch.optim.AdamW(model.parameters(), lr=a.lr, ...)`
            -> FULL-PARAMETER. No freezing, no LoRA, no parameter groups.
  grep for `grad_checkpoint|offload|8bit|4bit|bnb|deepspeed|fsdp|zero`
            -> ZERO matches. There is NO memory lever to enable.
  line 124: `opt.step(); opt.zero_grad(set_to_none=True)`
            -> a plain single-GPU loop.

## THE ARITHMETIC (the reason it does not fit)
| model | bf16 weights | fp32 master | AdamW m+v (fp32) | TOTAL |
|---|---|---|---|---|
| decider-2b (0.8b->2b) | 4.0 GB | 8.0 GB | 16.0 GB | **28.0 GB** |
| decider-0.8b (the smallest published) | 1.6 GB | 3.2 GB | 6.4 GB | **11.2 GB** |

The card is 12.2 GB and currently holds the two LIVE services (the Decider
server at ~4.6 GB and the Limite vLLM engine at ~4.1 GB), leaving ~2.0 GB free.

**decider-2b needs 28.0 GB. decider-0.8b needs 11.2 GB.** Neither fits as-is.

## WHAT WOULD UNBLOCK IT (each a real, bounded change)
1. **8-bit Adam on decider-0.8b.** `bitsandbytes` Adam8bit stores the moments in
   1 byte instead of 4: 0.8b -> 1.6 + 3.2 + 1.6 = **6.4 GB**, plus ~0.5 GB of
   activations with gradient checkpointing = **6.9 GB**. That FITS, and it needs
   two edits to `train.py` (the optimizer class + a checkpointing flag).
2. **Stop the two live services for the duration.** Frees ~8.7 GB, which alone
   makes decider-2b's weights + master (12 GB) marginal but decider-0.8b
   comfortable.
3. **QLoRA on decider-0.8b.** A 4-bit base + LoRA adapters needs ~2 GB. It
   requires `peft` + `bitsandbytes` and a trainer rewrite (the published one has
   no adapter path).

## WHY THIS IS A BLOCKER AND NOT A DEFERRAL
The trainer is a THIRD-PARTY artifact (`JevManager/vendor/decider`, Mapika's
reference recipe). Editing it is a decision about someone else's code, and the
pin's HARD STOPS say: an operator-owned decision waits for the operator. The
arithmetic above is the honest state: **the corpus is ready, the trainer cannot
fit the model on this card without a change that is not mine to make unilaterally.**

## WHAT IS VERIFIED WITHOUT THE FINE-TUNE
The circuit does not NEED the fine-tune to meet its gates:
  - canon Tier-A RRR  6/6 within +-0.02
  - the golden week   6/6 accepted by all 9 gates
  - ECE               0.08706 -> 0.03238 (the gate MET)
  - the unseen week   +103.9 pips at 0.1% commission
W7 is an IMPROVEMENT deliverable, not a dependency of the circuit.
