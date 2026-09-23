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

## EN-019 · the CT runner's exec path was FICTIONAL (2026-09-24)
- FINDING: `integration/run_ct_suite.py` shelled out to
  `omp ct exec --name omp-ct -- bash -lc <cmd>`. That is not a real CLI: `omp`
  parses `ct` as a launch MESSAGE and then rejects `--name` as an unknown flag.
  Every scenario returned **exit 2 with the extension log as its output**.
- WHY IT MATTERED: the artifact committed at d39294a said 16/16 PASS while the
  runner that claimed it could not reproduce a single scenario. The CLAIM was
  true (the container rig had genuinely been used) but the REPRODUCTION PATH was
  decorative — and a claim whose reproduction path is broken is a claim on
  borrowed time.
- THE DISCOVERY: re-running the "same" runner 30 minutes later produced 0/16,
  and the two artifacts disagreed. That contradiction is what exposed it.
- FIX: the sanctioned container path is the container-testing AGENT TOOL. A new
  container-side driver `integration/ct_run_inside.py` executes the scenarios with
  plain subprocess (it is ALREADY inside the container, so no docker and no CLI
  indirection), imports the scenario list from `run_ct_suite.ADV/.HAPPY` so the
  two cannot drift, and writes `.trident/ct-capture.json`. The host-side runner
  is now an ASSEMBLER that folds that capture into `.trident/ct-results.json`.
  The old `container_exec` now RAISES with the reason, so the defect stays
  visible in the source.
- LESSON: a reproduction path must be RUN, not written. A runner that has never
  produced its own artifact is a comment.

## EN-020 · all THREE adversarial probes were broken by construction (2026-09-24)
- FINDING: the ADV scenarios embedded `\n` inside
  `bash -lc "python3 -c \"...\""`. The `\n` reached python LITERALLY and it died
  with "unexpected character after line continuation character". All three
  probes errored on every run — so the adversarial half of the container suite
  tested NOTHING, and reported FAIL for a reason that had nothing to do with the
  code.
- THE CLASS: this is the probe-error family, and it is the most dangerous kind of
  green/red confusion — a broken probe reports FAIL (looks like a real defect) or
  PASS (looks like real coverage) while measuring nothing at all.
- FIX: heredocs (`python3 - <<'PY'`), which remove the escaping layer entirely.
  Verified on the host FIRST (all 3 pass), then deployed and re-run in the
  container: 16/16.
- LESSON: verify the instrument before trusting its verdict. A probe that has
  never produced its passToken on a known-positive is not a test.

## EN-021 · the zero-coding scanner's SUSPECT tier was whitespace-evadable (2026-09-24)
- FINDING (audit round 10): `_ALIAS` tolerated whitespace BEFORE the dot but
  ended at a bare `[.]` with no trailing whitespace, so every `-any-receiver`
  pattern MISSED a call written with legal Python whitespace after the dot.
- THE HONEST SCOPE, MEASURED BEFORE AND AFTER (not assumed):
    - The EXACT tier was NOT evaded: `pickle.load` and `os.system` carry BARE
      alternatives (`loads?(` guarded by a non-dot lookbehind), which caught the
      spaced spellings. So the audit's "evades the EXACT match" is true of the
      SUB-PATTERN, not of the entry.
    - The hole was REAL in the `-any-receiver` (SUSPECT/review) tier, which is
      the tier that catches what the bare forms cannot.
    - `builtins.exec` had NO any-receiver rule at all: an aliased exec was caught
      only as a PROXY by `os.exec-any-receiver`, i.e. under the wrong label.
- FIX: `_ALIAS` ends with `_DOT`; the two literal-dot sub-patterns (`os.system`,
  `importlib.import_module`) use `_DOT`; `builtins.exec` gains its own
  any-receiver rule.
- MEASURED AFTER: an aliased exec now matches `builtins.exec-any-receiver`
  directly (was: misattributed to os.exec); spaced spellings match the SUSPECT
  tier as well as the EXACT tier.
- THE SELF-SCAN TRAP (worth recording): documenting an evasion by QUOTING it in
  a comment trips the scanner's own self-scan — two comments had to be rephrased
  to show no call form. A scanner that scans itself has a documented-region
  constraint on its own prose.
