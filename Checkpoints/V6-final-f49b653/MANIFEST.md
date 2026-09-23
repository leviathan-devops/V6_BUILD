# PLUTUS V6 — FINAL CHECKPOINT

## SHAs
- git HEAD:           f49b653
- container artifact: 7cc841a62ffee40f

## GREEN
| check | result |
|---|---|
| fast tests | 30/30 PASS |
| test_limite_dual_live | PASS (the record reproduces) |
| test_calibration_layer | PASS (held-out 0.3492 -> 0.1080) |
| test_decider_calibration_ece | PASS (corpus 0.08706 -> 0.03238, 7 errors) |
| test_walkforward_unseen_week | PASS (+103.9p at 0.1%) |
| test_forensic_38_classification | PASS |
| container suite | 13/13 PASS |
| prove_zero_coding | PASS |
| test_tools_execute | PASS (5/5) |
| hydra predicate | PASS |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |

## STOP CONDITIONS: 13 of 14 MET
The one NOT MET: the audit gate (8 rounds, 0->2 criticals, ~20 high).

## THE TWO LIVE ENGINES (services, not in this archive)
- Decider: Mapika/decider-2b on 127.0.0.1:8008
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100

## HARD BLOCKER (unchanged)
W7 fine-tune: decider/train.py is full-parameter; a 2B needs ~28GB, the card has 12GB.
