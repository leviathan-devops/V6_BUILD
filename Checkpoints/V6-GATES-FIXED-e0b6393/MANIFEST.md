# PLUTUS V6 — CHECKPOINT (gates hardened, audit round 9)

## SHAs
- git HEAD:              e0b6393
- host container-suite:  33fd3e98a731fce1
- container isolation:   e89a66b03742c93c

## TALLIES
| suite | result |
|---|---|
| HOST tests (31) | PASS=31 FAIL=0 BLOCKED=0 |
| HOST container suite | 13/13 PASS |
| CONTAINER isolation suite | 16/16 PASS (stdlib only) |
| hydra predicate / zero-coding | PASS / PASS |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |

## ROUND 9 CLOSED THREE REAL GATE BYPASSES
1. G-RRR trusted the CALLER's rrr -> now RECOMPUTES from the geometry and
   rejects a stated/derived mismatch.
2. LAW 2 was unenforced -> the SL distance must now equal the zone width
   (0..5 pip buffer). The circuit's own default was the TP distance, so every
   candidate it built violated LAW 2 by its own reward.
3. The session gate ignored the timezone offset -> an offset-bearing stamp is
   converted to ET.

These are the class that matters: a gate reading the WRONG SUBJECT.

## STOP CONDITIONS: 13 of 14 MET
NOT MET: the audit gate (9 rounds now; the highs moved from surface defects to
semantic ones).

## THE W7 BLOCKER, MEASURED (finetune/FEASIBILITY.md)
The published trainer is full-parameter with NO memory lever (grep-verified).
decider-2b needs 28.0GB, decider-0.8b 11.2GB; the card is 12.2GB with ~2.0GB
free. Three concrete unblock paths are named. The circuit does NOT need it —
every gate is met without the fine-tune.
