# PLUTUS V6 — TESTING LOG

## THE SUITE (13 scenarios, adversarial first, happy path last)
Artifact: `.trident/container-test-results.json` (sha256 71016e6a2813bebd…)
Overall verdict: **PASS** — 13/13 (5 adversarial + 8 happy path)

| id | kind | scenario | passToken | verdict |
|---|---|---|---|---|
| ADV-1 | adversarial | empty bars | `NO_BARS` | PASS |
| ADV-2 | adversarial | bar past the anchor | `FUTURE_BAR_LEAK` | PASS |
| ADV-3 | adversarial | RRR below 2.5 | `G-RRR_REJECT` | PASS |
| ADV-4 | adversarial | session outside London | `G-SESSION_REJECT` | PASS |
| ADV-5 | adversarial | wrong Limite output | `LIMITE_CODE_DIVERGENCE` | PASS |
| HAPPY-1 | happy_path | golden week e2e | `test_golden_week_e2e` | PASS |
| HAPPY-2 | happy_path | Limite live temp=0 | `test_limite_serves_temp0` | PASS |
| HAPPY-3 | happy_path | Decider 17/17 non-uniform | `test_pass_e1_questions` | PASS |
| HAPPY-4 | happy_path | commission 0.1% profitable | `test_commission_0_1pct` | PASS |
| HAPPY-5 | happy_path | determinism SHA-identical | `test_determinism_sha_match` | PASS |
| HAPPY-6 | happy_path | TUI renders probabilities | `test_tui_renders_probabilities` | PASS |
| HAPPY-7 | happy_path | zero coding surface | `test_zero_coding_surface` | PASS |
| HAPPY-8 | happy_path | corpus 1267 records | `test_corpus_record_count` | PASS |

## THE PER-WORKER TESTS (23 files across 7 worktrees)
| worker | test | what it proves | verdict |
|---|---|---|---|
| WA | test_decider_load | the published Decider answers on cuda; OBCV reasoning correct (45/35=1.29<1.5 → fail) | PASS |
| WA | test_pass_e1_questions | 17/17 LIVE non-uniform distributions; expected_level 3.73 | PASS |
| WA | test_state_constructor_golden | 12 feeds parsed, state 836/8192 tokens, FUTURE_BAR_LEAK + NO_BARS fire | PASS |
| WA | test_session_london_window | inclusive boundaries; ET offset −4 Jul / −5 Jan | PASS |
| WB | test_limite_serves_temp0 | live `17+25=42`, byte-identical twice | PASS |
| WB | test_math_queries_shape | L1-L6 shadows: 10.0 / 13.0 / 1.5405 / 1.14074 / 8.5 / 28.5 | PASS |
| WB | test_dual_compute_catches_divergence | wrong answer caught; strict path raises | PASS |
| WB | test_gate_rrr_rejects | 5 adversarial RRR shapes; all 8 gate tokens emitted | PASS |
| WB | test_rrr_golden_reproduction | 6/6 canon DXY RRRs ±0.02 (max delta 0.0043) | PASS |
| WB | test_mpse_predicate_at03 | SIDE_INVERSION caught both directions; AT-09 catches a stated/derived mismatch | PASS |
| WB | test_trust_engine_verdicts | 3-way witness adjudication: TRUSTED / DIVERGENT | PASS |
| WC | test_oms_execute_order | long@TP +28.5p, long@SL −18.5p, DXY 17.0p, blueprint's 28.5→8.5 reproduced | PASS |
| WC | test_commission_0_1pct | 0%/+184.5p, 0.1%/+183.3p, 0.2%/+182.1p | PASS |
| WC | test_report_golden_check | 8 contiguous sections, bars, gate tokens, deterministic | PASS |
| WD | test_tui_renders_probabilities | 13 option rows with bars, ≤76 cols | PASS |
| WD | test_zero_coding_surface | 0 violations / 8 roots; negative control fires | PASS |
| WD | test_rejection_log_tokens | all 8 rejection tokens in one adversarial candidate | PASS |
| WD | test_not_headless | framed, multi-line, visual; not a JSON blob | PASS |
| WE | test_corpus_record_count | 1,267 records, zero provenance violations | PASS |
| WF | test_determinism_sha_match | 2 runs identical; volatile fields excluded; divergence names the stage | PASS |
| WF | test_memory_persistence | survives restart; append-only; one-writer-per-bank enforced | PASS |
| WF | test_no_sampling_path | 0 unseeded sampling primitives; seeded init allowed | PASS |
| WG | test_golden_week_e2e | 6/6 Tier-A accepted, 15/15 FX ≤3p, latency, determinism | PASS |
| WG | test_decision_latency | mean 0.058ms, p95 0.066ms, worst 0.099ms | PASS |
| WG | test_forensic_trade_classification | 7 laws extracted; 6/6 Tier-A classified | PASS |
| WG | test_decider_calibration_ece | **FAIL** — ECE 0.2139 measured (gate < 0.05) | FAIL |

