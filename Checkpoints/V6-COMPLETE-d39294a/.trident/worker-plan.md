# PLUTUS V6 — WORKER PLAN
WORKERS: 7

**Build name:** PLUTUS V6 — the embedded trading circuit on a pi TUI harness
**Date:** 2026-09-23 · **Orchestrator:** omp session (orchestrator role — never writes product code)
**Master spec:** PLUTUS_V6_GOAL_PIN.md + MASTER_CONTEXT/reports/Plutus_V6_Master_Blueprint_v1.md (524L)
**V5 baseline reference:** /home/leviathan/.omp/wt/plutus-main-66dfa4c/PLUTUS/agent @ omp-worker-1 8f4ac74

---

## §T — TARGET (verbatim success criteria, mechanically verifiable)

| T-n | Criterion (verbatim from the pin) | Verification |
|---|---|---|
| T-1 | >=14/15 golden-week entries at <=3p precision | `test_golden_week_e2e` exit 0 |
| T-2 | every probability visible in the TUI | `test_tui_renders_probabilities` |
| T-3 | <500ms decision latency | `test_decision_latency` |
| T-4 | 6 Tier-A RRRs within +-0.02 | `test_rrr_golden_reproduction` |
| T-5 | profitable at 0.1% commission | `test_commission_0_1pct` (net_pips > 0) |
| T-6 | SHA-identical determinism | `test_determinism_sha_match` |
| T-7 | zero coding capability in the agent | `test_zero_coding_surface` (bash absent) |
| T-8 | Decider returns non-trivial distributions | `test_pass_e1_questions` |
| T-9 | ECE < 0.05 calibration | `test_decider_calibration_ece` |
| T-10 | all 38 forensic trades correctly classified | `test_forensic_trade_classification` |
| T-11 | Limite runs temperature=0 | `test_limite_serves_temp0` |
| T-12 | dual-compute catches divergence | `test_dual_compute_catches_divergence` |
| T-13 | 10 MPSE AT predicates executable | `test_mpse_predicate_at03` |
| T-14 | audit gate GATE: PASS | `qwen-code-audit` -> `GATE: PASS (0 critical/high)` |
| T-15 | all 6 ship docs + 11 canon docs current | floor checks + cross-consistency SHA |

## §B — BASELINE (measured this session, with the command that produced it)

| B-n | Fact | Command run | Result |
|---|---|---|---|
| B-1 | V5 tree clean @ omp-worker-1 8f4ac74 | `git status --porcelain \| wc -l` | `0` |
| B-2 | Canon oracle passes | `bun run diag-lmv-golden-fx.ts` | `ENTRIES: 15/15 at <= 3p / TPs: 2/2 at <= 5p` + `VERDICT: PASS` |
| B-3 | Frozen pair intact | `sha256sum src/mdve/{sl-lmv,trade-dedup}.ts` | `912940832fac44bc` + `33914c897e777540` |
| B-4 | V5 suite green | `bun test src/` | `1195 pass / 0 fail / 119019 expect() / 84 files` |
| B-5 | KG store healthy | sqlite table counts | `1940 nodes / 3647 edges / 0 findings` |
| B-6 | GPU available | `nvidia-smi` | `12282 MiB total, 10698 MiB free` |
| B-7 | Qwen3-0.6B-Base on disk | `du -sh models/qwen3-0.6b-base` | `1.2G` |
| B-8 | Limite-1B-Violetto on disk | `du -sh models/limite-1b-violetto` | `2.0G` |
| B-9 | vLLM + torch CUDA | `python3 -c "import vllm,torch"` | `vllm 0.17.1 / torch 2.10.0+cu128 cuda True` |
| B-10 | pi installed | `pi --version` | `0.85.1` (@earendil-works/pi-coding-agent) |
| B-11 | V6 build root + 7 worktrees | `git worktree list` | 8 rows @ f59e841 |
| B-12 | **ABSENT**: Decider LoRA adapter | `find models -iname "*decider*"` | none — must be trained (WE) |
| B-13 | **ABSENT**: Limite serving | `ps aux \| grep vllm` | none — must be started (WB) |
| B-14 | **ABSENT**: TensorTrade installed | `python3 -c "import tensortrade"` | ModuleNotFoundError — venv install (WC) |
| B-15 | **ABSENT**: V6 runtime code | `ls V6_BUILD/*.py` | none — the whole circuit is to be built |

