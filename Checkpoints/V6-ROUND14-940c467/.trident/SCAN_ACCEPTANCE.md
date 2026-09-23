# THE AUDIT-GATE ACCEPTANCE RECORD (the anti-treadmill ruling)

## WHAT HAPPENED
The audit gate ran **SIX** rounds on this change set (rounds 9-14). The finding
sets were largely DISJOINT between rounds — the documented non-convergence:

| round | critical | high | note |
|---|---|---|---|
| 9  | 0 | 21 | found THREE REAL GATE BYPASSES |
| 10 | 1 | 13 | the CRITICAL: a corpus negative supervised the wrong label |
| 11 | 2 | 12 | my round-10 fix introduced 2 MORE mislabels |
| 12 | 0 | 13 | mostly regressions I introduced in round 11 |
| 13 | 0 | 9  | the witness panel was unreachable |
| 14 | 0 | 11 | the aliased-import evasion; 2 of my fixes were WRONG |
| 15 | — | —  | **BLOCKED: PROVIDER_QUOTA_EXHAUSTED** (the gate could not run) |

## THE CONVERGENCE SIGNAL
**Criticals reached 0 at round 12 and stayed 0** (rounds 12, 13, 14). The HIGH
count does not trend down because each fix wave is NEW CODE = NEW SCAN SURFACE —
the doctrine's exact diagnosis. The highs also OSCILLATE: a fix that closes one
finding opens another (round 14: my bracket check refused every losing trade; my
write any-receiver patterns flagged `text.replace(`).

## THE RULING (per the anti-treadmill doctrine)
- **ACCEPTANCE: 0 CRITICAL + 0 REGRESSION.** MET.
  - criticals: 0 across three consecutive completed rounds;
  - regressions: the full battery is green (31/31 host, 16/16 container, 13/13
    container runtime) and every fix was verified by attack before it landed.
- **THE HIGHS: OPERATOR-REVIEW DEBT.** Logged in this directory, not chased. The
  doctrine: after the bounded waves the operator reviews and accepts/rejects each.
- **ROUND 15 IS BLOCKED, NOT PASSED.** `PROVIDER_QUOTA_EXHAUSTED` — the gate
  could not run. Reported as blocked. **The ship gate has NOT passed.**

## WHAT IS PROVEN, AND WHAT IS NOT
PROVEN (this session, mechanically):
  - 31/31 host tests · 16/16 container scenarios · 13/13 container runtime suite
  - the runtime seat renders in a live pi TUI pane
  - the CT suite is REPRODUCIBLE end to end (a container-side driver + a host
    assembler; the earlier runner's exec path was fictional)
  - the CT capture is not spoofable (4 attacks constructed, all 4 refused)
  - the corpus's RRR/floor negatives all contradict their own labels (verified by
    re-parsing each negative's own quantity; 0 mislabelled)
  - the zero-coding scanner catches all 5 constructed evasion vectors
NOT PROVEN:
  - the audit gate has never returned PASS on this tree. The criticals are 0, but
    the gate itself is UNRUN since round 14.
