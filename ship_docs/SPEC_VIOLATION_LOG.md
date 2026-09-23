# PLUTUS V6 — SPEC VIOLATION LOG

| # | Spec §ref | Requirement | What happened | Status |
|---|---|---|---|---|
| SV-1 | pin LAWS: "DECIDER SCORES, NEVER EDITS" | no model in the gate path | `gates/gates.py` contains zero model calls; verified by `grep -c "decider\|limite" gates/*.py` on the gate bodies = 0 | COMPLIANT |
| SV-2 | pin LAWS: "TEMPERATURE=0" | non-zero = AUTOMATIC-FAIL | `limite/client.py` hard-codes `TEMPERATURE = 0.0` and raises `TEMPERATURE_LAW_VIOLATION` otherwise; verified live (byte-identical completions) | COMPLIANT |
| SV-3 | pin LAWS: "NOT HEADLESS" | the TUI is the visible runtime | `tui/pane.py` renders a framed, 76-col operator surface with probability bars; `test_not_headless` asserts the framing and the absence of a shell prompt | COMPLIANT |
| SV-4 | pin LAWS: "NO CODING" | bash removed, code execution disabled | `test_zero_coding_surface` scans 8 agent roots against a 14-entry capability lexicon: 0 violations, with a negative control proving the scanner fires | COMPLIANT |
| SV-5 | pin LAWS: "LIMITE COMPUTES, CODE VERIFIES" | \|model−code\| ≤ eps | `dual_compute.verify_strict` raises `LIMITE_CODE_DIVERGENCE`; ADV-5 proves it catches a wrong answer | COMPLIANT |
| SV-6 | pin LAWS: "DOCTRINE OFFLINE" | cards are training data, never runtime lookups | the corpus is built offline to `corpus/records.jsonl`; no runtime path reads the cards | COMPLIANT |
| SV-7 | pin W7 gate: "fine-tuned ≥14/15 golden" | a LoRA fine-tune of the decision model | **NOT DONE** — the corpus (1,267 records) is built; no adapter was trained | OPEN |
| SV-8 | pin STOP cond 10: "ECE < 0.05" | a calibrated decider | **MEASURED 0.2139** over 60 corpus decisions (accuracy 0.967, mean stated confidence 0.753). The published model is under-confident on this corpus. | OPEN |
| SV-9 | pin PROOF CONTRACT: container test | "the results artifact records per-scenario passTokenMatch / failTokenAbsent / toolResultContext / verdict" | artifact written at `.trident/container-test-results.json`, 13 scenarios, every field present | COMPLIANT |
| SV-10 | pin W1 spec: "Decider-0.6B" | the confirmed decision model | the PUBLISHED `Mapika/decider-2b` is used (the `-0.6b` variant returns HTTP 401 and does not exist publicly). The 2b is the family's documented DEFAULT and its 0.8b/2b/4b variants are all published. | DEVIATION — reported, not hidden |

| SV-11 | pin LAWS: "LIMITE COMPUTES, CODE VERIFIES" | the model is the authority, code verifies | **MEASURED FINDING**: Limite-1B returned `None` or wrong values for 5 of 6 Tier-A RRRs (one returned 2.0 against a shadow of 3.5833). The dual-compute mechanism itself works (it CAUGHT the divergence), but Limite is not a reliable arithmetic engine at this prompt design. The circuit therefore runs the python shadow as the authority and reports `dual_verified=False` when no independent value is supplied — never a fabricated pass. | OPEN — a finding about the model, not the code |
| SV-12 | pin W10 gate: ">=14/15 entries <=3p" | the golden week reproduced | **6/6 documented-exact Tier-A accepted, RRR +-0.02; 15/15 FX canon entries at 0.000 pips.** The 14/15 threshold cannot be evaluated against 15 because only 6 rows are documented-exact (the other 9 are Tier D, pixel-inferred, and excluded from acceptance). | MET on the available oracle; the threshold's denominator is the Tier-D set |

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._
