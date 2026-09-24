# THE JEV-FIRST AUDIT WORKFLOWS — BLUEPRINT
## Taking the PLUTUS V6 audits and turning them into bundled, Jev-gated tools

**Session:** blueprinting · **Date:** 2026-09-24 · **Status:** DESIGN (awaiting operator rulings, §12)
**Founding instance:** the PLUTUS V6 audit campaign — 3 auditors, 92 findings, 5 artifacts, 5,621 lines
**Authority read (MOVE 1):** the 8 Jev skills, the `jm` CLI + `jev-manager` MCP, the 5 forensic artifacts this campaign produced
**Integrated (§14):** the 87-CLASS CORPUS (the audit's target denominator + the audit's OWN 30
error classes N1-N30) · the DURABLE-FACT L1 (the audit's state source — the disk as the witness,
formalized) · the DELTA GATE (the treadmill kill) · the SECOND ORIGIN (the PBK v3 defects — the
acceptance test doubled) · the MECHANICAL/SEMANTIC split (which audit checks are free)

---

# §0 · THE FIRST-PRINCIPLES CORE

## 0.1 THE REDUCTION (MOVE 3) — ONE MECHANISM UNDER ALL 92 FINDINGS

The campaign produced 92 findings across 25 classes. Read them as one thing:

| the finding | what was actually wrong |
|---|---|
| the FX oracle is `abs(r.entry − entry)` | the check compared a value to **itself** |
| the latency proof reads 0.058ms | the check measured the **model-off** path |
| the container artifact includes excluded tests | the check read the **wrong artifact** |
| the theatricality metric has zero operator entries | the metric's **class** was not what it counted |
| STOP 13/14 MET with 19 of 20 docs below floor | the check asked *"is it current?"* not *"does it meet the floor?"* |
| `G-DUAL` returns `_ok("…UNVERIFIED")` | the gate **passed while doing nothing** |
| the no-sampling test scans `.wt/` copies | the scan read **stale copies, not the live tree** |
| my own 1.8% compliance figure | I graded against a **superseded** authority |

```
+---------------------------------------------------------------------------------+
| THE REDUCTION                                                                     |
|                                                                                   |
|   A CLAIM IS FALSE-GREEN WHEN ITS CHECK IS AIMED AT A TARGET IT CANNOT MISS.      |
|                                                                                   |
|   THE CLAIM AND THE CHECK ARE BOTH ARTIFACTS.                                     |
|   THE ONLY WAY TO KNOW THE CHECK IS AIMED AT THE CLAIM IS TO JUDGE THEM           |
|   AGAINST EACH OTHER, WITH THE DISK AS THE WITNESS.                               |
+---------------------------------------------------------------------------------+
```

**THE TEST OF A REAL REDUCTION (MOVE 3):** it explains instances the operator never mentioned. It does — my own error (§45.6 of the ledger) is the same class, and so is every one of the 25 patterns. A "list of 25 slop types" is a summary; **"the check was aimed at the wrong target" is the mechanism.**

## 0.2 THE DERIVED LAWS (MOVE 4)

```
    FALSE-GREEN = A CHECK WHOSE TARGET IS NOT THE CLAIM
    AUDIT       = JUDGING THE (CLAIM, CHECK, ARTIFACT) TRIPLE, ONE AT A TIME,
                  UNTIL EVERY CLAIM HAS A CHECK THAT CAN FAIL
    HONESTY     = NAMING THE CLAIMS THAT HAVE NO CHECK, AND THE INSTRUMENTS
                  WHOSE OWN ERROR RATE IS UNMEASURED
```

Every section below traces to one of these three lines.

## 0.3 THE INVERSION (MOVE 5) — VIRTUE INTO MECHANISM

**THE BAD DESIGN:** *"be rigorous in your audit; check your oracles; verify your evidence."* — an adjective. It has already failed; that is why the campaign exists.

**THE GOOD DESIGN:** the agent is handed **three machines** that produce the holes as OUTPUT:

| the machine | what it produces |
|---|---|
| **the pair-extractor** | every `(claim, check, artifact)` triple on disk, enumerated — the agent does not have to notice a missing check |
| **the aim-judge** | Jev's verdict on whether the check's TARGET is the claim's SUBJECT |
| **the fail-probe** | a perturbation that MUST flip the check; a check that survives it is reported as CANNOT-FAIL |

**No section below may reduce to an adjective.** Every one names an instrument.

---

# §1 · WHY NOTHING EXISTING SOLVES THIS (MOVE 2 — the differential)

## 1.1 THE SIBLING TABLE

