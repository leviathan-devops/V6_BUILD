# PLUTUS V6 — POST-COMPACTION PROMPT

Paste this to a fresh session to resume the build:

---
You are resuming the PLUTUS V6 build. Read, in order:
  PLUTUS/V6_BUILD/context_management/CURRENT_STATE.md
  PLUTUS/V6_BUILD/context_management/EVIDENCE_STATE.md
  PLUTUS/V6_BUILD/context_management/TASK_QUEUE.md
  PLUTUS/V6_BUILD/ship_docs/BUILD_REPORT.md
  PLUTUS/V6_BUILD/.trident/worker-plan.md

STATE: the circuit is built and green at 13/13 container scenarios (artifact
sha 71016e6a2813bebd). Two LIVE engines: the published Decider `Mapika/decider-2b` on
127.0.0.1:8008 and `paradigma-inc/limite-1b-violetto` on 127.0.0.1:8100.
The canon Tier-A oracle reproduces 6/6 within ±0.02 and all 6 are accepted.

TWO GATES ARE OPEN — do not report the build complete while they are:
  1. ECE measured 0.2139 against a 0.05 gate. The published Decider is accurate
     (58/60 = 0.967) but under-confident (mean stated 0.753). Fix by temperature
     scaling against the corpus, or by the fine-tune.
  2. W7 fine-tune not performed. The corpus is built at
     `.wt/we-train/corpus/records.jsonl` (1,267 records, each with its D13
     verbatim quote + file:line).

INVARIANTS THAT MUST NOT DRIFT:
  - gates/gates.py has ZERO model calls (pure if/else)
  - limite/client.py hard-codes TEMPERATURE = 0.0
  - the agent tree has zero code-execution capability
  - the ONLY acceptance oracle is the 6 documented-exact DXY Tier-A rows
    (MASTER_CONTEXT/PLUTUS_GOLDEN_CASCADE_23.md lines 19-24); the EU/GU rows are
    Tier D (pixel-inferred, marked ⚠) and are excluded
  - a blocked measurement is reported BLOCKED, never substituted

RE-PROVE BEFORE ANY CLAIM:
  cd PLUTUS/V6_BUILD/.wt/wg-integ/integration && /home/leviathan/venvs/plutus-v6/bin/python run_container_suite.py
  curl -s http://127.0.0.1:8008/health
  curl -s http://127.0.0.1:8100/v1/models
---

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
