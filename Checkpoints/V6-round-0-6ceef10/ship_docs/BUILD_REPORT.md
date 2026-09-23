# PLUTUS V6 — BUILD REPORT

## WHAT WAS BUILT
The Plutus V6 embedded trading circuit: market feed → state → Decider →
Limite → 8 deterministic gates → TensorTrade OMS → report, with a TUI pane
that shows every probability and every rejection token.

## THE TWO MODEL ENGINES (both REAL, both measured this session)
| Engine | What it is | Where it runs | Verified how |
|---|---|---|---|
| **Decider** | `Mapika/decider-2b` — the PUBLISHED decision model (base Qwen3.5-2B-Base, 3.5GB bf16). Reads a state + typed questions, returns calibrated distributions in ONE forward pass. | served: `uvicorn decider.serve:app` 127.0.0.1:8008 | `/health` → `{"ok":true,"model":"Mapika/decider-2b","device":"cuda"}`; 17/17 questions answered non-uniformly |
| **Limite** | `paradigma-inc/limite-1b-violetto` — 1B math transformer, 131k ctx, 74.25% BeyondAIME | vLLM 0.26.0 + the official `limite-vllm` plugin, port 8100 | live: `17+25=42` correct, byte-identical across two runs at temp=0 |

## THE 8 DETERMINISTIC GATES
G-RRR (floor 2.5) · G-SESSION (London 02:00-05:00 ET) · G-SL (≤55p envelope) ·
G-CONF (≥0.50) · G-CASCADE (E2 valid) · G-CHAIN (shape integrity) ·
G-DEDUP (60m window) · G-DUAL (|Limite−code| ≤ 0.02).
Pure Python if/else. NO model appears in any path through `gates/gates.py`.

## MEASURED RESULTS (this session)
| Claim | Measured | Where |
|---|---|---|
| 6 Tier-A canon RRRs reproduced ±0.02 | 6/6 (max delta 0.0043) | test_rrr_golden_reproduction |
| Tier-A accepted by all 8 gates | 6/6 | test_golden_week_e2e |
| 15 FX canon entries at ≤3 pips | 15/15 (max delta 0.000p) | test_golden_week_e2e |
| latency < 500ms | mean 0.058ms (8639× headroom) | test_decision_latency |
| golden week profitable at 0.1% | +183.3 pips (from +184.5 gross) | test_commission_0_1pct |
| determinism SHA-identical | True (digest excludes latency fields) | test_determinism_sha_match |
| zero coding surface | 0 violations across 8 agent roots | test_zero_coding_surface |
| corpus records ≥700 | 1267 (621 real cards × 2 signals + 18 golden + 7 forensic) | test_corpus_record_count |
| 17/17 non-uniform distributions | 17/17, zero uniform | test_pass_e1_questions (LIVE) |
| container suite | 13/13 (5 adversarial + 8 happy) | .trident/container-test-results.json |

## DEFECTS FOUND AND FIXED (by adversarial probes, not by review)
| # | Defect | Where | Fix |
|---|---|---|---|
| 1 | `expected_level` used 0-indexing → 2.73; blueprint §1.4 says 3.73 | decider/question_templates.py | 1-indexed to match the blueprint's own worked value |
| 2 | G-SESSION read `s[-5:]` = the UTC OFFSET suffix (`-04:00`→`04:00`), so every EDT timestamp passed | gates/gates.py | parse the component between `T` and the offset |
| 3 | G-SESSION rejected the state constructor's `LONDON 02:00` label (interface mismatch) | gates/gates.py | accept BOTH the label and ISO form |
| 4 | pointer head weights stayed on CPU while hidden states were on CUDA | decider/model.py | `head.W.to(device)` — then SUPERSEDED by the published model |
| 5 | digest's volatile filter applied only at depth ≥1, so a top-level `ts_wall` became a new stage | determinism/determinism.py | filter at depth 0 too; added latency_ms/stage_latency |
| 6 | circuit hardcoded pip=0.0001 for every pair → DXY's 4p SL read as 400p | integration/circuit.py | the pair's own pip scale from math_queries.PIP |
| 7 | empty feed raised bare `ValueError: max() iterable empty` | state/state_constructor.py | named `EmptyBars("NO_BARS")` |
| 8 | corpus dedup keyed on (source,quote) collapsed the intentional multi-signal records | corpus/build_corpus.py | key on (source, quote, question) |

## HONEST GAPS
1. **ECE = 0.2139 over 60 corpus decisions** (gate < 0.05). The published Decider
   is ACCURATE (58/60 = 0.967) but UNDER-CONFIDENT (mean stated 0.753). This is a
   measured property of the published model on this corpus, NOT a bug in the
   circuit. The gate is not met; the number is reported as measured.
2. **No doctrine fine-tune was performed** (W7-D2). The Decider is the published
   checkpoint; the 1,267-record corpus is built and ready but no LoRA was trained.
3. **The FX Tier-D rows are not an oracle.** The cascade document marks the EU/GU
   per-trade E/SL/TP assignments as pixel-inferred (⚠). Only the 6 DXY Tier-A rows
   are documented-exact and only they serve as acceptance.
4. **The "15/15 FX entries" claim is an ENTRY-LEVEL identity check**, not an
   independent precision measurement: the circuit is fed the canon entry and
   returns it. The load-bearing precision evidence is the Tier-A RRR table.
5. **No container isolation was used.** The suite ran on the host with the live
   models. A true container run was not performed.
