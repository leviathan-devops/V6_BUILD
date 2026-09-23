# PLUTUS V6 — CHECKPOINT (round 14: six audit rounds, the acceptance ruling)

## SHAs
- git HEAD:              940c467
- host runtime suite:    5a81d30562deda17
- container isolation:   0dfcfc31d641f477
- the raw CT capture:    02e011ed9ae214dc   (the container's own exec output)

## TALLIES — ALL RE-RUN THIS SESSION
| suite | result |
|---|---|
| HOST tests (31) | **PASS=31 FAIL=0 BLOCKED=0** |
| HOST runtime suite | 13/13 PASS (5 adversarial + 8 happy) |
| CONTAINER isolation | **16/16 PASS** (3 adversarial + 13 happy) |
| hydra predicate / zero-coding | PASS / PASS |
| RUNTIME SEAT | PROVEN LIVE in the pi TUI pane |

## THE AUDIT GATE — 0 CRITICAL, AND THE HONEST STATE
Six rounds (9-14). **Criticals reached 0 at round 12 and stayed 0.** The HIGH
count oscillates because each fix wave is new code = new scan surface.
- ACCEPTANCE (0 critical + 0 regression): **MET**
- the highs: logged as operator-review debt (.trident/SCAN_ACCEPTANCE.md)
- **round 15: BLOCKED (PROVIDER_QUOTA_EXHAUSTED) — NOT PASSED.** The ship gate
  has never returned PASS on this tree and is not reported as doing so.

## THE ROUNDS' SUBSTANTIVE FINDINGS (all fixed + pinned)
- r9  THREE REAL GATE BYPASSES: G-RRR trusted the CALLER's rrr; LAW 2 unenforced;
      the session gate ignored the timezone offset.
- r10 the CRITICAL corpus mislabel: a negative kept RRR=4.25 in its STATE while
      labelling a different option.
- r11 my r10 fix introduced 2 MORE mislabels + left forensic negatives impossible.
      Root cause: fixing the named INSTANCE, not the invariant.
- r12 _DOT was a THREE-character class, not a backslash class; the session type
      check missed; PIP stayed a live view over a mutable source.
- r13 the witness panel was UNREACHABLE; AT-10 compared times lexicographically.
- r14 the scanner's aliased-import hole; and TWO OF MY OWN FIXES WERE WRONG (a
      bracket check that refused every losing trade; write patterns that flagged
      text.replace( — both refused LEGITIMATE behaviour).

## STOP CONDITIONS: 13 of 14 MET
NOT MET: the audit gate (see above — 0 critical, gate unrun).
