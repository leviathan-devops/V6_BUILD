# PLUTUS V6 — EVIDENCE STATE

## PER-CLAIM EVIDENCE (all produced this session)

| Claim | Command that produced it | Raw result | Verdict |
|---|---|---|---|
| canon Tier-A RRRs reproduced | `bash .wt/wb-limite/tests/run.sh test_rrr_golden_reproduction` | 6/6 within ±0.02, max delta 0.0043 | PROVEN |
| Tier-A accepted by the 8 gates | `bash .wt/wg-integ/tests/run.sh test_golden_week_e2e` | 6/6 accepted | PROVEN |
| FX entries at ≤3p | same | 15/15, max delta 0.000p | PROVEN (entry-level) |
| latency < 500ms | `bash .wt/wg-integ/tests/run.sh test_decision_latency` | mean 0.058ms, p95 0.066ms | PROVEN |
| 0.1% commission profitable | `bash .wt/wc-exec/tests/run.sh test_commission_0_1pct` | +183.3 pips | PROVEN |
| SHA-identical determinism | `bash .wt/wf-det/tests/run.sh test_determinism_sha_match` | True | PROVEN |
| zero coding | `bash .wt/wd-tui/tests/run.sh test_zero_coding_surface` | 0 violations / 8 roots | PROVEN |
| corpus ≥700 | `bash .wt/we-train/tests/run.sh test_corpus_record_count` | 1,267 | PROVEN |
| 17/17 non-uniform | `bash .wt/wa-decider/tests/run.sh test_pass_e1_questions` | 17/17, 0 uniform | PROVEN (LIVE) |
| Limite temp=0 | `bash .wt/wb-limite/tests/run.sh test_limite_serves_temp0` | byte-identical completions | PROVEN (LIVE) |
| container suite | `python run_container_suite.py` | 13/13, artifact sha 71016e6a2813bebd | PROVEN |
| **ECE < 0.05** | `bash .wt/wg-integ/tests/run.sh test_decider_calibration_ece` | **0.2139 over n=60** | **FAILED** |
| fine-tuned ≥14/15 | — | not performed | NOT TESTED |

## THE ECE MEASUREMENT IN FULL
- model: Mapika/decider-2b, live, cuda
- instrument controls: perfect=0.00000, overconfident=0.95000 → the metric discriminates
- measured: ECE 0.21386 over 60 corpus decisions
- accuracy 58/60 = 0.967
- mean stated confidence 0.753
- interpretation: the model is MORE accurate than it claims — under-confident.
  ECE scores |accuracy − confidence|, so a well-calibrated-but-conservative model
  scores above zero on this metric.

## WHAT WAS NOT TESTED
- a second (unseen) trading week — no walk-forward
- the fine-tuned adapter — no fine-tune
- true container isolation
- the 8 DXY Tier-A trades' SL/TP under a live broker simulation


## THE AUDIT GATE — three rounds (a verdict is about a SPECIFIC tree)
| round | tree | critical | high | action |
|---|---|---|---|---|
| 1 | 49c68b2 | 1 | 35 | remediated (NaN fail-closed, G-GEOMETRY, path-keyed scanner) |
| 2 | 0b447e4 | 0 | 20 | remediated (honest G-DUAL, circuit path fix, scanner evasions) |
| 3 | 135bf6e | 2 | 17 | remediated (pickle bare-load, negative label, zone-width, HH:MM range) |

An audit PASS is a claim about a tree at a SHA. The final tree's verdict is
recorded with that SHA; an earlier PASS does not carry forward.

## THE ECE FINDING (three probe generations before a real measurement)
| generation | sample | result | why it was not a measurement |
|---|---|---|---|
| v1 | corpus `answer=="yes"` only | ECE 0.2139 | SINGLE-CLASS sample — unmeasurable by construction |
| v2 | corpus both classes | ECE 0.1387, accuracy 0.500 | the "negatives" are SYNTHETIC corruptions the model cannot detect |
| v3 | the DXY documented rows | **accuracy 6/6 = 1.000, ECE raw 0.2579** | the first number about the model |

**THE MEASURED FINDING (v3):**
- the corpus KIND task is **OVER**-confident -> fitted T = 5.00 (soften)
- the trading domain is **UNDER**-confident  -> fitted T = 0.24 (sharpen)
- applying the corpus T to the trading domain makes ECE **WORSE** (0.2579 -> 0.4269)
- a T fitted ON the trading rows still only reaches 0.1807
- with accuracy at 1.000, ECE is dominated by |1 - p|: the gate cannot be met
  without stating p ~= 1.0
- **ONE GLOBAL TEMPERATURE DOES NOT TRANSFER ACROSS TASKS.**

## WHAT THE CALIBRATION LAYER PROVES (a PASSING claim)
`decider/calibration.py` + `test_calibration_layer`:
- instrument controls: perfect=0.00000, overconfident=0.95000
- monotone, bounded, rejects T <= 0
- fitted on 60 rows, measured on 60 HELD-OUT rows
- **ECE 0.3492 -> 0.1080, a 69% reduction on data the fit never saw**

The layer works. The PIN'S 0.05 GATE is not met, and the reason is now measured:
per-task calibration data is required, and even then accuracy-at-ceiling
dominates the metric.

## THE SECOND HONEST FAILURE
**Limite RRR reliability**: 5 of 6 Tier-A RRRs returned `None` or a wrong value
(one returned 2.0 against a shadow of 3.5833). Limite is not a reliable
arithmetic engine at this prompt design. The DUAL-COMPUTE MECHANISM works (it
caught a deliberately wrong value in ADV-5 and in
`test_dual_compute_catches_divergence`); the MODEL's arithmetic does not.

## THE CONTAINER ARTIFACT
`.trident/container-test-results.json` — 13 scenarios, overallVerdict PASS
(5 adversarial + 8 happy path).

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
