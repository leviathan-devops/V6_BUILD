import _boot, sys, datetime as dt
from state_constructor import session_label, in_london, et_offset_hours

def utc_ms(y,m,d,H,M):
    return int(dt.datetime(y,m,d,H,M,tzinfo=dt.timezone.utc).timestamp()*1000)

# July = EDT (-4). London 02:00-05:00 ET == 06:00-09:00 UTC.
cases = [
    (utc_ms(2026,7,6,6,0),  True,  "London open"),
    (utc_ms(2026,7,6,7,30), True,  "mid London"),
    (utc_ms(2026,7,6,9,0),  True,  "London close"),
    (utc_ms(2026,7,6,9,30), False, "just after close"),
    (utc_ms(2026,7,6,5,30), False, "just before open"),
    (utc_ms(2026,7,6,3,0),  False, "Asian session"),
    (utc_ms(2026,7,6,14,0), False, "NY morning (08:00 ET is NY_AM)"),
]
bad = []
for ms, expect, desc in cases:
    got = in_london(ms)
    if got != expect: bad.append(f"{desc}: got {got} want {expect} ({session_label(ms)})")

# ADVERSARIAL: the boundary is INCLUSIVE on both ends
edge_ok = in_london(utc_ms(2026,7,6,6,0)) and in_london(utc_ms(2026,7,6,9,0))
# ADVERSARIAL: the ET offset flips outside DST months
off_ok = et_offset_hours(utc_ms(2026,7,6,12,0)) == -4 and et_offset_hours(utc_ms(2026,1,15,12,0)) == -5

ok = (not bad) and edge_ok and off_ok
print(f"[TOKEN] test_session_london_window" if ok else "[TOKEN-ABSENT] test_session_london_window")
for ms, expect, desc in cases:
    print(f"[DETAIL] {desc}: {session_label(ms)} in_london={in_london(ms)} (want {expect})")
print(f"[DETAIL] inclusive boundaries = {edge_ok} | ET offset Jul=-4 Jan=-5 = {off_ok}")
print(f"[DETAIL] mismatches={bad}")
print(f"RESULT: {'PASS' if ok else 'FAIL'} test_session_london_window")
sys.exit(0 if ok else 1)
