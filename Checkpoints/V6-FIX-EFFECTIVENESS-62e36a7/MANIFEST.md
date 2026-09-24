# PLUTUS V6 — CHECKPOINT (35 audit rounds; the fix-effectiveness suite added)

## HEAD: 62e36a7

## TALLIES
| suite | result |
|---|---|
| HOST tests | **PASS=30 FAIL=0** (29 + the new fix-effectiveness suite) |
| HOST runtime suite | 13/13 PASS |
| CONTAINER isolation | 16/16 PASS |
| the LIVE pipeline | 17 answers, ~400ms warm (budget 500ms) |

## THE 14 CONDITIONS: 13 MET
1 golden 15/15 <=3p · 2 forensic 38 · 3 profitable 0.1% unseen · 4 latency ~400ms
WITH THE MODEL IN THE LOOP · 5 zero coding · 6 TUI · 7 determinism · 8 golden RRR
6/6 · 9 mutant AT-03 · 10 ECE 0.03238 · 12 checkpoint · 13/14 docs
**11 THE AUDIT GATE: FAIL (0 critical, 7 high) — NOT MET, NOT reported as met.**

## THE NEW MECHANICAL GUARD
 — 26 behavioural invariants, each of which
FAILS if its fix is INERT. It exists because the dominant remaining defect source
was not the code: it was fixes that never applied, applied but were never called,
or were changed at one site while a sibling kept the old value (5 of 8 findings in
round 33; 4 of 7 in round 35). A "present in the file" check cannot catch those —
only an assertion on observable behaviour can.
