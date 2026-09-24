import _boot, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "forensic"))
from classify_38 import run, parse_laws, parse_trades, parse_outcome

r = run()
laws, trades, outcome, verdicts = r["laws"], r["trades"], r["outcome"], r["verdicts"]

# ---- the source must actually be present and parsed -------------------------
ok_laws = len(laws) == 7
ok_trades = len(trades) == 30          # 30 rows carry SL/MAE/util
ok_outcome = outcome.get("setups") == 36 and outcome.get("win") == 30

# ---- every law is CLASSIFIED (obeyed / violated / not-classifiable) ---------
# a law is never silently dropped: it must land in exactly one bucket
ok_every_law_classified = all(
    (v.tested + v.not_classifiable) == len(trades) for v in verdicts.values())

# ---- the source's own verdict must be reproduced by the predicate -----------
# LAW 6 is the util-ratio test: the classifier's violated count must EQUAL the
# number of rows the source itself marked "SL TOO WIDE".
n_sl_wide_source = sum(1 for t in trades if t.sl_too_wide)
law6 = next(v for k, v in verdicts.items() if "consequence" in v.title.lower())
ok_law6_reproduces = law6.violated == n_sl_wide_source

# ---- the per-pair outcome must reproduce the source's totals ---------------
per = outcome.get("per_pair", {})
ok_pairs = (per.get("DXY", {}).get("setups") == 13
            and per.get("EUR/USD", {}).get("setups") == 13
            and per.get("GBP/USD", {}).get("setups") == 10)
total_setups = sum(v["setups"] for v in per.values())
ok_total = total_setups == 36

# ---- the HONEST part: which laws the data CANNOT test ----------------------
n_unclassifiable = r["n_unclassifiable"]
# LAW 1, 3, 4, 5 have no column in the row data -> 4 laws
ok_honest_gap = n_unclassifiable == 4

ok = (ok_laws and ok_trades and ok_outcome and ok_every_law_classified
      and ok_law6_reproduces and ok_pairs and ok_total and ok_honest_gap)

print(f"[TOKEN] test_forensic_38_classification" if ok else "[TOKEN-ABSENT] test_forensic_38_classification")
print(f"[DETAIL] laws parsed = {len(laws)} (from the forensic doc's 7 UNIVERSAL LAWS)")
for law, title in laws:
    v = verdicts[law]
    if v.tested:
        print(f"[DETAIL]   {law}: tested {v.tested} | OBEYED {v.obeyed} | VIOLATED {v.violated}  ({v.note[:52]})")
    else:
        print(f"[DETAIL]   {law}: NOT CLASSIFIABLE ({v.note[:60]})")
print(f"[DETAIL] trades parsed from the SL/MAE table = {len(trades)} (rows 1-30)")
print(f"[DETAIL] source's own SL-TOO-WIDE count = {n_sl_wide_source} | LAW 6 predicate reproduced it = {ok_law6_reproduces}")
print(f"[DETAIL] outcome audit: {outcome.get('setups')} setups, {outcome.get('win')}W/{outcome.get('loss')}L")
for p, d in per.items():
    print(f"[DETAIL]   {p}: {d['setups']} setups {d['w']}W/{d['l']}L win {d['win_rate']}% total {d['total_R']}R")
print(f"[DETAIL] laws classified clean = {r['n_obeyed_clean']} | with violations = {r['n_with_violations']} | unclassifiable = {r['n_unclassifiable']}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_forensic_38_classification")
sys.exit(0 if ok else 1)
