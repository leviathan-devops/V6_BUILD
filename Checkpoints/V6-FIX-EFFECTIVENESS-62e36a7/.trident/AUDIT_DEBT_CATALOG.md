# THE AUDIT DEBT CATALOG — for operator review

The anti-treadmill doctrine's requirement after the bounded waves: **the operator
reviews the remaining findings and accepts/rejects each.** This is that list.

**STATE: the gate is FAIL (0 critical, 11 high).** The criticals are MET (0).
Every high below is a real finding from the round-17 run, with my own assessment
of severity and whether it is worth a fix wave. My judgement is stated so you can
overrule it cheaply.

---

## HIGH — I JUDGE THESE WORTH FIXING (5). Each is unambiguous correctness, and
each is the SAME CLASS as one already fixed, so the fix is a known quantity.

### H1 · `integration/run_ct_suite.py:220` — an EMPTY passToken passes vacuously
`isinstance(_tok, str)` is enforced, but `"" in ctx` is ALWAYS True — so a
fabricated PASS with `"passToken": ""` clears the evidence check.
**WHY IT MATTERS:** this is the CT evidence gate, the thing that proves the
container actually ran the scenario. An empty token defeats it.
**FIX:** require `_tok` to be non-empty. (One line.)
**RISK OF FIXING:** near zero — it can only refuse more.

### H2 · `mpse/predicates.py:60` — fail-closed broken on a NON-MAPPING input
`k not in c` raises `TypeError` when `c` is `None`/int/float, so `trust()` and
every `at_*` predicate RAISE instead of returning the documented
`INCONCLUSIVE`/failed verdict. **The module's own contract is fail-closed.**
**FIX:** an `isinstance(c, dict)` guard at the top of `_missing`. (Two lines.)
**RISK:** near zero.

### H3 · `mpse/predicates.py:276` — `c.get('direction')` sits BEFORE the try guard
Same class as H2, in `geometry_witness`: a direct call with `None`/list/str
raises `AttributeError` instead of the fail-closed `False`.
**FIX:** move the access inside the guarded block. (Two lines.)
**RISK:** near zero.

### H4 · `tui/coding_surface.py:397` — `scan_text` claims the FULL lexicon but omits `WRITE_SUSPECT`
The docstring says "FULL lexicon"; it scans only `EXEC_FORBIDDEN` +
`WRITE_FORBIDDEN`, so the negative control CANNOT see the aliased-write tier that
`scan_tree` reports. A test built on `scan_text` would certify less than it claims.
**FIX:** add the tier + the `confidence` field. (Four lines.)
**RISK:** near zero, but it CHANGES THE NEGATIVE CONTROL'S COVERAGE — worth
re-running `test_zero_coding_surface` after.

### H5 · `determinism/determinism.py:62` — float rounding collapses distinct decisions
`round(o, 10)` maps values differing by <1e-10 to the same canonical form, so real
nondeterminism can digest as a MATCH — a false-negative in a gate whose whole
purpose is detecting divergence.
**FIX:** hash the exact binary value (`struct.pack`) instead of a rounded decimal.
**RISK: MODERATE.** This is the pinned determinism LAW; changing the
representation changes every digest, and `test_determinism_sha_match` asserts
current behaviour. **I would NOT fix this one without your call** — it is a
deliberate design trade, not a defect, and the round-8 contract pinned it.

---

## HIGH — I JUDGE THESE REAL BUT LOWER-URGENCY (4). They are correctness gaps in
paths the circuit does not currently exercise, or they need a design decision.

### H6 · `oms/oms.py:127` — the unknown-pair check stays LAZY
`Fill.__post_init__` validates numerics and direction but not `pair in PIP`, so an
unknown pair constructs and fails later during aggregation — the exact lazy
failure mode round 14 claimed to close. `TradeDecision` has the same gap.
**WHY LOWER:** the circuit supplies pairs from a validated set, so the live path
never hits it. It is a latent trap, not a live bug.

### H7 · `oms/oms.py:196` — `Portfolio.starting_equity` unvalidated
NaN/inf/zero/negative silently poisons `max_drawdown` (NaN makes the `peak > 0`
guard false, so drawdown reads 0.0 — the WORST failure shape: no drawdown
reported on a poisoned book).
**WHY LOWER:** callers pass a literal; no live path supplies NaN.

### H8 · `oms/oms.py:180` — `TradeResult.outcome` never cross-checked
Nothing validates `outcome in ('tp','sl')` nor that `fill.exit` matches
`decision.tp`/`.sl` for that outcome, and `Portfolio.trades` is publicly mutable —
so a label can disagree with the numbers that produced the P&L.
**WHY LOWER:** needs a design decision about whether the outcome is authoritative
or derived.

### H9 · `corpus/build_corpus.py:158` — KIND questions keep a FIXED option order
The answer distribution is skewed to `mechanism` (583 mechanisms vs 38 rulings), so
the correct answer is almost always index 0 — **the constant-index positional
shortcut already fixed for golden/cascade with `_rotate`.**
**WHY IT MATTERS:** this is a TRAINING-SIGNAL defect, not a code defect: a model
can learn the position instead of the rule.
**WHY LOWER:** it needs a corpus-level decision (rotate, or rebalance the classes).

---

## HIGH — I JUDGE THESE THE LOWEST (2). Corpus-refinement items that cost
coverage rather than emitting anything wrong.

### H10 · `corpus/build_corpus.py:388` — substring-replace hits the FIRST occurrence, not the matched one
`r.quote.replace(_tok, ..., 1)` can rewrite `10` inside `100`, corrupting a
different number than the regex matched. **Conservative failure:** the negative
still changes the state, so it is not a MISLABEL — it is a less-precise corruption.
**FIX:** splice at the match span.

### H11 · `corpus/build_corpus.py:326` — the floor negative only handles `a/b/c RRR` rows
`harvest_gap_analysis` also accepts RRR-beside-label rows with no triple; those
SKIP, so they keep yes-only supervision. **Conservative failure:** SKIP is safe
(it never emits a wrong label) — it just leaves that subset uncovered.
**WHY LOWEST:** the SKIP is the correct behaviour; the gap is coverage, not
correctness.

---

## MY RECOMMENDATION
- **FIX NOW if you authorize a wave:** H1, H2, H3, H4 — four tiny, unambiguous,
  near-zero-risk fixes to fail-closed and evidence contracts. They are the same
  class as work already verified, so the regression risk is low.
- **YOUR CALL:** H5 (a pinned design trade), H9 (a corpus design decision).
- **LEAVE AS DOCUMENTED DEBT:** H6, H7, H8, H10, H11 — latent or conservative,
  none reachable on the live path.

**I have NOT run these fixes**, per the stop ruling: rounds 15 and 16 each
introduced a critical while fixing the prior round, so I am not spending another
wave without your go-ahead.