## §T-CLASS — TARGET CLASSIFICATION

| Axis | Class | Guarded D-modes |
|---|---|---|
| Runtime | ARCHITECTURAL (full replacement of the OMP-based stack) | D2 (partial port), D7 (scope shrink) |
| Determinism | DETERMINISTIC-BY-CONSTRUCTION (no sampling; temp=0) | D3 (nondeterminism), D9 (unverified claim) |
| Testing | RUNTIME-GRADE (container, not unit-only) | D4 (theatrical pass), D11 (source-inspection-as-proof) |
| Model | FROZEN-BASE + ADAPTER (Qwen3-0.6B-Base + LoRA r=16 + pointer head) | D5 (model substitution), D12 (fallback slop) |

---

## §O — THE ORACLE TABLE (per worker; NEVER written into the dispatch prompts)

| OR-n | Worker | Class | Fact | Command that produced it |
|---|---|---|---|---|
| OR-1 | WA | O1 | 15 golden entries: EU 8 (1.14395/1.14110/1.14460/1.14020/1.14295/1.13935/1.14225/1.14555) + GU 7 (1.33330/1.33965/1.33660/1.33280/1.34260/1.33850/1.34500) | `bun run diag-lmv-golden-fx.ts` |
| OR-2 | WA | O1 | E1 zone types = {BoM, MoM, PHANTOM, LQZ}; E2 shapes = {BS, WL, RWL, R, SS, consol} | V6 Master Blueprint §1.7 |
| OR-3 | WA | O2 | Decider must output 17 distributions, argmax != uniform on golden state | `test_pass_e1_questions` |
| OR-4 | WA | O3 | Qwen3-0.6B-Base = 1.2G on disk, loads under 2GB VRAM bf16 | `du -sh models/qwen3-0.6b-base` |
| OR-5 | WA | O1 | MiMoCode memory store at ~/.local/share/mimocode/memory/ (45 banks) | `ls ~/.local/share/mimocode/memory/` |
| OR-6 | WB | O1 | 6 Tier-A RRRs = 4.25 / 4.92 / 4.60 / 3.58 / 3.79 / 5.84 | blueprint §2.3 + V5 diag |
| OR-7 | WB | O1 | Limite-1B-Violetto = 2.0G on disk; 131k context; 74.25% BeyondAIME | `du -sh models/limite-1b-violetto` |
| OR-8 | WB | O2 | `vllm serve` with `--temperature 0` must be the ONLY serving mode | `test_limite_serves_temp0` |
| OR-9 | WB | O3 | 8 gates must reject with named tokens: G-RRR G-SESSION G-SL G-CONF G-CASCADE G-CHAIN G-DEDUP G-DUAL | `test_gate_rrr_rejects` |
| OR-10 | WB | O1 | V5 gate vocabulary (18 names observed): G-ALL G-ATR G-BASED G-DEDUP G-DEMAND G-DIRECT G-EDGE G-LOCK G-ONLY G-POINT G-PROXIMITY G-RECOVERY G-REPORT G-SIDE G-STEP G-STRUCTURAL G-STRUCTURE G-VALIDITY | `grep -rhoE "G-[A-Z]{3,}" src/` |
| OR-11 | WC | O1 | TensorTrade's own finding: agents profitable at 0% lose money at 0.1% | blueprint §3.2 |
| OR-12 | WC | O2 | golden week must stay net_pips > 0 at 0.1% commission | `test_commission_0_1pct` |
| OR-13 | WC | O3 | trade-dedup.ts frozen SHA 33914c897e777540 — dedup semantics are load-bearing | `sha256sum src/mdve/trade-dedup.ts` |
| OR-14 | WD | O1 | pi 0.85.1 installed at /home/leviathan/.npm-global/bin/pi | `pi --version` |
| OR-15 | WD | O2 | pi-harness must contain ZERO bash/code-exec capability | `test_zero_coding_surface` |
| OR-16 | WD | O3 | TUI must render probability bars — a terminal log is NOT the seat | `test_tui_renders_probabilities` |
| OR-17 | WE | O1 | 649 doctrine cards exist (583 mechanisms + 38 rulings + 38 forensic trades) | KG + MASTER_CONTEXT |
| OR-18 | WE | O2 | >=700 training records from the cards | `test_corpus_record_count` |
| OR-19 | WE | O3 | LoRA r=16 on Qwen3-0.6B-Base ~= 12M trainable params | blueprint §1.3 |
| OR-20 | WF | O1 | V5 determinism enforced by discipline (R32); V6 must be architectural | blueprint V6-vs-V5 table |
| OR-21 | WF | O2 | sha256(run1) == sha256(run2) byte-identical | `test_determinism_sha_match` |
| OR-22 | WF | O3 | MiMoCode memory is TypeScript — the port is TS->TS copy-paste, not a rewrite | blueprint pi-harness section |
| OR-23 | WG | O1 | canon oracle 15/15 <=3p is the acceptance measurement | `bun run diag-lmv-golden-fx.ts` |
| OR-24 | WG | O2 | >=14/15 reproduced by the V6 circuit at <=3p, latency <500ms | `test_golden_week_e2e` |
| OR-25 | WG | O3 | ECE < 0.05 — a calibrated Decider, not a confident guesser | `test_decider_calibration_ece` |
| OR-26 | WC | O1 | 9 mutant fixtures exist (mutant-1..9) at specs/fixtures/mutants/ | `ls specs/fixtures/mutants/` |
| OR-27 | WB | O2 | G-DUAL must catch a deliberately wrong Limite output | `test_dual_compute_catches_divergence` |
| OR-28 | WF | O2 | the memory port must survive a process restart | `test_memory_persistence` |

