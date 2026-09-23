# PLUTUS V6 CHECKPOINT — 2026-09-23T17:49:39Z

## WHAT THIS IS
The Plutus V6 embedded trading circuit at the round-0 gate: the 7-worker
topology merged, the 13-scenario container suite green, 26/28 tests green.

## THE ARTIFACT SHAs
- container results: 7a15bb68a5d661050402224a8a57c0bc
- git HEAD: 6ceef1098d0df1d40b41b2039f80831f91750dbb
- worker plan: b5700b1628bcdb87c07ba5a71fd5a790

## THE TWO LIVE ENGINES (not inside this checkpoint — they are services)
- Decider: Mapika/decider-2b on 127.0.0.1:8008 (POST /v1/systemone)
- Limite:  paradigma-inc/limite-1b-violetto on 127.0.0.1:8100 (vLLM + plugin)

## HONEST GAPS (do not ship as complete)
1. ECE measured 0.2139 (gate < 0.05) — the published Decider is accurate but
   under-confident.
2. Limite-1B returned None/wrong for 5 of 6 Tier-A RRRs — not a reliable
   arithmetic engine at this prompt design.
3. No LoRA fine-tune performed (the 1,267-record corpus is built).
4. test_walkforward_unseen_week not written.
5. No container isolation — the suite ran on the host.
6. The audit gate's round-3 fixes have not been re-audited.
