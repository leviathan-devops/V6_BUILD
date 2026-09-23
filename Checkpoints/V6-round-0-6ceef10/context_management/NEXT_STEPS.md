# PLUTUS V6 — NEXT STEPS

## IMMEDIATE (the two open gates)
1. **ECE**: the Decider is accurate (0.967) but under-confident (0.753). Two
   routes: (a) temperature-scale the published model's logits against the
   1,267-record corpus and re-measure; (b) fine-tune (Q-2). Route (a) is cheap
   and does not require a training run.
2. **Fine-tune**: the corpus is built (\`corpus/records.jsonl\`, 1,267 records,
   each carrying its D13 verbatim quote + file:line provenance). The training
   harness is not written.

## THEN
3. **Walk-forward**: harvest a second week ending at its own anchor, run the
   same 6-row Tier-A protocol on it, and write the test.
4. **Container isolation**: the suite currently runs on the host with the live
   models. A container run needs the two model servers reachable from inside.

## THE OPERATOR-OWNED DECISION
The cutover (V5 → V6 as the primary pipeline) is the operator's call. V5 is
green at 1195/0 with the canon oracle at 15/15; V6 is green at 13/13 container
scenarios with two open gates. The comparison is in BUILD_REPORT.

## RESUME POINTERS
- build root: \`/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD\`
- worker plan: \`.trident/worker-plan.md\` (WORKERS: 7, predicate PASS)
- container artifact: \`.trident/container-test-results.json\`
- ship docs: \`ship_docs/\` (6) · canon docs: \`context_management/\` (11)
- the two live engines: :8008 (Decider) · :8100 (Limite)
- the canon oracle: MASTER_CONTEXT/PLUTUS_GOLDEN_CASCADE_23.md lines 19-24
