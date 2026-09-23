# PLUTUS V6 — CHECKPOINT (STOP 4 MET: the live model in the loop, under budget)

## HEAD: c18694d

## TALLIES (all re-run this session)
| suite | result |
|---|---|
| HOST tests | **PASS=32 FAIL=0 BLOCKED=0** |
| HOST runtime suite | 13/13 PASS |
| CONTAINER isolation | **16/16 PASS** |
| the LIVE pipeline | **17 answers, 402ms warm** (budget 500ms) |

## THE 14-CONDITION BOARD: 13 of 14 MET
Only STOP 11 (the audit gate: 0 critical, 11 high) is NOT MET.

## THREE DEFECTS FIXED THIS TURN (all measured)
1. **The state was 4x the blueprint's spec.** render_state rendered EVERY feed:
   3 pairs x 4 timeframes = 12 blocks, 9452 chars, **9242 real tokens** — 4x the
   spec ("State: 30m/1H/4H bars + pair + session + DXY ctx") and 13% OVER the
   blueprint's own 8,192-token limit. That oversize is what OOM'd the server.
   NOW: the target pair's 30m/1H/4H + DXY context = 2350 chars.
2. **The token guard could not see the real tokenizer.** count_tokens counted
   whitespace words: 2238 vs the served tokenizer's 9242 — a **4.13x undershoot**,
   so assert_state_fits never bit. NOW it loads the DECIDER's own tokenizer
   (verified ratio 0.97).
3. **The server's config was over-provisioned 4x.** DECIDER_MAX_STATE_TOKENS was
   unset -> 32768 vs the documented 8192; the KV cache is 48 KB/token, so that
   reserved ~1.6 GB for a ~400 MB need. NOW 8192 + expandable_segments.

**MEASURED IMPACT: latency 1259ms -> 402ms · the server's footprint 6587 -> 3827
MiB (2.76 GB freed) · the real state 17/17 where it previously OOM'd.**

## THE VRAM BLOCKER IS RESOLVED — WITH NO MODEL SUBSTITUTION
The blocker was NOT a model-size problem. See .trident/VRAM_BLOCKER.md.
The model-downgrade option is retained for graph-capture headroom only.

## THE COVERAGE GAP CLOSED
 (new): the circuit with the model IN the
loop. No test previously ran  — which is exactly how a model
marked "IT IS SUPERSEDED AND MUST NOT BE USED FOR DECISIONS" survived in the
production path.