## HONEST TESTING GAPS
1. `test_decider_calibration_ece` **FAILS**. The published Decider is accurate
   (58/60) but under-confident (mean 0.753). The instrument controls pass; the
   gate does not. This is reported as a FAIL, not reframed.
2. `test_walkforward_unseen_week` and `test_finetuned_golden_precision` were
   **not written** — the walk-forward needs a second harvested week and the
   fine-tune was not performed. Both are open, not passed.
3. No container isolation: the suite ran on the host with the live models.
4. The 15/15 FX claim is an entry-level identity check, not an independent
   precision measurement (see BUILD_REPORT honest gap 4).

## THE AUDIT GATE (qwen-code-audit) — three rounds, each a real FAIL
| round | critical | high | the headline finding |
|---|---|---|---|
| 1 | 1 | 35 | the zero-coding allowlist was keyed on BASENAME → a spawn primitive in `evil/report.py` passed |
| 2 | 0 | 20 | NaN fail-open in every threshold gate; no gate read direction/entry/sl/tp; the dual-compute was tautological |
| 3 | 2 | 17 | a bare `pickle.load` bypass; a negative label that was never a selectable option |

Every round was remediated and the suite re-run. The final state of the gate is
recorded in EVIDENCE_STATE (an audit verdict is a CLAIM about a specific tree,
so it is always stated with the tree's SHA).

## THE FINAL TEST TALLY (integrated tree)
26 of 28 tests PASS. The two that do not:
1. `test_decider_calibration_ece` — **FAIL**, and it must: ECE 0.2139 measured
   against a 0.05 gate. The published Decider is accurate (0.967) but
   under-confident (mean stated 0.753).
2. `test_limite_dual_live` — **FAIL**, and it must: Limite-1B returned `None` or
   wrong values for 5 of the 6 Tier-A RRRs (one returned 2.0 against a shadow of
   3.5833). Limite is NOT a reliable arithmetic engine at this prompt design.

Both are reported as measured. Neither was reframed, substituted, or deleted.

## THE CONTAINER SUITE (13 scenarios)
13/13 PASS — 5 adversarial first, 8 happy path last. Artifact at
`.trident/container-test-results.json`.

## THE RUNTIME SEAT — proven live (2026-09-23)
The pin's RUNTIME SEAT requirement is met and was observed:

| # | the claim | the evidence |
|---|---|---|
| 1 | the pi TUI boots | status bar: `kimi-k2.6 • medium`, `3.7%/131k` |
| 2 | the extension loads | pane banner: `Plutus V6 circuit loaded — trading tools only, no coding surface` |
| 3 | 7 tools register, no others | `prove_zero_coding` PASS — every name is `plutus_*` |
| 4 | the tools EXECUTE | `test_tools_execute` PASS — 5/5 payloads run verbatim |
| 5 | the agent DRIVES them | the operator's prompt produced `plutus_probe` then `plutus_run_golden`; the pane streamed the RRR table |
| 6 | zero coding surface | `--no-builtin-tools` removes read/bash/powershell/edit/write/grep/find/ls |
| 7 | NOT headless | the TUI pane is the output; no `--print`, no `--mode json` |

The agent's own words in the pane:
  "All 5 adversarial probes returned their named refusal tokens."
  "Golden week: 6/6 accepted, all canon RRRs reproduced within tolerance
   (all_rrr_within_tol: true)."

## THE W7 FINE-TUNE — a MEASURED hard blocker, not a deferral
`decider/train.py` trains with `AdamW(model.parameters())` — FULL-parameter,
no freezing, no LoRA path in the code. The VRAM arithmetic:

    2B params  bf16 weights        4.0 GB
               fp32 master         8.0 GB
               AdamW m + v (fp32) 16.0 GB
               --------------------------
               TOTAL              28.0 GB      the card has 12.0 GB

A LoRA r=16 would need ~0.14 GB and would fit, but the training code has no
LoRA support to enable. The corpus (2,509 records with D13 provenance) is
built and ready; the adapter cannot be trained on this hardware with this
trainer. Reported as BLOCKED with the arithmetic, not as skipped.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

## THE AUDIT GATE — FIVE ROUNDS, AND THE TREADMILL IS REAL
| round | tree | crit | high | the headline finding |
|---|---|---|---|---|
| 1 | 49c68b2 | 1 | 35 | the zero-coding allowlist was BASENAME-keyed |
| 2 | 0b447e4 | 0 | 20 | NaN fail-open in EVERY threshold gate |
| 3 | 135bf6e | 2 | 17 | a bare `pickle.load` bypass; an out-of-vocabulary negative label |
| 4 | bf04465 | 0 | 21 | the `ANSWER:` regex truncated scientific notation; the OMS assumed a WIN |
| 5 | (post-4) | 0 | 28 | my own round-4 fixes' edge cases (`|=` bypassed the frozen dict; `_freeze` did not recurse tuples) |

**THE HONEST FINDING ABOUT THE GATE ITSELF.** Across five rounds the critical
count went 1 → 0 → 2 → 0 → 0 and the HIGH count went 35 → 20 → 17 → 21 → 28.
The class of finding did not shrink; it MOVED. Round 4's fixes produced round
5's findings (the immutable dict's `|=` slot, the freeze function's tuple
blindness). This is the shape of an adversarial reviewer against a codebase with
a large defensive surface: each fix adds surface, and the surface is what gets
audited.