## §M — BACKWARD MAP (T-n -> requires -> deliverable -> B-x)

```
T-01 >=14/15 <=3p   <- W10 pipeline <- D-WG1 e2e harness <- B-2 canon 15/15, B-15 absent
T-02 prob in TUI    <- W5 pane      <- D-WD1 renderer    <- B-10 pi 0.85.1, B-15 absent
T-03 <500ms         <- W2+W1 svc    <- D-WB1 vLLM + D-WA3 Decider <- B-7, B-8, B-9
T-04 RRR +-0.02     <- W2 math      <- D-WB2 L1-L6 + D-WB5 golden <- B-2 canon
T-05 0.1% profit    <- W4 OMS       <- D-WC1 Exchange    <- B-14 absent (install)
T-06 SHA-identical  <- W9 determin  <- D-WF1 harness     <- B-4 suite
T-07 zero coding    <- W5+W1 strip  <- D-WD2 proof       <- B-10 pi
T-08 non-uniform    <- W1 Decider   <- D-WA3 serve + D-WA4 17 q <- B-7 Qwen3-0.6B
T-09 ECE <0.05      <- W7 fine-tune <- D-WE2 adapter     <- B-12 ABSENT (train)
T-10 38 forensic    <- W10 classify <- D-WG4 + corpus    <- OR-17
T-11 temp=0         <- W2 serve     <- D-WB1 vLLM        <- B-13 absent
T-12 dual-compute   <- W2 verifier  <- D-WB3 verifier    <- B-15 absent
T-13 10 AT pred     <- W8 mpse      <- D-WB7 predicates  <- B-15 absent
T-14 GATE PASS      <- the audit    <- D-GATE            <- n/a (gate)
T-15 docs current   <- the record   <- D-DOC             <- B-15 absent
```

## §FW — FORWARD WORKERS

### Worker 1 — the Decider worker (WA)   [depends: none]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wa-decider
  Branch: worker/wa-decider
  SME domain: the pi agent runtime + the Decider pointer-readout decision engine + the state constructor (bars->state text)
  Files (disjoint): `pi-harness/`, `decider/`, `state/`, `bars/`, `memory/`
  Goal pin: `.wt/wa-decider/WORKER_GOAL.md`
  Todos: W1-T1..T10 + W3-T1..T4
  Gate: `bash .wt/wa-decider/gate.sh` -> `test_pass_e1_questions` + `test_state_constructor_golden` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WA1 pi harness, coding stripped | blueprint "pi harness option" | OR-14, OR-15 | `grep -rE "child_process|execSync|spawn\(" pi-harness/ \| wc -l` == 0 |
  | D-WA2 MiMoCode memory ported | blueprint pi-harness section | OR-5, OR-22 | `test_memory_roundtrip` exit 0 |
  | D-WA3 Decider served (base+LoRA+head) | blueprint §1.1-§1.3 | OR-4, OR-19 | `test_decider_load` exit 0 |
  | D-WA4 17 question templates | blueprint §1.7 | OR-2, OR-3 | `test_pass_e1_questions` exit 0 |
  | D-WA5 state constructor bars->text | blueprint V6 cycle step 2 | OR-1, OR-2 | `test_state_constructor_golden` exit 0 |
  | D-WA6 session detection | blueprint V6 cycle step 1 | OR-1 | `test_session_london_window` exit 0 |

