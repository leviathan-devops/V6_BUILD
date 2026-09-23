# PLUTUS V6 — FAILURE LOG (the derailment ledger)

## F-01 · a hand-built Decider was built while the real one was on the host
- WHAT HAPPENED: `decider/model.py` was authored to construct a Decider from
  Qwen3-0.6B-Base + a hand-initialised `PointerHead`. The real, published Decider
  family (`Mapika/decider-2b`, `-0.8b`, `-4b`, `-35b-a3b`) was already present
  at `JevManager/vendor/decider/` and ALREADY SERVED on 127.0.0.1:8008.
- WHY IT WAS ALLOWED: `Mapika/decider-0.6b` returned HTTP 401 (private), and the
  probe concluded no published Decider was reachable. The probe did not search
  the HOST for a local implementation of the family it was trying to call.
- COST: an untrained head, an ECE of 0.3858, and a device-placement defect.
- FIX: `decider/client.py` calls the published model over its own wire format;
  the hand-built head is pinned in `decider/SUPERSEDED.md`.
- THE LAW THIS VIOLATED: a "published model is unavailable" claim requires a
  host-side search, not only a registry probe.

## F-02 · the acceptance oracle was invented instead of read
- WHAT HAPPENED: the first golden-week e2e test used EU/GU entries with SL/TP
  values derived by hand. They produced RRR ≈ 2.5, below the operator's own
  stated floor ("NOT A SINGLE ONE OF MY TRADES IS BELOW RRR = 3.5").
- WHY IT WAS ALLOWED: the canon cascade document was not read before the test
  was written; the derived numbers were plausible.
- COST: a failing test that was measuring the probe, not the circuit.
- FIX: the e2e test now uses ONLY the 6 documented-exact Tier-A DXY rows, with
  the canon RRR values as the oracle. The Tier-D FX rows are explicitly excluded
  from acceptance because the canon marks them pixel-inferred (⚠).
- THE LAW THIS VIOLATED: an oracle must be the MEASUREMENT, and a measurement
  must come from the operator's record, never from a derivation.

## F-03 · a circular calibration fixture
- WHAT HAPPENED: the first ECE test asserted "the canon week won, so claims of
  grade A are correct", then measured calibration against that same assertion.
  The measurement was a tautology; it scored 0.25 and proved nothing.
- WHY IT WAS ALLOWED: the fixture was convenient and the number looked like a
  result.
- FIX: the ECE test now measures the LIVE Decider against 60 corpus records
  whose answers are known independently of the model.
- THE LAW THIS VIOLATED: a measurement whose ground truth is supplied by the
  thing being measured is not a measurement.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
