"""tests/test_fix_effectiveness.py — EVERY FIX, VERIFIED BY EFFECT.

THE CLASS THIS GUARDS (35 audit rounds, measured): a fix that is WRITTEN but
- never applied (a batch script that aborted at its first anchor miss),
- applied but INERT (a helper never called; an attribute that exists nowhere; a
  dict built but never read), or
- changed at ONE site while a sibling kept the old value.

Those three accounted for 4-5 of every 7-8 findings in rounds 33 and 35. A
"present in the file" check cannot catch them — only asserting the OBSERVABLE
BEHAVIOUR can. Each assertion below FAILS if its fix is inert.
"""
import _boot, sys, json, re
from pathlib import Path

R = Path(__file__).resolve().parent.parent
for _m in ("gates", "limite", "mpse", "oms", "state", "tui", "determinism",
           "decider", "integration"):
    sys.path.insert(0, str(R / _m))

import predicates as pr
import oms
import determinism as det
import coding_surface as cs
import pane

failures = []
def check(label, cond):
    if not cond:
        failures.append(label)
    print(f"[DETAIL]   {'ok  ' if cond else 'FAIL'} {label}")

# ============ 1. AT-02 recomputes the distance and fails closed ============
_v = pr.at_02_sl_envelope({"pair": "EUR/USD", "direction": "long", "entry": 1.14110,
                           "sl": 1.14100, "tp": 1.145, "rrr": 5,
                           "zone_width_pips": 1, "sl_distance_pips": 10,
                           "confidence": 0.7})
check("AT-02 refuses a stated/geometry distance mismatch", not _v.passed)
_v2 = pr.at_02_sl_envelope({"pair": "EUR/USD", "direction": "long", "entry": 1.14,
                            "sl": 1.139, "tp": 1.145, "rrr": 5, "zone_width_pips": 4,
                            "sl_distance_pips": -10, "confidence": 0.7})
check("AT-02 refuses a NEGATIVE distance", not _v2.passed)
_v3 = pr.at_02_sl_envelope({"pair": "FAKE", "direction": "long", "entry": 1.14,
                            "sl": 1.139, "tp": 1.145, "rrr": 5, "zone_width_pips": 4,
                            "sl_distance_pips": 4, "confidence": 0.7})
check("AT-02 fails closed on an UNKNOWN pair", not _v3.passed)

# ============ 2. an unvetted predicate is NOT trusted from one vote ========
def _custom(c): return pr._v("AT-99", True, "X", "d")
_t = pr.trust(_custom, {"pair": "EUR/USD", "direction": "long", "entry": 1.14,
                        "sl": 1.139, "tp": 1.145, "rrr": 5, "zone_width_pips": 4,
                        "sl_distance_pips": 4, "confidence": 0.7})
check("an UNVETTED predicate is INCONCLUSIVE, not TRUSTED", _t.status == "INCONCLUSIVE")
_t2 = pr.trust(pr.at_01_rrr_floor, {"pair": "EUR/USD"})
check("the INCONCLUSIVE path uses the AT-XX token", _t2.predicate.startswith("AT-"))

# ============ 3. geometry: non-physical prices + swapped scales ===========
check("a NEGATIVE price set fails closed",
      pr.geometry_witness({"pair": "EUR/USD", "direction": "long", "entry": -1.14,
                           "sl": -1.15, "tp": -1.10}) is False)
check("a SWAPPED pip scale is rejected",
      pr.geometry_witness({"pair": "EUR/USD", "direction": "long", "entry": 100.9,
                           "sl": 100.8, "tp": 101.0}) is False)

# ============ 4. the determinism type tags are unforgeable ================
_pairs = [(1.0, "__py_float__1.0", "float vs a tag-shaped string"),
          (b"abc", "__py_bytes__abc", "bytes vs a tag-shaped string"),
          (b"abc", bytearray(b"abc"), "bytes vs bytearray"),
          ([1, 2], (1, 2), "list vs tuple"),
          ({1, 2}, frozenset({1, 2}), "set vs frozenset")]
for _a, _b, _l in _pairs:
    check(f"distinct: {_l}", det.canonical(_a) != det.canonical(_b))
try:
    det.canonical({"__py_float__": "x"}); check("a forged tag is refused", False)
except ValueError:
    check("a forged tag is refused", True)
try:
    det.digest({"s": det._Tag({"__py_float__": "x"})}); check("a forged tag via digest is refused", False)
except ValueError:
    check("a forged tag via digest is refused", True)
