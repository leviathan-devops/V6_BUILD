# PLUTUS V6 — CURRENT STATE

## THE SYSTEM
An embedded trading circuit: market feed → state constructor → Decider →
Limite → 8 deterministic gates → TensorTrade OMS → report, with a TUI pane.
Zero coding capability. Not headless. Runs on the RTX 4080 Laptop 12GB.

## THE TWO LIVE ENGINES (both verified this session)
| Engine | Identity | Endpoint | Evidence |
|---|---|---|---|
| Decider | `Mapika/decider-2b` (published, base Qwen3.5-2B-Base, 3.5GB bf16) | 127.0.0.1:8008 `POST /v1/systemone` | `/health` → ok:true, model:Mapika/decider-2b, device:cuda; 17/17 non-uniform |
| Limite | `paradigma-inc/limite-1b-violetto` (1B math, 131k ctx) | 127.0.0.1:8100 vLLM 0.26.0 + limite-vllm plugin | `17+25=42`, byte-identical at temp=0 |

## THE CIRCUIT (7 worktrees, 23 test files)
| worker | worktree | owns | tests |
|---|---|---|---|
| WA decider | .wt/wa-decider | pi-harness/ decider/ state/ bars/ memory/ | 4 |
| WB limite | .wt/wb-limite | limite/ gates/ mpse/ | 7 |
| WC exec | .wt/wc-exec | oms/ report/ | 3 |
| WD tui | .wt/wd-tui | tui/ | 4 |
| WE train | .wt/we-train | corpus/ finetune/ | 1 |
| WF det | .wt/wf-det | determinism/ | 3 |
| WG integ | .wt/wg-integ | integration/ main.py .trident/ | 4 |

## THE CONTAINER ARTIFACT
`.trident/container-test-results.json` — sha256 `bf04465`2813bebd…`, 13 scenarios,
overallVerdict PASS (5 adversarial + 8 happy path).
Build HEAD: `ff5eb6a`

## THE MEASURED NUMBERS
- 6/6 canon Tier-A RRRs within ±0.02 (max delta 0.0043)
- 6/6 Tier-A accepted by all 8 gates
- 15/15 FX canon entry levels at 0.000 pips delta
- latency mean 0.058ms (gate 500ms → 8639× headroom)
- commission: +184.5p @0% → +183.3p @0.1% → +182.1p @0.2%
- determinism: two runs byte-identical
- zero coding surface: 0 violations / 8 roots
- corpus: 1,267 records, zero provenance violations

## THE GATE LAYER (9 gates, all fail-closed)
G-GEOMETRY · G-RRR · G-SESSION · G-SL · G-CONF · G-CASCADE · G-CHAIN ·
G-DEDUP · G-DUAL. Every threshold gate rejects NaN / non-finite / out-of-range
input (audit round 1: they all passed NaN). G-GEOMETRY reads direction and the
price geometry, which NO gate read before the audit. G-DUAL reports
G-DUAL_UNVERIFIED when no independent Limite value is supplied — never a
tautological pass.

## OPEN (NOT PASSED — reported as measured)
1. **ECE gate < 0.05 NOT MET.** Measured on the trading domain: 6/6 correct
   (accuracy 1.000), raw ECE 0.2579. The calibration LAYER works (held-out ECE
   0.3492 -> 0.1080, a 69% reduction) but **one global temperature does not
   transfer across tasks** — the corpus task is over-confident (T=5.00) while
   the trading domain is under-confident (T=0.24).
2. **Limite RRR reliability**: 5 of 6 Tier-A RRRs returned `None` or a wrong
   value. The dual-compute MECHANISM works; the MODEL's arithmetic on this task
   does not.
3. **No fine-tune** (W7-D2). Corpus built (1,267 records); no LoRA trained.
4. `test_walkforward_unseen_week` not written (needs a second harvested week).
5. No container isolation — the suite ran on the host.
6. The audit gate's rounds 1-3 were remediated but the tree has not been
   re-audited since the round-3 fixes.

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._


## STATE AT HEAD e83ad14 — 13 of 14 CONDITIONS MET
| # | condition | verdict | evidence |
|---|---|---|---|
| 1 | golden >=14/15 <=3p | MET | 15/15, max_delta 0.000p (`test_golden_week_e2e`) |
| 2 | 38 forensic classified | MET | `test_forensic_38_classification` |
| 3 | profitable 0.1% unseen week | MET | `test_walkforward_unseen_week` |
| 4 | latency <500ms, MODEL IN LOOP | MET | **398ms warm** (`test_decider_live_pipeline`) |
| 5 | zero coding agent | MET | `test_zero_coding_surface` |
| 6 | TUI shows every probability/gate | MET | `test_tui_renders_probabilities` |
| 7 | determinism SHA-identical | MET | `test_determinism_sha_match` |
| 8 | golden RRR +-0.02 | MET | 6/6 (`test_rrr_golden_reproduction`) |
| 9 | mutant tests fire | MET | AT-03 side-inversion |
| 10 | ECE < 0.05 | MET | 0.03238 |
| **11** | **audit gate GATE: PASS** | **NOT MET** | **FAIL (0 critical, 8 high)** |
| 12 | checkpoint sealed | MET | 14 |
| 13 | 6 ship docs | MET | 6 |
| 14 | 11 canon docs | MET | 11 |

## THE VRAM BLOCKER: RESOLVED, NO MODEL SUBSTITUTION
Three defects, all measured, fixed: the state rendered 4x the blueprint's spec
(9242 tokens vs the documented 8192 limit — `state/state_constructor.py`
render_state); `count_tokens` counted whitespace words (2238 vs the tokenizer's
9242, a 4.13x undershoot, so `assert_state_fits` never bit); and
`DECIDER_MAX_STATE_TOKENS` was unset (32768 vs the documented 8192). Latency
1259ms -> 398ms; the server's footprint 6587 -> 3827 MiB.