That is a REAL property of the method, not an excuse. It means:
  - the gate is a genuine defect-finder (it found the ANSWER truncation, the
    assumed WIN, the render-time anchor gap — all real);
  - "GATE: PASS" is not reachable by iterating, because iteration is what
    creates the next finding;
  - the honest position is to report the gate's verdict WITH the round count and
    the tree SHA, and to say plainly that a PASS has not been achieved.

WHAT WAS ACTUALLY FIXED ACROSS THE FIVE ROUNDS (real defects, all re-verified):
  the ANSWER truncation (a 10000x arithmetic error on scientific notation)
  the OMS defaulting to a WIN for an unlabelled trade
  NaN passing every threshold gate
  the session gate reading the UTC offset as the local time
  the circuit hardcoding one pip scale for every pair (a 100x DXY error)
  render_state never enforcing the temporal anchor
  the zero-coding scanner's basename bypass
  the memory digest omitting source and never being verified on read
  the circuit importing stale pre-merge modules through hardcoded paths

## THE WALK-FORWARD — STOP condition 3, MET (2026-09-23)
`test_walkforward_unseen_week` — the circuit on a week it has never been
pointed at (2026-06-22, two weeks BEFORE the golden week):

| what | measured |
|---|---|
| the temporal law at a NEW anchor | 6,160 bars dropped past it |
| feeds built | 10 |
| candidates from the unseen week's structure | 6 |
| accepted by all 9 gates | 6/6 |
| outcomes COMPUTED from the forward bars | tp=3, sl=3 (a 50% win rate) |
| net @ 0% commission | +184.3 pips |
| net @ 0.1% commission | **+103.9 pips — PROFITABLE** |
| net @ 0.2% commission | +23.5 pips |
| latency | mean 0.897 ms |
| determinism on the unseen week | SHA-identical |

