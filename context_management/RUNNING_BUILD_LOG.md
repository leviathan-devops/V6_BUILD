# PLUTUS V6 — RUNNING BUILD LOG (high frequency, append-only)

## 2026-09-23 · the build turn
1. Re-verified the V5 baseline: canon oracle 15/15 ≤3p + 2/2 TP, frozen pair
   MATCH (912940832fac44bc / 33914c897e777540), suite 1195/0, KG 0 findings,
   GPU 10,698 MiB free, pi 0.85.1 present.
2. Purged the Bonsai weights (9,534 MiB) at the operator's order → 10,698 free.
3. Acquired the models: qwen3-0.6b-base (1.2G) + limite-1b-violetto (2.0G).
4. Built the 7-worktree topology; the hydra predicate exits 0.
5. Cloned the official Limite plugin; `uv sync --locked` → a 7.5GB venv with
   vLLM 0.26.0 + torch 2.11 cu130.
6. Served Limite: first attempt failed (no plugin → unknown architecture), then
   `--temperature` is not a serve flag, then flashinfer's JIT sampler failed to
   compile → `VLLM_USE_FLASHINFER_SAMPLER=0` → `Application startup complete`.
   LIVE: `17+25=42`, byte-identical twice.
7. Discovered the PUBLISHED Decider already served on :8008 (`Mapika/decider-2b`).
   Pinned the hand-built head as SUPERSEDED; wrote the real client.
8. LIVE: 17/17 non-uniform distributions; E1.Q1 → LQZ 0.7789; E3.Q1 → short 0.7441.
9. Wrote + ran 23 test files across the 7 worktrees; 8 defects found and fixed.
10. Built the corpus: 1,267 records from 621 real cards (583 mechanisms + 38 rulings).
11. Built the 13-scenario container suite: 5 adversarial FIRST, 8 happy path LAST.
    RESULT: 13/13 PASS. Artifact sha 71016e6a2813bebd.
12. Wrote the 6 ship docs + the 11 canon docs.
13. Dispatched the independent zero-context verifier (VerifyGoldenWeek).

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._

## 2026-09-23 · the harness + audit rounds 3-4
14. BUILT the pi TUI harness (W1's core deliverable, previously empty):
    - plutus-circuit.ts: 7 plutus_* tools registered via pi's own API
    - launch.sh: --no-builtin-tools (removes all 8 of pi's tools)
    - the trading system prompt
    - prove_zero_coding PASS · test_tools_execute PASS (5/5)
15. RUNTIME SEAT PROVEN LIVE: the pi TUI booted, loaded the extension, and the
    agent drove plutus_probe -> 5 named tokens and plutus_run_golden -> 6/6
    accepted, streaming the RRR table in the pane.
16. FOUND + FIXED the provider chain: the go gateway requires an
    x-opencode-session header; and muse-spark-1.3/1.2 + grok-4.6 return 503
    (upstream down) while deepseek-v4-flash / glm-5.1 / kimi-k2.6 return 200.
17. BUILT decider/calibration.py and CORRECTED the ECE probe across THREE
    generations (single-class sample -> synthetic-label sample -> the trading
    domain). The measured finding: one global temperature does NOT transfer.
18. AUDIT ROUND 4: 0 critical / 21 high, all remediated.
    Final: HEAD bf04465, container artifact 6a3eaee694e44fcc.

---
_ROUND-9 STAMP: HEAD f8b9250 · container artifact 9f8dfc263d58dca3 · 2026-09-23._
