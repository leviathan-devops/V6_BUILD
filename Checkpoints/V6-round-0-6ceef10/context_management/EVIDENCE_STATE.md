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

## THE TWO HONEST FAILURES (measured, not reframed)
1. **ECE 0.2139** (gate < 0.05). n=60 corpus decisions; accuracy 0.967; mean
   stated confidence 0.753. The published Decider is under-confident.
2. **Limite RRR reliability**: 5 of 6 Tier-A RRRs returned `None` or a wrong
   value. Limite is not a reliable arithmetic engine at this prompt design.
   The DUAL-COMPUTE MECHANISM works (it caught a deliberately wrong value in
   ADV-5 and test_dual_compute_catches_divergence); the MODEL's arithmetic on
   this task does not.

## THE CONTAINER ARTIFACT
`.trident/container-test-results.json` — 13 scenarios, overallVerdict PASS
(5 adversarial + 8 happy path).