THE OUTCOME IS NOT ASSUMED: for each accepted trade the test walks the 15m bars
forward from the entry and records which level price reaches FIRST. That is the
ground truth the accept/reject is measured against, and it is the difference
between this and the golden-week test (where the outcome is the canon record).

WHAT IS NOT CLAIMED: the candidate levels come from a simple structural rule
(swing extremes), not the full E1/E2 zone pipeline. This measures the GATES +
OMS on unseen data, which is what the STOP condition asks. It does not claim the
zone pipeline reproduces an undocumented week.

## THE 38 FORENSIC TRADES — STOP condition 2 (2026-09-23)
`test_forensic_38_classification` PASS.

THE SOURCE IS TEXT, NOT JUST IMAGES. The forensic doc's sibling artifacts in
`ARCHIVE/agent/Visual_Evals/v4.5.1/` carry the per-trade data:
  SL_vs_ENTRY_ANALYSIS.md   30 rows: pair, direction, day, SL pips, MAE pips,
                            util = MAE/SL, and the source's own verdict
  OUTCOME_AUDIT.md          36 setups: 30W/6L, per-pair win rate and total R

THE 7 LAWS, APPLIED AS PREDICATES:
| law | tested | obeyed | violated | note |
|---|---|---|---|---|
| LAW 1 entry at a zone edge | 0 | — | — | NOT CLASSIFIABLE: no entry price in the row data |
| LAW 2 SL at the invalidation point | 30 | **30** | 0 | SL distances VARY (mean 17.7p, sd 7.3p) — structural, not a fixed buffer |
| LAW 3 SL buffer 2-5 pips | 0 | — | — | NOT CLASSIFIABLE: no buffer column |
| LAW 4 TP at an opposing zone | 0 | — | — | NOT CLASSIFIABLE: no TP column |
| LAW 5 the LSZ is a shield | 0 | — | — | NOT CLASSIFIABLE: no shield column |
| LAW 6 RRR is a consequence | 30 | 5 | **25** | util < 0.40 — and the count reproduces the source's own verdict EXACTLY |
| LAW 7 ladder entries, one zone | 30 | **30** | 0 | the ladders share pair+day |

THE VALIDATION THAT MATTERS: LAW 6's predicate counted 25 violations, and the
source document's own tally is `SL TOO WIDE=25`. The classifier is measuring the
right thing, independently of the source's prose.

A DEFECT I CAUGHT IN MY OWN CLASSIFIER: the first LAW 2 predicate called a
SHARED SL distance a "fixed buffer" violation — which directly CONTRADICTS LAW 7
(ladder entries on one zone legitimately share an SL). The two predicates
disagreed on the same rows. The sound signal is the SPREAD, not the sharing: a
fixed buffer is constant, a structural SL varies. Corrected, LAW 2 is OBEYED 30/30.

HONEST SCOPE: 4 of the 7 laws have no column in the row data and are reported
NOT CLASSIFIABLE, never as passes. The 38 IMAGES exist (3.0MB, v4.5.1) and a VLM
pass would be needed to classify LAWS 1/3/4/5 from pixels.

## THE AUDIT GATE — SEVEN ROUNDS (the full record)
| round | tree | crit | high | the headline finding |
|---|---|---|---|---|
| 1 | 49c68b2 | 1 | 35 | the zero-coding allowlist was BASENAME-keyed |
| 2 | 0b447e4 | 0 | 20 | NaN fail-open in EVERY threshold gate |
| 3 | 135bf6e | 2 | 17 | bare `pickle.load`; an out-of-vocabulary negative label |
| 4 | bf04465 | 0 | 21 | the `ANSWER:` regex truncated scientific notation; the OMS assumed a WIN |
| 5 | (post-4) | 0 | 28 | round-4's own fixes' edge cases (`|=` bypassed the frozen dict) |
| 6 | 75fe448 | 2 | 25 | `_finite` coerced numeric STRINGS; the ATR read the OLDEST bars |
| 7 | (post-6) | 2 | 25 | **`_guard` was DEAD CODE** (`Verdict.__bool__` swallowed it); aliased-module evasion |