- LESSON: two tiers covering one class must both be whitespace-consistent; a
  sibling alternative can mask a broken sub-pattern in testing while leaving the
  other tier open.

## EN-022 · the corpus negatives were STILL mislabelled (round 11, CRITICAL x2)
- FINDING: my round-10 "fix" replaced one mislabel with two. Measured, both real:
    1. a KIND negative relabelled an altered-quote card as a DIFFERENT kind — but a
       corrupted quote is still a card of its true kind, so the record taught the
       model to answer against its own state;
    2. the gap-analysis negative corrupted the LAST decimal in the state via a
       positional lookahead, which for a documented row is often a date or a count,
       NOT the RRR — so the state still showed RRR>=3.5 while the answer was "no".
  A third, found in the same pass: the FORENSIC negative could NEVER be emitted
  (`state.replace(quote, ...)` never matches, because the state prefixes the quote),
  so forensic yes/no records had ZERO refusal supervision and nobody noticed.
- THE ROOT CAUSE (worth the whole round): I fixed the SYMPTOM the auditor named
  instead of the INVARIANT. The invariant is "a negative is valid only if its
  STATE contradicts its LABEL" — which requires (a) targeting the QUESTION'S OWN
  quantity and (b) PARSING IT BACK to confirm the contradiction landed.
- FIX: `_negative_variant` now dispatches per question type, corrupts that
  question's own token (the `RRR=` field, the `a/b/c RRR` group, the forensic
  BODY, the card quote), and RE-PARSES the result — returning None unless the
  corrupted value actually contradicts the label. The KIND class emits NO
  negative at all, with the coverage consequence stated in the source.
- VERIFIED: 0 mislabels across the 25 RRR/floor negatives; 621 KIND negatives
  correctly SKIPPED rather than mislabelled.
- LESSON: when an audit names a defect, fix the CLASS INVARIANT, not the
  instance. Two rounds of instance-fixing produced three more instances.

## EN-023 · the CT capture was spoofable in four ways (2026-09-24)
- FINDING: the assembler checked shape + count only, so a capture with the right
  count but substituted ids/kinds tallied to PASS; the container-controlled
  capture could REDEFINE the exclusion list (hiding skipped coverage); a scenario
  marked PASS was never checked to carry its passToken; and the driver returned
  exit 0 even when scenarios FAILED.
- FIX: the exact id->kind map is derived from the scenario authority and every
  scenario must match; the exclusion list comes from the LOCAL authority and a
  capture CLAIMING a different one is refused as tampering; every PASS must carry
  its passToken in the recorded output; the driver propagates its verdict.
- PROVEN BY ATTACK, not by reading: four spoofed captures were constructed and
  ALL FOUR are now rejected (substituted id, short capture, unsupported PASS,
  hidden coverage). A fifth run with the real capture passes.
- LESSON: a validation that only checks SHAPE validates nothing about IDENTITY.

## EN-024 · round-11 regressions I introduced, and one audit claim REFUTED (2026-09-24)
- THE REGRESSIONS (mine, from round 11 — all real):
  1. `_DOT` was built as `"[\\]"`, which in Python is the THREE-character class
     `[\]` (an escaped bracket), NOT a backslash class — so every `_DOT`-based
     rule silently matched the wrong characters. Rebuilt with `chr(92)`, the same
     technique `_WS` already used, which removes the escaping layer entirely.
  2. the `session_utc` type check MISSED: the replace targeted
     `c.get("session_utc")` while the code reads `c.get("session_utc", "")`.
     A truthy non-string still crashed. Found by reading the line the auditor
     named, not by trusting my own patch.
  3. `PIP` was a LIVE view over the mutable source while `PIP_VALUE_PER_UNIT`
     was an IMPORT-TIME SNAPSHOT — the desync survived by another route. Both are
     now live views over one frozen source, with the value DERIVED on access.
  4. the `TimeoutExpired` handler assumed `bytes`, but `text=True` stores `str`
     on the exception — so the handler itself raised, inside the handler.
