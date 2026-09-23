# PLUTUS V6 — CHANGELOG (append-only)

## 2026-09-23 · the build session
### ADDED
- the 7-worker topology: worker-plan (331L, WORKERS: 7, predicate PASS),
  7 worktrees, 7 worker specs (90L each), 7 goal pins (56L each), 7 gates
- the Decider client (`Mapika/decider-2b`, `POST /v1/systemone`)
- the Limite engine (vLLM 0.26.0 + the official plugin, temp=0)
- 6 math queries L1-L6 + the dual-compute verifier
- the 8 deterministic gates (G-RRR G-SESSION G-SL G-CONF G-CASCADE G-CHAIN
  G-DEDUP G-DUAL)
- the 10 MPSE AT predicates + the 3-way trust engine
- the state constructor (bars → Decider state, temporal filter, session label)
- the 17 question templates (E1:5 E2:4 E3:5 PVE:3) + the 4-call packer
- the TensorTrade OMS + commission sensitivity
- the 8-section report generator
- the TUI pane (probability bars, gate decisions, rejection log)
- the doctrine corpus builder (1,267 records from 621 real cards)
- the determinism module (run digest, volatile filter, stage diff)
- the memory store port (append-only, one-writer-per-bank, durable)
- the assembled circuit + the 13-scenario container suite
- the container results artifact (sha 71016e6a2813bebd)
- the 6 ship docs + the 11 canon docs

### FIXED (8 defects, all found by adversarial probes)
EN-001 0-indexed expected level (2.73 → 3.73 per blueprint §1.4)
EN-002 the session gate read the UTC offset suffix as the local time
EN-003 the session gate rejected the state constructor's own label
EN-004 the circuit hardcoded one pip scale for every pair
EN-005 the digest's volatile filter missed depth 0
EN-006 an empty feed raised a bare stdlib ValueError instead of NO_BARS
EN-007 the corpus dedup collapsed intentional multi-signal records
EN-008 the pointer head stayed on CPU (in the SUPERSEDED hand-built path)

### REMOVED
- the Bonsai 27B seat weights (5.6GB) at the operator's order — the workspace
  folder `JARVIS_LOCAL_BONSAI` was left intact
- the hand-built Decider head — SUPERSEDED by the published model

### MEASURED
- container suite 13/13 (5 adversarial + 8 happy) · overallVerdict PASS
- 6/6 canon Tier-A RRR ±0.02 · 6/6 accepted · 15/15 FX entries ≤3p
- latency mean 0.058ms · commission +183.3p @0.1% · determinism True
- corpus 1,267 records · zero coding violations / 8 roots
- ECE 0.2139 (FAIL, gate < 0.05)

---
_ROUND-4 STAMP: build HEAD `bf04465` · container artifact `6a3eaee694e44fcc` · 2026-09-23._
