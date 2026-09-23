from pathlib import Path
import _boot, sys, random
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "determinism"))
from determinism import RunDigest, digest, compare, canonical, assert_deterministic, VOLATILE

# a representative multi-stage run
def stage_run(seed: int):
    rng = random.Random(seed)          # seeded => deterministic
    decider = {f"E1.Q{i}": {"yes": round(rng.random(),6), "no": round(1-rng.random(),6)}
               for i in range(1,6)}
    limite = {f"L{i}": {"model": 4.25, "code": 4.25, "delta": 0.0, "pass": True}
              for i in range(1,7)}
    gates = [{"gate":"G-RRR","passed":True,"token":"G-RRR_PASS"},
             {"gate":"G-SESSION","passed":True,"token":"G-SESSION_PASS"}]
    decision = {"accepted": True, "direction": "long", "rrr": 4.25}
    return {"decider": decider, "limite": limite, "gates": gates, "decision": decision}

# 1) two identical runs -> identical SHA
a, b = RunDigest(stage_run(42)), RunDigest(stage_run(42))
r_same = compare(a, b)
ok1 = r_same["match"] and a.sha == b.sha

# 2) a DIFFERENT seed -> different SHA (the digest actually bites)
c = RunDigest(stage_run(43))
ok2 = c.sha != a.sha

# 3) AUDIT ROUND 8 CHANGED THIS CONTRACT, DELIBERATELY.
# The old behaviour stripped VOLATILE keys at the TOP level too, so a caller
# could add `ts_wall` without changing the digest. The audit found that a STAGE
# named `ts`/`timing` was then silently dropped from the hash — a real decision
# field, unhashed. Volatile filtering now happens INSIDE payloads only
# (canonical), and a TOP-LEVEL key is a STAGE NAME the caller chose, so it IS
# hashed. The test asserts the NEW contract: adding a top-level key CHANGES the
# digest, and a volatile key NESTED inside a stage does not.
d = RunDigest({**stage_run(42), "ts_wall": 1234567})
ok3_top = d.sha != a.sha                      # a top-level key is hashed now
nested_a = RunDigest({"s": {"decided": 1, "duration_ms": 5}})
nested_b = RunDigest({"s": {"decided": 1, "duration_ms": 999}})
ok3_nested = nested_a.sha == nested_b.sha     # a nested volatile key is not
ok3 = ok3_top and ok3_nested

# 4) a divergence NAMES the stage
e = RunDigest({**stage_run(42), "decision": {"accepted": False, "direction": "short", "rrr": 1.0}})
r_div = compare(a, e)
ok4 = (not r_div["match"]) and "decision" in r_div["divergent_stages"]

# 5) assert_deterministic over a pure function
r5 = assert_deterministic(stage_run, 7)
ok5 = r5["match"]

ok = ok1 and ok2 and ok3 and ok4 and ok5
print(f"[TOKEN] test_determinism_sha_match" if ok else "[TOKEN-ABSENT] test_determinism_sha_match")
print(f"[DETAIL] run1 sha={a.sha}")
print(f"[DETAIL] run2 sha={b.sha}  match={r_same['match']} (pass={ok1})")
print(f"[DETAIL] different seed sha={c.sha} differs={ok2}")
print(f"[DETAIL] top-level keys ARE hashed (round-8 contract) = {ok3_top}; "
      f"nested volatile keys excluded = {ok3_nested}")
print(f"[DETAIL] divergence names the stage={ok4} stages={list(r_div['divergent_stages'])}")
print(f"[DETAIL] assert_deterministic(pure fn) match={ok5}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_determinism_sha_match")
sys.exit(0 if ok else 1)
