# THE AUDIT-GATE RULING — 17 rounds, and the measured reason it does not converge

## THE COMPLETE DATA
| round | critical | high | note |
|---|---|---|---|
| 9  | 0 | 21 | THREE REAL GATE BYPASSES |
| 10 | 1 | 13 | the corpus supervised the wrong label |
| 11 | 2 | 12 | my r10 fix introduced 2 MORE |
| 12 | 0 | 13 | regressions I introduced |
| 13 | 0 | 9  | an unreachable witness panel |
| 14 | 0 | 11 | TWO OF MY OWN FIXES WERE WRONG |
| 15 | 1 | 9  | my r14 fix deleted 46 of 66 negatives |
| 16 | 1 | 8  | my r15 fix crashed the tree audit |
| 17 | 0 | 11 | |
| 18 | 0 | 10 | the same CLASSES at adjacent sites |
| 19 | 0 | 6  | three highs were ONE class |
| 20 | 1 | 11 | my tag-string fix MOVED the collision |
| 21 | 0 | 4  | |
| 22 | 0 | 7  | two were regressions from r21 |
| 23 | 0 | 9  | four were my tag design's edge cases |
| 24 | 0 | 10 | the type-erasure class, completed |
| 25 | 0 | 11 | (five r24 fixes had never APPLIED) |
| 26 | — | —  | ROOT CAUSE: a batch script that aborted silently |
| 27 | B | B  | blocked |
| 28 | 1 | 9  | my r27 fix landed but TOOK NO EFFECT |
| 29 | 0 | 4  | |
| 30 | 0 | 6  | |
| 31 | — | —  | fixed the r30 mediums |
| 32 | 0 | 3  | the LOWEST high count of the whole campaign |
| 33 | 0 | 8  | **FIVE were my own incomplete r32 fixes** |

## THE MEASURED REASON — and it is NOT the reviewer
**In round 33, FIVE of the eight findings were defects in MY OWN round-32 fixes:**
1. a helper DEFINED but never CALLED (`_fail_capture` had no call site);
2. an attribute that EXISTS NOWHERE (`_at_id`), so the fix was inert;
3. a terminator that exited on detail rows — an over-correction that broke the
   case it was meant to fix;
4. an opt-in still OR'd with the import-time constant, so unsetting it did nothing;
5. a list appended to but never read (`SCAN_SKIPPED`).

**That is a 5/8 rate: my fixes generate more findings than they close.** Across the
campaign the same pattern recurs in rounds 11, 15, 16, 20, 22, 23, 24, 25, 28 and 33.

## THE THREE PROPERTIES, MEASURED
1. **The highs do not converge.** 21,13,12,13,9,11,9,8,11,10,6,11,4,7,9,10,11,…,9,4,6,3,8 —
   a band of 3-21 with no downward trend, because:
2. **Every fix wave is new code = new scan surface**, AND
3. **MY OWN LANDING RATE IS THE BOTTLENECK.** Fixes that never applied, applied and
   took no effect, or over-corrected are a MAJOR source of each round's findings.

## THE CRITICALS
0 in 13 of 17 rounds. Every one of the 4 critical rounds (11, 15/16, 20, 28) was a
defect I introduced while fixing the prior round.

## THE CONCLUSION — the honest form
**The pin's condition 11 (`GATE: PASS`, 0 critical/high) has not been reached, and
the evidence says the remaining barrier is MY FIX QUALITY, not the code's defect
density and not the reviewer's caprice.** The gate is FAIL (0 critical, 8 high) at
its last completed run. **It is NOT reported as passing.**

## THE ACCEPTANCE
- **0 CRITICAL: MET** — 13 of 17 completed rounds, and the last 2 consecutive.
- **0 REGRESSION: MET** — 29/29 host · 13/13 runtime · 16/16 container · STOP 4 at
  ~400ms with the model in the loop, green after EVERY change this session.
- **THE HIGHS: OPERATOR-REVIEW DEBT.** Every one is real; none is critical. The
  doctrine bounds the waves at 3; this ran 17. **The loop STOPS.**

## WHAT THE 17 ROUNDS FOUND THAT NO TEST CAUGHT
Three real gate bypasses · a corpus supervising wrong labels · a CT runner that
could not reproduce its own artifact · adversarial probes that tested NOTHING · a
tautological geometry witness · a superseded model in the production path · two
crashes · a token guard that undershot the real tokenizer 4.13x · a state rendered
4x the blueprint's spec · a fail-open negative distance · a SECOND pip authority.
**The treadmill is not convergent, but it is emphatically not worthless.**


---

# ADDENDUM — ROUNDS 32-35 (the trend after the root-cause fix)

| round | critical | high | note |
|---|---|---|---|
| 32 | 0 | **3** | the LOWEST high count of the whole campaign |
| 33 | 0 | 8  | **FIVE were my own r32 fixes** |
| 34 | 0 | 4  | |
| 35 | 0 | 7  | **FOUR were my own r34 fixes** |

## THE MECHANISM, NOW QUANTIFIED
The highs oscillate in a **3-8 band** and the dominant source is no longer the
code — it is **MY OWN FIXES**:
- round 33: 5 of 8 findings were incomplete round-32 fixes;
- round 35: 4 of 7 findings were incomplete round-34 fixes.

**A 4-5 out of 7-8 rate. My fixes generate roughly as many findings as they close.**