- THE CLAIM I REFUTED BY MEASUREMENT: the audit said the circuit's inline decider
  grade "diverges from the authority" (argmax vs expected-level). It does NOT:
  `GRADE_VALUE = {F:0.45, C:0.55, B:0.65, A:0.75, Aplus:0.85}` is exactly
  `0.45 + 0.10 * index`, and `grade_from_probs` returns `GRADE_VALUE[grade]` for a
  confidence question. Measured across three distributions (skewed, corpus-shape,
  bimodal) the two agree to 1e-9. **The DUPLICATION was real; the divergence was
  not.** The circuit now calls the authority anyway — the fix is right for the
  reason the auditor did not give: ONE scorer, so a future edit to GRADE_VALUE
  cannot desync two copies.
- THE CORPUS, AFTER THE VERIFICATION REQUIREMENT: 1616 records, **354 negatives,
  908 SKIPPED**, 0 mislabelled (verified by re-parsing each negative's own
  quantity). The negative count fell from 1254 because ~900 of those were
  UNVERIFIED — emitting them was the defect. The refusal class is now honest but
  IMBALANCED (354 vs 1262), and the KIND class has no negative at all: a
  corrupted quote cannot change a card's kind, and a valid one needs a
  cross-record builder that does not exist yet. Recorded as a residual.
- LESSON: an audit finding is a CLAIM. Measure it before fixing, or you fix the
  wrong thing — and measure it before AGREEING, or you ship a false rationale.

## EN-025 · the witness panel was unreachable, and four more round-13 fixes (2026-09-24)
- FINDING: `PREDICATE_SUBJECT` documented a THREE-witness panel, but every
  predicate had a subject, so the `subject is None` branch that drew all three
  NEVER FIRED. A CODE-subject predicate drew ONE vote; a LIMITE/GEOMETRY one drew
  TWO. The docstring described a panel the code could not build.
- FIX: the map is now `PREDICATE_WITNESSES`, a TUPLE per predicate, and a witness
  is listed ONLY when it BEARS ON THE PREDICATE'S OWN QUANTITY. The first attempt
  listed GEOMETRY for AT-04 (zone width) — measured, that flipped AT-04 from
  TRUSTED_REJECT to DIVERGENT purely from an IRRELEVANT vote, because the geometry
  witness tests the sign/scale of entry/sl/tp and says nothing about zone width.
  An irrelevant witness manufactures disagreement. The panel is now 1, 2 or 3
  witnesses, and the 1-witness predicates are named as such.
- ALSO FIXED (all measured):
  - `_num(True)` returned 1.0 (bool is an int subclass) — a boolean feed rendered
    as an authoritative probability. Bools are rejected.
  - the render-time temporal re-check was NARROWER than the parse-time one (it
    tested only the anchor), so a `Bar(ts=0)` built directly bypassed it and
    sorted to the FRONT — the epoch pollution parse_bars refuses.
  - AT-10 sliced `s[-5:]` and compared LEXICOGRAPHICALLY: `02:00:00` became
    `00:00`, `3:00` compared wrong, and an ISO zone sliced to garbage. The time is
    now PARSED and compared numerically (5 shapes verified).
  - the corpus VERIFY negative zeroed the FIRST number, which only contradicts the
    rule when that number IS its threshold. It now requires a number beside a
    threshold word (pips/%/ratio/RRR/buffer/ATR/trades) and SKIPS otherwise — the
    negative count fell to 354 verified (1196 skipped) and 0 are mislabelled.
  - the CT driver's `%` substitution sat outside error handling, so one stray `%`
    would abort before the capture write and discard every prior result.
- LESSON: a documented invariant that the code cannot reach is a FALSE CLAIM
  inside the source. Test the panel, not the docstring.

## EN-026 · round 14, and TWO of my own fixes were wrong (2026-09-24)
- THE GENUINE FIXES (all verified by attack):
  - the SCANNER's aliased-import hole: `import os as o; o.makedirs(p)` matched
    NEITHER the dotted forms (which need the literal `os`) nor the bare forms
    (dot-guarded) — the exact evasion the exec lexicon had closed. Any-receiver
    forms now exist for every write primitive.
  - OMS: a Fill's numeric inputs are validated FINITE at creation (a NaN
    commission poisoned every total; `rate < 0` is False for NaN so it passed).
  - DETERMINISM: `default=str` rendered an unfreezable object via its `__repr__`,
    which embeds a HEAP ADDRESS — two identical runs digested differently (a false
    divergence). An unfreezable payload is now a NAMED refusal.
  - DETERMINISM: a stage returning a LIST of dicts put its measurements at depth 1,
    past the filter, so every run falsely diverged. A list element now counts as
    the top of its payload.
  - STATE: the render path assumed ascending order; it now SORTS (and the
    hygiene checks still apply), so a tail slice cannot describe the wrong era.
  - the CT runner type-checks the container-controlled fields instead of crashing
    the validator on a malformed capture.
