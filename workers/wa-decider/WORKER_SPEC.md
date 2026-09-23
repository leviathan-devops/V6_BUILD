# WORKER SPEC — Decider worker
Master spec: ../../PLUTUS_V6_GOAL_PIN.md   (106L, validator PASS)
Master blueprint: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/MASTER_CONTEXT/reports/Plutus_V6_Master_Blueprint_v1.md (524L)
Worker-plan: ../../.trident/worker-plan.md (331L)
Worker: wa-decider
Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider
Branch: worker/wa-decider
SME domain: the pi agent runtime + the Decider pointer-readout decision engine + the state constructor (bars->state text)

## §W0 SCOPE (what THIS worker owns)
Deliverables assigned by the worker-plan, verbatim:
D-WA1 pi harness, coding stripped | D-WA2 MiMoCode memory ported | D-WA3 Decider served (Qwen3-0.6B-Base + LoRA + pointer head) | D-WA4 17 question templates (E1:5 E2:4 E3:5 PVE:3) | D-WA5 state constructor | D-WA6 session detection

Files owned (disjoint from every other worker):
pi-harness/, decider/, state/, bars/, memory/

NON-GOALS (must NOT touch):
- any other worker's owned paths (`gates/` `oms/` `tui/` `corpus/` `determinism/` `integration/`)
- the V5 reference tree /home/leviathan/.omp/wt/plutus-main-66dfa4c/PLUTUS/agent — READ-ONLY reference
- the frozen pair src/mdve/sl-lmv.ts (912940832fac44bc) + src/mdve/trade-dedup.ts (33914c897e777540)

## §W1 THE MASTER-SPEC SLICES (references, never copies)
- Plutus_V6_Master_Blueprint_v1.md — the Decider architecture (§1.1-§1.8), the Limite math calls
  (§2.1-§2.4), the TensorTrade OMS (§3.1-§3.4), the merged runtime diagram, the complete V6 cycle
- PLUTUS_V6_GOAL_PIN.md — the 9 LAWS, the PROOF CONTRACT, the ADVERSARIAL LOOP, the STOP conditions
- PLANNING_SUITE_Plutus_V6_Build_Package.md (374L) — the 10 component specs W1-W10

GLOBAL LAWS binding this worker (verbatim from the pin):
- RIPWIRE FIRST-CLASS: `ripwire verb=map` before every structural edit; `verb=callers` on every symbol change
- DECIDER SCORES, NEVER EDITS: model outputs are INPUTS; only the gate layer (pure if/else) accepts/rejects
- LIMITE COMPUTES, CODE VERIFIES: dual-compute |model - code| <= eps or LIMITE_CODE_DIVERGENCE
- TEMPERATURE=0: any temperature > 0 on the Limite path = AUTOMATIC-FAIL
- NOT HEADLESS: the pi TUI is the visible runtime; a headless run = AUTOMATIC-FAIL
- NO CODING: zero bash, zero code-exec in the trading agent
- DOCTRINE OFFLINE: cards are training data, never runtime lookups (determinism)

Interfaces CONSUMED (must exist first — supplied by the orchestrator as shared fixtures):
- the golden-week bars fixture (restored at /tmp/opencode/bars_raw.json, 4,138,750 bytes, sha f0408f0eedc1afe3)
- the V5 reference implementations (READ-ONLY for algorithm parity)

Interfaces PRODUCED (other workers depend on these):
test_pass_e1_questions, test_state_constructor_golden, test_decider_load, test_memory_roundtrip, test_session_london_window

## §W2 THE TASKS (per-task WHAT / HOW / WHY / EXPECTED)
D-WA1 pi harness, coding stripped | D-WA2 MiMoCode memory ported | D-WA3 Decider served (Qwen3-0.6B-Base + LoRA + pointer head) | D-WA4 17 question templates (E1:5 E2:4 E3:5 PVE:3) | D-WA5 state constructor | D-WA6 session detection

## §W3 TESTING (this worker's own proof obligation)
Every test carries a TOOL-RESULT-BOUND passToken (never free text) and a failToken.
Adversarial cases FIRST; the happy path LAST.
Mutation check: each test must FAIL when the implementation is deliberately broken.

Test identifiers owned by this worker: test_pass_e1_questions, test_state_constructor_golden, test_decider_load, test_memory_roundtrip, test_session_london_window

## §W4 SUCCESS CRITERIA (mechanical, per deliverable)
Each criterion is a command + an expected output. No subjective criteria.

## §W5 ANTI-PATTERNS (this worker's failure classes, each with mechanical detection)
| Anti-pattern | Mechanical detection |
|---|---|
| Theatrical pass (claim with no tool result) | the gate's exit code must be 0, read from the run |
| Model in the gate path | `grep -rn "decider\|limite" gates/*.py \| grep -v "^.*#" \| wc -l` == 0 |
| Silent fallback | `grep -rn "except.*: *pass\|fallback" <files> \| wc -l` == 0 |
| Estimated numbers | every constant carries its measured source in a comment |
| Copy instead of reference | the spec cites paths + section ids, never restates |

## §W6 THE GATE (the worker's done-when)
Command: `bash /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/gate.sh`
Expected: exit 0, with the passTokens printed in a tool-result context.
PR required checks: `gates/test` (the suite), `gates/spec-gate` (this spec's §W4).
THE WORKER CANNOT MERGE ITS OWN PR — Anchor 1: GitHub owns the deny.

## §W7 THE TODO ANCHOR (the pinned todo list)
W1-T1..W1-T10 + W3-T1..W3-T4

## §W8 THE GOAL PIN (the behavior program)
Path: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/WORKER_GOAL.md
The worker loads it at L2 and re-asserts the 9 laws every turn.

## §W9 THE SELF-AUDIT TABLE (§A — written at plan time, executed at L5)
Oracle rows this worker judges: OR-1..OR-5, OR-14, OR-15, OR-22
Per expected hunk: the claim -> the verify command -> the oracle row -> the verdict.
NEVER improvised under return-plausibility pressure.

## §W10 RESUME POINTERS (compaction survival)
Read in this order on resume:
1. /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/WORKER_SPEC.md (this file)
2. /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.trident/worker-plan.md (the grouping)
3. ../../PLUTUS_V6_GOAL_PIN.md (the master authority)
4. the pinned todo list (Anchor 2)
5. /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider/WORKER_GOAL.md (Anchor 3)