THE TWO ROUND-7 CRITICALS ARE THE MOST INSTRUCTIVE:
1. **`_guard` never fired.** It returned `Verdict(passed=False)` to signal "the
   candidate is missing a field", and `Verdict.__bool__` returns `passed` — so
   the caller's `if g: return g` was FALSY and the guard was unreachable. A
   helper whose SIGNAL is the same object it uses for its own truthiness is a
   trap; the fix returns a tuple.
2. **`import os as o; o.system(...)` evaded the scanner.** The dotted branch
   needs the literal module name; the bare branch is dot-guarded. Two branches,
   and the alias fell between them. The first fix over-corrected (a bare
   `.loads(` is an ordinary method) and the second under-corrected (a leading
   dot was required, so nothing matched). The third attempt — an alias-shaped
   receiver plus a safe-receiver exclusion — catches 4/4 evasions with 0 false
   positives, verified both directions.

THE TREADMILL, RESTATED WITH THE NUMBERS: the HIGH count across seven rounds is
35 → 20 → 17 → 21 → 28 → 25 → 25. It has NOT trended to zero and is not going
to. The criticals are now zero in most rounds because the critical CLASS
(an unreachable guard, a two-branch gap) was closed by fixing the ARCHITECTURE —
but each fix adds surface, and the surface is what gets audited. A "GATE: PASS"
is not reachable by iterating; the honest report is the verdict WITH the round
count and the SHA.

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._


## THE AUDIT GATE — ROUND 9, AND WHAT IT FOUND
The gate has now run NINE rounds. Round 9 produced **0 critical, 21 high** — and
three of those highs were REAL GATE BYPASSES, the class that matters most:

1. **G-RRR trusted the caller's RRR.** The floor was compared against a value the
   caller supplied, not against the trade's geometry. A gate reading a
   model-supplied number as fact is precisely the bypass the pin's
   "DECIDER SCORES, NEVER EDITS" law exists to prevent.
2. **LAW 2 was unenforced.** zone_width and sl_distance were validated
   independently; a candidate claiming zone=10p / sl=50p passed both.
3. **The session gate ignored the offset.** `...T03:00:00Z` is 23:00 ET and it
   PASSED the London window.

All three are now fixed with regression pins. This is the strongest argument for
the treadmill: the audit's HIGH count stopped trending down because it moved from
surface defects (a missing guard) to SEMANTIC ones (a gate that reads the wrong
subject). That class is worth every round.


## THE CONTAINER SUITE, NOW GENUINELY REPRODUCIBLE (round 10)
The container claim was 16/16 — and it was TRUE, but for the wrong reason: the
host-side runner that asserted it shelled out to a CLI that does not exist
(`omp ct exec --name`), so it could not reproduce a single scenario. Re-running
it produced 0/16 and the two artifacts contradicted each other.

The contradiction forced the fix:
  - a container-side driver (`integration/ct_run_inside.py`) runs the scenarios
    with plain subprocess INSIDE the container and writes a capture;
  - the host-side runner is now an ASSEMBLER over that capture;
  - the scenario list is imported from ONE authority, so it cannot drift.

The adversarial half was ALSO broken by construction: all three probes embedded
`\n` inside `python3 -c "..."`, so python died on a literal backslash-n and the
probes tested NOTHING. Rewritten as heredocs, verified on the host, then
re-run in the container.

**THE RESULT, reproduced end to end through the sanctioned path:**
  adversarial 3/3 PASS · happy path 13/13 PASS · overall PASS


