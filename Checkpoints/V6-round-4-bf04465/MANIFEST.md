# PLUTUS V6 CHECKPOINT — round 4 — 2026-09-23T18:43:10Z

## SHAs
- git HEAD:            cc5b771de43c1df15f6c3be652fa916251273736
- container artifact:  6a3eaee694e44fcc1e0081e5bcd59715
- worker plan:         b5700b1628bcdb87c07ba5a71fd5a790

## VERIFIED AT THIS CHECKPOINT
- fast tests              26/26 PASS
- test_calibration_layer  PASS (held-out ECE 0.3492 -> 0.1080)
- container suite         13/13 PASS (5 adversarial FIRST + 8 happy LAST)
- prove_zero_coding       PASS (pi's 8 built-ins removed, 7 plutus_* tools)
- test_tools_execute      PASS (5/5 tool payloads)
- hydra predicate         PASS
- RUNTIME SEAT            PROVEN LIVE (the agent drove probe + golden week in the pane)
- canon Tier-A RRR        6/6 within +-0.02
- FX entries              15/15 at 0.000 pips

## THE TWO LIVE ENGINES (services, not in this archive)
- Decider: Mapika/decider-2b on 127.0.0.1:8008 (POST /v1/systemone)
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100 (vLLM + plugin)

## HONEST GAPS
1. ECE gate < 0.05 NOT MET. Measured 0.2579 raw on the trading domain; the
   calibration LAYER works (held-out 0.3492 -> 0.1080) but one global
   temperature does not transfer across tasks.
2. Limite-1B returned None/wrong for 5 of 6 Tier-A RRRs — not a reliable
   arithmetic engine at this prompt design.
3. NO fine-tune. MEASURED BLOCKER: decider/train.py is full-parameter
   (AdamW over all params); a 2B needs ~28GB, the card has 12GB.
4. No walk-forward test (needs a second harvested week).
5. No container isolation — the suite ran on the host.
6. The audit gate was remediated across 4 rounds but each round found the next
   layer; the tree has not been re-audited since the round-4 fixes.
