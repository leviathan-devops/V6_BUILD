# PLUTUS V6 — CHECKPOINT (40 audit rounds; 13 of 14 conditions MET)

## HEAD: f1050c6

## TALLIES
| suite | result |
|---|---|
| HOST tests | **PASS=30 FAIL=0** |
| HOST runtime suite | 13/13 PASS |
| CONTAINER isolation | 16/16 PASS |
| the LIVE pipeline | 17 answers, **430ms warm** (budget 500ms) |

## THE 14 CONDITIONS: 13 MET
1 golden 15/15 <=3p · 2 forensic 38 · 3 profitable 0.1% unseen · 4 latency 430ms
WITH THE MODEL IN THE LOOP · 5 zero coding · 6 TUI · 7 determinism · 8 golden RRR
6/6 · 9 mutant AT-03 · 10 ECE 0.03238 · 12 checkpoint · 13/14 docs
**11 THE AUDIT GATE: FAIL (0 critical, 8 high) — NOT MET, NOT reported as met.**

## THE VRAM BLOCKER: RESOLVED, NO MODEL SUBSTITUTION
The state was 4x the blueprint's spec (9242 tokens vs the documented 8192 limit);
count_tokens undershot the real tokenizer 4.13x; DECIDER_MAX_STATE_TOKENS was
unset (32768 vs 8192). Latency 1259ms -> ~430ms; 2.76 GB freed.

## THE AUDIT GATE: 40 ROUNDS, AND THE MEASURED BARRIER
1. the criticals are ZERO except when MY OWN FIXES introduce one (5 of 18
   completed rounds, every one a defect I created fixing the prior);
2. the highs do NOT converge (a band of 3-21);
3. the DOMINANT SOURCE is my own incomplete fixes (r33: 5-of-8; r35: 4-of-7;
   r38: an over-correction; r39: a fix at one of two sites).
THE ROOT CAUSE (r26): my batch script aborted at its first anchor miss, silently
killing every later edit. THE MECHANICAL GUARD: tests/test_fix_effectiveness.py,
30+ behavioural invariants that fail if a fix is inert.
