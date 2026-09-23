# CONTAINER TEST PLAN — PLUTUS V6 HERMETICITY AUDIT

## 1. OBJECTIVE
Prove that the Plutus V6 circuit's OFFLINE code runs in a CLEAN container with no
host environment. The host has satisfied this suite silently for the whole build;
the container exposes every environment dependency the host was hiding. The claim
under test: the gates, the math shadows, the OMS, the report, the TUI pane, the
determinism digest, the memory store and the state constructor import and execute
with nothing but the Python standard library and the circuit's own files.

WHAT IS EXPLICITLY NOT CLAIMED: the two MODEL-DEPENDENT tests (the live Decider on
:8008 and the live Limite on :8100) are NOT hermetic by construction — they call
host services. This plan tests the code that must not need them.

## 2. TOOLS UNDER TEST
The circuit files copied into the container:
  gates/gates.py           the 9 deterministic gates (the fail-closed law)
  limite/math_queries.py   the 6 numeric queries + the python shadows
  limite/dual_compute.py   the |model-code| verifier
  oms/oms.py               the execution simulation + commission
  report/report.py         the 8-section report
  tui/pane.py              the seat's renderer
  tui/coding_surface.py    the zero-coding source check
  determinism/determinism.py  the run digest
  memory/memory_store.py   the append-only store
  state/state_constructor.py  bars -> state text + the temporal law
  mpse/predicates.py       the 10 AT predicates + the trust engine
  integration/circuit.py   the assembled circuit
  tests/                   the offline test files
BLAST RADIUS: every one of these is imported by `integration/circuit.py`, so a
single missing stdlib-only assumption breaks the assembled circuit end to end.

## 3. TEST SCENARIOS (each with passToken + failToken)

SCENARIO ADV-1 (adversarial, runs FIRST): a sub-floor RRR in the container.
  command: python -c "the gates on rrr=1.54"
  passToken: G-RRR_REJECT      failToken: ACCEPTED_BADLY
  proves: the RRR floor fires in a clean environment, not just on the host.

SCENARIO ADV-2 (adversarial): a bar past the temporal anchor.
  command: python -c "parse_bars with a post-anchor bar"
  passToken: FUTURE_BAR_LEAK   failToken: LEAK_NOT_CAUGHT
  proves: the temporal law is enforced by the code, not by the host's clock.

SCENARIO ADV-3 (adversarial): an unknown pair must fail closed.
  command: python -c "pip_for('USD/JPY')"
  passToken: UNKNOWN_PAIR      failToken: 0.0001
  proves: the pip authority refuses rather than defaulting to FX scale.

SCENARIO HAPPY-1: the full golden-week e2e in the container.
  command: bash tests/run.sh test_golden_week_e2e
  passToken: test_golden_week_e2e   failToken: [TOKEN-ABSENT]
  proves: 6/6 Tier-A accepted and the canon RRRs reproduce WITHOUT the host.

SCENARIO HAPPY-2: the fail-closed gate battery in the container.
  command: bash tests/run.sh test_gate_fail_closed
  passToken: test_gate_fail_closed  failToken: [TOKEN-ABSENT]
  proves: all 22 NaN/geometry probes behave in a clean environment.

SCENARIO HAPPY-3: determinism in the container.
  command: bash tests/run.sh test_determinism_sha_match
  passToken: test_determinism_sha_match   failToken: [TOKEN-ABSENT]
  proves: the digest is a pure function of its inputs, not of the host.

SCENARIO HAPPY-4: the memory store's durability in the container.
  command: bash tests/run.sh test_memory_persistence
  passToken: test_memory_persistence      failToken: [TOKEN-ABSENT]
  proves: the sqlite store writes and re-reads with no host state.

SCENARIO HAPPY-5: the TUI pane renders in the container.
  command: bash tests/run.sh test_tui_renders_probabilities
  passToken: test_tui_renders_probabilities   failToken: [TOKEN-ABSENT]
  proves: the seat's renderer needs no terminal capability beyond text.

## 4. ADVERSARIAL COVERAGE
Three adversarial scenarios run BEFORE any happy path (ADV-1, ADV-2, ADV-3),
covering the three failure classes the circuit's own laws name: the RRR floor,
the temporal anchor, and the pip authority. Each asserts a NAMED refusal token.
The happy path runs LAST, as the post-debug confirmation — never first.

## 5. EVIDENCE CHANNELS
- exec stdout: the passToken must appear IN THE COMMAND'S OUTPUT, captured by the
  container tool. A passToken in the agent's prose is CIRCULAR and is a FAIL.
- the results artifact: .trident/ct-results.json, per-scenario
  (passTokenMatch, failTokenAbsent, toolResultContext, timedOut, verdict).
- the container's own python version + a `pip list` to show the stdlib-only state.

## 6. PASS CRITERIA (the Phase-E circuit breaker)
ALL of: (a) the container reports its python version; (b) the circuit files are
present at the expected paths (an ls proves the copy); (c) ADV-1/2/3 each return
their named token; (d) HAPPY-1..5 each return their passToken; (e) no failToken
appears anywhere; (f) no scenario times out; (g) the results artifact is written.
Any one unmet = the test is NOT PASSED and is reported as such.

## 7. WHAT WOULD FALSIFY THIS
If any offline test FAILS in the container while passing on the host, that test
had a host dependency — a REAL hermeticity defect, and the finding is the point
of the exercise. If a file is missing from the copy, the import graph is
incomplete. Both are reportable defects, not failures of the method.