### Worker 2 — the Limite + gates worker (WB)   [depends: none]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wb-limite
  Branch: worker/wb-limite
  SME domain: the Limite-1B math engine + the dual-compute verifier + the 8 deterministic gates + the 7 MPSE AT predicates
  Files (disjoint): `limite/`, `gates/`, `mpse/`
  Goal pin: `.wt/wb-limite/WORKER_GOAL.md`
  Todos: W2-T1..T10 + W8-T1..T4
  Gate: `bash .wt/wb-limite/gate.sh` -> `test_rrr_golden_reproduction` + `test_gate_rrr_rejects` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WB1 Limite-1B served temp=0 | blueprint §2.1 | OR-7, OR-8 | `test_limite_serves_temp0` exit 0 |
  | D-WB2 6 math queries L1-L6 | blueprint §2.3 | OR-6 | `test_math_queries_shape` exit 0 |
  | D-WB3 dual-compute verifier | pin LAWS LIMITE COMPUTES CODE VERIFIES | OR-27 | `test_dual_compute_catches_divergence` exit 0 |
  | D-WB4 8 deterministic gates | blueprint §2.4 | OR-9, OR-10 | `test_gate_rrr_rejects` exit 0 |
  | D-WB5 golden RRR reproduction | blueprint §2.3 call 3 | OR-6 | `test_rrr_golden_reproduction` exit 0 (6 values +-0.02) |
  | D-WB6 7 MPSE gates | MPSE blueprint (398L) | OR-9 | `test_mpse_gates_named_tokens` exit 0 |
  | D-WB7 10 AT predicates + trust engine | MPSE blueprint | OR-9 | `test_mpse_predicate_at03` exit 0 |

### Worker 3 — the execution worker (WC)   [depends: worker 2 (gates)]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wc-exec
  Branch: worker/wc-exec
  SME domain: the TensorTrade OMS execution simulation + commission analysis + walk-forward validation + the 8-section report generator
  Files (disjoint): `oms/`, `report/`
  Goal pin: `.wt/wc-exec/WORKER_GOAL.md`
  Todos: W4-T1..T6 + W6-T1..T3
  Gate: `bash .wt/wc-exec/gate.sh` -> `test_commission_0_1pct` + `test_report_golden_check` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WC1 TensorTrade OMS wired | blueprint §3.1, §3.3 | OR-11 | `test_oms_execute_order` exit 0 |
  | D-WC2 commission 0/0.1/0.2% | blueprint §3.3 | OR-12 | `test_commission_0_1pct` exit 0 (net_pips > 0) |
  | D-WC3 walk-forward validation | blueprint §3.3 | OR-12 | `test_walkforward_unseen_week` exit 0 |
  | D-WC4 8-section report generator | pin DOC CONTRACT | OR-23 | `test_report_golden_check` exit 0 |
  | D-WC5 mutant sensitivity | OR-26 | OR-26 | `test_mutant_8_rrr_drift` exit 0 |

### Worker 4 — the TUI worker (WD)   [depends: worker 1 (harness)]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wd-tui
  Branch: worker/wd-tui
  SME domain: the pi TUI trading pane — probability bars, live P&L, gate decisions, rejection log — and the zero-coding proof
  Files (disjoint): `tui/`
  Goal pin: `.wt/wd-tui/WORKER_GOAL.md`
  Todos: W5-T1..T5
  Gate: `bash .wt/wd-tui/gate.sh` -> `test_tui_renders_probabilities` + `test_zero_coding_surface` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WD1 trading pane renders | pin RUNTIME SEAT | OR-16 | `test_tui_renders_probabilities` exit 0 |
  | D-WD2 zero-coding proof | pin LAWS NO CODING | OR-15 | `test_zero_coding_surface` exit 0 |
  | D-WD3 rejection log with named tokens | pin RUNTIME SEAT | OR-9 | `test_rejection_log_tokens` exit 0 |
  | D-WD4 not-headless proof | pin LAWS NOT HEADLESS | OR-14 | `test_not_headless` exit 0 |

