import _boot, sys, json, urllib.request
BASE = "http://127.0.0.1:8100/v1"

# 1) the server answers /v1/models
try:
    with urllib.request.urlopen(f"{BASE}/models", timeout=10) as r:
        models = json.loads(r.read())
    served = [m["id"] for m in models["data"]]
except Exception as e:
    print(f"[TOKEN-ABSENT] test_limite_serves_temp0"); print(f"[DETAIL] server unreachable: {e}")
    print(f"RESULT: FAIL test_limite_serves_temp0"); sys.exit(1)

# 2) the client HARD-CODES temperature=0 and refuses otherwise
from client import TEMPERATURE
temp_law = TEMPERATURE == 0.0

# 3) a real completion at temperature=0 is deterministic across two calls
body = json.dumps({"model":"limite-1b","prompt":"Compute 17 + 25. Answer with just the number.\nANSWER:",
                   "temperature":0.0,"top_p":1.0,"max_tokens":64,"stream":False}).encode()
def call():
    req = urllib.request.Request(f"{BASE}/completions", data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["text"]

try:
    a = call(); b = call()
    deterministic = (a == b)
except Exception as e:
    print(f"[TOKEN-ABSENT] test_limite_serves_temp0"); print(f"[DETAIL] completion failed: {type(e).__name__}: {e}")
    print(f"RESULT: FAIL test_limite_serves_temp0"); sys.exit(1)

ok = ("limite-1b" in served) and temp_law and deterministic
print(f"[TOKEN] test_limite_serves_temp0" if ok else "[TOKEN-ABSENT] test_limite_serves_temp0")
print(f"[DETAIL] served models = {served}")
print(f"[DETAIL] client TEMPERATURE = {TEMPERATURE} (law: must be 0.0) -> {temp_law}")
print(f"[DETAIL] run1 = {a[:80]!r}")
print(f"[DETAIL] run2 = {b[:80]!r}")
print(f"[DETAIL] deterministic (temp=0 => byte-identical) = {deterministic}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_limite_serves_temp0")
sys.exit(0 if ok else 1)