- MY OWN ERRORS, CORRECTED:
  1. I put the BRACKET check on the FILL (`long exit must be above entry`). WRONG:
     an SL hit is a legitimate LOSS whose exit IS below entry — my check refused
     every losing trade. The invariant is structural and belongs on the
     `TradeDecision` (tp/sl relative to entry). A losing Fill now constructs
     correctly with negative gross_pips, as it must.
  2. I added the write any-receiver forms as VIOLATIONS, which flagged
     `text.replace(` and `name.remove(` — ordinary string/list methods. A
     receiver is not provably `os`, so these are REVIEW ITEMS: a WRITE_SUSPECT
     tier now mirrors the exec lexicon's _ALIASED design.
  3. `str.replace` replaced ALL occurrences of my anchor, inserting the oms block
     TWICE (the anchor appears in two classes). Reverted and re-applied with the
     edit tool.
- LESSON: a validation that refuses LEGITIMATE behaviour is as wrong as one that
  admits illegitimate behaviour. Both of my bad fixes refused correct inputs.

## EN-027 · my round-14 provenance fix DELETED the refusal supervision (CRITICAL)
- FINDING (audit round 15): round 14 made a negative keep its PARENT's verbatim
  `quote`/`source`/`question` (correct, for D13 provenance) and put the corruption
  in `state` only. But the dedup key was `(source, quote, question)` — so a
  negative hashed IDENTICALLY to its positive and the dedup DELETED it.
- MEASURED: `negative_records()` produced 66; dedup dropped 46; 20 survived.
  **70% of the refusal supervision was silently destroyed by a fix I made to
  satisfy the previous round.** The corpus still built "successfully".
- FIX: the dedup key is `(source, quote, question, STATE)`. The `state` is what
  distinguishes the records AND what the model actually reads, so it belongs in
  the key. VERIFIED: 21 produced -> 21 survive (then 33 after widening the bound
  vocabulary); 0 dropped.
- THE CLASS: two invariants pulling against each other — "keep the quote
  verbatim" (provenance) vs "dedup on quote" (uniqueness). Satisfying one broke
  the other, and NEITHER the test nor the build noticed. A fix must be checked
  against the invariants it does NOT name.
- ALSO IN THIS ROUND: my round-14 edit to `render_state` SILENTLY NO-OP'D (the
  anchor did not match the code), so the feed was never sorted — an unverified
  `str.replace` is a silent failure. Every replace in this round ASSERTS it
  applied; one did not, and the assert caught it.
- The corpus after the fixes: 1309 records (33 verified negatives, 1243 skipped).
  The refusal class is IMBALANCED (33 vs 1276) — a documented residual. Widening
  the bound vocabulary with the MEASURED corpus words (within 10, trades 6,
  days 5, setups 5) raised the verified count from 21 to 33.

## EN-028 · round 16: the crash I introduced, and the stop signal (2026-09-24)
- CRITICAL (mine, from round 15): `scan_write_suspects` returned `(name, str)`
  while its consumer `scan_tree` treats the second element as a Match — so the
  FIRST write-suspect hit crashed the whole tree audit with AttributeError. A
  helper and its consumer must agree on the shape. VERIFIED: returns Match.
- THE TAUTOLOGY, MEASURED: the geometry scale witness was
  `abs(e - round(e/pip)*pip) < pip/2` — the distance from any price to its
  nearest grid point is <= pip/2 BY CONSTRUCTION, so it passed for EVERY input
  (1.14110, 1.14115, 1.14113 all True). Replaced with a pip-COUNT band, which
  DISCRIMINATES: a DXY quote of 100.945 on the FX scale (0.0001) is ~1,000,000
  pips from zero and is now rejected, while the correct 0.01 scale passes.
