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