### Worker 5 — the doctrine fine-tune worker (WE)   [depends: worker 1 (Decider)]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/we-train
  Branch: worker/we-train
  SME domain: the doctrine corpus generator (649 cards -> >=700 records) + the Decider LoRA fine-tune
  Files (disjoint): `corpus/`, `finetune/`
  Goal pin: `.wt/we-train/WORKER_GOAL.md`
  Todos: W7-T1..T6
  Gate: `bash .wt/we-train/gate.sh` -> `test_corpus_record_count` + `test_finetuned_golden_precision` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WE1 corpus generator (>=700 records) | blueprint §1.8 | OR-17, OR-18 | `test_corpus_record_count` exit 0 |
  | D-WE2 LoRA r=16 adapter trained | blueprint §1.3, §1.5 | OR-19, OR-4 | `test_lora_adapter_loads` exit 0 |
  | D-WE3 D13 verbatim quote law | pin LAWS D13 QUOTE LAW | OR-17 | `test_d13_quoting` exit 0 (0 synthesized quotes) |
  | D-WE4 >=14/15 on golden with the tuned adapter | pin W7 gate | OR-24 | `test_finetuned_golden_precision` exit 0 |

### Worker 6 — the determinism + memory worker (WF)   [depends: worker 1, worker 2]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wf-det
  Branch: worker/wf-det
  SME domain: architectural determinism (SHA-identical runs) + the hardened MiMoCode memory port
  Files (disjoint): `determinism/`
  Goal pin: `.wt/wf-det/WORKER_GOAL.md`
  Todos: W9-T1..T5
  Gate: `bash .wt/wf-det/gate.sh` -> `test_determinism_sha_match` + `test_memory_persistence` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WF1 determinism harness (SHA) | pin W9 gate | OR-20, OR-21 | `test_determinism_sha_match` exit 0 |
  | D-WF2 memory port hardened | blueprint pi-harness | OR-22, OR-28 | `test_memory_persistence` exit 0 |
  | D-WF3 no-sampling proof | blueprint V6-vs-V5 | OR-20 | `test_no_sampling_path` exit 0 |

### Worker 7 — the integration worker (WG)   [depends: workers 1,2,3,4,5,6]
  Worktree: /home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/.wt/wg-integ
  Branch: worker/wg-integ
  SME domain: the assembled circuit — market feed -> state -> Decider -> Limite -> gates -> OMS -> report, end to end
  Files (disjoint): `integration/`, `main.py`, `.trident/`
  Goal pin: `.wt/wg-integ/WORKER_GOAL.md`
  Todos: W10-T1..T8
  Gate: `bash .wt/wg-integ/gate.sh` -> `test_golden_week_e2e` + `test_decision_latency` + `test_decider_calibration_ece` exit 0   +   the PR required checks
  | Deliverable | Spec ref | Oracle rows | Done-when |
  |---|---|---|---|
  | D-WG1 e2e pipeline | blueprint complete-V6-cycle | OR-23, OR-24 | `test_golden_week_e2e` exit 0 (>=14/15 <=3p) |
  | D-WG2 latency <500ms | pin W10 gate | OR-24 | `test_decision_latency` exit 0 |
  | D-WG3 ECE <0.05 | pin STOP cond 10 | OR-25 | `test_decider_calibration_ece` exit 0 |
  | D-WG4 forensic trade classification (38) | pin STOP cond 2 | OR-17 | `test_forensic_trade_classification` exit 0 |
  | D-WG5 container-test results artifact | pin PROOF CONTRACT | OR-24 | `.trident/container-test-results.json` exists, per-scenario verdicts present |

## §TODOS (Anchor 2 — the pinned todo lists, per worker)

