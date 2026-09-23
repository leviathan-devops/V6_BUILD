import _boot, sys, json
from pathlib import Path
from state_constructor import (parse_bars, render_state, atr, swing_levels,
                               FutureBarLeak, EmptyBars, session_label, in_london,
                               count_tokens, assert_state_fits, STATE_DELIM)

ANCHOR = 1783317600000   # the harness canon (golden-week.json meta.analysisPointMs)
FIX = Path("/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD/shared/fixtures/bars_raw.json")
raw = json.loads(FIX.read_text())

feeds, errors = {}, []
for feed in raw:
    pair, tf, bars = feed["pair"], feed["timeframe"], feed.get("bars") or []
    try:
        feeds[(pair, tf)] = parse_bars(bars, ANCHOR)
    except FutureBarLeak as e:
        errors.append(f"{pair} {tf}: {e}")
    except EmptyBars as e:
        errors.append(f"{pair} {tf}: {e}")

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

# ADVERSARIAL B: empty bars must RAISE with a NAMED token
empty_ok = False
try:
    parse_bars([], ANCHOR)
except EmptyBars as e:
    empty_ok = "NO_BARS" in str(e)

# ADVERSARIAL C: every kept bar is <= anchor
all_le = all(b.ts <= ANCHOR for bars in feeds.values() for b in bars)

# ADVERSARIAL D: the state must carry the grammar delimiters
grammar_ok = state.startswith(STATE_DELIM)

ok = (not errors) and leak_ok and empty_ok and all_le and grammar_ok and n_tok <= 8192
print(f"[TOKEN] test_state_constructor_golden" if ok else f"[TOKEN-ABSENT] test_state_constructor_golden")
print(f"[DETAIL] feeds parsed={len(feeds)} errors={errors}")
print(f"[DETAIL] EUR/USD 30m bars={len(main)} ATR14={a} swing=({hi},{lo})")
print(f"[DETAIL] state tokens={n_tok}/8192 (limit ok)")
print(f"[DETAIL] FUTURE_BAR_LEAK fires on a post-anchor bar = {leak_ok}")
print(f"[DETAIL] NO_BARS fires on an empty feed = {empty_ok}")
print(f"[DETAIL] all retained bars <= anchor = {all_le}")
print(f"[DETAIL] state opens with {STATE_DELIM!r} = {grammar_ok}")
print(f"[DETAIL] session at anchor = {session_label(ANCHOR)} in_london={in_london(ANCHOR)}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_state_constructor_golden")
sys.exit(0 if ok else 1)