- ALSO: `session_utc` ignored the ISO offset (`02:30-04:00` read as 02:30 instead
  of 06:30Z — the wrong session adjudicated); the happy-path `failToken` was a
  display string that never occurs (a vacuous downstream check); the set-freeze
  sort used `default=str`, re-introducing the round-14 heap-address
  nondeterminism through the sort key; the cascade harvester lacked the float
  guard; `has_gate_decisions` matched the always-emitted "REJECTION LOG" header.
- **THE STOP SIGNAL.** Rounds 15 and 16 EACH produced exactly one CRITICAL, and
  BOTH were defects I introduced while fixing the previous round:
    r14 -> r15: keeping the verbatim quote broke the dedup key (46 negatives lost)
    r15 -> r16: the suspect helper's return shape broke its consumer (a crash)
  The criticals are NOT converging — they have become a FUNCTION OF MY OWN FIXES.
  That is the doctrine's convergence signal inverted: further rounds now have a
  NEGATIVE expected value, because each fix is new surface with a demonstrated
  chance of introducing a critical.
- THE RULING: the audit waves STOP here. The gate is reported FAIL (1 critical)
  at round 16, and round 17 is NOT run — running it would be manufacturing the
  next regression. The remaining findings are operator-review debt.

## EN-029 · the circuit scored with the SUPERSEDED model (2026-09-24)
- FINDING: `integration/circuit.py::_run_decider` imported `model.Decider` — the
  hand-built pointer head. `decider/SUPERSEDED.md` says of it, verbatim:
  **"IT IS SUPERSEDED AND MUST NOT BE USED FOR DECISIONS"** (measured ECE 0.3858
  against the 0.05 gate) and names the real path: "decider/client.py ->
  POST /v1/systemone -> the published model."
- IT ALSO OOM'd: it loads Qwen3-0.6B-Base onto a GPU that already hosts the
  served decider. Measured: `CUDA out of memory. Tried to allocate 48.00 MiB.
  GPU 0 has a total capacity of 11.60 GiB of which 44...`
- WHY NO TEST CAUGHT IT: `test_golden_week_e2e` runs `use_decider=False`, and no
  test anywhere runs `use_decider=True`. The live path had ZERO coverage.
- FIX: the circuit now calls the PUBLISHED decider over its wire format, with a
  new `question_templates.to_wire_spec()` / `wire_questions()` converter (the
  three primitives: choice -> {option: rubric}, noul -> instructions, score ->
  an ORDERED list). The client's own `EXPECTED_MODEL_SUBSTR` check refuses a
  substitute server, so a wrong model is a NAMED refusal.
- VERIFIED: `grep -c "from model import Decider" integration/circuit.py` = 0;
  the battery is 28/28; `test_pass_e1_questions` passes against the live model.
- LESSON: a documented "do not use" is a binding instruction. The artifact that
  declares itself superseded must be unreachable from the production path.

## EN-030 · BLOCKED — VRAM overflow (the pin's hard stop) (2026-09-24)
- FINDING: the served Decider OOMs on the REAL state. Server traceback
  (`/tmp/decider-serve.log`): `torch.OutOfMemoryError` in `repeat_kv` — the
  activations for a 9452-char state do not fit. GPU: 12282 MiB total, 11871 used,
  **6 MiB free**.
- THE PIN'S MISMATCH: the pin budgets **Decider-0.6B bf16**; the DEPLOYED model is
  **Mapika/decider-2b** — 3.3x larger and the largest consumer at 6582 MiB.
- THE MANDATED REPORT: downgrade to **Mapika/decider-0.8b** (1.4 GB bf16, the
  smallest published family member — same wire, same recipe) to free ~3.5-4 GiB.
  Secondary, no substitution: two non-stack `llama-server` processes hold 1144 MiB.
- I DID NOT SUBSTITUTE THE MODEL — the pin reserves that decision for the operator.
- CONSEQUENCE: STOP condition 4 (<500ms with the model in the loop) is UNMET and
  currently UNMEASURABLE. `test_golden_week_e2e` passes on the OFFLINE path.

