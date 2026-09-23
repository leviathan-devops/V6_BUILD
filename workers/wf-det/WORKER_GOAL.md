## GOAL
Build the PLUTUS V6 **determinism + memory worker** — architectural determinism (SHA-identical runs) + the hardened MiMoCode memory port — inside worktree /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det on branch worker/wf-det, to the master authority at /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/MASTER_CONTEXT/reports/Plutus_V6_Master_Blueprint_v1.md (524L) and the build package PLANNING_SUITE_Plutus_V6_Build_Package.md (374L), delivering every assigned deliverable with its gate command exiting 0 in a tool-result context.

## BASELINE
- V5 reference (READ-ONLY): /home/leviathan/.omp/wt/plutus-main-66dfa4c/PLUTUS/agent @ omp-worker-1 8f4ac74, tree clean (verified: `git status --porcelain | wc -l` = 0)
- Canon oracle PASSES: `bun run diag-lmv-golden-fx.ts` -> ENTRIES 15/15 at <=3p, TPs 2/2 at <=5p, VERDICT PASS
- Frozen pair MATCH: sl-lmv.ts 912940832fac44bc + trade-dedup.ts 33914c897e777540
- V5 suite: `bun test src/` -> 1195 pass / 0 fail / 119019 expect() / 84 files
- KG: 1940 nodes / 3647 edges / 0 findings
- GPU: RTX 4080 Laptop 12282 MiB total, 10698 MiB free
- Models on disk: qwen3-0.6b-base (1.2G) + limite-1b-violetto (2.0G)
- pi 0.85.1 installed; vllm 0.17.1 + torch 2.10.0+cu128 (cuda True); tensortrade 1.0.4 in /home/leviathan/venvs/plutus-v6

## WORKERS
WORKERS: 7 (this worker is wf-det; see ../../.trident/worker-plan.md for the full topology)

## LAWS
- RIPWIRE FIRST-CLASS: `ripwire verb=map` before every structural edit, `verb=callers` on every symbol change, `verb=quality-delta` after — a blind edit FAILS this worker on sight
- DECIDER SCORES, NEVER EDITS: model outputs are INPUTS; only the deterministic gate layer accepts/rejects
- LIMITE COMPUTES, CODE VERIFIES: dual-compute |model - code| <= eps, else LIMITE_CODE_DIVERGENCE
- TEMPERATURE=0: any temperature > 0 on the Limite path = AUTOMATIC-FAIL
- NOT HEADLESS: the pi TUI is the visible runtime; a headless run = AUTOMATIC-FAIL
- NO CODING: zero bash, zero code execution in the trading agent
- DOCTRINE OFFLINE: cards are training data, never runtime lookups (determinism law)
- E2 DESIGNATES, E3 OBEYS: every trade traces to an E1 zone + E2 shape day
- D13 QUOTE LAW: doctrine is quoted verbatim, never synthesized

## HARD STOPS
- Secrets never in the repo, chat, or rows
- GPU unavailable: BLOCKED state (not a pass), resume when it returns
- VRAM overflow: BLOCKED + name which model to downgrade
- The worker never merges its own PR — GitHub owns the deny (Anchor 1)

## PROOF CONTRACT
Every pass token MUST appear in a tool-result context (exit code, JSON field, artifact) — never free text.
Gate: `bash /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det/gate.sh` -> exit 0 with the passTokens printed.
Required tests owned: test_determinism_sha_match, test_memory_persistence, test_no_sampling_path
A stated hash is a claim; the disk's hash is evidence.
AUTOMATIC-FAIL: a deliverable marked done without its gate's tool-result evidence; any temp > 0; any headless run; any bash in the trading agent.

## STOP
This worker is done ONLY when every assigned deliverable's gate command exits 0 with its passToken in a tool-result context, the self-audit table (§W9) is executed with verdicts, the PR is opened with the required checks armed, and the canon + ship docs record the milestone. Anything less is OPEN.

## ANTI-DERAIL
- SCOPE SHRINK: deliver every assigned deliverable; a subset is a FAILED delivery
- THEATRICAL COMPLETION: "it works" without the passToken in a tool result is VOID
- MODEL SUBSTITUTION: do not swap the confirmed models without the orchestrator
- HEADLESS DRIFT: any run without the TUI visible = AUTOMATIC-FAIL

## RESUME POINTERS
- this pin: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det/WORKER_GOAL.md
- worker spec: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det/WORKER_SPEC.md
- worker plan: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.trident/worker-plan.md
- master authority: ../../PLUTUS_V6_GOAL_PIN.md
- master blueprint: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/MASTER_CONTEXT/reports/Plutus_V6_Master_Blueprint_v1.md
- build package: .../PLANNING_SUITE_Plutus_V6_Build_Package.md
