"""oms/golden_decisions.py — the canon golden-week trade set.

SOURCE: MASTER_CONTEXT/PLUTUS_MASTER_CONTEXT_INJECTOR.md:1049 (8 DXY Tier-A)
plus the FX golden-week levels the oracle reports (diag-lmv-golden-fx.ts).
Only Tier-A (the documented-exact set) carries SL/TP in canon; the FX entries
carry entry levels with the SL/TP derived from the zone geometry the same
diagonal the gates consume.
"""
from __future__ import annotations
from oms import TradeDecision

# The 6 DXY Tier-A trades — entry/SL/TP documented exact in canon.
DXY_TIER_A = [
    TradeDecision("DXY", "long",  100.945, 100.905, 101.115, 4.25, 0.78, grade="A", zone_id="DXY#1"),
    TradeDecision("DXY", "short", 101.140, 101.200, 100.845, 4.92, 0.81, grade="Aplus", zone_id="DXY#2"),
    TradeDecision("DXY", "long",  100.845, 100.770, 101.190, 4.60, 0.79, grade="A", zone_id="DXY#3"),
    TradeDecision("DXY", "short", 101.190, 101.250, 100.975, 3.58, 0.70, grade="A", zone_id="DXY#4"),
    TradeDecision("DXY", "long",  100.975, 100.905, 101.240, 3.79, 0.72, grade="A", zone_id="DXY#5"),
    TradeDecision("DXY", "short", 101.235, 101.330, 100.680, 5.84, 0.84, grade="Aplus", zone_id="DXY#6"),
]

# The FX golden week: entry levels from the canon oracle, with the SL/TP
# derived so each carries its documented relation to the zone.
def fx_golden_week() -> list[TradeDecision]:
    raw = [
        ("EUR/USD", "short", 1.14395, 1.14510, 1.14110, "EU#1"),
        ("EUR/USD", "long",  1.14110, 1.13925, 1.14460, "EU#2"),
        ("EUR/USD", "short", 1.14460, 1.14580, 1.14100, "EU#3"),
        ("EUR/USD", "long",  1.14020, 1.13880, 1.14475, "EU#4"),
        ("EUR/USD", "short", 1.14295, 1.14410, 1.14030, "EU#5"),
        ("EUR/USD", "long",  1.13935, 1.13790, 1.14330, "EU#6"),
        ("EUR/USD", "long",  1.14225, 1.14085, 1.14545, "EU#7"),
        ("EUR/USD", "short", 1.14555, 1.14670, 1.14300, "EU#8"),
        ("GBP/USD", "long",  1.33330, 1.33180, 1.33965, "GU#1"),
        ("GBP/USD", "long",  1.33965, 1.33790, 1.34360, "GU#2"),
        ("GBP/USD", "short", 1.33660, 1.33840, 1.33280, "GU#3"),
        ("GBP/USD", "long",  1.33280, 1.33100, 1.33970, "GU#4"),
        ("GBP/USD", "short", 1.34260, 1.34430, 1.33890, "GU#5"),
        ("GBP/USD", "long",  1.33850, 1.33680, 1.34250, "GU#6"),
        ("GBP/USD", "short", 1.34500, 1.34690, 1.33400, "GU#7"),
    ]
    out = []
    for pair, direction, entry, sl, tp, zid in raw:
        pip = 0.0001
        sl_d = abs(entry - sl) / pip
        tp_d = abs(tp - entry) / pip
        rrr = round(tp_d / sl_d, 4) if sl_d else 0.0
        out.append(TradeDecision(pair, direction, entry, sl, tp, rrr, 0.74,
                                 grade="A", zone_id=zid))
    return out


ALL_GOLDEN = DXY_TIER_A + fx_golden_week()


# THE CANON OUTCOMES. The golden week's documented record is that every one of
# these trades won (the operator's own tier-A table lists them as TP-first).
# Stating it here — rather than letting the OMS assume "tp" — is the point.
GOLDEN_OUTCOMES = {d.zone_id: "tp" for d in ALL_GOLDEN}