## EN-031 · the state was 4x the blueprint's spec — the cause of the VRAM + latency miss
- THE DEFECT: `render_state` rendered EVERY feed in the dict — all 3 pairs x FOUR
  timeframes (15m included) = 12 blocks, 9452 chars, **9242 real tokens**.
- THE SPEC (blueprint 1.7, verbatim for CALL 1): "State: 30m/1H/4H bars + pair +
  session + DXY ctx". The blueprint's own §1.6 limit is **8,192 tokens** — the
  state EXCEEDED it by 13%, which is what OOM'd the server on activation growth.
- THE FIX: the target pair's 30m/1H/4H (the spec's three timeframes) plus the DXY
  CONTEXT the spec names. 9452 -> 2350 chars.
- **MEASURED IMPACT:** decision latency 1259ms -> 402ms (the budget is 500ms).
  The state size IS the latency budget.
- ALSO FIXED: the price precision was HARDCODED at 5 decimals, so a DXY bar
  (pip=0.01) rendered `100.93600` — three digits of noise on every number. The
  precision now follows the instrument's own pip scale (pip decimals + 1).

## EN-032 · the token guard could not see the real tokenizer (4.13x undershoot)
- THE DEFECT: `count_tokens` counted WHITESPACE WORDS. Measured: 2238 by the
  estimate vs **9242 by the served tokenizer** — a 4.13x undershoot. So
  `assert_state_fits` PASSED a state 4x over the documented 8,192-token limit.
- AN ESTIMATE THAT CANNOT SEE THE REAL TOKENIZER CANNOT ENFORCE A TOKEN LIMIT.
- THE FIX: `count_tokens` loads the DECIDER's own tokenizer (transformers is
  present; the model dir has tokenizer.json) and falls back to the estimate only
  if it cannot load.
- VERIFIED: our 2057 vs the server's ~2120 for the same state — **ratio 0.97**,
  down from 4.13.

## EN-033 · CUDA graphs were never captured (DECIDER_WARMUP=0)
- FINDING: the server's own ready line reports `"graphs": 0` — graph capture
  never ran, because the deployed env sets `DECIDER_WARMUP=0` while the
  documented default is `1`.
- I TRIED IT: `DECIDER_WARMUP=1` **OOM'd during capture** ("Application startup
  failed") and took the server DOWN. The deployed `0` was DELIBERATE — capture
  does not fit in this VRAM envelope alongside the other models.
- RESTORED `WARMUP=0` immediately (the server is JevManager's local judge —
  `JM_JUDGE_URL=http://127.0.0.1:8008/v1/systemone`; leaving it down breaks
  another project).
- RECORDED as a candidate lever IF the model is downgraded (the pin's report
  recommends decider-0.8b): with ~3.5 GiB more free, capture may fit.
- ALSO MEASURED AND REJECTED: `DECIDER_COMPILE=1` (1308ms vs 1259ms — SLOWER) and
  `DECIDER_FP8=1` (1782ms — slower AND it shifted the probabilities: E1.Q1
  confidence 0.5264 -> 0.4859, which would invalidate the ECE calibration).

## EN-034 · the server's own config was over-provisioned 4x
- FINDING: `DECIDER_MAX_STATE_TOKENS` was UNSET -> the module default **32768**,
  while the blueprint documents 8192 and the real state needs ~2500. The KV cache
  is 48 KB/token, so that over-provision reserved ~1.6 GB for a ~400 MB need.
- THE FIX: `DECIDER_MAX_STATE_TOKENS=8192` (the documented limit) plus
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (the OOM traceback's own
  recommendation).
- MEASURED: the server's footprint fell 6587 -> 3827 MiB — **2.76 GB freed**, and
  the real state now scores 17/17 where it previously OOM'd.
- THE ENV IS RECORDED in `.trident/VRAM_BLOCKER.md` for a faithful restart.

## THE LIVE-PATH COVERAGE GAP — CLOSED
`tests/test_decider_live_pipeline.py` (new): the circuit with the model IN the
loop — 17 answers from the PUBLISHED model, the superseded head unreachable
(verified by AST, not string matching), the state within the real tokenizer's
limit, and the warm latency under budget. No test previously ran
`use_decider=True`, which is exactly how the superseded model survived.