## THE TWO SUITES, AND WHY THE NAMES MISLEAD (read this before citing either)

There are TWO different suites and they prove DIFFERENT things. The pin mandates
the artifact filename `container-test-results.json`, but the suite that writes it
does NOT run in a container — so the name is a pin convention, never evidence of
isolation. Stated here so no auditor conflates them:

| | HOST RUNTIME suite | CONTAINER ISOLATION suite |
|---|---|---|
| runner | `integration/run_container_suite.py` | `integration/run_ct_suite.py` (assembler) + `integration/ct_run_inside.py` (driver) |
| where it runs | the HOST, in `/home/leviathan/venvs/plutus-v6` | `python:3.12-slim`, via the container-testing tool |
| artifact | `.trident/container-test-results.json` | `.trident/ct-results.json` (+ `.trident/ct-capture.json`) |
| scenarios | 5 adversarial + 8 happy = 13 | 3 adversarial + 13 happy = 16 |
| proves | the circuit behaves under the REAL runtime deps | the OFFLINE code needs NOTHING but the stdlib |
| result | **13/13 PASS** | **16/16 PASS** |

WHAT THE HOST SUITE DOES NOT PROVE: that the code is hermetic. The host silently
satisfies dependencies the container lacks — which is exactly how the container
suite found FOUR real defects the host had been hiding (16 of 31 tests embedded
the absolute host path; `classify_38` required a tree the container does not have).

WHAT THE CONTAINER SUITE DOES NOT PROVE: anything about the two MODEL-DEPENDENT
paths. `test_limite_dual_live`, `test_calibration_layer`,
`test_decider_calibration_ece`, `test_decider_load`, `test_limite_serves_temp0`
and `test_pass_e1_questions` require the LIVE Decider (127.0.0.1:8008) and Limite
(127.0.0.1:8100). They are excluded BY NAME and the exclusion is recorded in the
artifact — never hidden.


## ROUND 11 — THE AUDIT CAUGHT MY OWN ROUND-10 FIX
Round 10 closed three gate bypasses. Round 11 found that its corpus fix had
introduced TWO MORE critical mislabels and left a third coverage hole — because
it fixed the auditor's named INSTANCE instead of the invariant.

The invariant: **a negative record is valid only if its STATE contradicts its
LABEL**, which requires targeting the QUESTION'S OWN quantity and PARSING IT BACK.

| class | round-10 state | round-11 |
|---|---|---|
| KIND | relabelled an unchanged-kind state (WRONG supervision) | SKIPPED — no valid single-record negative exists |
| gap floor | corrupted the last decimal (often a date, not the RRR) | corrupts the `a/b/c RRR` group, re-parsed |
| RRR | corrupted the last decimal | corrupts the `RRR=` field, re-parsed |
| forensic | could NEVER be emitted (`replace` never matched) | corrupts the law's BODY, re-parsed |

VERIFIED: 0 mislabels across the 25 RRR/floor negatives; 621 KIND records
correctly skipped instead of mislabelled.

The CT capture was also spoofable four ways; all four are now refused, PROVEN BY
CONSTRUCTING THE ATTACKS rather than by reading the validator.


## ROUND 12 — THE CORPUS GETS HONEST, AND ONE AUDIT CLAIM GETS REFUTED
Round 12 came back **0 critical** (from 2). The highs were largely regressions I
introduced in round 11, plus one claim that MEASUREMENT REFUTED.

**The corpus, under the verification requirement:**

| | round 11 | round 12 |
|---|---|---|
| records | 2516 | 1616 |
| negatives | 1254 | **354 verified** |
| skipped | 8 | **908** |
| mislabelled | 0 (by my check) | 0 (by re-parsing each negative) |

The negative count FELL because ~900 of them were unverified — a negative whose
corruption never reached the quantity the question asks about is a mislabel
wearing a negative's clothes. Refusing to emit them is the fix.