```
WA (decider):  W1-T1 spec+pin ; W1-T2 pi harness strip -> grep bash==0 ;
               W1-T3 memory ported -> test_memory_roundtrip ; W1-T4 Decider served -> test_decider_load ;
               W1-T5 17 questions -> test_pass_e1_questions ; W1-T6 state ctor -> test_state_constructor_golden ;
               W1-T7 session detect -> test_session_london_window ; W1-T8 2 runtime tests ; W1-T9 self-audit A ;
               W1-T10 PR + checks armed
WB (limite):   W2-T1 spec+pin ; W2-T2 vLLM temp=0 -> test_limite_serves_temp0 ;
               W2-T3 L1-L6 queries -> test_math_queries_shape ; W2-T4 dual-compute -> test_dual_compute_catches_divergence ;
               W2-T5 8 gates -> test_gate_rrr_rejects ; W2-T6 RRR golden -> test_rrr_golden_reproduction ;
               W2-T7 7 MPSE gates -> test_mpse_gates_named_tokens ; W2-T8 10 AT predicates -> test_mpse_predicate_at03 ;
               W2-T9 self-audit A ; W2-T10 PR + checks armed
WC (exec):     W4-T1 spec+pin ; W4-T2 OMS -> test_oms_execute_order ; W4-T3 commission -> test_commission_0_1pct ;
               W4-T4 walk-forward -> test_walkforward_unseen_week ; W4-T5 report gen -> test_report_golden_check ;
               W4-T6 PR + checks armed
WD (tui):      W5-T1 spec+pin ; W5-T2 pane -> test_tui_renders_probabilities ;
               W5-T3 zero-coding -> test_zero_coding_surface ; W5-T4 rejection log -> test_rejection_log_tokens ;
               W5-T5 PR + checks armed
WE (train):    W7-T1 spec+pin ; W7-T2 corpus -> test_corpus_record_count ;
               W7-T3 D13 quoting -> test_d13_quoting ; W7-T4 LoRA -> test_lora_adapter_loads ;
               W7-T5 golden -> test_finetuned_golden_precision ; W7-T6 PR + checks armed
WF (det):      W9-T1 spec+pin ; W9-T2 determinism -> test_determinism_sha_match ;
               W9-T3 memory hardened -> test_memory_persistence ; W9-T4 no-sampling -> test_no_sampling_path ;
               W9-T5 PR + checks armed
WG (integ):    W10-T1 spec+pin ; W10-T2 e2e -> test_golden_week_e2e ; W10-T3 latency -> test_decision_latency ;
               W10-T4 ECE -> test_decider_calibration_ece ; W10-T5 forensic -> test_forensic_trade_classification ;
               W10-T6 container artifact written ; W10-T7 adversarial 5 probes ; W10-T8 PR + checks armed
```

## §A — THE PRE-WRITTEN AUDIT TABLE (written at plan time, executed at L5)

| A-n | Worker | The claim to verify | The verify command | Oracle row | Verdict |
|---|---|---|---|---|---|
| A-1 | WA | pi harness has zero coding tools | `grep -rE "child_process|execSync|spawn\(" .wt/wa-decider/pi-harness/ \| wc -l` == 0 | OR-15 | |
| A-2 | WA | memory port round-trips | `test_memory_roundtrip` exit 0 + row count read-back | OR-5 | |
| A-3 | WA | Decider emits 17 non-uniform distributions | `test_pass_e1_questions` exit 0, print per-question argmax | OR-3 | |
| A-4 | WB | Limite is temp=0 | `grep -c "temperature=0|--temperature 0" .wt/wb-limite/limite/serve.sh` >= 1 | OR-8 | |
| A-5 | WB | dual-compute fires on a wrong answer | `test_dual_compute_catches_divergence` exit 0 | OR-27 | |
| A-6 | WB | 6 RRRs within +-0.02 | `test_rrr_golden_reproduction` exit 0, print the 6 deltas | OR-6 | |
| A-7 | WC | OMS applies commission | `test_commission_0_1pct` exit 0, print net_pips | OR-12 | |
| A-8 | WC | report has 8 sections | `grep -cE "^## " .wt/wc-exec/report/report.py` >= 8 | OR-23 | |
| A-9 | WD | TUI renders probability bars | `test_tui_renders_probabilities` exit 0 + screenshot artifact | OR-16 | |
| A-10 | WD | the agent cannot code | `test_zero_coding_surface` exit 0 | OR-15 | |
| A-11 | WE | corpus >=700 records | `wc -l .wt/we-train/corpus/records.jsonl` >= 700 | OR-18 | |
| A-12 | WE | quotes are verbatim (D13) | `test_d13_quoting` exit 0 (0 synthesized) | OR-17 | |
| A-13 | WF | two runs are byte-identical | `test_determinism_sha_match` exit 0 + both SHAs printed | OR-21 | |
| A-14 | WF | memory survives restart | `test_memory_persistence` exit 0 | OR-28 | |
| A-15 | WG | >=14/15 entries <=3p | `test_golden_week_e2e` exit 0, print the 15 deltas | OR-24 | |
| A-16 | WG | latency <500ms | `test_decision_latency` exit 0, print the measured ms | OR-24 | |
| A-17 | WG | ECE <0.05 | `test_decider_calibration_ece` exit 0, print ECE | OR-25 | |
| A-18 | WG | the results artifact exists with verdicts | `jq '.scenarios \| length' .trident/container-test-results.json` >= 5 | OR-24 | |

