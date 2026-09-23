# PLUTUS V6 CHECKPOINT — round 8

## SHAs
- git HEAD:           e1496fb
- container artifact: 9977253a1d44d74d

## GREEN AT THIS CHECKPOINT
| check | result |
|---|---|
| hydra worker predicate | PASS (7 worktrees) |
| fast tests | 28/28 PASS |
| test_calibration_layer | PASS (held-out ECE 0.3492 -> 0.1080) |
| test_walkforward_unseen_week | PASS (+103.9p at 0.1% on an UNSEEN week) |
| test_forensic_38_classification | PASS (LAW 6 reproduces the source's own count) |
| container suite | 13/13 PASS |
| prove_zero_coding | PASS |
| test_tools_execute | PASS (5/5) |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |
| canon Tier-A RRR | 6/6 within +-0.02 |

## STOP CONDITIONS: 11 of 14 MET
MET:      1 (entries) 3 (unseen week) 4 (latency) 5 (zero coding) 6 (TUI)
          7 (determinism) 8 (RRR) 9 (mutants) 12 (checkpoint) 13 (ship docs)
          14 (canon docs)
PARTIAL:  2 (38 forensic: 7 laws + 30 rows classified; 4 laws have no column)
NOT MET:  10 (ECE 0.2579 vs 0.05)
          11 (audit GATE: FAIL — 8 rounds, 0->2 criticals, ~25 high, not trending to 0)

## THE AUDIT GATE — EIGHT ROUNDS
criticals: 1, 0, 2, 0, 0, 2, 2, 2      highs: 35, 20, 17, 21, 28, 25, 25, 19
The HIGH count does not trend to zero. Each round's fixes create the next
round's surface. The round-8 criticals were BOTH in my own scanner — an
alias-length cap and a name-based safe list the attacker controls.

## THE TWO LIVE ENGINES (services, not in this archive)
- Decider: Mapika/decider-2b on 127.0.0.1:8008 (POST /v1/systemone)
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100 (vLLM + plugin)

## HARD BLOCKER
W7 fine-tune: decider/train.py is FULL-PARAMETER (AdamW over all params).
A 2B needs ~28GB; the card has 12GB. No LoRA path exists in the trainer.
