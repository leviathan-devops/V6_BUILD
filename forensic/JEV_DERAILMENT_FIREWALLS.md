# THE JEV DERAILMENT FIREWALLS — BLUEPRINT
## Mechanically chaining the model: every macro derailment blocked at every enforcement point, with Jev as the intelligence

**Status:** DESIGN (for operator approval before minting)
**Input:** `MACRO_FAILURE_PATTERNS.md` (6 macro + 25 fine patterns, each traced to a measured artifact)
**Input (integrated):** the MERGED 87-CLASS CORPUS across 14 groups (57 master + 30 new, from 16
corpus files + 2 streamed sessions, 2 independent scouts reconciled) — **§8**
**Input (integrated):** the DURABLE-FACT L1 (17 fact classes, the 4 properties, the DELTA GATE) — **§9**
**Input (integrated):** the 30 NEW misfire/lifecycle/probe/dodge classes — **§10**
**Input (integrated):** the JEV-TREE L0/L1/L2 ownership map (the Paragon kernels) — **§11**
**Input (integrated):** the 5 VERDICTS + the 12 FROZEN NODES — **§12**
**Input (integrated):** the SECOND ORIGIN — the PBK v3 defects, measured, a different tree — **§13**
**Input (integrated):** the MECHANICAL/SEMANTIC split (the free layer) — **§14**
**Skills composed:** `typesafe-jev-judge-wiring` (the transport) · `jev-scale-judgment-pipeline` (the deterministic-first narrowing) · `jev-decision-gate-firewall` (the architecture) · `fact-judge-enforce` (the 3-layer law)
**The law this obeys:** **a lexicon DETECTS, Jev DECIDES, code ENFORCES.** Never regex-as-decision. Never an LLM grading its own work.

---

## §1 · THE ARCHITECTURE (one shape, eight instances)

```
+---------------------------------------------------------------------------------+
| THE THREE LAYERS — every firewall is the same shape                               |
+---------------------------------------------------------------------------------+
|                                                                                   |
|  L1 · THE STATE BUILDER  (pure code, DISK-READ, ungameable)                       |
|      reads the real artifacts: the diff, the test result, the ledger row,         |
|      the file on disk, the commit. NO model prose. NO agent self-report.          |
|              |                                                                    |
|              v                                                                    |
|  L2 · THE JEV JUDGE  (one forward pass, calibrated probabilities)                  |
|      receives the state + a typed question set; returns {choice|score|noul}       |
|      with probabilities. NO generation, NO chain-of-thought, NO parsing.          |
|              |                                                                    |
|              v                                                                    |
|  L3 · THE ENFORCER  (pure code, fail-closed)                                      |
|      maps the probability to an ACTION: BLOCK | REQUIRE_EVIDENCE | LEDGER | PASS.  |
|      writes a ledger row per decision. Never a soft warning.                       |
+---------------------------------------------------------------------------------+
|                                                                                   |
|  THE INVARIANT: the model never sees its own claim. It sees the ARTIFACT.          |
|  THE GUARANTEE: L1 cannot be gamed (it reads disk), L3 cannot be argued with       |
|  (it is an exit code), and L2 is a MEASUREMENT of the artifact, not an opinion     |
|  about the agent.                                                                  |
+---------------------------------------------------------------------------------+
```

### §1.1 WHY JEV (and not a regex, and not a chat LLM)

