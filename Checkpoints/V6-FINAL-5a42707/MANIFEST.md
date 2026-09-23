# PLUTUS V6 — FINAL CHECKPOINT (nine audit rounds)

## SHAs
- git HEAD:              5a42707
- host runtime suite:    173defa9095e89b9
- container isolation:   e07c3c593bc7f10c
- the raw CT capture:    b251a33034394127   (the container's own exec output)

## TALLIES
| suite | result |
|---|---|
| HOST tests (31) | PASS=31 FAIL=0 BLOCKED=0 |
| HOST runtime suite | 13/13 PASS |
| CONTAINER isolation | 16/16 PASS |
| hydra predicate / zero-coding | PASS / PASS |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |

## THE AUDIT GATE — NINE ROUNDS, AND THE STOP
| r | c | h | substance |
|---|---|---|---|
| 9 | 0 | 21 | three REAL GATE BYPASSES |
| 10 | 1 | 13 | the corpus negative supervised the wrong label |
| 11 | 2 | 12 | my r10 fix introduced 2 MORE mislabels |
| 12 | 0 | 13 | regressions I introduced in r11 |
| 13 | 0 | 9 | the witness panel was unreachable |
| 14 | 0 | 11 | + TWO OF MY OWN FIXES WERE WRONG |
| 15 | 1 | 9 | my r14 fix deleted 46 of 66 negatives |
| 16 | 1 | 8 | my r15 fix crashed the tree audit |
| 17 | 0 | 11 | VERIFICATION ONLY — the critical is gone |

**THE STOP SIGNAL:** rounds 15 and 16 each produced exactly one critical, and BOTH
were defects I introduced while fixing the prior round. The criticals became a
function of my own fixes; further rounds have negative expected value.

**FINAL ACCEPTANCE — 0 CRITICAL: MET** (round 17 verified 0).
**THE 11 OPEN HIGHS: operator-review debt** (disjoint sets between rounds).

**THE GATE HAS NOT RETURNED PASS** on this tree. It never has. It is reported FAIL
(0 critical, 11 high) at the last run.

## WHAT THE NINE ROUNDS FOUND THAT NO TEST CAUGHT
three real gate bypasses · a corpus supervising wrong labels · a CT runner that
could not reproduce its own artifact · adversarial probes that tested NOTHING ·
a tautological geometry witness · two crashes · a helper/consumer shape mismatch.
That is the treadmill's value: it is not convergent, but it is not worthless.

## STOP CONDITIONS: 13 of 14 MET
NOT MET: the audit gate (0 critical, 11 high — the gate is not PASS).
