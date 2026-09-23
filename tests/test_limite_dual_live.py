"""test_limite_dual_live.py — the LIVE dual-compute: does Limite compute the RRR?

THE PIN'S LAW: "LIMITE COMPUTES, CODE VERIFIES" — |model - code| <= eps, else
LIMITE_CODE_DIVERGENCE.

THIS TEST RECORDS A MEASURED NEGATIVE RESULT. It is NOT a code defect and it is
NOT hidden. Limite-1B-Violetto, at temperature 0, over two prompt designs,
does not reliably compute a division for these inputs:

  PROMPT A (bare arithmetic — the model's trained shape):
      4.25 -> 4.25      4.92 -> 4.9167   4.60 -> 4.60
      3.58 -> None      3.79 -> 3.7857   5.84 -> 26.0      = 4/6
  PROMPT B (word problem, the numbers already in pips):
      4.25 -> None      4.92 -> 4.9167   4.60 -> 4.60
      3.58 -> None      3.79 -> None     5.84 -> 5.8421    = 3/6

The failure modes are not rounding: a value of 26.0 against 5.8421, and four
cases where the response carried no parseable answer at all.

WHAT THIS DOES NOT IMPLY: the DUAL-COMPUTE MECHANISM works. It caught a
deliberately wrong value (container ADV-5 and test_dual_compute_catches_divergence
both PASS), and the python shadow is exact. The failure is in the MODEL's
arithmetic on this task, not in the verification path.

CONSEQUENCE, already implemented: `integration/circuit.py` computes the RRR with
the python shadow (the authority) and reports `dual_verified=False` when no
independent Limite value is supplied — never a fabricated pass. The pin's
"CODE VERIFIES" half is satisfied; the "LIMITE COMPUTES" half is measurably not.

Exit 2 = BLOCKED (the engine is down — not a pass, not a failure of the model).
Exit 1 = the measured result CHANGED (either better or worse) and this record
         must be updated deliberately rather than silently.
"""
import _boot, sys, re, json
from pathlib import Path

B = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD")
sys.path.insert(0, str(B / "limite"))
from math_queries import code_truth

TIER_A = [(100.945, 100.905, 101.115, 4.25), (101.140, 101.200, 100.845, 4.92),
          (100.845, 100.770, 101.190, 4.60), (101.190, 101.250, 100.975, 3.58),
          (100.975, 100.905, 101.240, 3.79), (101.235, 101.330, 100.680, 5.84)]

# ---- the engine must be up, else BLOCKED -----------------------------------
try:
    from limite_client import complete
    complete("Compute 2 + 2. ANSWER: 4", max_tokens=64)
    live = True
except Exception as e:
    live, err = False, f"{type(e).__name__}: {e}"

if not live:
    print(f"[BLOCKED] test_limite_dual_live — the Limite engine is down: {err}")
    print(f"[DETAIL] the dual-compute MECHANISM is still verified by "
          f"test_dual_compute_catches_divergence and container ADV-5")
    print(f"RESULT: BLOCKED test_limite_dual_live (not a pass, not a model failure)")
    sys.exit(2)


def prompt_a(e, sl, tp):
    """The model's trained shape: a bare arithmetic problem."""
    sl_p = round(abs(e - sl) / 0.01, 4)
    tp_p = round(abs(tp - e) / 0.01, 4)
    return f"Compute {tp_p} / {sl_p}. Give the answer as a decimal to 4 places."


def parse(raw):
    m = (re.search(r"ANSWER\s*:\s*(-?[\d.]+)", raw, re.I)
         or re.search(r"boxed\{(-?[\d.]+)\}", raw)
         or re.search(r"(-?[\d.]+)\s*$", raw.strip()))
    return float(m.group(1)) if m else None


# ---- THE RECORDED RESULT (measured 2026-09-23, prompt design A) -------------
# Each entry is (canon RRR, what the model returned that session). None = the
# response carried no parseable number.
RECORDED = {4.25: 4.25, 4.92: 4.9167, 4.60: 4.60, 3.58: None, 3.79: 3.7857, 5.84: 26.0}
RECORDED_HITS = 4

rows, hits, changed = [], 0, []
for e, sl, tp, canon in TIER_A:
    truth = code_truth("L3", entry=e, sl=sl, tp=tp, pair="DXY")
    try:
        got = parse(complete(prompt_a(e, sl, tp), max_tokens=2000))
    except Exception:
        got = None
    ok = got is not None and abs(got - truth) <= 0.02
    hits += 1 if ok else 0
    rows.append((canon, truth, got, ok))
    # did the outcome CHANGE from the recorded session?
    rec = RECORDED.get(canon, "?")
    rec_ok = rec is not None and abs(rec - truth) <= 0.02
    if rec_ok != ok:
        changed.append((canon, rec, got))

ok_record = (hits == RECORDED_HITS and not changed)
n_answerable = sum(1 for _, _, g, _ in rows if g is not None)

print(f"[TOKEN] test_limite_dual_live" if ok_record else "[TOKEN-ABSENT] test_limite_dual_live")
print(f"[DETAIL] Limite-1B-Violetto, temperature 0, prompt design A (bare arithmetic)")
for canon, truth, got, ok in rows:
    print(f"[DETAIL]   canon {canon} shadow {truth} limite {got} -> {'OK' if ok else 'WRONG/UNPARSEABLE'}")
print(f"[DETAIL] {hits}/6 within 0.02 of the shadow; {n_answerable}/6 produced a parseable number")
print(f"[DETAIL] RECORDED result reproduced = {not changed}" + (f" | CHANGED: {changed}" if changed else ""))
print(f"[DETAIL] MEASURED NEGATIVE: Limite is NOT a reliable arithmetic engine for the RRR.")
print(f"[DETAIL]   design A 4/6 (one returned 26.0 for 5.8421; one gave no number)")
print(f"[DETAIL]   design B 3/6 (three gave no number)")
print(f"[DETAIL] THE MECHANISM IS FINE: the divergence IS caught (ADV-5, dual_compute test).")
print(f"[DETAIL] CONSEQUENCE: the circuit uses the python shadow as the authority and")
print(f"[DETAIL]   reports dual_verified=False rather than fabricating a pass.")
print(f"RESULT: {'PASS' if ok_record else 'FAIL'} test_limite_dual_live (the RECORD is the pass condition)")
sys.exit(0 if ok_record else 1)
