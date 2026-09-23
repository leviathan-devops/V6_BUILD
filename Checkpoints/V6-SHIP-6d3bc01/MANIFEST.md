# PLUTUS V6 — SHIP CHECKPOINT

## SHAs
- git HEAD:           6d3bc01
- container artifact: 9f8dfc263d58dca3

## THE DEFINITIVE TALLY
PASS=31 FAIL=0 BLOCKED=0

## EVERY CHECK, VERIFIED THIS SESSION
| check | result |
|---|---|
| hydra worker predicate | PASS (7 worktrees, WORKERS: 7) |
| all 31 tests | PASS=31 FAIL=0 BLOCKED=0 |
| container suite | 13/13 PASS (5 adversarial FIRST, 8 happy LAST) |
| prove_zero_coding | PASS (pi's 8 built-ins removed; 7 plutus_* tools) |
| test_tools_execute | PASS (5/5 payloads) |
| RUNTIME SEAT | PROVEN LIVE (the agent drove probe + golden week in the pane) |
| canon Tier-A RRR | 6/6 within +-0.02 |
| walk-forward | +103.9p at 0.1% on an UNSEEN week |
| ECE | 0.08706 -> 0.03238 on 60 eval rows WITH 7 errors |
| forensic 38 | 7 laws applied; LAW 6 reproduces the source's own count |

## STOP CONDITIONS: 13 of 14 MET
The one NOT MET: the audit gate (8 rounds; 0->2 criticals; the high count
does not trend to zero).

## THE TWO LIVE ENGINES (services)
- Decider: Mapika/decider-2b on 127.0.0.1:8008 (POST /v1/systemone)
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100 (vLLM + plugin)

## HARD BLOCKER
W7 fine-tune: decider/train.py is full-parameter (AdamW over all params).
A 2B needs ~28GB; the card has 12GB. No LoRA path exists in the trainer.

## THE OPERATOR-OWNED DECISION
The V5 -> V6 cutover. V5: canon 15/15, suite 1195/0. V6: 31/31 tests,
container 13/13, the runtime seat proven live, 13 of 14 STOP conditions met.
