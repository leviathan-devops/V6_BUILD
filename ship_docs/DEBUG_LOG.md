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

## EN-009 · the circuit imported the STALE worktree modules after the merge (2026-09-23)
- FINDING: the integrated tree's fixes had no effect; the golden week still
  reported 0/6 accepted while the gate chain in the master tree had 9 gates.
- ROOT CAUSE: `integration/circuit.py` resolved its siblings through HARDCODED
  `.wt/wb-limite/gates`-style paths. Those are the PRE-MERGE copies, and
  `sys.path.insert(0, ...)` put them ahead of the integrated tree, so the
  circuit imported the worktree's older `gates.py`. Every fix applied after the
  merge was silently shadowed.
- FIX: resolve the siblings relative to THIS file's own location (`_HERE.parent`)
  and `append` (never prepend) so stdlib cannot be shadowed.
- VERIFICATION: `circuit.py` now reports `gates.__file__` = the master tree,
  chain size 9, `G-DUAL_UNVERIFIED` present.
- LESSON: a hardcoded path to a sibling module is a time bomb that detonates at
  the moment the layout changes. Resolve relative to `__file__`.

## EN-010 · the harness fixture had NO usable timestamps (2026-09-23)
- FINDING: after the timestamp validation was added, every feed raised
  BAR_MISSING_TIMESTAMP.
- ROOT CAUSE: the harvester writes the key `timestamp`; `parse_bars` looked for
  `ts` then `time`. Every bar therefore resolved to `ts = 0`, which PASSED the
  `ts > anchor` check and sorted to the front — **the temporal filter had never
  actually run on this fixture.** The fixture also genuinely spans ~5 days past
  the anchor, so a correct filter must drop 1,000+ bars.
- FIX: accept `ts | time | timestamp`; build `shared/fixtures/bars_anchored.json`
  (every bar <= the anchor) as the canonical fixture and keep `bars_raw.json` as
  the wide harvest used to PROVE the leak fires.
- VERIFICATION: `test_state_constructor_golden` asserts the wide harvest is
  REFUSED (404 bars past the anchor) and no retained bar has ts == 0.
- LESSON: a silent `or 0` default turned a strict filter into a no-op. The
  fixture was never actually filtered, and every downstream result inherited it.

## EN-011 · the audit gate's first two rounds (2026-09-23)
- ROUND 1: GATE FAIL (1 critical, 35 high). The critical: the zero-coding
  scanner's write-allowlist was keyed on BASENAME, so any file named `report.py`
  anywhere was skipped for ALL capabilities — a spawn primitive hidden in
  `evil/report.py` passed the scan.
- ROUND 2: GATE FAIL (0 critical, 20 high). The remaining highs were NaN
  fail-open in every threshold gate, a missing geometry gate, a tautological
  dual-compute, predicate-independent trust witnesses, unvalidated
  pair/direction/outcome, and several scanner evasions.
- ROUND 3: GATE FAIL (2 critical, 17 high). The criticals: a bare `pickle.load`
  bypass (only `loads` was matched) and a negative-supervision label that was
  never a selectable option.
- THE PATTERN: each round the auditor found the NEXT layer — first the bypass,
  then the fail-open semantics, then the evasion corners. Fixing a class
  (fail-closed validation, path-keyed exemptions) removed many findings at once;
  patching a site moved the finding one line.

## EN-012 · the ECE probe measured itself three times before measuring the model (2026-09-23)
- FINDING: the calibration gate reported FAIL at 0.2139, then 0.1387, then 0.1808
  — three different numbers for the same model, none of them a measurement of
  the model's calibration.
