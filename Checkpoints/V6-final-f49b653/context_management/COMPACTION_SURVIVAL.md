# PLUTUS V6 — COMPACTION SURVIVAL

## READ IN THIS ORDER ON RESUME
1. `context_management/CURRENT_STATE.md` — what exists now
2. `context_management/EVIDENCE_STATE.md` — every claim with its command + raw result
3. `context_management/TASK_QUEUE.md` — the 4 open items
4. `ship_docs/BUILD_REPORT.md` — the honest gaps
5. `.trident/worker-plan.md` — the 7-worker topology
6. `ship_docs/THEATRICALITY_LOG.md` — the six recorded theatrical moves

## THE ONE-PARAGRAPH STATE
Plutus V6 is an embedded trading circuit on 7 git worktrees under
`PLUTUS/V6_BUILD`, with two LIVE engines: the published `Mapika/decider-2b`
on :8008 and `paradigma-inc/limite-1b-violetto` on :8100. The 13-scenario
container suite passes 13/13 (5 adversarial first, 8 happy last) with the
artifact at `.trident/container-test-results.json`. The canon Tier-A oracle
reproduces 6/6 within ±0.02 and all 6 are accepted by the 8 deterministic
gates. TWO GATES ARE OPEN: ECE (measured 0.2139 against a 0.05 gate — the
published model is accurate but under-confident) and the W7 fine-tune (the
1,267-record corpus is built; no adapter was trained).

## THE INVARIANTS THAT MUST NOT DRIFT
- `gates/gates.py` contains ZERO model calls — the gates are pure if/else.
- `limite/client.py` hard-codes `TEMPERATURE = 0.0`.
- the agent tree has zero code-execution capability (14-entry lexicon, 0 hits).
- the ONLY acceptance oracle is the 6 documented-exact DXY Tier-A rows; the
  EU/GU rows are Tier D (pixel-inferred) and are excluded from acceptance.
- a blocked measurement is reported BLOCKED, never substituted.

## THE COMMANDS THAT RE-PROVE THE STATE
```
cd PLUTUS/V6_BUILD/.wt/wg-integ/integration && /home/leviathan/venvs/plutus-v6/bin/python run_container_suite.py
bash PLUTUS/V6_BUILD/.wt/wb-limite/tests/run.sh test_rrr_golden_reproduction
curl -s http://127.0.0.1:8008/health
curl -s http://127.0.0.1:8100/v1/models
bash ~/.omp/agent/managed-skills/hydra-workers/scripts/check.sh PLUTUS/V6_BUILD
```

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