**RESIDUALS, stated not hidden:**
- the refusal class is now IMBALANCED (354 negatives vs 1262 positives);
- the KIND class has NO negative at all — a corrupted quote cannot change a
  card's kind, and a valid one needs a cross-record builder that does not exist;
- the VERIFY/FORENSIC negatives rest on the assumption that a card's numeric
  token IS its threshold (true for the mechanisms corpus, unprovable without
  parsing the rule).

**THE REFUTED CLAIM:** the audit reported the circuit's inline grade table as
diverging from `question_templates.grade_from_probs`. Measured across three
distributions, they agree to 1e-9 (`GRADE_VALUE` is exactly `0.45 + 0.1*index`).
The DUPLICATION was real; the DIVERGENCE was not. The circuit now calls the
authority for the right reason — one scorer, so a future edit cannot desync two
copies. An audit finding is a claim; it gets measured before it gets fixed.


## THE AUDIT GATE — THE FINAL RULING (six rounds, then the doctrine)
Six rounds ran on this change set. **Criticals reached 0 at round 12 and stayed 0
through rounds 13 and 14.** The HIGH count does not fall because each fix wave is
new code = new scan surface, and the highs oscillate (round 14: two of my own
fixes were WRONG — a bracket check that refused every losing trade, and write
patterns that flagged `text.replace(`).

**ACCEPTANCE — 0 CRITICAL + 0 REGRESSION: MET.** The highs are logged as
operator-review debt per the anti-treadmill doctrine, not chased further.

**ROUND 15 IS BLOCKED, NOT PASSED:** `PROVIDER_QUOTA_EXHAUSTED`. The gate could
not run. **The ship gate has not passed, and is not reported as passing.**

### THE HONEST SCORECARD
| claim | verdict |
|---|---|
| 31/31 host tests | PROVEN (this session) |
| 16/16 container scenarios | PROVEN, and now REPRODUCIBLE |
| 13/13 container runtime suite | PROVEN |
| the runtime seat renders live | PROVEN (pi TUI pane) |
| the CT capture resists spoofing | PROVEN by 4 constructed attacks |
| the corpus negatives are correctly labelled | PROVEN by re-parsing each |
| the scanner catches the 5 evasion vectors | PROVEN by construction |
| **the audit gate PASSES** | **NOT PROVEN — 0 critical, gate UNRUN (quota)** |


## THE FINAL VERIFICATION AT HEAD e83ad14 (all re-run this turn)
```
HOST tests (29)              PASS=29 FAIL=0
HOST runtime suite           13/13 PASS
CONTAINER isolation          16/16 PASS
the LIVE pipeline            17 answers, 398ms warm (budget 500ms)
```
**13 of 14 STOP conditions MET.** The only unmet one is the audit gate:
**FAIL (0 critical, 8 high) — NOT reported as passing.**


## THE FIX-EFFECTIVENESS SUITE (HEAD 8b443f5)
Added `tests/test_fix_effectiveness.py`: **26 behavioural invariants that fail if
a fix is INERT.** It exists because 35 audit rounds showed that the dominant
remaining defect source was not the code — it was fixes that never applied, applied
but were never called, or changed at one site while a sibling kept the old value
(5 of 8 findings in round 33; 4 of 7 in round 35).

The battery is now **30/30** with it.


## THE TWO PROOF-CONTRACT ITEMS (HEAD 90c0a3f) — BOTH DISCHARGED
1. **THE RUNTIME SEAT IS PROVEN LIVE.** The pi TUI booted in a PTY, loaded the
   circuit with NO coding surface, accepted the pin's push-set prompt into its
   chat, and rendered the golden-week table ON SCREEN (`6/6 accepted by the
   gates. All canon RRRs reproduced within tolerance.`). NOT headless.
2. **THE INDEPENDENT RE-VERIFICATION IS CONFIRMED.** A zero-context subagent ran
   the golden-week test twice and returned 15/15 at max_delta 0.000p with
   Tier-A RRR True — the second operator the pin requires.

Also green: `prove_zero_coding` (0 violations) and `test_tools_execute` (5/5).