# THE PUBLIC BYPASS (round 36): `canonical(obj, _trust=False)` skipped the refusal,
# so ANY caller could forge a tag. The parameter must not exist.
check("canonical has NO trust-bypass parameter",
      "_trust" not in det.canonical.__code__.co_varnames)
check("_render is its own function, not a canonical flag",
      det._render.__code__.co_argcount == 1)
_c = {}; _c["self"] = _c
try:
    det.canonical(_c); check("a cycle is a NAMED refusal", False)
except ValueError:
    check("a cycle is a NAMED refusal", True)
# round 39: a scalar SUBCLASS must be tagged (IntEnum/StrEnum/custom subclasses)
import enum as _enum
class _E(_enum.IntEnum): X = 1
check("an IntEnum is distinct from its base int",
      det.canonical(_E.X) != det.canonical(1))
class _S(str): pass
check("a str subclass is distinct from a plain str",
      det.canonical(_S("a")) != det.canonical("a"))

# round 39: the session hour needs a LEFT boundary
check("a 3-digit hour is refused", pr._session_hhmm("1102:00") is None)
check("a valid session still parses", pr._session_hhmm("02:00") == (2, 0, 0))

# round 39: a duplicate zone_id must be refused
_d = oms.TradeDecision(pair="EUR/USD", direction="long", entry=1.14, sl=1.139,
                       tp=1.145, rrr=5, confidence=0.7, zone_id="Z")
try:
    oms.simulate([_d, _d], 0.001, {"Z": "tp"}); check("a duplicate zone is refused", False)
except ValueError:
    check("a duplicate zone is refused", True)

check("the pinned determinism law still holds",
      det.RunDigest({"s": {"decided": 1}}).sha == det.RunDigest({"s": {"decided": 1}}).sha)

# ============ 5. the OMS refuses invalid books ============================
for _r, _l in ((float("nan"), "nan"), (-1, "negative")):
    try:
        oms.simulate([], _r, {}); check(f"simulate([], {_l}) refuses", False)
    except ValueError:
        check(f"simulate([], {_l}) refuses", True)
try:
    oms.Portfolio(trades=["junk"]); check("Portfolio refuses a non-TradeResult", False)
except ValueError:
    check("Portfolio refuses a non-TradeResult", True)

# ============ 6. the scanner catches the evasions =========================
_ev = [("from os import open\nopen(p, O_WRONLY)", "os.open via from-import"),
       ("from os import mkdir\nmkdir(p)", "a from-import writer"),
       ("import os as o\no.makedirs(p)", "an aliased writer"),
       ("open(get(),\"w\")", "a nested-call write"),
       ("open(path,\n \"w\")", "a multiline write")]
for _src, _l in _ev:
    _hit = bool([n for n, p in cs.WRITE_FORBIDDEN.items() if re.search(p, _src)]) or \
           bool(cs.scan_write_suspects(_src))
    check(f"the scanner catches: {_l}", _hit)
for _src, _l in (("open(p, \"r\")", "a plain read"), ("open(\"bar\",\"r\")", "a filename with a mode letter")):
    _hit = bool([n for n, p in cs.WRITE_FORBIDDEN.items() if re.search(p, _src)])
    check(f"no false positive: {_l}", not _hit)

# ============ 7. the pane predicates are not forgeable ====================
_forged_g = " GATE DECISIONS\n [????  ] G-X\n            [REJECT] fake"
check("has_gate_decisions resists a forged detail marker",
      pane.has_gate_decisions(_forged_g) is False)
_forged_p = (" DECIDER PROBABILITIES (x)\n===\n REJECTION LOG (1)\n [REJECT] x\n"
             "            argmax= | #")
check("has_probability_bars resists a forged payload",
      pane.has_probability_bars(_forged_p) is False)
_real = pane.render(pane.PaneModel(
    pair="DXY", session="L", pnl_pips=1, open_positions=1,
    decider={"E1.Q4": {"strong_supply": 0.83, "neutral": 0.12, "strong_demand": 0.05}},
    gates=[{"gate": "G-RRR", "passed": True, "token": "G-RRR_PASS", "detail": "ok"}],
    rejections=[]))
check("has_probability_bars sees a REAL pane", pane.has_probability_bars(_real) is True)
check("has_gate_decisions sees a REAL verdict", pane.has_gate_decisions(_real) is True)

ok = not failures
print(f"[TOKEN] test_fix_effectiveness" if ok else "[TOKEN-ABSENT] test_fix_effectiveness")
print(f"[DETAIL] fix-effectiveness checks = {len(failures)} FAILED of the suite")
for f in failures:
    print(f"[DETAIL]   FAILED: {f}")
sys.exit(0 if ok else 1)