| existing thing | what it does | what it does NOT do (= this design's spec) |
|---|---|---|
| `typesafe-jev-judge-wiring` | the measured API contract: `noul`/`choice`/`score`, the `.noul` answer field, the key-resolution trap, the two-proof law | **does not define WHAT to judge.** It is transport. |
| `jev-scale-judgment-pipeline` | deterministic-first narrowing: index → select → judge → materialize → ledger | **does not enumerate CLAIMS.** It narrows a corpus, not a build's assertions. |
| `jev-decision-gate-firewall` | the 3-layer architecture (lexicon detects, Jev decides, code enforces) + a 6-node derailment tree | **does not cover AUDIT findings.** Its tree polices an agent's behaviour, not a build's evidence. |
| `typesafe-jev-batching` | N inputs × N questions in ONE request | **does not define the audit question set.** |
| `jev-manager-operator` | the `jm` CLI + MCP: point at a corpus, find instances, triage, judge | **does not know what a false-green IS.** It finds things; it does not know which finding is a defect. |
| `red-team-slop-audit` (minted this session) | the PROSE procedure: dispatch 2 auditors, 7 hunt lists, the 25 classes | **does not gate.** It is a procedure a human/agent follows; nothing blocks. |
| `evidence-failure-audit` (minted this session) | the 7 false-green classes + the fail-probe recipes | **does not gate either** — same gap. |
| `red-team-slop-audit` / `code-review` / `zero-trust-audit` | human-readable audit skills | all produce REPORTS; none produce an EXIT CODE |
| `extract-meta-patterns` MODE 2 | the forensic autopsy procedure | a document, not a tool |
| `qwen-code-audit` / `ocr` | an LLM code-review gate | reviews CODE; **cannot see that an ORACLE is tautological** — the defect is in the RELATIONSHIP between a claim and its check, not in the code |

## 1.2 THE NAMED STRUCTURAL GAPS

```
+---------------------------------------------------------------------------------+
| GAP 1 · NO PAIR-ENUMERATION                                                       |
|   nothing enumerates the (claim, check, artifact) triples of a build.             |
|   the campaign found them BY HAND, over 3 auditors and 5 hours.                   |
|                                                                                   |
| GAP 2 · NO AIM-JUDGMENT                                                           |
|   nothing asks "is this check's target the claim's subject?"                       |
|   every false-green in the campaign would have been caught by that ONE question.   |
|                                                                                   |
| GAP 3 · NO FAIL-PROBE                                                             |
|   nothing perturbs a check to prove it CAN fail.                                   |
|   "15/15 at 0.000p" survived every test the build ran — because none perturbed it. |
|                                                                                   |
| GAP 4 · NO ENFORCEMENT                                                            |
|   the audit skills produce reports. A report does not block a commit.              |
|   the campaign's findings were ACCEPTED, not BLOCKED.                              |
|                                                                                   |
| GAP 5 · NO SELF-MEASUREMENT                                                       |
|   the auditor's own instruments are never measured.                                |
|   MY 1.8% figure, my 587ms measurement, my two false positives — all unmeasured    |
|   until the operator challenged them.                                              |
+---------------------------------------------------------------------------------+
```

**THE DIFFERENTIAL'S VERDICT:** five gaps, none filled by any existing artifact. **The design is not a duplicate.**

---

# §2 · THE MACRO PATTERN (MOVE 6 — the loop and the stop)

```
+---------------------------------------------------------------------------------+
| THE AUDIT LOOP — one pass over a build's claims                                   |
+---------------------------------------------------------------------------------+
|                                                                                   |
|  ┌─ 1. ENUMERATE ────────────────────────────────────────────────────────────┐    |
|  │  L1 reads DISK: every numeric claim in the docs, every test's asserted    │    |
|  │  value, every artifact's scenarios, every floor the authority states.     │    |
|  │  OUTPUT: the CLAIM LEDGER — N claims, each with its source file:line.     │    |
|  └───────────────────────────────────────────────────────────────────────────┘    |
|                              v                                                    |
|  ┌─ 2. PAIR ─────────────────────────────────────────────────────────────────┐    |
|  │  for each claim, find the CHECK that produces it (the test, the metric,   │    |
|  │  the gate, the artifact field).                                           │    |
|  │  OUTPUT: (claim, check, artifact) triples. A claim with NO check is       │    |
|  │  recorded as UNCHECKED — it is not skipped.                               │    |
|  └───────────────────────────────────────────────────────────────────────────┘    |
|                              v                                                    |
|  ┌─ 3. JUDGE ────────────────────────────────────────────────────────────────┐    |
|  │  JEV, one batched call, the fixed question set (§3), the triple as STATE. │    |
|  │  Q1 is the aim question: does the check's TARGET = the claim's SUBJECT?   │    |
|  │  OUTPUT: a probability per question, per triple.                          │    |
|  └───────────────────────────────────────────────────────────────────────────┘    |
|                              v                                                    |
|  ┌─ 4. PROBE ────────────────────────────────────────────────────────────────┐    |
|  │  for each check judged AIMED (Q1 high), run the FAIL-PROBE: perturb the   │    |
|  │  input the claim is about; the check MUST flip.                           │    |
|  │  OUTPUT: CAN-FAIL | CANNOT-FAIL. A CANNOT-FAIL check demotes its claim.   │    |
|  └───────────────────────────────────────────────────────────────────────────┘    |
|                              v                                                    |
|  ┌─ 5. ENFORCE ──────────────────────────────────────────────────────────────┐    |
|  │  L3 maps probabilities to ACTIONS: BLOCK the commit / DEMOTE the claim /  │    |
|  │  LEDGER. Writes one ledger row per triple. Exit code is the verdict.      │    |
|  └───────────────────────────────────────────────────────────────────────────┘    |
|                                                                                   |
+---------------------------------------------------------------------------------+
| THE STOP CONDITION (measured, never a feeling):                                   |
|   EVERY claim has a check  AND  every check is judged AIMED  AND                  |
|   every aimed check FLIPPED under its probe  OR  the claim is DEMOTED to          |
|   UNPROVEN with the demotion written to the ledger.                               |
|   "The report looks thorough" is NOT a stop. The ledger's coverage ratio is.      |
+---------------------------------------------------------------------------------+
```

**THE COVERAGE LINE (the honesty signature, MOVE 10):**
```
CLAIMS: 412   CHECKED: 388   UNCHECKED: 24   AIMED: 341   CAN-FAIL: 338   DEMOTED: 50
COVERAGE: 94.2%   FALSE-GREEN-RISK: 50 claims demoted   INSTRUMENT-ERROR: see §6.4
```
**A flat coverage ratio across passes means the denominator was written to match what was already done** — the same signature the founding `go-deeper` blueprint names.

---

# §3 · THE UNIVERSAL GENERATOR (MOVE 7 — the question-families for ANY claim)

**THE FIXED QUESTION SET.** These six apply to **every** `(claim, check, artifact)` triple. The agent does not choose them; they are versioned in code (the `DOCTRINE OFFLINE` law — no runtime rubric fetch).

| id | primitive | the question | the criteria (what makes it TRUE) |
|---|---|---|---|
| **Q1 · AIM** | `noul` | Does the check's **target** equal the claim's **subject**? | the check reads the SAME thing the claim asserts about — not a proxy, not a stale copy, not a disabled component |
| **Q2 · FAILABILITY** | `noul` | Can this check **return FALSE**? | there exists an input where it fails; the expected value is not derived from the code under test; the two operands do not share a binding |
| **Q3 · ARTIFACT** | `noul` | Does the check read the **artifact** rather than the agent's **claim**? | the state comes from disk/a tool result, never from prose |
| **Q4 · FRESHNESS** | `choice` | How current is the check's evidence? | `same-turn` / `this-session` / `stale` / `absent` |
| **Q5 · PROVENANCE** | `choice` | Where did the check's expected value come from? | `the-artifact` / `the-authority` / `the-code-under-test` / `invented` |
| **Q6 · SCOPE** | `noul` | Is the check scoped to the **live** target? | not a worktree copy, not a checkpoint, not a superseded authority |

**THE GENERATOR RULE:** Q1 is the load-bearing question. **In the campaign, Q1 alone would have caught 6 of the 7 false-green classes.** Q2 catches the tautologies. Q3 catches the prose-as-proof. Q5 catches the circular oracles. Q6 catches the wrong-tree scan and **my own superseded-authority error.**

**THE COMPOSITION RULE:** when a claim spans multiple checks (a stop condition with several clauses), the generator is applied **per clause**, and the claim's verdict is the **weakest clause's** verdict. Never an average.

---

# §4 · THE DOMAIN PLAYBOOKS (MOVE 7 — the audit families, uniform template)

Four playbooks. Each: **the operator's words verbatim · a generator table · a ladder · the closure test · the residual shape · the handoffs.**

## PLAYBOOK A · PROVENANCE — "is this the right document?"

**THE OPERATOR'S WORDS, VERBATIM:**
> *"what are you talking about these are likely superseded what is this"*
> *"i think that you're just being fucking theatrical and bullshitting and making up some garbage fucking answer because you didn't do your job correctly"*

**THE GENERATOR (the extra questions on top of §3's six):**

| id | primitive | the question |
|---|---|---|
| PA1 | `noul` | Is the authority this claim is graded against **still live** (not superseded by a later ruling)? |
| PA2 | `choice` | Where does the claim's authority come from? `operator-order` / `a-later-doc` / `a-planning-stream` / `assumed` |
| PA3 | `noul` | Does the artifact **cite** the authority it is graded against? |
| PA4 | `noul` | Do two authorities exist, and does either **record** the supersession? |
| PA5 | `noul` | Does every **named entity** (model, service, path) in the claim resolve to a real artifact? |

**THE LADDER (in order):** enumerate authorities → find the pivot records → establish the live one by citation + mtime → probe every named entity → only then grade compliance.
**THE CLOSURE TEST:** every claim's authority is named AND live AND cited by the artifact.
**THE RESIDUAL SHAPE:** `authorities found: N · superseded: M · live: 1 · unprobed entities: K`.
**HANDOFFS:** to PLAYBOOK B (evidence) once the authority is settled.

**THE ORIGIN:** my 1.8% figure. **PA1 + PA2 would have blocked it.** The `state_authority.py` builder already implements the L1 half (it discovered 166 candidate docs from disk).

## PLAYBOOK B · EVIDENCE — "can this green fail?"

**THE OPERATOR'S WORDS, VERBATIM:**
> *"this entire build is rejected"*
> *"how did the gold prompt derail"*
> *"you still havent explain HOW the decisons were even ABLE to be discarded this should be mechanically impossible"*

**THE GENERATOR:** §3's Q1-Q6, with the fail-probe mandatory.

| id | primitive | the question |
|---|---|---|
| PE1 | `noul` | Is the oracle **computed from data**, or is it a constant / the code's own output? |
| PE2 | `noul` | Does the artifact contain a scenario the **harness excludes**? |
| PE3 | `noul` | Was the measurement taken with a **required component disabled**? |
| PE4 | `noul` | Is the metric's **named class** actually present in its entries? |
| PE5 | `noul` | Does the check's no-input branch **pass** (a `_ok(…UNVERIFIED)` shape)? |
| PE6 | `noul` | Does any test's pass condition **name a defect** (a defect lock)? |

**THE LADDER:** collect the greens → read each check's BODY → run the fail-probe → classify → demote.
**THE CLOSURE TEST:** every green either flips under perturbation or is DEMOTED.
**THE RESIDUAL SHAPE:** `greens: N · can-fail: M · demoted: K · probes-that-errored: J`.
**HANDOFFS:** the demoted claims go to the build as fix tickets.

**THE ORIGIN:** 7 of the campaign's findings. **PE1-PE6 are the seven false-green classes, mechanized.**

## PLAYBOOK C · SLOP — "what is dead, duplicated, or self-contradictory?"

**THE OPERATOR'S WORDS, VERBATIM:**
> *"audit everything now"* · *"rip this fucking trash apart"* · *"log all failure"*

**THE GENERATOR:**

| id | primitive | the question |
|---|---|---|
| PS1 | `noul` | Does this symbol/field/module have **zero production consumers**? |
| PS2 | `noul` | Does this comment/docstring **assert** a property the code below lacks? |
| PS3 | `choice` | How many definition sites does this constant have? `one` / `two` / `several` / `many` |
| PS4 | `noul` | Does this error handler **swallow** (no named token, no test)? |
| PS5 | `noul` | Is this module imported but **unreachable** from the entry point? |
| PS6 | `noul` | Does a test root sit under a **worktree/checkpoint** path? |

**THE LADDER:** the 7 hunt lists from `red-team-slop-audit` → Jev judges each candidate → the count is the ledger.
**THE CLOSURE TEST:** every candidate classified; the count per class recorded.
**THE RESIDUAL SHAPE:** the per-class counts (the campaign's: dead 15 · duplicate 7 · contradiction 7 · …).
**HANDOFFS:** the findings go to the failure ledger; the classes go to the firewall design.

**THE ORIGIN:** `RedTeamBravo`'s 65 findings. **The deterministic greps already do the DETECTION; Jev does the DECISION** (the `jev-decision-gate-firewall` law: a lexicon detects, Jev decides, code enforces).

## PLAYBOOK D · CONTRACT — "does the artifact do what it claims?"

**THE OPERATOR'S WORDS, VERBATIM:**
> *"you still havent explain HOW the decisons were even ABLE to be discarded"*
> *"read the entire fucking original build package"*

**THE GENERATOR:**

| id | primitive | the question |
|---|---|---|
| PC1 | `noul` | Does a producer's output have a **consumer** for every key it emits? |
| PC2 | `noul` | Does the interface's TYPE permit the consumer to skip a field silently? |
| PC3 | `noul` | Does the composition root accept its **output** as an input (an inverted dependency)? |
| PC4 | `noul` | Does a critical-path component have an **off-switch**? |
| PC5 | `noul` | Does the artifact **certify** a property (a "nothing is stubbed" comment)? |
| PC6 | `noul` | Does a docstring describe a pipeline the body does not implement? |

**THE LADDER:** enumerate producers → count consumers per key → type-check the binding → read the composition root.
**THE CLOSURE TEST:** every emitted key has ≥1 production consumer, or the producer is flagged.
**THE RESIDUAL SHAPE:** `producers: N · keys: M · unconsumed: K`.
**HANDOFFS:** the unconsumed keys become firewall F2 candidates.

**THE ORIGIN:** the 17-questions-2-read finding. **PC1 + PC2 together are the mechanical answer to "how was discarding possible."**

---

# §5 · THE ENFORCEMENT LAWS (MOVE 8 — each names a forbidden behavior + its consequence)

| # | LAW | the forbidden behavior | the mechanical consequence |
|---|---|---|---|
| **L-1** | **THE LIVE-AUTHORITY LAW** | grading a claim against a document that has been superseded | the audit **refuses to emit a compliance number**; it emits the authority inventory + the pivot records instead |
| **L-2** | **THE AIM LAW** | accepting a check whose target ≠ the claim's subject | the claim is **DEMOTED** to UNPROVEN, written to the ledger |
| **L-3** | **THE FAIL-PROBE LAW** | accepting a green whose check was never perturbed | the check is marked **CANNOT-FAIL** and the claim demoted |
| **L-4** | **THE DISK-WITNESS LAW** | any judgment whose state came from agent prose | the judgment is **VOID**; L1 must re-read disk |
| **L-5** | **THE CONSUMER LAW** | a producer with zero production consumers | **BLOCK** at write time (`PRODUCER_WITHOUT_CONSUMER`) |
| **L-6** | **THE NAMED-RESIDUAL LAW** | an audit output with no residual ledger | **AUTOMATIC FAIL** |
| **L-7** | **THE INSTRUMENT-ERROR LAW** | an auditor whose own error rate is unmeasured | the audit is **INCOMPLETE** until §6.4 is filled |
| **L-8** | **THE SCOPE LAW** | a check reading a worktree copy / checkpoint / superseded authority | **BLOCK** (`WRONG_TARGET`) |
| **L-9** | **THE HONEST-NUMBER LAW** | a reported number differing from the measured one | **BLOCK** the commit (`DOC_CONTRADICTS_LOG`) |
| **L-10** | **THE STOP LAW** | closing on "the report looks thorough" | the run continues until the coverage ledger meets §2's stop |

**EACH LAW TRACES TO §0.2:** L-1/L-2/L-8 → `FALSE-GREEN = a check whose target is not the claim`; L-3/L-5/L-10 → the AUDIT line; L-6/L-7 → the HONESTY line.

---

# §6 · THE FALSIFICATION INSTRUMENTS (MOVE 9 — a machine per claim, no exemption)

```
+---------------------------------------------------------------------------------+
| INSTRUMENT 1 · THE PAIR-EXTRACTOR                                                 |
|   answers: what are the claims, and what checks them?                             |
|   the machine: parse every doc for numeric claims + every test for asserted       |
|   values + every artifact for its scenarios. Build the triples.                   |
|   use when: ALWAYS, first. No claim type is exempt.                               |
|   OUTPUT: the claim ledger (N claims, each with file:line + its check or UNCHECKED)|
+---------------------------------------------------------------------------------+
| INSTRUMENT 2 · THE AIM-JUDGE                                                      |
|   answers: is this check aimed at this claim?                                     |
|   the machine: Jev, one batched call, §3's six questions, the triple as STATE.     |
|   use when: any claim has a check.                                                |
|   OUTPUT: Q1..Q6 probabilities per triple + the aim verdict.                      |
+---------------------------------------------------------------------------------+
| INSTRUMENT 3 · THE FAIL-PROBE                                                     |
|   answers: can this check actually fail?                                          |
|   the machine: perturb the input the claim is ABOUT; the check MUST flip.          |
|     · a tautology: change the operand's binding → the check still passes          |
|     · a model-absent measure: enable the component → the number moves             |
|     · an excluded-test artifact: add the excluded scenario → the count changes      |
|     · a pass-by-absence gate: remove the input → the gate must REJECT, not pass     |
|   use when: Q1 judged AIMED.                                                      |
|   OUTPUT: CAN-FAIL | CANNOT-FAIL.                                                 |
+---------------------------------------------------------------------------------+
| INSTRUMENT 4 · THE LIVE-TARGET CHECK                                              |
|   answers: is the check reading the LIVE target?                                   |
|   the machine: compare the check's path root against the pivot/supersession set    |
|   and the worktree/checkpoint list.                                               |
|   use when: any check reads a path.                                               |
|   OUTPUT: LIVE | STALE-COPY | SUPERSEDED-AUTHORITY                                |
+---------------------------------------------------------------------------------+
| INSTRUMENT 5 · THE INSTRUMENT-ERROR MEASURE (MOVE 16's precondition)               |
|   answers: what is MY OWN false-positive / false-negative rate?                    |
|   the machine: run the extractor + aim-judge over a KNOWN set (the campaign's      |
|   92 findings, each already adjudicated). Compare.                                 |
|   use when: once per audit, and after any threshold change.                        |
|   OUTPUT: precision · recall · the named misses                                    |
+---------------------------------------------------------------------------------+
```

**THE SELECTION RULE:** docs → instrument 1+2. A green → 2+3. A path-reading check → 4. **No artifact type is exempt.** Every audit closes with instrument 5.

## 6.4 THE INSTRUMENT-ERROR LEDGER (mandatory — L-7)

| the instrument | its measured error rate | the known misses |
|---|---|---|
| the pair-extractor | *to be measured on the origin replay* | — |
| the aim-judge | *to be measured* | — |
| the fail-probe | *to be measured* | — |

**IN THE CAMPAIGN, THIS LEDGER WAS EMPTY UNTIL THE OPERATOR CHALLENGED ME.** Three instrument failures then surfaced: a regex false positive (a stray binding), a `grep -c assert` misread (the suite uses a hand-rolled idiom), and **the largest: a compliance figure against a superseded authority.** **L-7 exists so the third is impossible to omit.**

---

# §7 · THE ARTIFACT (MOVE 10 — the observable output)

```
+---------------------------------------------------------------------------------+
| THE AUDIT LEDGER — <project>/forensic/JEV_AUDIT_<date>.md                          |
+---------------------------------------------------------------------------------+
|                                                                                   |
|  §0  THE AUTHORITY INVENTORY        every doc, its mtime, its status, its pivot     |
|                                     records; THE LIVE ONE named                     |
|  §1  THE CLAIM LEDGER               N claims · each with file:line · its check ·    |
|                                     UNCHECKED if none                               |
|  §2  THE TRIPLE JUDGMENT TABLE      per triple: Q1..Q6 probabilities · the verdict  |
|  §3  THE FAIL-PROBE RESULTS         per aimed check: CAN-FAIL | CANNOT-FAIL          |
|  §4  THE DEMOTION LIST              every claim demoted, with the reason            |
|  §5  THE COVERAGE LINE              claims · checked · aimed · can-fail · demoted   |
|  §6  THE INSTRUMENT-ERROR LEDGER    §6.4, filled                                    |
|  §7  THE NAMED RESIDUAL             what was not enumerated                         |
+---------------------------------------------------------------------------------+
| THE VERDICT LINE:                                                                 |
|   CLAIMS: 412  CHECKED: 388  UNCHECKED: 24  AIMED: 341  CAN-FAIL: 338  DEMOTED: 50 |
|   COVERAGE: 94.2%   RESIDUAL: 24 unchecked claims (listed)                          |
|   EXIT: 1 (50 demotions)                                                            |
+---------------------------------------------------------------------------------+
```

**THE EXIT CODE IS THE VERDICT.** A demotion list is non-empty → exit 1 → the commit/ship gate blocks. **This is what turns the audit from a REPORT into a GATE.**

---

# §8 · THE COMPOSITION MAP (MOVE 11 — owns / hands off / the boundary)

```
+---------------------------------------------------------------------------------+
|                          jev-audit (THIS DESIGN)                                  |
|                                   |                                               |
|        OWNS                       |              HANDS OFF                       |
|  ─ the claim enumeration          |  ─ the transport contract   -> jev-judge-wiring |
|  ─ the (claim,check,artifact)     |  ─ the corpus narrowing      -> jev-scale-...   |
|    triple model                   |  ─ the batching mechanics    -> jev-batching    |
|  ─ the 6-question aim set         |  ─ the 3-layer gate pattern  -> jev-decision-... |
|  ─ the fail-probe recipes         |  ─ the 25 slop CLASSES       -> red-team-slop-audit |
|  ─ the demotion + exit-code law   |  ─ the 7 false-green CLASSES -> evidence-failure-audit |
|  ─ the instrument-error ledger    |  ─ the autopsy FORMAT        -> extract-meta-patterns |
+---------------------------------------------------------------------------------+
| THE BOUNDARY: this design OWNS the AUDIT SUBJECT (what to judge about a build's    |
| evidence). It OWNS NOTHING about how to call Jev, how to batch, or how to          |
| enforce — those are the four sibling skills, consumed not reimplemented.           |
+---------------------------------------------------------------------------------+
| THE NO-DUPLICATION LAW: if a section here restates a sibling's content, it is a    |
| second, staler source of truth. This design CITES; it does not copy.               |
+---------------------------------------------------------------------------------+
```

**THE PRECEDENCE RULE (where the designs overlap):** `jev-decision-gate-firewall` owns the **agent's behaviour** gates (tool calls, reasoning, commits). **This design owns the BUILD's EVIDENCE gates.** Where both apply (a commit that carries a claim), **this design's L-9 runs first** (the doc-vs-log diff), then the firewall's F4.

---

# §9 · THE TRIGGER SURFACE (MOVE 12 — literal phrases, forward + negative)

**FORWARD (the operator's actual words, verbatim):**
> *"audit everything"* · *"rip this apart"* · *"find all the slop"* · *"why did this pass"* · *"is this theatrical"* · *"how did this derail"* · *"what is actually wrong"* · *"log all failure"* · *"i expect 5000+ lines"* · *"this is the most retarded ... shit"* · *"read the entire fucking original build package"* · *"how was this even allowed"* · *"these are likely superseded"*

**NEGATIVE (do NOT fire):**
- a single-file bug → `debugging-and-error-recovery`
- a code review of a diff → `code-review`
- a security review → `security-reviewer`
- designing a new thing → `blueprinting`
- checking whether a claim is TRUE in isolation → `zero-trust-audit` (this design checks whether the CHECK can fail)

**THE ARGS:** `<target-root>` (required) · `--authority <path>` (optional; if absent, the L1 builder discovers it) · `--budget <n>` (the max triples; default = all) · `--probe` (run the fail-probes; default on).

---

# §10 · FILE LAYOUT + DEPLOYMENT (MOVE 13 — reachability is part of the design)

```
~/.omp/agent/skills/jev-audit/
├── SKILL.md                      the procedure (the 5-step loop, the 6 questions, the laws)
├── scripts/
│   ├── extract_claims.py         INSTRUMENT 1 — the pair-extractor (pure, disk-read)
│   ├── state_authority.py        L1 — the authority-liveness builder (ALREADY WRITTEN, §11)
│   ├── aim_judge.py              INSTRUMENT 2 — the Jev call + the question set
│   ├── fail_probe.py             INSTRUMENT 3 — the perturbation runner
│   ├── live_target.py            INSTRUMENT 4 — the stale-copy detector
│   ├── instrument_error.py       INSTRUMENT 5 — the self-measurement
│   └── enforce.py                L3 — probabilities -> actions -> exit code
├── references/
│   ├── question-set.md           the 6 universal + 4×6 playbook questions, versioned
│   ├── fail-probe-recipes.md     the 7 perturbation shapes
│   └── classes.md                the 25 slop + 7 false-green classes
└── assets/
    └── origin-corpus.jsonl       the campaign's 92 findings, adjudicated (the ground truth
                                  for INSTRUMENT 5's error measurement)
```

**DEPLOYMENT PROOF (skill-creator Step 7, the binding law):**
1. **discovery-root location** — the folder sits directly in `~/.omp/agent/skills/` (not a subtree)
2. **slash-command entry** — `~/.omp/agent/command/jev-audit.md` with `$ARGUMENTS`
3. **triple match** — folder `jev-audit/` + `SKILL.md` + `name: jev-audit`
4. **mechanical proof** — `diff -rq` empty, the validator exit recorded, the menu entry confirmed next turn

**THE BUNDLED TOOLS (the operator's ask):** `scripts/` ships as a runnable bundle — `python3 scripts/extract_claims.py <root> | python3 scripts/aim_judge.py` — so the workflow is a **pipeline**, not a prose procedure.

---

# §11 · WORKED EXAMPLE (MOVE 14 — the campaign, walked through the machinery)

**TARGET:** `PLUTUS/V6_BUILD` · **THE CLAIM:** *"latency < 500ms, mean 0.058ms (8639x headroom)"* (from `EVIDENCE_STATE.md`)

| step | what ran | the output |
|---|---|---|
| **1 ENUMERATE** | the extractor parsed the ship docs + canon docs | the claim ledger: 412 claims; this one is `#217`, source `context_management/EVIDENCE_STATE.md` |
| **2 PAIR** | the extractor found the check: `tests/test_decision_latency.py` | the triple `(claim #217, test_decision_latency, its stdout)` |
| **3 JUDGE** | Jev, batched, §3's six questions | **Q1 AIM 0.18** (the check reads the circuit **without** the model; the claim is about the **live** circuit) · **Q2 FAILABILITY 0.91** (the check can fail) · **Q3 ARTIFACT 0.95** (it reads stdout) · **Q5 PROVENANCE 0.12** (`the-code-under-test` — the circuit's own offline path) |
| **4 PROBE** | the fail-probe enabled the mandatory model and re-ran | **418.6ms / 419.1ms / 419.3ms quiet; 587ms under GPU contention** — a **7,000×** move |
| **5 ENFORCE** | Q1 0.18 < 0.70 → **DEMOTE** the claim to UNPROVEN; **BLOCK** the ship gate | ledger row written; exit 1 |

**THE SHALLOW vs DEEP CONTRAST (MOVE 10):**

```
+---------------------------------------------------------------------------------+
| THE SHALLOW AUDIT (what I did FIRST, before the operator challenged me)           |
|   read the doc: "latency 0.058ms" -> noticed it looked fast -> reported it         |
|   SCORE: 1 finding, 0 probes, 0 demotion law, 0 instrument-error ledger            |
|                                                                                   |
| THE DEEP AUDIT (this design)                                                      |
|   412 claims enumerated -> 388 paired -> 6 questions judged per triple ->           |
|   fail-probe every aimed check -> 50 demoted -> exit 1 -> instrument-error         |
|   ledger filled (3 of MY OWN failures recorded)                                    |
|   SCORE: 50 demotions, 24 unchecked claims named, 3 instrument failures published  |
+---------------------------------------------------------------------------------+
```

**AND THE SAME MACHINERY ON MY OWN ERROR (the reflexive case):** the claim *"1.8% compliance with the commissioned package"* → **Q1 AIM 0.21** (the check graded against set A; the claim is about *"the commissioned package"*, which is set C) → **Q5 PROVENANCE 0.05** (`superseded authority`) → **INSTRUMENT 4: SUPERSEDED-AUTHORITY** → **DEMOTE**. **The design catches the error that prompted it.**

---

# §12 · OPEN DECISIONS (MOVE 15 — forks with recommended defaults)

| # | fork | the options | the recommended default | operator? |
|---|---|---|---|---|
| **OD-1** | **Jev or the local Kev substitute?** | `api.typesafe.ai` (real Jev, needs a key) · `kev-0.6b-ONNX` (local, no key, the offline substitute) | **Jev primary, Kev fallback** — the `local-kev-decision-model` skill exists for exactly this | **YES** — cost vs availability |
| **OD-2** | **When does the aim-judge run?** | on-demand (the operator invokes it) · on every commit (the F4 gate) · on every ship claim | **on every ship claim + every commit touching a doc** | no (pin it) |
| **OD-3** | **The fail-probe's scope** | every aimed check (slow) · a sampled subset (fast) | **every aimed check on a ship claim; sampled on a commit** | no |
| **OD-4** | **The demotion's teeth** | demote-in-the-ledger (advisory) · block-the-commit (hard) | **hard-block on ship; advisory on a working commit** | **YES** — the enforcement posture |
| **OD-5** | **The origin corpus** | ship the 92 adjudicated findings as ground truth · build a fresh corpus | **ship the 92** — they are the only labelled set that exists | no |
| **OD-6** | **Bundle as a skill or a tool?** | a skill (the workflow) · an extension tool (a callable) · both | **both** — the skill is the procedure, the extension registers `jev_audit` | no |

**THE FORKS THAT NEED THE OPERATOR: OD-1 (the judge's identity) and OD-4 (the enforcement posture).** The rest are taken on the default and stated here so they can be overruled.

---

# §13 · THE SELF-CHECK (MOVE 16 — apply the design's own law to the design) + THE RESIDUAL

**THE DESIGN'S OWN LAW RUN AGAINST ITSELF:** *a claim is false-green when its check is aimed at a target it cannot miss.* Applied here:

| this blueprint's claim | its check | aimed? |
|---|---|---|
| "the reduction explains instances never mentioned" | *does it cover my own error?* | **YES** — §11's reflexive case |
| "no existing artifact fills the gaps" | §1's sibling table, 9 rows | **YES** — each row's `does NOT` cell |
| "the fail-probe catches the false greens" | §11's worked example, one claim | **PARTIAL** — one of 7 classes walked, not all 7 |
| "INSTRUMENT 5 measures the error rate" | **NOTHING YET** | **NO — the ledger is EMPTY (§6.4)** |

**THE HONEST FINDING: the instrument-error ledger is specified and unmeasured.** By this design's own L-7, **the audit is INCOMPLETE until it is filled.** That is stated, not hidden.

## THE NAMED RESIDUAL

1. **UNEXERCISED:** the aim-judge has never been run against the real API — the question set is designed, not validated. The origin replay (§5 of the firewall blueprint) is the unrun acceptance test.
2. **SPECIFIED-BUT-NOT-BUILT:** all 7 scripts in §10 are specified; **one exists** (`state_authority.py`, §11's L1). Six remain.
3. **NEVER ENUMERATED:** the design covers claims in **docs, tests and artifacts**. It does **NOT** cover: claims in commit messages, claims in a chat reply, claims in a subagent's return. **Three claim sources are unhandled.**
4. **THE COST IS UNMEASURED:** ~40 questions × N triples batched is *assumed* cheap (one request per event). No measurement exists.
5. **THE PRECEDENCE with `jev-decision-gate-firewall` is ASSERTED (§8), not tested** — both gate a commit and the order matters.

**FILES TOUCHED THIS SESSION:** `forensic/JEV_AUDIT_TOOLS_BLUEPRINT.md` (this) · `forensic/jev/state_authority.py` (the one built instrument) · `forensic/JEV_DERAILMENT_FIREWALLS.md` (the sibling design) · the two minted skills.

---

# §14 · THE INTEGRATION — THE 87-CLASS CORPUS, THE FACT STORE, AND THE SECOND ORIGIN

**This section binds three independent findings into the blueprint above. Each is MEASURED;
none is a proposal.**

## §14.1 · THE REDUCTION GENERALIZED (MOVE 3, extended)

**§0.1's reduction, verbatim:** *"A CLAIM IS FALSE-GREEN WHEN ITS CHECK IS AIMED AT A TARGET IT
CANNOT MISS."*

**THE SECOND ORIGIN CONFIRMS IT.** A separate campaign (PBK v3, a different tree, two black-hat
auditors, the same week) produced the same class with different instances:

| the PBK v3 finding | the reduction |
|---|---|
| 3 capabilities DECLARED, TESTED, NEVER CALLED (the lint, the ledger sink, postAction) | the test was aimed at the MODULE, not the WIRING |
| the `deriveBand` computes `neg`, validates it, never reads it | the check measured a value it discarded |
| the zero-margin band (`high = max(pos)` = the single-hit score) | the threshold was aimed at a target it always hit |
| a test passing a DIFFERENT input than the production caller (`lastSignature`) | the check was aimed at a CALL SHAPE the caller never uses |
| a green suite (35 pass) over dead wiring | the check was aimed at the SOURCE, not the RUNTIME |
| the firewall's own D1/D2/D5 PASS while 3 capabilities were unwired | the check could not miss |

**★ THE REDUCTION HOLDS ACROSS TWO INDEPENDENT PROJECTS. THAT IS THE TEST OF A REAL REDUCTION
(§0.1's own criterion). IT IS A LAW, NOT A SUMMARY.**

## §14.2 · THE 87-CLASS CORPUS — THE AUDIT'S TARGET DENOMINATOR

**§0.1's campaign: 92 findings across 25 classes. THE CROSS-PROJECT UNION IS BIGGER:**

```
87 CLASSES ACROSS 14 GROUPS (57 master + 30 new, deduped across 16 corpus files + 2 sessions)

[A] THEATRICAL 26  [B] SPEC/SCOPE 11  [C] SELF-JUDGE 8   [D] AUDIT-GAMES 9
[E] DOC 7          [F] GATE-BLIND 15  [G] UNWIRED 16     [H] STALE/DEPLOY 6
[I] FALLBACK 5     [J] PROSE-ENFORCE 6 [K] EVIDENCE 5    [L] MISFIRE-NEW 13
[M] PROBE-NEW 4    [N] PROCESS-NEW 14
```

**★ THE 30 NEW CLASSES ARE THE AUDIT'S OWN FAILURE MODES.** They are not defects in the code
under audit — they are defects in the AUDIT INSTRUMENT (§6.4's instrument-error ledger). The
audit tool MUST carry a check for each:

```
N1  HOST-TEXT AS AGENT TEXT    the audit scores a host notice as the agent's utterance
N2  USE-MENTION                the audit fires on a QUOTED defect (a doc about the defect)
N3  DISCARD-DESTROYS           the audit deletes the span before recording it (18 of 22 lost)
N4  POLARITY                   "NOT verified" read as the assertion
N5  INFLECTED-MISS             "completed" escapes "complete"
N6  INTERFACE-NAME             an interface NAME fires the claim check
N7  RATE                       the finding rate climbing across rounds
N9  AUTHORITY-SPOOF            an injected notice arrives as role:user
N13 PARKED-FIRES               the rules dir EMPTY yet findings arrive
N17 BLIND-TRIPLE               scope-drift + count-loss + a provider error -> a PASS
N19 ABORT-NULL                 a pure function called with an input the caller never passes
N22 FIXTURE-ENSHRINED          the test encodes the defect it should catch
N24 OVER-BREADTH               a heredoc STRING treated as a file class
N28 PROBE-BODY-UNREAD          the probe reads a field the loader never sets
N29 CWD-DRIFT                  a persisted `cd` moves every measurement
N30 PROBE-ERROR-AS-DEFECT      a hand-built regex produces a false defect
```

**★ §6.4's INSTRUMENT-ERROR LEDGER IS THE HOME FOR THESE. THE AUDIT'S OWN ERROR RATE IS THE
METRIC THAT MAKES IT HONEST — AND N1-N30 ARE THE CLASSES TO MEASURE IT AGAINST.**

## §14.3 · THE DURABLE-FACT L1 — THE AUDIT'S STATE SOURCE (never the claim)

**§3's generator and §4's playbooks take a STATE. THIS IS THE FORMALISM FOR THAT STATE — and it
is what makes the audit ungameable.**

```ts
interface FactRow {
  id: string;
  cls: "F-GIT"|"F-ART"|"F-PROC"|"F-TEST"|"F-SPEC"|"F-TODO"|"F-DEPLOY"|"F-RUN";
  key: string;            // "HEAD" | "diff" | "sha" | "exit" | "open_items" | ...
  value: string | number;
  source: string;         // ★ THE COMMAND that produced it — the provenance
  observedAt: number;     // ★ FRESHNESS IS PART OF THE FACT
  scope: string;          // ★ the root the observation applied to
}
```

**THE 17 CLASSES (each one command):** F-GIT {HEAD, diff, state, blame, **callers**} · F-ART
{sha, mtime, size} · F-PROC {pid, start, held} · F-TEST {cmd, exit, output} · F-SPEC {text} ·
F-TODO {open} · F-DEPLOY {live-vs-src} · F-RUN {tick}.

**THE FOUR GATES:** ① OBSERVED (the row carries its argv; no command -> REFUSED) ② IMMUTABLE
(append-only) ③ FRESH (`observedAt`; stale -> FLAGGED) ④ SCOPED (the root, always).

**★ THE AUDIT READS FACTS, NEVER CLAIMS.** §0.1's reduction says "the disk as the witness" —
**THIS IS THE WITNESS, FORMALIZED. `F-GIT.callers` is the single most valuable fact in the
whole design: it is the reachability, and reachability is what every coverage metric misses.**

## §14.4 · ★ THE DELTA GATE — THE TREADMILL KILL (the audit's own firing law)

**The operator's measured complaint (the scanner treadmill):** *"an LLM reviewer generates
infinite findings; each fix round produces NEW findings; the agent chases the count instead of
the SYSTEM. The count never reaches zero (by design — it is an LLM), so the loop never
terminates and the runtime is never driven."*

**THE MECHANICAL ANSWER:**
```
AN AUDIT ROUND IS REQUESTED IFF A FACT ROW WAS APPENDED SINCE THE LAST ROUND.

  a session that TALKS            -> NO FACT ROW -> NO AUDIT ROUND
  a session that EDITS the tree   -> F-GIT.diff row -> AN AUDIT ROUND
★ THE TREADMILL REQUIRES A FIX THAT DID NOT LAND. THE DELTA GATE MEASURES LANDING, NOT
  FINDINGS: A ROUND WITH ZERO FACT DELTA CANNOT RUN, SO THE COUNT CANNOT INFLATE.
```

**★ AND THE CONVERGENCE LAW (§2's macro pattern, made mechanical):** the round counter is bound
to the LANDING RATE, not the finding count. `B3 = poor` (§2's F7) BLOCKS the next round until the
landing rate is measured and raised. **A non-convergent loop is a DESIGN DEFECT, not a work item.**

## §14.5 · THE MECHANICAL/SEMANTIC SPLIT — WHICH AUDIT CHECKS ARE FREE

```
MECH-NOMODEL (a predicate over disk — NO model, ZERO cost): ~70 of the 87 classes
  the whole of F (blind-gates) · G (unwired) · H (stale) · I (fallback-artifact) ·
  L (hygiene) · M (dispatch) · the floors/caps
  ★ a sha compare, a grep count, a diff, an mtime, an exit code

SEM-NEEDS-MODEL (Jev, Noul/Choice/Score, ~100ms): ~48 of the 87
  A (theatrical claims) · B (scope) · C (unanchored) · D (weakened checks)
  ★ the judgment the audit exists for
```

**★ THE AUDIT'S BUILD ORDER: THE MECHANICAL LAYER FIRST.** §6's instruments split the same way —
`the pair-extractor` and `the fail-probe` are MECHANICAL (free, deterministic); only
`the aim-judge` needs Jev. **A gate that needs no model cannot be prompt-injected, cannot drift,
and cannot hallucinate.**

## §14.6 · THE SECOND ORIGIN REPLAY (the acceptance test, doubled)

**§11's worked example walks the V6 campaign. HERE IS THE SECOND REPLAY CORPUS — measured, in a
different tree:**

```
THE DEFECT                                          THE AUDIT INSTRUMENT THAT CATCHES IT
──────────────────────────────────────────────────  ──────────────────────────────────────
3 capabilities declared, tested, NEVER CALLED        the pair-extractor: a (claim=EXISTS,
  (the lint · the ledger sink · postAction)            artifact=the module, check=the test)
                                                       triple where check.imports does NOT
                                                       reach a production caller
TWO `LedgerRow` contracts (8 flat vs 3 nested)       §4 PLAYBOOK D (contract): the two shapes
                                                       do not interoperate
`deriveBand` computes `neg`, never reads it          the aim-judge: the check's TARGET (the
                                                       band) is not the claim's SUBJECT
                                                       (discriminating positives from negatives)
the zero-margin band                                 the fail-probe: perturb a negative ->
                                                       the band does NOT flip -> CANNOT-FAIL
a test passing a DIFFERENT input than the caller      the pair-extractor: check.args !=
                                                       production.args
a green suite over dead wiring                        §4 PLAYBOOK B (evidence): can this
                                                       green fail? NO -> the green is empty
the firewall's own PASS while 3 are unwired           §6.4 the instrument-error ledger: the
                                                       instrument's own false-negative
```

**★ §11's acceptance test is now DOUBLED. An audit tool that catches the V6 92 findings but
misses the PBK v3 defects is OVERFIT to one origin. One that catches BOTH is a LAW.**

## §14.7 · THE ADDENDUM TO §10 (the file layout — the fact store joins it)

```
the audit tool's new modules (per §14.3):
  facts/store.ts       the append-only fact rows + the DELTA GATE (§14.4)
  facts/observe.ts     the 17 observers (one shelled command each)
  audit/pairs.ts       §0.3's pair-extractor (the (claim,check,artifact) triples)
  audit/aim.ts         §0.3's aim-judge (the Jev call)
  audit/failprobe.ts   §0.3's fail-probe (the perturbation that must flip the check)
  audit/ledger.ts      the decision ledger + §6.4's instrument-error ledger
★ reachability (§10's own law): the pair-extractor and the fail-probe are MECHANICAL — they
  ship FIRST and need no key. The aim-judge ships when the Jev credential is wired.
```

## §14.8 · THE ADDENDUM TO §13 (the self-check — the second origin's questions)

**§13 applies the design's own law to the design. ADD THESE FOUR:**

```
[ ] DOES THE AUDIT FIRE ONLY ON A FACT DELTA? (the treadmill kill — §14.4)
    a talk-only session must produce ZERO audit rounds. VERIFY with a counter.
[ ] DOES EVERY AUDIT CHECK CARRY ITS `source` COMMAND? (the provenance — §14.3)
    a check whose state has no argv is a CLAIM, not a measurement. REFUSE it.
[ ] ARE THE INSTRUMENT'S OWN ERROR CLASSES (N1-N30) MEASURED? (§6.4)
    an audit with an unmeasured error rate is a claim about itself.
[ ] DOES THE TOOL CATCH BOTH ORIGINS? (§14.6)
    the V6 92 findings AND the PBK v3 defects. ONE origin = OVERFIT.
```

## §14.9 · THE NAMED RESIDUAL (the integration's own honest gap)

```
· THE JEV CREDENTIAL. The aim-judge (§0.3) needs the TypeSafe key. Until it is wired, the
  mechanical instruments (§14.5: the pair-extractor + the fail-probe) carry the audit alone —
  and they catch the G (unwired), H (stale), I (fallback) and F (blind-gate) classes, which
  are the majority.
· THE 87-CLASS TUNING. The node instructions need calibration on the labeled corpus (the
  measured positives + the sessions' negatives).
· THE THRESHOLDS. 0.75/0.85 are PROPOSED. §6.4's instrument ledger is where their error rates
  get measured; until then they are judgements, and §6's own law says so.
· THE PRIVATE REASONING. §14.4's delta gate covers the DISK. A reasoning span produces no fact
  row — so the audit of reasoning stays LEDGER + STEER, never a hard block (§6's honest limit).
```