- ROOT CAUSE, in three layers:
  v1  the sample filtered to `answer == "yes"` — a SINGLE-CLASS sample. On such
      a sample every claim is correct ~97% of the time while the model states
      ~0.75, which produces a large ECE **by construction**, however well
      calibrated the model is.
  v2  the "negative" records in the corpus are SYNTHETIC corruptions of a
      doctrine quote (a digit replaced with 0). The model has no basis to detect
      that, so it scored 40/80 = 0.500 — CHANCE. The number measured the
      evaluation set.
  v3  the trading-domain set (the operator's own documented rows) gave 6/6
      CORRECT at 1.000 accuracy with a raw ECE of 0.2579 — the first number that
      is about the model.
- THE ACTUAL FINDING (v3, held out):
  * the corpus KIND task is **OVER**-confident  -> a fitted T = 5.00 (soften)
  * the trading domain is **UNDER**-confident    -> a fitted T = 0.24 (sharpen)
  * applying the corpus T to the trading domain makes ECE **WORSE**
    (0.2579 -> 0.4269)
  * even a T fitted ON the trading rows only reaches 0.1807 — with accuracy at
    1.000, the ECE is dominated by |1 - p| and cannot reach 0.05 without
    stating p ~= 1.0.
- FIX: `decider/calibration.py` (the temperature-scaling layer) plus
  `test_calibration_layer`, which measures the LAYER on held-out data
  (ECE 0.3492 -> 0.1080, a 69% reduction) and passes.
- VERIFICATION: `test_calibration_layer` PASS; `test_decider_calibration_ece`
  remains FAIL and now reports all three numbers plus the transfer finding.
- LESSON: when a metric is computed over a sample, the SAMPLE is part of the
  instrument. A single-class sample, a synthetic-label sample, and a
  domain-mismatched sample each produce a confident number that means nothing.

## EN-013 · the extension's python preamble had no trailing newline (2026-09-23)
- FINDING: every `plutus_*` tool would have failed in the TUI with
  `SyntaxError: invalid syntax` at the first statement of its snippet.
- ROOT CAUSE: the BOOT preamble is a TS template literal appended directly
  before each tool's python snippet. It ended `sys.path.append(str(R))` with no
  newline, so the preamble's last statement was concatenated with the snippet's
  first: `sys.path.append(str(R))import json`.
- FIX: a trailing blank line in the template literal (now documented as
  load-bearing in the extension).
- VERIFICATION: `pi-harness/tests/test_tools_execute.py`, which extracts every
  snippet and runs it verbatim — 5/5 pass.
- LESSON: an embedded-language boundary is a place where two languages' rules
  meet, and neither language checks the seam. The seam needs its own test.

## EN-014 · a model entry missing `input` broke the whole seat (2026-09-23)
- FINDING: sending a prompt gave `Error: Cannot read properties of undefined
  (reading 'includes')`.
- ROOT CAUSE: pi's model resolution calls `.includes` on each model's `input`
  array. My `registerProvider` entries declared only `id`/`name`/`reasoning`.
  Every field — `input`, `cost`, `contextWindow`, `maxTokens` — is required.
- FIX: complete model entries (documented in the extension).
- VERIFICATION: the seat booted with `0.0%/131k` in the status bar.

## EN-015 · the 503 was the MODEL's upstream, not the provider (2026-09-23)
- FINDING: after the provider worked, every send retried 3x and failed with
  `503 {"type":"server_error","message":"Upstream request failed: Endpoint is
  unavailable."}`
- ROOT CAUSE, established by probing each model id against the gateway:
    muse-spark-1.3-contributor  503      deepseek-v4-flash  200
    muse-spark-1.2-contributor  503      glm-5.1            200
    grok-4.6                    503      kimi-k2.6          200
  The muse family and grok-4.6 had a DOWN UPSTREAM; the gateway and the key
  were fine. Registering a 503 model as the seat's default produced the loop.
- ALSO FOUND: the gateway requires an `x-opencode-session` header. Without it:
  `{"type":"error","error":{"type":"MissingSessionID"}}`. Added to the provider.
- FIX: register the three MEASURED-working models; keep muse listed but LABELED
  with its 503 date.
- LESSON: a 503 from a gateway is a claim about a ROUTE. Probe the routes
  individually before touching the key, the base URL, or the client.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._

## EN-016 · G-RRR trusted the caller's RRR instead of the trade's (2026-09-23)
- FINDING (audit round 9): `g_rrr` compared `t.rrr` — a value the CALLER
  supplied — against the floor. A candidate with coherent prices but an inflated
  `rrr` passed.
- WHY IT IS THE MOST DANGEROUS CLASS: the pin's own law is "DECIDER SCORES,
  NEVER EDITS" and the gates are "THE LAW". A gate that reads a model-supplied
  number as fact is the exact bypass the law exists to prevent: the floor was
  being checked against a CLAIM, not against the trade.
- FIX: `recompute_rrr(t)` derives the RRR from entry/sl/tp and the pip
  authority. G-RRR applies the floor to the DERIVED value, and a stated value
  that disagrees with the geometry is its own rejection.
- VERIFICATION: `test_gate_rrr_rejects` now BUILDS candidates by MOVING THE
  STOP rather than by typing an rrr — the geometry is the input and the rrr
  follows. The 5 adversarial RRR shapes pass.
- LESSON: a gate must read only what it can VERIFY. Anything the caller hands
  it is a claim.

## EN-017 · LAW 2 was stated in the header and enforced nowhere (2026-09-23)
- FINDING: `_geometry_ok` validated `zone_width_pips > 0` and `g_sl` validated
  `sl_distance_pips in (0, 55]` — INDEPENDENTLY. A candidate claiming zone=10p
  and sl_distance=50p passed both. LAW 2 (the SL sits at the structural
  invalidation point, so the SL DISTANCE IS THE ZONE WIDTH) had two authorities
  and no check that they agreed.
- THE SAME DEFECT IN THE CIRCUIT: `zone_width` defaulted to `abs(tp-entry)/pip`
  — the TP DISTANCE — so every candidate the circuit built violated LAW 2 by
  the width of its own reward. The default is now the RISK.
- FIX: `g_sl` requires |sl_distance − zone_width| ≤ 5 pips (the operator's own
  documented buffer range).
- LESSON: a law written in a docstring is not a law. If two fields describe one
  quantity, a gate must compare them.

## EN-018 · the session gate ignored the timezone offset (2026-09-23)
- FINDING: `_local_hhmm` took the wall-clock after `T` verbatim and compared it
  to the ET window. `2026-07-06T03:00:00Z` is 23:00 ET — OUTSIDE the window —
  and it PASSED. Every non-ET timestamp was read as if it were already ET.
- FIX: an offset-bearing stamp (Z or ±HH:MM) is CONVERTED to ET. Both the EDT
  and EST offsets are tried, because a bare timestamp carries no date to decide
  DST; the stamp is accepted only if it lands inside a window.
- VERIFICATION: `test_session_london_window` (7 cases + inclusive boundaries +
  the DST offset check) passes.
- LESSON: a wall-clock without its offset is half a value.
