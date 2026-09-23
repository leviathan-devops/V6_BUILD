# PLUTUS V6 — DEBUG LOG (append-only)

## EN-001 · the 0-indexed expected level (2026-09-23)
- FINDING: `expected_level({"F":0.02,...,"Aplus":0.20})` returned 2.73; the
  blueprint §1.4 states the same distribution yields 3.73.
- ROOT CAUSE: `enumerate(levels)` starts at 0; the blueprint's formula Σ(i·p_i)
  is 1-indexed over the ordered scale.
- FIX: `(i + 1) * probs.get(lv, 0.0)`; `grade_from_probs` index = round(exp)-1.
- VERIFICATION: test_pass_e1_questions → expected_level = 3.73 (matches §1.4).
- LESSON: when a spec states a worked value, assert against THAT VALUE — a
  formula reading is not enough.

## EN-002 · the session gate read the UTC offset as the time (2026-09-23)
- FINDING: a candidate at `2026-07-06T14:30:00-04:00` PASSED the London window.
- ROOT CAUSE: `s[-5:]` on an ISO string returns the offset suffix `-04:00`,
  whose last 5 chars are `04:00` — inside 02:00-05:00. Every EDT timestamp
  silently passed; every EST timestamp (`-05:00` → `05:00`) also passed.
- FIX: take the component between `T` and the offset.
- VERIFICATION: `2026-07-06T14:30:00-04:00` → G-SESSION_REJECT.
- LESSON: a slice at the END of a structured string is a guess about its shape.

## EN-003 · the session gate rejected the state constructor's own label (2026-09-23)
- FINDING: 0/15 golden entries accepted; G-SESSION reported "no parseable
  session timestamp on the candidate ('LONDON 02:00')".
- ROOT CAUSE: the state constructor emits a human label; the gate parsed only
  ISO timestamps. Two modules, two session formats, no shared contract.
- FIX: the gate accepts both forms.
- VERIFICATION: label → PASS, ISO in-window → PASS, both out-of-window → REJECT.
- LESSON: an interface between two modules is a CONTRACT; assert it in a test
  that crosses the boundary.

## EN-004 · the circuit hardcoded one pip scale for every pair (2026-09-23)
- FINDING: DXY Tier-A trades all rejected; their 4-pip stops were reported as 400 pips.
- ROOT CAUSE: `integration/circuit.py` used the literal `0.0001` as the pip for
  every pair, but DXY's pip is `0.01` — a 100× error on every DXY distance.
- FIX: read the pair's pip from the single authority (`math_queries.PIP`).
- VERIFICATION: 6/6 Tier-A accepted; RRR reproduced ±0.02.
- LESSON: a magic constant that is correct for the pair you are testing with is
  the most dangerous constant in the file.

## EN-005 · the digest's volatile filter missed depth 0 (2026-09-23)
- FINDING: two identical runs produced different digests once `ts_wall` was added.
- ROOT CAUSE: `strip()` filtered volatile keys INSIDE each stage; a volatile key
  at the TOP level became a new stage named `ts_wall`.
- FIX: filter at depth 0 as well; add `latency_ms`/`stage_latency` to VOLATILE.
- VERIFICATION: two runs byte-identical with latency fields present.
- LESSON: a recursive filter must handle its own base case.

## EN-006 · the empty feed raised an unnamed stdlib error (2026-09-23)
- FINDING: `ValueError: max() iterable argument is empty` from `swing_levels`.
- ROOT CAUSE: `max()` over an empty window. The module HAS a name for this
  condition (`EmptyBars`/`NO_BARS`) but did not use it on this path.
- FIX: raise `EmptyBars("NO_BARS: ...")` before the max/min.
- VERIFICATION: ADV-1 in the container suite → REFUSED NO_BARS.
- LESSON: a module that defines a named refusal must raise it on EVERY path
  that reaches the condition.

## EN-007 · the corpus dedup collapsed intentional multi-signal records (2026-09-23)
- FINDING: 1,242 card records collapsed to 621 after dedup.
- ROOT CAUSE: the key was (source, quote); the same card yields two DIFFERENT
  training signals (verify + classify) that share a source and quote.
- FIX: key on (source, quote, question).
- VERIFICATION: 1,267 records, zero provenance violations.
- LESSON: a dedup key must include every field that distinguishes the records
  you intend to keep.

## EN-008 · the pointer head stayed on CPU (2026-09-23)
- FINDING: `RuntimeError: Expected all tensors to be on the same device ... mat2 is on cpu`
- ROOT CAUSE: `PointerHead.__init__` created `self.W` on CPU; the hidden states
  came back on cuda:0.
- FIX: `self.head.W = self.head.W.to(self.device)`; `load()` takes a device.
- VERIFICATION: the head then produced distributions on the live model.
- LESSON: a module that participates in a forward pass must live on the device
  of the pass.
- SUPERSEDED: the hand-built head was replaced by the published `Mapika/decider-2b`
  (see decider/SUPERSEDED.md). The defect is retained as a record of the wrong path.
