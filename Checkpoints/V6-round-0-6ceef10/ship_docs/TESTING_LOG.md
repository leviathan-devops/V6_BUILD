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