| the property | why it matters here | the measured failure it prevents |
|---|---|---|
| **one forward pass, no generation** | cannot be talked around, cannot be prompt-injected into prose, returns the same answer twice | the build's 40 rounds of prose self-assessment |
| **calibrated probabilities** | a threshold is a measurement, not a guess | the `OPERATOR-CAUGHT: 0` metric inversion |
| **a typed question set** | the question is FIXED before the state is seen | the "which number do I report?" drift |
| **batched (N states, N questions, ONE request)** | 40+ firewalls at per-decision cost | the 40-round audit's per-round latency |
| **no runtime queries to a doctrine store** | the questions live in code, versioned | `DOCTRINE OFFLINE` (the pin's own law) |

### §1.2 THE COST MODEL

Jev answers a **fixed question set** over a state in one pass. The 8 firewalls below define **~40 questions total**. Because Jev batches (N states in ONE request), a full gate sweep across 8 enforcement points is **one request per event**, not 40. At the decider-0.8b-class cost (~4ms with CUDA graphs, ~400ms eager) a firewall sweep is **below the noise of the action it guards**.

---

## §2 · THE EIGHT ENFORCEMENT POINTS

Each point: **when it fires · the state it reads (L1) · the Jev questions (L2) · the thresholds (L3) · the action.**

---

### FIREWALL 1 · THE PLAN GATE — `plan.emit`

**BLOCKS:** M-1 (the unread package), M-2 (the nonexistent model), S-03 (spec self-contradiction)

**FIRES:** when a planning document or goal pin is emitted.

**L1 · THE STATE (disk-read, ungameable):**
```
{
  "specs_present":   [glob of every *DPL1*/*BLUEPRINT*/*BUILD_PACKAGE*/*GOAL_PIN*],
  "read_receipts":   [the authoring doc's §0 READ RECEIPTS, parsed],
  "models_named":    [every model string in the emit],
  "model_probes":    [{name, http_code} from huggingface.co/api/models/<org>/<name>],
  "parent_claims":   [model names, counts, call-shapes extracted from the authority],
  "pin_claims":      [the same extracted from the emit],
  "laws":            [every LAW bullet], "stops": [every STOP bullet],
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question | criteria |
|---|---|---|---|
| P1 | `noul` | Does the emit's read-receipt list name at least one prior specification (not only skills)? | yes = a spec path appears |
| P2 | `noul` | Do ALL models named in the emit resolve to a real artifact (HTTP 200 or a local path)? | yes = every probe is 200/present |
| P3 | `noul` | Is every model named in the emit ALSO named in the authority it cites? | yes = a subset |
| P4 | `score` | How completely do the emit's claims agree with its declared authority? | `none/partial/most/all` |
| P5 | `noul` | Do any two LAW/STOP bullets contradict (one forbids what the other requires)? | yes = a contradiction |
| P6 | `noul` | If two spec packages exist, does either record the supersession? | yes = a header names the other |

**L3 · THE THRESHOLDS (fail-closed):**
| question | action |
|---|---|
| P1 < 0.70 | **BLOCK** `PLAN_UNREAD_PACKAGE` — the planner did not read the specs |
| P2 < 0.95 | **BLOCK** `MODEL_DOES_NOT_EXIST` — with the probe output |
| P3 < 0.80 | **BLOCK** `PIN_CONTRADICTS_AUTHORITY` — with the diff |
| P4 = `none/partial` | **BLOCK** `CLAIM_DRIFT` |
| P5 > 0.50 | **REQUIRE_OPERATOR_RULING** — a self-contradictory spec cannot be executed |
| P6 < 0.90 | **BLOCK** `UNRECORDED_SUPERSESSION` |

**THE ORIGIN:** P1 would have caught 09-17 (5 skills, 0 specs). P2 would have caught `Decider-0.6B` (401). P3 would have caught the name-collision merge. **All three fired in this project and none existed.**

---

### FIREWALL 2 · THE CONTRACT GATE — `tool.call` (pre-write)

**BLOCKS:** S-13 (optional authority), S-14 (absolute paths), S-02 (a producer with no consumer), S-12 (a silent fallback)

**FIRES:** before any source write or edit.

**L1 · THE STATE:**
```
{
  "diff":            the pending hunk(s),
  "symbols_added":   [names defined in the hunk],
  "consumers":       [grep counts of each new symbol across the live tree],
  "paths_literal":   [absolute path literals in the hunk],
  "switches_added":  [bool parameters whose name matches use_|enable_|opt_],
  "fallbacks_added": [assignments seeding a value from an input before a computation],
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question |
|---|---|---|
| C1 | `noul` | Does this hunk add a producer (function/field/emitter) with ZERO consumers in the live tree? |
| C2 | `noul` | Does this hunk add an off-switch on a critical-path component? |
| C3 | `noul` | Does this hunk seed a value from an input that a later computation may fail to overwrite? |
| C4 | `score` | How many absolute host paths does this hunk introduce? | `none/one/several/many` |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| C1 > 0.75 | **BLOCK** `PRODUCER_WITHOUT_CONSUMER` — "wire it or do not write it" |
| C2 > 0.70 | **BLOCK** `OPTIONAL_AUTHORITY` — "absence must be a loud refusal at construction" |
| C3 > 0.70 | **REQUIRE_EVIDENCE** — the hunk must carry the probe that shows a failure is loud |
| C4 ≥ `one` | **BLOCK** `ABSOLUTE_PATH` — one boot module only |

**WHY AT THE TOOL CALL:** the 15 discarded questions and the 16 absolute paths were written into the tree at authoring time. **A pre-write gate is the only point where they are cheap to stop.**

---

### FIREWALL 3 · THE REASONING GATE — `reason.step` (the stream)

**BLOCKS:** M-6 (self-measuring process), S-07 (self-certification), M-4 (a fix without an effect check)

**FIRES:** on a reasoning/thinking span, via the host's stream hook.

**L1 · THE STATE (the recent span + the disk facts):**
```
{
  "span":              the last N tokens of reasoning,
  "claims_made":       [{claim, has_command, has_output}],  // parsed
  "recent_tool_calls": [the tools actually invoked this turn],
  "tests_run":         [test files executed this turn],
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question | criteria |
|---|---|---|---|
| R1 | `noul` | Does the span assert a completion or verification for which NO tool was invoked this turn? | yes = a claim with no run |
| R2 | `noul` | Does the span describe the work as complete/correct WITHOUT naming the run that proves it? | yes = self-certification |
| R3 | `noul` | Does the span propose a fix WITHOUT naming the effect-check that will prove it landed? | yes = a fix without an effect check |
| R4 | `score` | How many of the span's factual claims trace to a tool result in this turn? | `none/some/most/all` |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| R1 > 0.75 | **STEER** — "name the run, or state it as unverified" |
| R2 > 0.75 | **STEER** — the self-certifying-comment ban |
| R3 > 0.70 | **REQUIRE_EVIDENCE** — the effect-check must be named before the fix is attempted |
| R4 = `none/some` | **LEDGER** + escalate at 3 occurrences in a session |

**WHY AT REASONING:** the build's 49 doc commits and six 'DEFINITIVE RULING' documents were all *reasoning-adjacent* artifacts. **The reasoning stream is where a claim becomes prose, and prose is where the theatre lives.**

**CAVEAT (honest):** a reasoning-stream gate is advisory-by-necessity (the private deliberation is not hookable on every host). It must be **LEDGER-heavy and STEER-light** — never a hard block on a private thought.

---

### FIREWALL 4 · THE ARTIFACT GATE — `commit.pre` (the push gate)

**BLOCKS:** M-5 (evidence aimed where it cannot fail), S-24 (a table contradicting a log), S-10 (unmet-as-met)

**FIRES:** before any commit/push of a claim-bearing artifact (a doc, a results file, a report).

**L1 · THE STATE:**
```
{
  "doc_changed":     the file,
  "numeric_claims":  [{value, context} extracted from the diff],
  "log_values":      [the same quantity read from the LOG/ledger, if present],
  "artifact_present":[does the results artifact exist and postdate the run?],
  "floor":           the class floor for this doc (from the authority),
  "lines":           wc -l,
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question |
|---|---|---|
| A1 | `noul` | Does the doc assert a numeric value that contradicts a value in the project's own log/ledger? |
| A2 | `noul` | Does the doc cite a results artifact that does not exist or predates the run it describes? |
| A3 | `noul` | Does the doc's claim rest on a measurement that was taken with the component under test DISABLED? |
| A4 | `noul` | Is the doc below the floor its own authority states? |
| A5 | `noul` | Does the doc flip a previously-NOT-MET condition to MET by changing the measurement rather than the code? |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| A1 > 0.75 | **BLOCK** `DOC_CONTRADICTS_LOG` — "the honest number and the reported number must be the same number" |
| A2 > 0.70 | **BLOCK** `CLAIM_WITHOUT_ARTIFACT` |
| A3 > 0.70 | **BLOCK** `MODEL_ABSENT_MEASUREMENT` — the 0.058ms class |
| A4 > 0.90 | **BLOCK** `DOC_BELOW_FLOOR` |
| A5 > 0.75 | **REQUIRE_OPERATOR_RULING** — a redefined gate |

**WHY AT THE COMMIT:** the build's docs and its audit tables disagreed **in the same session**. A pre-commit diff against the log is the cheapest place to catch it. **A1 is the single highest-value firewall in this design.**

---

### FIREWALL 5 · THE VERIFICATION GATE — `goal.verify`

**BLOCKS:** the whole M-5 set, S-18 (no influence test), S-16 (artifact vs harness)

**FIRES:** when a goal/stop-condition is claimed MET.

**L1 · THE STATE:**
```
{
  "condition":       the stop condition text,
  "evidence":        the artifact/command/output the agent cites,
  "artifact_ids":    the scenario ids in the results artifact,
  "harness_excluded":[the driver's own exclusion list],
  "influence_tests": [does any test vary the component's input and check the output?],
  "oracle_shape":    [{expr, operands, shares_binding}]  // the x-x detector
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question |
|---|---|---|
| V1 | `noul` | Is the cited evidence a MEASUREMENT of the condition, or a restatement of it? |
| V2 | `noul` | Does the results artifact contain a scenario the harness EXCLUDES? |
| V3 | `noul` | Does any oracle in the evidence compare a value to itself or to a value derived from the code under test? |
| V4 | `noul` | Is there a test asserting the component's answers CHANGE A VERDICT (not merely that it answers)? |
| V5 | `score` | How many of the condition's clauses have a tool-result-bound proof? | `none/some/most/all` |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| V1 > 0.70 | **BLOCK** `RESTATEMENT_AS_PROOF` |
| V2 > 0.80 | **BLOCK** `ARTIFACT_CONTRADICTS_HARNESS` |
| V3 > 0.75 | **BLOCK** `TAUTOLOGICAL_ORACLE` |
| V4 > 0.70 | **BLOCK** `UNTESTED_INFLUENCE` |
| V5 = `none/some` | **DOWNGRADE** to NOT MET |

**WHY HERE:** this is where the build's 13-of-14 board was assembled. **V3 and V4 together would have failed the entire V6 build on its first verification.**

---

### FIREWALL 6 · THE TODO GATE — `todo.close`

**BLOCKS:** S-05 (a fix at one site), M-4 (a fix that did not land), S-22 (self-found fixes)

**FIRES:** when a pinned todo is closed.

**L1 · THE STATE:**
```
{
  "todo":          the item text,
  "declared_fix":  the file:line the agent claims changed,
  "disk_state":    the file content at that line NOW,
  "class_sites":   [grep of the same idiom/constant across the tree],
  "effect_probe":  [a command that shows the fix's BEHAVIOUR changed],
  "prior_round":   [was this item a finding in a previous round?],
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question |
|---|---|---|
| T1 | `noul` | Is the declared fix ACTUALLY PRESENT on disk (not merely claimed)? |
| T2 | `noul` | Does the same defect CLASS exist at other sites in the tree? |
| T3 | `noul` | Is there a probe showing the fix's EFFECT (not its presence)? |
| T4 | `noul` | Is this item a re-finding of a prior round's item (i.e. a fix that never landed)? |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| T1 > 0.90 | **BLOCK** `PHANTOM_FIX` |
| T2 > 0.70 | **BLOCK** `CLASS_NOT_SWEPT` — "fix the class, not the site" |
| T3 < 0.60 | **REQUIRE_EVIDENCE** — the effect probe |
| T4 > 0.70 | **LEDGER** `TREADMILL` + escalate the round counter |

**WHY HERE:** the build's four incomplete-landing classes (never applied / inert / one-site / over-corrected) all close as DONE. **T1 and T2 are the mechanical answer to `test_fix_effectiveness.py`'s IDEA — as a gate instead of a test.**

---

### FIREWALL 7 · THE ROUND BUDGET GATE — `audit.round`

**BLOCKS:** S-21 (the treadmill), M-4 (the fix loop as the finding source)

**FIRES:** on each audit round's completion.

**L1 · THE STATE:**
```
{
  "round":             n,
  "findings_by_sev":   {critical, high, medium, low},
  "findings_by_source":{code, own_prior_fix, probe_error, harness},
  "delta":             the change from round n-1,
  "landing_rate":      the fraction of prior fixes that TOOK EFFECT,
}
```

**L2 · THE JEV QUESTIONS:**
| id | type | question |
|---|---|---|
| B1 | `noul` | Are this round's findings predominantly DEFECTS IN THE PRIOR ROUND'S FIXES (not in the original code)? |
| B2 | `noul` | Is the finding count failing to trend down across rounds? |
| B3 | `score` | What is the measured landing rate of the prior round's fixes? | `poor/mixed/good/excellent` |

**L3 · THE THRESHOLDS:**
| question | action |
|---|---|
| B1 > 0.60 | **STEER** — "stop fixing; the fix process is the defect. Fix the landing." |
| B2 > 0.70 AND round > 5 | **REQUIRE_OPERATOR_RULING** — a non-convergent loop is a design defect, not a work item |
| B3 = `poor` | **BLOCK** the next round until the landing rate is measured and raised |

**WHY HERE:** the build ran **40 rounds** and its own ruling says *"condition 11 is not reachable by this process"*. **B2 would have escalated at round 5 instead of round 40 — saving ~70 commits and the entire second day.**

---

### FIREWALL 8 · THE SHIP GATE — `ship.authorize`

**BLOCKS:** the union — every pattern that reaches a ship claim

**FIRES:** before any ship/deploy/merge/primary-cutover claim.

**L1 · THE STATE:** the union of the seven prior states + the authority's full stop-condition list.

**L2 · THE JEV QUESTIONS:** the union of P/C/R/A/V/T/B (batched, one request) + three ship-specific:

| id | type | question |
|---|---|---|
| SH1 | `noul` | Does every stop condition's row cite a command whose output is quoted? |
| SH2 | `noul` | Does any condition read MET while its measurement was taken with a required component disabled or excluded? |
| SH3 | `score` | What is the measured COMPLIANCE against the authority the operator commissioned? | `none/low/partial/high` |

**L3 · THE THRESHOLDS:** any BLOCK from F1-F7 blocks the ship. **SH3 below `high` requires an explicit operator acknowledgement of the gap.**

---

## §3 · THE LEDGER (every decision, one row)

```json
{"ts":"2026-09-24T…","firewall":"F4.artifact","event":"commit.pre",
 "state_hash":"sha256(the L1 state)","question":"A1",
 "p":0.83,"threshold":0.75,"action":"BLOCK","token":"DOC_CONTRADICTS_LOG",
 "evidence":"doc says 0.058ms; EVIDENCE_STATE says the model ran off",
 "ledger_row":18442}
```

**THE LEDGER IS THE INSTRUMENT.** Its rows answer: *which firewall fired, on what state, with what probability, and what the code did.* **A firewall with no ledger row is unproven** — the same law the build violated with `_grade_fallback`.

---

## §4 · THE FAIL-CLOSED POLARITY TABLE

| the situation | the polarity | why |
|---|---|---|
| the state builder cannot read the artifact | **BLOCK** (named: `STATE_UNAVAILABLE`) | a missing substrate is never an ALLOW |
| Jev is unreachable | **BLOCK** (named: `JUDGE_UNAVAILABLE`) for the plan/ship gates; **LEDGER+PROCEED** for the reasoning gate | a critical gate fails closed; an advisory gate fails open and logs |
| Jev's probability is in the gray band (0.4-0.6) | **REQUIRE_EVIDENCE** | never a silent pass |
| the question set is empty or malformed | **BLOCK** | a gate that cannot ask is a gate that cannot stop |
| the artifact is newer than the claim | proceed | freshness is the point |

**THE RULE:** a gate on a CRITICAL path fails CLOSED; an ADVISORY gate fails OPEN and logs. **One global mode is either a frozen system or an unguarded one.**

---

## §5 · THE MINT PLAN (the waves, per `typesafe-jev-judge-wiring` + `jev-scale-judgment-pipeline`)

| wave | deliverable | the gate |
|---|---|---|
| **J1** | the **state builders** (8 pure functions, disk-read, unit-tested against fixtures) | each builder returns the same state for the same disk |
| **J2** | the **question sets** (40 questions, typed, versioned in code) | each question's answer is deterministic on a frozen state |
| **J3** | the **Jev transport** (one batched client; the wire format; the key resolver; the loud-fail on 401/timeout) | a live probe returns probabilities for all 40 questions in ONE request |
| **J4** | the **enforcers** (8 pure functions: probability → action; the ledger writer) | every threshold has a test that flips it |
| **J5** | the **host wiring** (the tool-call hook, the commit hook, the goal-verify hook, the todo hook) | a planted defect of each class is BLOCKED in a live session |
| **J6** | **the origin replay** — re-run the V6 build's 92 findings through the firewalls | **every critical finding is BLOCKED by ≥1 firewall** |

**THE J6 GATE IS THE ACCEPTANCE TEST:** if the firewalls cannot block the 92 findings this project produced, they are documentation. **The origin replay IS the proof.**

---

## §6 · THE HONEST LIMITS (what a firewall CANNOT do)

| limit | why | the mitigation |
|---|---|---|
| **a private reasoning token cannot be hard-blocked on every host** | not all runtimes expose a stream hook | LEDGER + STEER only; never a hard block on a thought |
| **Jev measures the state it is given** | a bad state builder yields a confident wrong answer | the state builders are pure and unit-tested; the state is DISK-READ, never agent-reported |
| **a threshold is a judgement** | 0.75 is a choice | every threshold carries its cost matrix and a calibration run |
| **a firewall cannot know the operator's intent** | a legitimate deviation looks like drift | the gray band REQUIRES evidence; the operator rules |
| **a gate that fires on everything is as broken as one that never fires** | alert fatigue disables gates | the origin replay measures both false-positive and false-negative rates |

---

## §7 · THE ONE-LINE SUMMARY

> **Every firewall is the same shape: a pure function reads the ARTIFACT from disk (never the agent's claim), Jev measures the artifact against a fixed typed question (never an opinion about the agent), and pure code acts on the probability (never a warning).**
>
> **The model is never asked to grade itself, and the gate never accepts a form where it can only check content.**

---

# §8 · THE MERGED CORPUS — 87 CLASSES, 14 GROUPS (the reconciled denominator)

**The source:** two independent scouts over 16 corpus files + 2 streamed sessions (135MB + 52MB),
plus the master 57. **The census:** `57 master (KIND P 14 phrase + D ~21 doctrine + M ~25
mechanical) + 30 NEW (misfire/lifecycle/probe/dodge) = 87 CLASSES ACROSS 14 GROUPS`.

```
GROUP                     COUNT  THE LAYER THAT OWNS IT                     THE KILL
[A] THEATRICAL             26    L2 close-gate                              spec_satisfied
[B] SPEC/SCOPE             11    L2 edit-gate                               spec_item_count
[C] SELF-JUDGE              8    L2                                         self_certified
[D] AUDIT-GAMES             9    L1 facts (the count TREND) + L2            the trend fact
[E] DOC                     7    L1 facts                                   the doc/src ratio
[F] GATE-BLIND             15    L1 facts                                   the fireability
[G] UNWIRED                16    ★ L1 facts (F-GIT.callers)                 callers == 0
[H] STALE/DEPLOY            6    L1 facts                                   observedAt
[I] FALLBACK                5    L1 facts                                   the artifact sha
[J] PROSE-ENFORCE           6    L2                                         the judgment
[K] EVIDENCE                5    L1 facts                                   the `source` field
[L] MISFIRE-NEW            13    ★ L1 (the DELTA GATE) + the channel fact   no fact delta
[M] PROBE-NEW               4    L1 facts                                   pwd + the control
[N] PROCESS-NEW            14    L1 facts                                   the deploy contract
```

**★ THE RELATION TO §2's FIREWALLS:** the 6 macro + 25 fine patterns in
`MACRO_FAILURE_PATTERNS.md` are a SUBSET — they are the PLUTUS V6 campaign's own instances.
The 87 classes are the cross-project union. **EVERY ONE OF THE 87 MAPS TO A FIREWALL OR A
FACT COMPARISON — NONE REQUIRES A PHRASE MATCH.**

---

# §9 · THE DURABLE-FACT L1 (the state builder, formalized)

**§2's L1 says "the state builder reads disk". THIS IS THE FORMALISM — and it is what makes
the misfire class impossible.**

## §9.1 · THE FACT ROW (every row carries its own provenance)

```ts
interface FactRow {
  id: string;
  cls: "F-GIT"|"F-ART"|"F-PROC"|"F-TEST"|"F-SPEC"|"F-TODO"|"F-DEPLOY"|"F-RUN";
  key: string;            // "HEAD" | "diff" | "sha" | "exit" | "open_items" | ...
  value: string | number; // the OBSERVED value
  source: string;         // ★ THE COMMAND that produced it — the provenance
  observedAt: number;     // ★ FRESHNESS IS PART OF THE FACT
  scope: string;          // ★ the root the observation applied to
}
```

## §9.2 · THE 17 FACT CLASSES (each observed by ONE command)

| cls | key | THE COMMAND | WHAT IT PROVES |
|---|---|---|---|
| F-GIT | HEAD | `git rev-parse HEAD` | the tree's identity |
| F-GIT | diff | `git diff --name-only <ref>` | what CHANGED |
| F-GIT | state | `git status --porcelain` | what is DIRTY |
| F-GIT | blame | `git blame -L n,m <file>` | WHO wrote the line |
| F-GIT | callers | `grep -rn '<sym>' <src>` | **WHO CALLS IT (the reachability)** |
| F-ART | sha | `sha256sum <file>` | the artifact's identity |
| F-ART | mtime | `stat -c %Y <file>` | WHEN it was written |
| F-ART | size | `stat -c %s <file>` | how much is there |
| F-PROC | pid | `pgrep -f <pat>` | the live process |
| F-PROC | start | `stat /proc/<pid>` | WHEN the process was born |
| F-PROC | held | the module's fd | WHAT the process HOLDS |
| F-TEST | cmd | the captured argv | the exact command |
| F-TEST | exit | `$?` | the code |
| F-TEST | output | the captured bytes | the raw result |
| F-SPEC | text | `sed -n '<range>p' <spec>` | the requirement, verbatim |
| F-TODO | open | the todo store + bug ledger | the OPEN rows |
| F-DEPLOY | live | `sha256sum <deployed>` vs `<src>` | the match/mismatch |
| F-RUN | tick | a heartbeat row + ts | liveness |

## §9.3 · THE FOUR GATES THAT MAKE A FACT TRUSTWORTHY

```
① OBSERVED   every row carries `source` = the exact argv. A fact without its command is a
             CLAIM and the store REFUSES it.
② IMMUTABLE  append-only. The agent cannot edit a fact; it can only cause a new observation.
             THE HISTORY IS THE RECORD.
③ FRESH      every row carries `observedAt`. A fact older than the phase boundary is FLAGGED
             STALE and the judge is told (never used silently).
④ SCOPED     every row carries the root. A fact about tree A is NEVER used on tree B.
```

## §9.4 · ★ THE DELTA GATE — THE MISFIRE KILL (the operator's core demand)

```
A JUDGMENT IS REQUESTED IFF A FACT ROW WAS APPENDED SINCE THE LAST JUDGMENT.

  the agent writes "let me start with the structure"   -> NO FACT ROW -> NO JUDGMENT -> NO ABORT
  the agent edits src/gate/provenance.ts               -> F-GIT.diff row -> JUDGMENT

★ A SESSION THAT TALKS PRODUCES ZERO FACTS. THE ENTIRE MISFIRE CLASS IS DEAD BY CONSTRUCTION.
★ MEASURED (the PBK v3 ledger): 1166 rows fired on prose; ~90 firings in one session's tail
  were benign planning sentences. THE DELTA GATE MAKES EVERY ONE OF THEM IMPOSSIBLE.
```

---

# §10 · THE 30 NEW CLASSES (what the 6+25 missed — the misfire/lifecycle/probe/dodge family)

**These are NOT in `MACRO_FAILURE_PATTERNS.md`. Each was measured in a live session. They are
the classes the ENFORCEMENT ITSELF produced.**

```
N1  HOST-TEXT AS AGENT TEXT   a todo-done notice / a task-completed / an xd-notice scored as
                              the agent's own utterance. THE FACT: the ROLE.
N2  USE-MENTION               a QUOTED trigger fires (docs about the rules).
N3  DISCARD-DESTROYS          the span is deleted BEFORE it is recorded (18 of 22 lost).
N4  POLARITY                  "NOT verified" reads as the assertion.
N5  INFLECTED-MISS            "completed" escapes "complete".
N6  INTERFACE-NAME            a `goal.complete` INTERFACE fires the claim rule.
N7  RATE                      22/37 -> 24/42 -> 24/74: the firing rate climbing.
N8  ACCUSATION-QUOTE          "You are declaring..." fires.
N9  AUTHORITY-SPOOF           `sendUserMessage` arrives as role:user ("supersedes").
N10 PACKAGE-RENDER            `display:true` vs the native `display:false` + details.
N11 GOAL-BREAK                `abort()` ignoring `interruptMode:"never"`.
N12 NO-HOT-CONTROL            the ESM cache; no live off switch.
N13 PARKED-FIRES              the rules dir EMPTY yet firings arrive.
N14 UNREACHABLE-REMEDY        the gate names a remedy it cannot execute.
N15 DEPLOY-CONTRACT           no default export -> the deploy loads NOTHING.
N16 STALE-HANDOFF             58L aa8d1d3d vs 74L 6e3b6215.
N17 BLIND-TRIPLE              scope-drift + count-loss + 429 -> a PASS.
N18 TSC-SCOPE                 `tsc` includes only SEAM -> a planted error passes.
N19 ABORT-NULL                `proseAction`'s lastSignature ALWAYS equals sig.
N20 REIMPL                    a second implementation (the spec's banned class).
N21 INVENTED-SCHEMA           "noul" vs boolean/choice/score.
N22 FIXTURE-ENSHRINED         the test encodes the defect.
N23 UNWIRED                   attachChain / createSessionTracking / markReady dead.
N24 OVER-BREADTH              a heredoc STRING + a 68L file treated as generic.
N25 UNFALSIFIABLE-INDEX       a sentinel-0 the corpus cannot falsify.
N26 NO-ESCAPE                 the guardians masked; an eval hole.
N27 DODGE-UNARMED             8x "absent/idle" as NOT-avoidance.
N28 PROBE-BODY-UNREAD         the probe reads a field the loader never sets.
N29 CWD-DRIFT                 a persisted `cd` moves every measurement.
N30 PROBE-ERROR-AS-DEFECT     a hand-built regex produces a false defect.
```

**★ THE 30's COMMON ROOT (the through-line):**
> **THE ENFORCEMENT LAYER HAD NO NOTION OF PROVENANCE.** It scored TEXT, not ACTORS; it
> compared BYTES, not FACTS; it had no ROLE, no CHANNEL, no TURN BOUNDARY, and no external
> judge. **THE L1 FACTS CARRY EXACTLY THOSE FOUR: the SOURCE command, the SCOPE, the
> OBSERVED-AT, and the ROLE (who wrote it).**

---

# §11 · THE JEV-TREE — THE L0/L1/L2 OWNERSHIP MAP (from the Paragon kernels)

**The measured Paragon shape, reconciled with §2's eight firewalls:**

```
L0 · THE SPAN LAYER (BEFORE any discard):
     · the span sidecar (record BEFORE the discard — N3)
     · the inflection expansion (N5: exit vs exits)
     · the telemetry (N7: the firing rate)
     · ★ THE ROLE FILTER (N1: is this the agent's voice or a host message?)
     · the parked-inert check (N13: the rules dir EMPTY yet firings arrive)
     · the sentinel + the interruptMode honouring (N11, N12)
     · THE NATIVE PEDIGREE (customType `ttsr-injection` · display:false ·
       attribution:agent · details{rules,confidence,sourceKind,span}) — N9, N10

L1 · THE EDIT JUDGE (per FACT DELTA, ~100ms, act 0.8 / flag 0.5):
     · quote-vs-claim (N2)      · polarity (N4)       · interface-vs-claim (N6)
     · own-voice (N1)           · shape-freeze (N22)
     · orphan / first-call / live-path (N23 — the three reachability facts)

L2 · THE CLOSE-GATE (per turn, FAIL-CLOSED):
     · premature-done · green-without-liveness · library-as-system · spec-drop
     ★ ALL bound to THIS-TURN spans; FAIL-CLOSED; the verdict binds to the fact

THE PROBE LAYER (the instrument's own validity):
     · the known-effect control (N28) · pwd (N29) · the Side-A adjudication (N30)
     · the scope declaration (source | container | host-live)
     · ★ THE REAL-HANDLER DRIVE (N19: the test must drive the PRODUCTION path)
```

---

# §12 · THE FIVE VERDICTS + THE 12 FROZEN NODES

## §12.1 · THE VERDICT VOCABULARY (the close-gate's output — §2 named four; here are five)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  PASS          every node answered in the passing band  -> THE TURN CLOSES        │
│  REJECT        a node failed its act threshold          -> BLOCKED; comply        │
│  FABRICATED    the claim CONTRADICTS a fact             -> THE CLAIM IS FALSE;    │
│                                                           the token names the     │
│                                                           exact mismatch          │
│  FAIL_CLOSED   NO verdict was obtainable                -> BLOCKED.               │
│                                                           ★ A MISSING JUDGE IS    │
│                                                             NEVER A PASS          │
│  WRONG_SPAN    the judge read the wrong thing           -> re-derive ONCE; a      │
│                                                           second = FAIL_CLOSED   │
└──────────────────────────────────────────────────────────────────────────────────┘
★ §4's FAIL-CLOSED POLARITY TABLE IS THE SAME LAW — THIS IS ITS VERDICT VOCABULARY.
```

## §12.2 · THE 12 FROZEN NODES (code constants — the agent cannot add, remove, or rewrite one)

| the 6 EDIT nodes (L2a, per fact delta) | the token | the §2 firewall |
|---|---|---|
| `spec_satisfied` | `SPEC_NOT_MET` | F1 plan, F2 contract |
| `claim_scope_matches` | `CLAIM_OUTRUNS_EVIDENCE` | F3 reasoning, F4 artifact |
| `self_certified` | `SELF_CERTIFIED_PASS` | F3 reasoning |
| `tests_cover_diff` | `TESTS_MISS_THE_DIFF` | F5 verification, F6 todo |
| `finding_disposition` | `FINDING_IGNORED` | F6 todo, F7 round-budget |
| `claim_contradicts_state` | `CLAIM_CONTRADICTS_STATE` | F4 artifact, F5 verification |

| the 6 CLOSE nodes (L2b, the terminal gate) | the token |
|---|---|
| `every_spec_item_delivered` | ALL_DELIVERED / PARTIAL / NONE / NOT_ADDRESSED |
| `deploy_is_current` | `DEPLOY_STALE` |
| `evidence_is_external` | `SELF_JUDGED` |
| `runtime_observed` | `RUNTIME_UNPROVEN` |
| `bugs_all_dispositioned` | `BUGS_UNDISPOSITIONED` |
| `claim_is_measurable` | `CLAIM_UNMEASURABLE` |

## §12.3 · THE STATE — assembled by code, every field a FactRow, the agent types nothing

```
spec_requirement←F-SPEC   spec_item_count←F-SPEC   delivered_sha←F-ART
changed_files←F-GIT       file_callers←F-GIT       test_command←F-TEST
test_exit←F-TEST          test_imports←F-GIT       open_items←F-TODO
deploy_live_sha←F-DEPLOY  deploy_src_sha←F-DEPLOY  proc_start←F-PROC
verifier_author←F-GIT.blame:test   subject_author←F-GIT.blame:src
```

---

# §13 · THE MEASURED EVIDENCE — THE ORIGIN REPLAY'S SECOND CORPUS (the PBK v3 defects)

**§5's J6 gate says: "re-run the V6 build's 92 findings through the firewalls; every critical
finding is BLOCKED by ≥1 firewall." HERE IS A SECOND, INDEPENDENT REPLAY CORPUS — measured
today, in a different tree, by two black-hat auditors.**

```
THE DEFECT                                              THE FIREWALL THAT CATCHES IT
──────────────────────────────────────────────────────  ──────────────────────────────────
3 CAPABILITIES DECLARED, TESTED, NEVER CALLED            F2 (C1: a producer with ZERO
  (the lint runner · the ledger sink · postAction)         consumers) -> BLOCK
                                                          ★ THE EXACT CLASS §2's C1 NAMES
TWO INCOMPATIBLE `LedgerRow` CONTRACTS                   F2 (S-14/S-13 class)
  (the seam's 8 flat fields vs the writer's 3 nested)      -> BLOCK PRODUCER_WITHOUT_CONSUMER
`deriveBand` COMPUTES `neg` AND NEVER READS IT           F5 (V3: a tautological oracle)
  (the band's discriminating input, discarded)            -> BLOCK TAUTOLOGICAL_ORACLE
THE ZERO-MARGIN BAND (high = max(pos) = the single-      F7 (B3: the landing rate) + the
  hit score -> ANY hit aborts)                             calibration law
A TEST PASSING A DIFFERENT INPUT THAN THE CALLER         F5 (V1: restatement-as-proof)
  (the lastSignature bug — 33 tests green, the             -> BLOCK RESTATEMENT_AS_PROOF
   production path always null)                          ★ §2's V1 IS THIS EXACT DEFECT
A GREEN SUITE OVER DEAD WIRING (35 pass, 3 modules        F5 (V5: how many clauses have a
  never invoked)                                           tool-result-bound proof) -> DOWNGRADE
THE UNRUN DETECTOR (the firewall's own D1/D2/D5 pass      F6 (T3: a probe showing the fix's
  while 3 capabilities are unwired)                        EFFECT) -> REQUIRE_EVIDENCE
```

**★ THE SIGNIFICANCE:** the V6 corpus and the PBK v3 corpus are DIFFERENT PROJECTS with the
SAME DEFECT CLASSES. **A firewall design validated on ONE origin can be overfit to it; validated
on TWO INDEPENDENT origins, it is a LAW.** §5's J6 must replay BOTH.

---

# §14 · THE MECHANICAL/SEMANTIC SPLIT (the free layer — build it first)

```
MECH-NOMODEL (a predicate over disk — NO model needed, ZERO cost):
  the whole of F (blind-gates) · G (unwired) · H (stale) · I (fallback-artifact)
  J03 J05 J07-J11 J14 J15 J17 · L (hygiene) · M (dispatch) · the floors/caps
  ★ ~70 OF THE 87 CLASSES. A sha compare, a grep count, a diff, an mtime, an exit code.

SEM-NEEDS-MODEL (Jev, Noul/Choice/Score, ~100ms):
  A (theatrical claims) · B (scope) · C (unanchored) · D (weakened checks)
  J02 J04 J06 J12 J13 J16 · K02 K03
  ★ ~48 OF THE 87. THESE NEED THE JUDGE.

★★ THE BUILD ORDER: THE MECHANICAL LAYER FIRST. It is FREE, it is DETERMINISTIC, and it
   covers the majority. The semantic layer pays ~100ms per fact delta and covers the rest.
   ★ A GATE THAT NEEDS NO MODEL CANNOT BE PROMPT-INJECTED, CANNOT DRIFT, AND CANNOT HALLUCINATE.
```

---

# §15 · THE ADDENDUM TO THE MINT PLAN (§5)

| wave | deliverable | the gate |
|---|---|---|
| **J1a** | **the fact store** (`src/facts/store.ts`: append-only rows + the DELTA GATE) | a benign span appends ZERO rows; an edit appends ONE |
| **J1b** | **the observers** (`src/facts/observe.ts`: the 17 classes, one shelled command each) | each observer's row carries its `source` argv |
| **J1c** | **the state builders** (8 pure functions, disk-read — §5's J1) | each builder returns the same state for the same disk |
| **J2** | the question sets (the 12 frozen nodes + §2's ~40 questions, typed, versioned) | each answer is deterministic on a frozen state |
| **J3** | the Jev transport (§5's J3) | a live probe returns probabilities in ONE request |
| **J4** | the enforcers (probability → action; the 5 verdicts; the ledger writer) | every threshold has a test that flips it |
| **J5** | the host wiring (the tool-call hook, the commit hook, the goal-verify hook, the todo hook) | a planted defect of each class is BLOCKED live |
| **J6** | **THE DOUBLE ORIGIN REPLAY** — the V6 92 findings AND the PBK v3 defects | **every critical finding is BLOCKED by ≥1 firewall in BOTH corpora** |

**★ J6 IS NOW A TWO-CORPUS GATE. A firewall that blocks the V6 findings but not the PBK v3
findings is overfit; one that blocks BOTH is a law.**
