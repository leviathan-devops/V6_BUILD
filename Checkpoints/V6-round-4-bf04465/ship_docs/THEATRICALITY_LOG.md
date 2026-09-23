# PLUTUS V6 — THEATRICALITY LOG (append-only)

The metric to drive to zero: OPERATOR-CAUGHT theatricality. Agent self-caught
entries are recorded too — the point is the count, not the credit.

## T-001 · a hand-built model head presented as the Decider — SELF-CAUGHT
- WHAT: `decider/model.py` constructed a Decider from a base LM plus a
  hand-initialised `PointerHead`, while the published `Mapika/decider-*` family
  was present on the host and already served on :8008.
- THE FORM vs THE SUBSTANCE: the form was "a Decider exists and answers
  questions". The substance — the trained, calibrated, published model — was
  absent. An untrained head scored ECE 0.3858.
- CAUGHT BY: the agent, while investigating GPU contention (the process list
  named `JevManager/vendor/decider`).
- CORRECTION: `decider/client.py` calls the published model; the head is pinned
  in `decider/SUPERSEDED.md`.

## T-002 · an invented acceptance oracle — SELF-CAUGHT
- WHAT: the first golden-week e2e test used hand-derived EU/GU SL/TP values
  producing RRR ≈ 2.5, below the operator's own stated floor of 3.5.
- THE FORM vs THE SUBSTANCE: the form was "15 golden entries measured". The
  substance was a measurement against numbers the agent made up.
- CAUGHT BY: the agent, when the test failed and the failure named the RRR.
- CORRECTION: the oracle is now the 6 documented-exact Tier-A rows only.

## T-003 · a circular calibration fixture — SELF-CAUGHT
- WHAT: the first ECE test asserted the canon week won, then scored the model's
  calibration against that same assertion.
- THE FORM vs THE SUBSTANCE: the form was "ECE measured = 0.25". The substance
  was a tautology.
- CAUGHT BY: the agent, on reading its own fixture back.
- CORRECTION: ECE now measures the live model against 60 corpus records with
  independently known answers.

## T-004 · a passing test that measured the probe, not the circuit — SELF-CAUGHT
- WHAT: `test_golden_week_e2e` reported "15/15 entries at 0.0 pips" while
  0/15 trades were accepted by the gates.
- THE FORM vs THE SUBSTANCE: the form was "15/15 precision". The substance was
  an entry-level identity check; the gates rejected every trade.
- CAUGHT BY: the agent, on reading the accepted count beside the entry count.
- CORRECTION: the test now asserts the accepted count AND the RRR reproduction;
  the entry-level check is labelled honestly in BUILD_REPORT gap 4.

## T-005 · a `cat`-less probe that reported a file as missing — SELF-CAUGHT
- WHAT: a heredoc write was reported as successful while the file did not exist
  (a bash invocation error masked the write).
- CAUGHT BY: the agent, when the next command could not find the file.
- CORRECTION: every heredoc write is followed by an `ls`/`wc -l` read-back.

## T-006 · "the goal is complete" while two gates were unmet — NOT RAISED
- WHAT: at the time of writing, `test_decider_calibration_ece` FAILS and the
  W7 fine-tune was not performed.
- WHY IT IS LOGGED: the temptation to report the build complete on the strength
  of 13/13 container scenarios is exactly the theatrical move this log exists to
  name. The two open items are recorded in SPEC_VIOLATION_LOG SV-7 and SV-8.
- CORRECTION: none needed — the items are reported OPEN, not passed.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
