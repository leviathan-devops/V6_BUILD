# PLUTUS V6 — BUILD STATE

## GIT
- build root: `PLUTUS/V6_BUILD` (its own repo)
- HEAD: `bf04465`
- worktrees: 7 (worker/wa-decider … worker/wg-integ) + master
- `.gitignore` excludes `.wt/` (worktrees are separate repos), `logs/`, `models/`

## THE VENVS
| venv | python | torch | serves |
|---|---|---|---|
| `/home/leviathan/venvs/plutus-v6` | 3.12.3 | 2.14.0+cu130 | the circuit's tests + TensorTrade 1.0.4 |
| `V6_BUILD/vendor/limite-violetto/.venv` | 3.12 | 2.11.0+cu130 | vLLM 0.26.0 + the Limite plugin (7.5GB) |
| `JevManager/vendor/decider/.venv` | — | — | the published Decider, uvicorn :8008 |

## THE MODELS ON DISK
| path | size | what |
|---|---|---|
| `/home/leviathan/models/qwen3-0.6b-base` | 1.2G | Qwen3-0.6B-Base (used by the SUPERSEDED hand-built head) |
| `/home/leviathan/models/limite-1b-violetto` | 2.0G | Limite 1B Violetto (the math engine) |
| the Decider | — | served from JevManager; not copied |

## THE ARTIFACTS
| path | sha/size | what |
|---|---|---|
| `.trident/container-test-results.json` | `71016e6a2813bebd…`, 11,135B | the 13-scenario runtime suite |
| `.trident/worker-plan.md` | 331L | WORKERS: 7, predicate PASS |
| `ship_docs/` | 307L total | BUILD_REPORT DEBUG_LOG FAILURE_LOG SPEC_VIOLATION_LOG TESTING_LOG THEATRICALITY_LOG |
| `context_management/` | 11 docs | this canon set |
| `corpus/records.jsonl` | 1,267 records | the doctrine corpus |

## THE GPU (12,282 MiB total)
| consumer | MiB | note |
|---|---|---|
| the Decider (JevManager) | ~4,014 | the published model, uvicorn :8008 |
| the Limite vLLM engine | ~4,060 | the math engine, :8100 |
| llama-embed ×2 | 1,144 | embedding servers |
| free | ~1,000 | headroom |
| **REMOVED this session** | **9,534** | the Bonsai 27B seat weights were purged at the operator's order (the workspace folder was left intact) |

## THE PERTURBATIONS
- flashinfer 0.6.14's JIT sampling kernel fails against this CUDA/cub →
  `VLLM_USE_FLASHINFER_SAMPLER=0`
- the Limite server needs `VLLM_PLUGINS=limite` or it cannot resolve
  `LimiteForCausalLM`
- the Decider server is a long-running process started outside this build

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._


## STATE AT HEAD 2a21fa8
| STOP condition | verdict |
|---|---|
| 1. golden week >=14/15 <=3p | MET (15/15, max_delta 0.000p) |
| 2. 38 forensic classified | MET (test_forensic_38_classification PASS) |
| 3. profitable at 0.1% unseen week | MET (test_walkforward_unseen_week PASS) |
| 4. latency <500ms (model IN the loop) | **BLOCKED — VRAM** (offline path 4.46ms) |
| 5. zero coding agent | MET (test_zero_coding_surface PASS) |
| 6. TUI shows every probability/gate | MET (test_tui_renders_probabilities PASS) |
| 7. determinism SHA-identical | MET (test_determinism_sha_match PASS) |
| 8. golden RRR +-0.02 | MET (6/6) |
| 9. mutant tests fire | MET (AT-03 side-inversion, test_mpse_predicate_at03 PASS) |
| 10. ECE < 0.05 | MET (0.03238; test_decider_calibration_ece PASS) |
| 11. audit gate GATE: PASS | **NOT MET** (0 critical, 11 high — .trident/AUDIT_DEBT_CATALOG.md) |
| 12. checkpoint sealed | MET (10 checkpoints) |
| 13. 6 ship docs | MET (6 present, current) |
| 14. 11 canon docs | MET (11 present, current) |
**12 of 14 MET. 4 is BLOCKED (operator: downgrade decision). 11 is NOT MET.**