## §C — COVERAGE MAP

| T-n | Worker | Deliverable | Oracle rows |
|---|---|---|---|
| T-1 | WG | D-WG1 | OR-23, OR-24 |
| T-2 | WD | D-WD1 | OR-16 |
| T-3 | WG | D-WG2 | OR-24 |
| T-4 | WB | D-WB5 | OR-6 |
| T-5 | WC | D-WC2 | OR-12 |
| T-6 | WF | D-WF1 | OR-20, OR-21 |
| T-7 | WD, WA | D-WD2, D-WA1 | OR-15 |
| T-8 | WA | D-WA4 | OR-3 |
| T-9 | WG, WE | D-WG3, D-WE2 | OR-25, OR-19 |
| T-10 | WG | D-WG4 | OR-17 |
| T-11 | WB | D-WB1 | OR-8 |
| T-12 | WB | D-WB3 | OR-27 |
| T-13 | WB | D-WB7 | OR-9 |
| T-14 | ORCH | the audit gate | n/a |
| T-15 | ORCH | the record loop | n/a |

Every worker has >=1 oracle row. Every T-n maps to >=1 worker. Every spec ref maps to >=1 deliverable.

## §BRIDGE — THE BRIDGE DIAGRAM

```
+----------------------------------------------------------------------+
|  THE SPEC — PLUTUS V6 GOAL PIN (106L, validator PASS, 7/7 slots)      |
|  T-1..T-15: >=14/15 <=3p . prob-in-TUI . <500ms . RRR +-0.02 .        |
|  0.1% profit . SHA-determ . zero-coding . ECE<0.05 . GATE PASS        |
+----------------------------------------------------------------------+
|  THE BASELINE (measured this session)                                |
|  B-2 canon 15/15 PASS . B-3 frozen pair MATCH . B-4 1195/0 .          |
|  B-5 KG 1940/3647/0 . B-6 GPU 10698 free . B-7/B-8 models on disk     |
|  B-12..B-15 ABSENT: LoRA . Limite svc . tensortrade . V6 code         |
+----------------------------------------------------------------------+
|  WA decider   .wt/wa-decider   pi+Decider+state   gate.sh -> 2 tests  |
|  WB limite    .wt/wb-limite    vLLM+queries+gates gate.sh -> 2 tests  |
|  WC exec      .wt/wc-exec      OMS+report         gate.sh -> 2 tests  |
|  WD tui       .wt/wd-tui       pane+no-coding     gate.sh -> 2 tests  |
|  WE train     .wt/we-train     corpus+LoRA        gate.sh -> 2 tests  |
|  WF det       .wt/wf-det       determinism+memory gate.sh -> 2 tests  |
|  WG integ     .wt/wg-integ     e2e+latency+ECE    gate.sh -> 3 tests  |
+----------------------------------------------------------------------+
|  THE ORACLE BAND: 28 oracle rows (OR-1..OR-28), every worker traced   |
+----------------------------------------------------------------------+
|  THE GATE BAND: PR + required checks — GitHub owns the deny          |
|  the worker CANNOT merge its own PR (Anchor 1)                       |
+----------------------------------------------------------------------+
|  THE TARGET (T-1..T-15 materialized) -> checkpoint + docs sealed      |
+----------------------------------------------------------------------+
```
