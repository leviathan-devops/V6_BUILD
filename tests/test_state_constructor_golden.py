import _boot, sys, json
from pathlib import Path
from state_constructor import (parse_bars, render_state, atr, swing_levels,
                               FutureBarLeak, EmptyBars, session_label, in_london,
                               count_tokens, assert_state_fits, STATE_DELIM)

ANCHOR = 1783317600000   # the harness canon (2026-07-06T06:00:00Z)
FIXD = Path(__file__).resolve().parent.parent / "shared/fixtures"

# THE ANCHORED FIXTURE: every bar <= the anchor. This file is the canonical
# one; bars_raw.json is the WIDE harvest (it spans days past the anchor).
anchored = json.loads((FIXD/"bars_anchored.json").read_text())
raw      = json.loads((FIXD/"bars_raw.json").read_text())

feeds, errors = {}, []
for feed in anchored:
    pair, tf, bars = feed["pair"], feed["timeframe"], feed.get("bars") or []
    try:
        feeds[(pair, tf)] = parse_bars(bars, ANCHOR)
    except (FutureBarLeak, EmptyBars, ValueError) as e:
        errors.append(f"{pair} {tf}: {type(e).__name__}: {e}")

state = render_state("EUR/USD", ANCHOR, feeds, session_utc=session_label(ANCHOR))
n_tok = assert_state_fits(state)
main = feeds.get(("EUR/USD","30m"), [])
a, (hi, lo) = atr(main), swing_levels(main)

# ADVERSARIAL A: a bar past the anchor must RAISE (not be silently dropped)
leak_ok = False
try:
    parse_bars([{"ts": ANCHOR+1, "open":1,"high":1,"low":1,"close":1}], ANCHOR)
except FutureBarLeak as e:
    leak_ok = "FUTURE_BAR_LEAK" in str(e)

# ADVERSARIAL A2: THE WIDE HARVEST must be REFUSED — this is the probe that
# proves the temporal law bites on real data, not just a synthetic bar. The
# fixture spans days past the anchor, so parsing it unfiltered MUST raise.
wide_refused, wide_detail = False, ""
try:
    parse_bars((raw[0].get("bars") or []), ANCHOR)
except FutureBarLeak as e:
    wide_refused, wide_detail = True, str(e)[:70]

# ADVERSARIAL B: empty bars must RAISE with a NAMED token
empty_ok = False
try:
    parse_bars([], ANCHOR)
except EmptyBars as e:
    empty_ok = "NO_BARS" in str(e)

# ADVERSARIAL C: a bar with NO timestamp must RAISE (the audit fix — it used
# to become ts=0, pass the anchor check, and pollute the ordering)
nots_ok = False
try:
    parse_bars([{"open":1,"high":1,"low":1,"close":1}], ANCHOR)
except ValueError as e:
    nots_ok = "BAR_MISSING_TIMESTAMP" in str(e)

# ADVERSARIAL D: every kept bar is <= anchor
all_le = all(b.ts <= ANCHOR for bars in feeds.values() for b in bars)
# ADVERSARIAL E: no kept bar has ts == 0 (the silent-epoch defect)
no_epoch = all(b.ts > 0 for bars in feeds.values() for b in bars)

grammar_ok = state.startswith(STATE_DELIM)
ok = (not errors) and leak_ok and wide_refused and empty_ok and nots_ok \
     and all_le and no_epoch and grammar_ok and n_tok <= 8192

print(f"[TOKEN] test_state_constructor_golden" if ok else f"[TOKEN-ABSENT] test_state_constructor_golden")
print(f"[DETAIL] anchored feeds parsed={len(feeds)} errors={errors}")
print(f"[DETAIL] EUR/USD 30m bars={len(main)} ATR14={a} swing=({hi},{lo})")
print(f"[DETAIL] state tokens={n_tok}/8192")
print(f"[DETAIL] FUTURE_BAR_LEAK fires on a synthetic post-anchor bar = {leak_ok}")
print(f"[DETAIL] THE WIDE HARVEST IS REFUSED = {wide_refused} ({wide_detail})")
print(f"[DETAIL] NO_BARS fires on an empty feed = {empty_ok}")
print(f"[DETAIL] BAR_MISSING_TIMESTAMP fires on a timeless bar = {nots_ok}")
print(f"[DETAIL] all retained bars <= anchor = {all_le} | no ts==0 epoch bars = {no_epoch}")
print(f"[DETAIL] state opens with {STATE_DELIM!r} = {grammar_ok}")
print(f"[DETAIL] session at anchor = {session_label(ANCHOR)} in_london={in_london(ANCHOR)}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_state_constructor_golden")
sys.exit(0 if ok else 1)
