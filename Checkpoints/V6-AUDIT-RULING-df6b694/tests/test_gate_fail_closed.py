import _boot, sys, math
from gates import TradeCandidate, evaluate, g_sl, g_rrr, g_conf, g_dual, g_geometry, GATES, GATE_NAMES

# A COHERENT candidate: sl_d = 4.0 pips, tp_d = 17.0 pips -> RRR 4.25, and the
# zone width EQUALS the SL distance (LAW 2, buffer 0). Every field agrees with
# the geometry, which is the only kind of candidate the gates should accept.
BASE = dict(pair="EUR/USD", direction="long", entry=1.14110, sl=1.14070, tp=1.14280,
            rrr=4.25, zone_width_pips=4.0, sl_distance_pips=4.0, confidence=0.75,
            session_utc="LONDON 02:00", dedup_key="X", limite_rrr=4.25)

def cand(**over):
    d = {**BASE, **over}
    return TradeCandidate(**d)

NAN = float("nan")
INF = float("inf")
fails = []

# ---- the NaN fail-open class (the audit's most dangerous finding) ----------
for name, over, gate, tok in [
    ("NaN rrr",           dict(rrr=NAN, limite_rrr=NAN),  g_rrr,  "G-RRR_REJECT"),
    ("NaN sl_distance",   dict(sl_distance_pips=NAN),     g_sl,   "G-SL_REJECT"),
    ("zero sl_distance",  dict(sl_distance_pips=0.0),     g_sl,   "G-SL_REJECT"),
    ("negative sl",       dict(sl_distance_pips=-5.0),    g_sl,   "G-SL_REJECT"),
    ("inf sl",            dict(sl_distance_pips=INF),     g_sl,   "G-SL_REJECT"),
    ("NaN confidence",    dict(confidence=NAN),           g_conf, "G-CONF_REJECT"),
    ("confidence > 1",    dict(confidence=5.0),           g_conf, "G-CONF_REJECT"),
    ("inf confidence",    dict(confidence=INF),           g_conf, "G-CONF_REJECT"),
    ("NaN limite_rrr",    dict(limite_rrr=NAN),           g_dual, "G-DUAL_REJECT"),
]:
    r = gate(cand(**over))
    if r.passed or r.token != tok:
        fails.append(f"{name}: got passed={r.passed} token={r.token} want {tok}")

# ---- the geometry class (no gate read direction/entry/sl/tp before) --------
for name, over, tok in [
    ("no_trade direction", dict(direction="no_trade"),        "G-GEOMETRY_REJECT"),
    ("typo direction",     dict(direction="Long"),            "G-GEOMETRY_REJECT"),
    ("empty direction",    dict(direction=""),                "G-GEOMETRY_REJECT"),
    ("inverted long",      dict(sl=1.14510, tp=1.14100),      "G-GEOMETRY_REJECT"),
    ("collapsed levels",   dict(sl=1.14110),                  "G-GEOMETRY_REJECT"),
    ("NaN entry",          dict(entry=NAN),                   "G-GEOMETRY_REJECT"),
]:
    r = g_geometry(cand(**over))
    if r.passed or r.token != tok:
        fails.append(f"{name}: got passed={r.passed} token={r.token} want {tok}")
    # and the FULL chain must reject it
    v = evaluate(cand(**over))
    if v.accepted:
        fails.append(f"{name}: the full gate chain ACCEPTED it")

# ---- the session parser must not scrape an arbitrary HH:MM -----------------
from gates import _local_hhmm
for s, want in [("LONDON 02:00","02:00"), ("2026-07-06T02:30:00-04:00","02:30"),
                ("OFF_SESSION 14:30","14:30"), ("garbage 99:99",None),
                ("2026-07-06Txx:yy:00-04:00",None), ("",None), ("2026-07-06T02:30", "02:30")]:
    got = _local_hhmm(s)
    if got != want: fails.append(f"_local_hhmm({s!r}) -> {got!r} want {want!r}")

# ---- the honest path still passes ------------------------------------------
v_ok = evaluate(cand())
if not v_ok.accepted:
    fails.append(f"the honest candidate was REJECTED: {[r.token for r in v_ok.rejections]}")

ok = not fails
print(f"[TOKEN] test_gate_fail_closed" if ok else "[TOKEN-ABSENT] test_gate_fail_closed")
print(f"[DETAIL] gate chain = {len(GATES)} gates: {GATE_NAMES}")
print(f"[DETAIL] honest candidate accepted = {v_ok.accepted} ({v_ok.tokens})")
print(f"[DETAIL] NaN/geometry/session probe failures = {len(fails)}")
for f in fails: print(f"[DETAIL]   FAIL {f}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_gate_fail_closed")
sys.exit(0 if ok else 1)
