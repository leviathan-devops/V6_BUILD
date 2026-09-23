# PLUTUS V6 — TASK QUEUE

## OPEN (blocking the STOP conditions)
| # | Task | Gate | Blocks |
|---|---|---|---|
| Q-1 | Improve ECE below 0.05 (temperature scaling on the Decider's outputs, or a fine-tune) | \`test_decider_calibration_ece\` | STOP cond 10 |
| Q-2 | Fine-tune the decision model on the 1,267-record corpus | \`test_finetuned_golden_precision\` | W7-D2 |
| Q-3 | Harvest a second week's bars and write \`test_walkforward_unseen_week\` | that test | STOP cond 3 |
| Q-4 | Run the suite in true container isolation | the results artifact | PROOF CONTRACT |

## QUEUED (non-blocking)
| # | Task | Why |
|---|---|---|
| Q-5 | Wire the circuit to the live pi TUI process (the pane exists; the host loop does not) | the seat is currently exercised by tests, not by a running pi session |
| Q-6 | Add the angels (tiny trained policies) as micronodes | named in the objective; not yet built |
| Q-7 | Port the MiMoCode memory store's full semantics (currently the core: append-only, one-writer, durable) | the port is partial |
| Q-8 | Extend the corpus with the 38 forensic trade IMAGES (only the 7 laws are text-extractable) | STOP cond 2 asks for 38 classified |

## DONE (this session)
- W1 pi-harness/Decider · W2 Limite/gates · W3 state/bars · W4 OMS · W5 TUI
- W6 report · W8 MPSE predicates · W9 determinism/memory · W10 integration
- the container results artifact · 6 ship docs · 8 canon docs · 8 defect fixes
