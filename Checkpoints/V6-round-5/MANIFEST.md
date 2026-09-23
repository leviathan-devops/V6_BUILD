# PLUTUS V6 CHECKPOINT — round 5 (final for this session)

## SHAs
- git HEAD:            see `git rev-parse HEAD` in the build root
- container artifact:  .trident/container-test-results.json
- worker plan:         .trident/worker-plan.md (WORKERS: 7, predicate PASS)

## VERIFIED GREEN AT THIS CHECKPOINT
| check | result |
|---|---|
| hydra worker predicate | PASS |
| fast tests | 26/26 PASS |
| test_calibration_layer | PASS (held-out ECE 0.3492 -> 0.1080) |
| container suite | 13/13 PASS (5 adversarial FIRST, 8 happy LAST) |
| prove_zero_coding | PASS (pi's 8 built-ins removed; 7 plutus_* tools) |
| test_tools_execute | PASS (5/5 payloads) |
| RUNTIME SEAT | PROVEN LIVE in the pane |
| canon Tier-A RRR | 6/6 within +-0.02 |
| FX canon entries | 15/15 at 0.000 pips |

## THE TWO LIVE ENGINES (services — not in this archive)
- Decider: Mapika/decider-2b on 127.0.0.1:8008 (POST /v1/systemone)
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100 (vLLM + plugin)

## NOT GREEN — report as measured
1. AUDIT GATE: FAIL (0 critical, 28 high). Five rounds; the class of finding
   MOVED rather than shrank (each round's fixes created the next round's
   surface). A PASS was not achieved. Every round's findings were remediated and
   the suite re-run.
2. ECE gate < 0.05 NOT MET. 0.2579 raw on the trading domain. The calibration
   LAYER works on held-out data; one global temperature does not transfer
   across tasks.
3. Limite-1B RRR: 5 of 6 wrong or None. Not a reliable arithmetic engine at
   this prompt design. The dual-compute MECHANISM works.
4. NO fine-tune. HARD BLOCKER: decider/train.py is full-parameter (AdamW over
   all params); a 2B needs ~28GB, the card has 12GB. No LoRA path exists in the
   trainer to enable.
5. No walk-forward test (needs a second harvested week).
6. No isolation — the suite ran on the host.

## THE WORKER TOPOLOGY (7 worktrees, merged)
WA decider  .wt/wa-decider   pi harness + Decider client + state
WB limite   .wt/wb-limite    Limite + 6 queries + 9 gates + MPSE
WC exec     .wt/wc-exec      OMS + report
WD tui      .wt/wd-tui       pane + zero-coding audit
WE train    .wt/we-train     corpus (2,534 records)
WF det      .wt/wf-det       determinism + memory
WG integ    .wt/wg-integ     the assembled circuit + the container suite

## NEXT (in priority order)
1. Per-task calibration data for the trading domain (the ECE fix).
2. A LoRA-capable trainer for the 2B (or the 0.8B variant) to unblock W7.
3. Harvest a second week -> the walk-forward test.
4. An isolated run of the container suite.
5. The operator's cutover decision (V5 -> V6 as primary).