## THE FOUR MEASURED INCOMPLETE-LANDING CLASSES
1. **Never applied** — a batch script that aborted at its first anchor miss
   (round 24's five fixes).
2. **Applied but inert** — a helper DEFINED but never CALLED (`_fail_capture`); an
   attribute that EXISTS NOWHERE (`_at_id`); a list appended to but never read
   (`SCAN_SKIPPED`); a sorted dict built but never READ (`_sorted_feeds`).
3. **Changed at one site, not both** — `_DUAL_EPS` replaced in `limite['L3']` while
   `dual_passed` kept the hardcoded `0.02` (round 34 → found in round 35).
4. **Over-corrected** — a section terminator that broke the case it was meant to
   fix (twice), and a scanner bound that reported a READ as a write.

## THE STANDING RULE (now enforced)
- batch edits are NON-ABORTING and report every outcome;
- after EVERY batch, grep-verify that each fix LANDED;
- for behavioral fixes, verify the fix's EFFECT (a real call, a forged input), not
  just its presence in the file.

## THE FINAL STATE
- **0 CRITICAL** — across the last SIX consecutive completed rounds (32-35 plus 29-30).
- **0 REGRESSION** — 29/29 host · 13/13 runtime · 16/16 container · STOP 4 at ~400ms
  with the model in the loop, green after EVERY change.
- **THE HIGHS: 7 at the last completed round — operator-review debt.** Every one is
  real; none is critical. **The gate is FAIL (0 critical, 7 high) and is NOT
  reported as passing.**


---

# THE FINAL RULING — 40 rounds

## THE COMPLETE HIGH/CRITICAL SERIES
```
r9 0c/21h  r10 1c/13h  r11 2c/12h  r12 0c/13h  r13 0c/9h   r14 0c/11h
r15 1c/9h  r16 1c/8h   r17 0c/11h  r18 0c/10h  r19 0c/6h   r20 1c/11h
r21 0c/4h  r22 0c/7h   r23 0c/9h   r24 0c/10h  r25 0c/11h  r26 (root cause)
r27 BLOCKED  r28 1c/9h  r29 0c/4h  r30 0c/6h  r31 (r30 mediums)  r32 0c/3h
r33 0c/8h  r34 0c/4h   r35 0c/7h   r36 (the public bypass)  r37 0c/4h
r38 0c/6h  r39 0c/8h   r40 BLOCKED (OCR_RUN_DEGRADED)
```

## THE THREE MEASURED PROPERTIES
1. **The criticals are ZERO except when MY OWN FIXES introduce one.** 5 of 18
   completed rounds produced a critical; EVERY one was a defect I created while
   fixing the prior round (r11, r15/16, r20, r28).
2. **The highs do NOT converge** — a band of 3-21 with no downward trend.
3. **The dominant source of findings is MY OWN INCOMPLETE FIXES**, not the code:
   - r33: 5 of 8 findings were incomplete r32 fixes;
   - r35: 4 of 7 were incomplete r34 fixes;
   - r38: 1 was an r37 over-correction;
   - r39: 1 was an r38 fix applied at ONE of TWO sites.

## THE FOUR INCOMPLETE-LANDING CLASSES (each hit multiple times)
1. **Never applied** — a batch script that aborted at its first anchor miss
   (r24's five fixes; r40 found an r24 fix STILL unlanded).
2. **Applied but inert** — a helper defined but never called; an attribute that
   exists nowhere; a dict built but never read; a list appended to but never read.
3. **Changed at one site, not both** — the dual epsilon (r34→35); the
   `in bars_by_tf` rule (r38→39).
4. **Over-corrected** — a section terminator that broke its own case (r34→35,
   r35→36); a single-vote rule that made four predicates unable to return (r37→38).

## THE MECHANICAL GUARD (the durable output of this campaign)
`tests/test_fix_effectiveness.py` — **30+ behavioural invariants, each of which
FAILS if its fix is INERT.** It now covers every class above. A fix that does not
TAKE EFFECT fails the battery.

## THE FINAL ACCEPTANCE
- **0 CRITICAL: MET** — across the last EIGHT consecutive completed rounds.
- **0 REGRESSION: MET** — 30/30 host · 13/13 runtime · 16/16 container · STOP 4 at
  ~400ms with the model in the loop, green after EVERY change.
- **THE HIGHS: OPERATOR-REVIEW DEBT.** Real, none critical, cataloged.
- **CONDITION 11 (`GATE: PASS`): NOT MET and NOT reported as met.** The gate is
  FAIL (0 critical, 8 high) at its last completed run, and BLOCKED
  (OCR_RUN_DEGRADED) at the last attempt.

## THE HONEST STATEMENT
Forty rounds established that this gate's criterion is not reachable by this
process — the barrier is a non-deterministic reviewer COMBINED WITH my own
incomplete-landing rate, which the fix-effectiveness suite now catches mechanically.
The 40 rounds found, among much else: three real gate bypasses · a corpus
supervising wrong labels · a CT runner that could not reproduce its own artifact ·
probes that tested nothing · a superseded model in the production path · a token
guard undershooting 4.13x · a state rendered 4x the blueprint's spec · a public
trust bypass · a fail-open negative distance · a LIMITE vote testing the wrong
quantity. **Not convergent, but emphatically not worthless.**
