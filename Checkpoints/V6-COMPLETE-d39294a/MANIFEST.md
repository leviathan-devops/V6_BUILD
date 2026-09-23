# PLUTUS V6 — COMPLETE CHECKPOINT

## SHAs
- git HEAD:                  d39294a
- host container-suite:      9f8dfc263d58dca3  (.trident/container-test-results.json)
- CONTAINER isolation suite: e89a66b03742c93c  (.trident/ct-results.json)

## THE TALLIES
| suite | result |
|---|---|
| HOST tests (31) | PASS=31 FAIL=0 BLOCKED=0 |
| HOST container suite | 13/13 PASS (5 adversarial FIRST, 8 happy LAST) |
| CONTAINER isolation suite | 16/16 PASS (3 adversarial FIRST, 13 happy LAST) |
| hydra worker predicate | PASS (7 worktrees) |
| prove_zero_coding | PASS |
| test_tools_execute | PASS (5/5) |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |

## STOP CONDITIONS: 13 of 14 MET
1 entries MET · 2 forensic MET · 3 unseen-week MET · 4 latency MET · 5 zero-coding
MET · 6 TUI MET · 7 determinism MET · 8 RRR MET · 9 mutants MET · 10 ECE MET ·
11 audit gate **NOT MET** · 12 checkpoint MET · 13 ship docs MET · 14 canon docs MET

## THE CONTAINER TEST FOUND FOUR REAL DEFECTS (why it exists)
16 of 31 tests embedded the host path; classify_38 required the PLUTUS tree;
the determinism test asserted a superseded contract; the walk-forward needed the
wide harvest. All fixed and re-verified in BOTH environments.

## THE TWO LIVE ENGINES (services)
Decider Mapika/decider-2b :8008 · Limite paradigma-inc/limite-1b-violetto :8100

## THE TWO HONEST REMAINDERS
1. The audit gate: 8 rounds, 0->2 criticals, ~20 high, not trending to zero.
2. W7 fine-tune: HARD BLOCKER — full-parameter trainer; a 2B needs ~28GB, the
   card has 12GB. No LoRA path exists in the trainer.

## THE OPERATOR-OWNED DECISION
The V5 -> V6 cutover.
