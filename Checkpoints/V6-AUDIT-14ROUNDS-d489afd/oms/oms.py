"""oms/oms.py — the order-management simulation for the Plutus V6 circuit.

Wraps the execution-cost question the blueprint names as the single most
important validation (blueprint §3.2 / TensorTrade's own research finding):
    agents profitable at 0% commission LOSE MONEY at 0.1% commission.
Whether the golden week survives that is the reason this layer exists.

Arithmetic is explicit and per-fill. Commission is modelled as a round-trip
rate applied to notional, exactly per blueprint §2.3 MATH CALL 5:
    commission_cost = units * rate * 2      (currency units)
    cost_in_pips    = commission_cost / (units * pip)
                    = rate * 2 / pip        (independent of units)
Worked example from the blueprint: 100000 * 0.001 * 2 = $200 = 20.0 pips at
$10/pip, so 28.5 gross -> 8.5 net. This module reproduces that exactly.
"""
from __future__ import annotations
from types import MappingProxyType
from collections.abc import Mapping
from dataclasses import dataclass, field

# AUDIT FIX (round 11): the round-10 fix made PIP_VALUE_PER_UNIT read-only but
# left PIP a plain MUTABLE dict — so `PIP['EUR/USD'] = 9.9` after import still
# desynced cost_pips from equity, and the comment claimed otherwise. Both maps
# now derive from ONE read-only source.
# AUDIT FIX (round 12): `PIP` was a LIVE view over the mutable source while
# PIP_VALUE_PER_UNIT was an IMPORT-TIME SNAPSHOT — so mutating the source (or
# adding a pair) changed cost_pips but left equity stale, re-creating the exact
# desync by another route. Both are now LIVE views over ONE frozen source, and
# PIP_VALUE_PER_UNIT is DERIVED at access time so it cannot drift.
_PIP_SOURCE = MappingProxyType({"EUR/USD": 0.0001, "GBP/USD": 0.0001,
                                "DXY": 0.01})
PIP = _PIP_SOURCE
# $/pip at DEFAULT_UNITS (100k). DERIVED, not asserted: units * pip.
#   EUR/USD  100_000 * 0.0001 =    10.0
#   DXY      100_000 * 0.01   = 1_000.0
# AUDIT FIX (round 9): DXY was 1.0, which DISAGREED with the cost model by
# 1000x — `Fill.cost_pips` implies $/pip = units*pip = 1000 for DXY, while the
# equity conversion used 1.0. Two conversions for one quantity must agree, and
# the derivation above is the single source.

DEFAULT_UNITS = 100_000
# AUDIT FIX (round 10): PIP and PIP_VALUE_PER_UNIT were two MUTABLE dicts for
# one quantity, so a post-import mutation (or a pair added to only one) made
# equity and cost_pips disagree silently — the same 1000x class as before, but
# undetectable. Both are now read-only views.
class _DerivedPipValue(Mapping):
    """$/pip, DERIVED from PIP and DEFAULT_UNITS at ACCESS time.

    A snapshot would silently desync from PIP the moment either input changes
    (audit round 12); deriving on access makes drift impossible by construction.
    """
    def __getitem__(self, pair): return DEFAULT_UNITS * PIP[pair]
    def __iter__(self): return iter(PIP)
    def __len__(self): return len(PIP)
    def __contains__(self, pair): return pair in PIP


PIP_VALUE_PER_UNIT = _DerivedPipValue()
# NOTE: no flat EQUITY_PER_PIP constant. $/pip is per-pair AND per-size; a flat
# value is the DXY 1000x error waiting to happen. Portfolio._equity_per_pip
# derives it.


@dataclass(frozen=True)
class TradeDecision:
    """The typed output of the circuit — the only thing OMS consumes."""
    pair: str
    direction: str          # long | short
    entry: float
    sl: float
    tp: float
    rrr: float
    confidence: float
    session_utc: str = ""
    grade: str = ""
    zone_id: str = ""

    def __post_init__(self):
        """THE BRACKET INVARIANT, checked where it belongs.

        AUDIT FIX (round 14): the orientation was never validated anywhere, so an
        inverted bracket (a long with tp < entry, or sl > entry) flowed into the
        OMS and produced NEGATIVE gross_pips on a "tp" win — inverting the P&L
        with no error. The invariant is structural: for a long the target is
        ABOVE entry and the stop BELOW; for a short, the reverse.
        """
        if self.direction not in ("long", "short"):
            raise ValueError(f"INVALID_DIRECTION: {self.direction!r}")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   and v == v and abs(v) != float("inf")
                   for v in (self.entry, self.sl, self.tp)):
            raise ValueError(f"INVALID_PRICES: non-finite entry/sl/tp in {self!r}")
        if self.direction == "long" and not (self.tp > self.entry > self.sl):
            raise ValueError(
                f"INVALID_BRACKET: long needs tp > entry > sl, got "
                f"tp={self.tp} entry={self.entry} sl={self.sl}")
        if self.direction == "short" and not (self.sl > self.entry > self.tp):
            raise ValueError(
                f"INVALID_BRACKET: short needs sl > entry > tp, got "
                f"sl={self.sl} entry={self.entry} tp={self.tp}")


@dataclass(frozen=True)
class Fill:
    """One executed trade. The pair travels WITH the fill (pip source)."""
    pair: str
    direction: str
    entry: float
    exit: float
    units: int
    commission_rate: float     # round-trip rate, e.g. 0.001

    def __post_init__(self):
        """AUDIT FIX (round 14): validation was LAZY — it ran only when a property
        was accessed — so an invalid Fill constructed fine, entered a Portfolio,
        and failed much later during aggregation. This module's contract is to
        fail LOUDLY, and the earliest honest place is creation.

        Three classes were reachable before this guard:
          - a NON-FINITE input: `rate < 0` is False for NaN, and entry/exit were
            never checked, so a NaN commission poisoned every downstream total
            and an inf price produced inf pips;
          - a NON-POSITIVE unit count (already caught lazily, now eagerly);
          - an INVERTED BRACKET: a long whose exit sat BELOW its entry produced
            NEGATIVE gross_pips on a "win", inverting the P&L with no error.
        """
        vals = (self.entry, self.exit, self.units, self.commission_rate)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   and v == v and abs(v) != float("inf") for v in vals):
            raise ValueError(f"INVALID_FILL: non-finite or non-numeric input {self!r}")
        if self.units <= 0:
            raise ValueError(f"INVALID_UNITS: {self.units} (must be positive)")
        if self.commission_rate < 0:
            raise ValueError(f"INVALID_COMMISSION: {self.commission_rate} (must be >= 0)")
        if self.direction not in ("long", "short"):
            raise ValueError(f"INVALID_DIRECTION: {self.direction!r}")
        # AUDIT FIX (round 17 H6): the unknown-pair check stayed LAZY (it lived
        # only in the `pip` property), so a bad pair constructed fine, entered a
        # Portfolio, and failed much later during aggregation — the exact lazy
        # failure mode this __post_init__ exists to close.
        if self.pair not in PIP:
            raise ValueError(f"UNKNOWN_PAIR: {self.pair!r} has no declared pip scale "
                             f"(known: {sorted(PIP)})")
        # NOTE (round 14, my own correction): a first version ALSO checked that a
        # long's exit sat above its entry. That is WRONG — an SL hit is a
        # legitimate LOSS whose exit is below entry. The bracket invariant belongs
        # on the DECISION (tp/sl relative to entry), not on the fill's outcome.

    @property
    def pip(self) -> float:
        # AUDIT FIX: an unknown pair must fail loudly, not default to FX scale.
        if self.pair not in PIP:
            raise ValueError(f"UNKNOWN_PAIR: {self.pair!r} has no declared pip scale "
                             f"(known: {sorted(PIP)})")
        return PIP[self.pair]

    @property
    def gross_pips(self) -> float:
        # AUDIT FIX: any direction other than exactly "long"/"short" silently
        # inverted P&L. Validate.
        if self.direction not in ("long", "short"):
            raise ValueError(f"INVALID_DIRECTION: {self.direction!r}")
        sign = 1.0 if self.direction == "long" else -1.0
        return round(sign * (self.exit - self.entry) / self.pip, 4)

    @property
    def commission_cost(self) -> float:
        """Round-trip cost in quote currency: units * rate * 2."""
        return self.units * self.commission_rate * 2

    @property
    def cost_pips(self) -> float:
        """The same cost expressed in pips: (units*rate*2) / (units*pip)."""
        # AUDIT FIX: units=0 divided by zero, and a negative rate turned the cost
        # into a rebate that inflated P&L.
        if self.units <= 0:
            raise ValueError(f"INVALID_UNITS: {self.units} (must be positive)")
        if self.commission_rate < 0:
            raise ValueError(f"INVALID_COMMISSION: {self.commission_rate} (must be >= 0)")
        return round(self.commission_cost / (self.units * self.pip), 4)

    @property
    def net_pips(self) -> float:
        return round(self.gross_pips - self.cost_pips, 4)


@dataclass(frozen=True)
class TradeResult:
    # AUDIT FIX (round 17 H8): nothing checked that `outcome` was one of
    # ('tp','sl') nor that the fill's exit MATCHED the level that outcome names —
    # so `outcome='tp'` beside a fill that exited at the STOP was accepted and
    # corrupted the aggregate. The label must agree with the numbers.
    decision: TradeDecision
    fill: Fill
    outcome: str            # "tp" | "sl"

    def __post_init__(self):
        """THE LABEL MUST AGREE WITH THE NUMBERS (audit round 17 H8).

        `simulate` derives the exit from the outcome (`d.tp if outcome == "tp"
        else d.sl`), but nothing ENFORCED that a manually built TradeResult obeys
        the same rule — so `outcome="tp"` beside a fill that exited at the STOP
        was accepted, and the aggregate reported a winner that lost. The invariant
        is checked here, where the pair (decision, fill, outcome) first exists.
        """
        if self.outcome not in ("tp", "sl"):
            raise ValueError(f"INVALID_OUTCOME: {self.outcome!r} (want 'tp'|'sl')")
        if self.fill.pair != self.decision.pair:
            raise ValueError(f"OUTCOME_PAIR_MISMATCH: fill {self.fill.pair!r} vs "
                             f"decision {self.decision.pair!r}")
        if self.fill.direction != self.decision.direction:
            raise ValueError(f"OUTCOME_DIRECTION_MISMATCH: fill "
                             f"{self.fill.direction!r} vs decision "
                             f"{self.decision.direction!r}")
        want = self.decision.tp if self.outcome == "tp" else self.decision.sl
        if abs(self.fill.exit - want) > 1e-9:
            raise ValueError(
                f"OUTCOME_EXIT_MISMATCH: outcome {self.outcome!r} names {want}, "
                f"but the fill exited at {self.fill.exit}")

    @property
    def gross_pips(self) -> float: return self.fill.gross_pips

    @property
    def cost_pips(self) -> float: return self.fill.cost_pips

    @property
    def net_pips(self) -> float: return self.fill.net_pips


# AUDIT FIX (round 19): all four were MUTABLE dataclasses, so the eager
# __post_init__ validation was bypassable by post-construction assignment
# (`fill.entry = nan`, `d.tp = <inverted>`, `pf.starting_equity = nan`) — the
# invariants held only until someone reassigned a field. Frozen dataclasses make
# the validated state the ONLY state. (The `trades` LIST is still mutable, which
# is what `pf.trades.append` needs.)
@dataclass(frozen=True)
class Portfolio:
    starting_equity: float = 100_000.0
    trades: list[TradeResult] = field(default_factory=list)

    def __post_init__(self):
        """AUDIT FIX (round 17 H7): starting_equity was the ONE numeric input with
        no validation — and it is the WORST place to skip one. A NaN start made
        `if peak > 0` false, so `max_drawdown` returned 0.0 on a POISONED book:
        the report said "no drawdown" on outright ruin. A non-positive start is
        refused by name.
        """
        # AUDIT FIX (round 26): `trades` was stored BY REFERENCE, so a caller
        # holding the original list could mutate the book behind the digest —
        # and its ELEMENTS were never checked, so `Portfolio(trades=['junk'])`
        # constructed fine and failed much later in net_pips_total with an
        # AttributeError. It stays a LIST (simulate appends), but it is a COPY
        # of a VALIDATED list.
        _bad = [t for t in self.trades if not isinstance(t, TradeResult)]
        if _bad:
            raise ValueError(
                f"INVALID_TRADES: {len(_bad)} element(s) are not TradeResult "
                f"(first: {type(_bad[0]).__name__})")
        # AUDIT FIX (round 30): a plain list stays MUTABLE on a frozen dataclass,
        # so `pf.trades.append('junk')` bypassed the validation above. A tuple is
        # immutable — and `simulate` builds its Portfolio from the final list.
        object.__setattr__(self, "trades", tuple(self.trades))
        e = self.starting_equity
        if isinstance(e, bool) or not isinstance(e, (int, float)) \
                or e != e or abs(e) == float("inf"):
            raise ValueError(f"INVALID_STARTING_EQUITY: non-finite {e!r}")
        if e <= 0:
            raise ValueError(
                f"INVALID_STARTING_EQUITY: {e} must be positive (a non-positive "
                f"book cannot express a drawdown)")

    @property
    def net_pips_total(self) -> float:
        return round(sum(t.net_pips for t in self.trades), 4)

    @property
    def gross_pips_total(self) -> float:
        return round(sum(t.gross_pips for t in self.trades), 4)

    @property
    def total_costs(self) -> float:
        return round(sum(t.cost_pips for t in self.trades), 4)

    @property
    def win_rate(self) -> float:
        if not self.trades: return 0.0
        return round(sum(1 for t in self.trades if t.net_pips > 0) / len(self.trades), 4)

    def _equity_per_pip(self, t) -> float:
        """$/pip for this FILL.

        AUDIT FIX (round 6): $/pip scales LINEARLY with size — a 10k lot moves
        equity 10x less than a 100k lot. The first version returned a fixed
        $/pip per pair, so any Fill not at DEFAULT_UNITS silently misstated
        equity and drawdown. The size is now part of the conversion.
        """
        pair = t.fill.pair
        if pair not in PIP_VALUE_PER_UNIT:
            raise ValueError(
                f"UNKNOWN_PIP_VALUE: {pair!r} has no PIP_VALUE_PER_UNIT entry "
                f"(known: {sorted(PIP_VALUE_PER_UNIT)})")
        base = PIP_VALUE_PER_UNIT[pair]         # $/pip at DEFAULT_UNITS
        return base * (t.fill.units / DEFAULT_UNITS)

    @property
    def max_drawdown(self) -> float:
        equity, peak, dd = self.starting_equity, self.starting_equity, 0.0
        for t in self.trades:
            equity += t.net_pips * self._equity_per_pip(t)
            peak = max(peak, equity)
            if peak > 0:
                dd = max(dd, (peak - equity) / peak)
        return round(dd, 4)


def simulate(decisions: list[TradeDecision], commission_rate: float,
             outcomes: dict[str, str]) -> Portfolio:
    """Execute every decision at the given round-trip commission rate.

    `outcomes` maps zone_id -> "tp" | "sl" and is REQUIRED. AUDIT FIX: it used
    to default to "tp" (a WIN), so a missing or typo'd zone silently inflated
    P&L. The caller states each outcome; the OMS never assumes one.
    """
    if not isinstance(outcomes, dict):
        raise ValueError(
            f"OUTCOMES_REQUIRED: pass {{zone_id: 'tp'|'sl'}} — got {type(outcomes).__name__}")
    # AUDIT FIX (round 30): the book is built in a LOCAL list and handed to the
    # Portfolio at the end, because Portfolio.trades is now an IMMUTABLE tuple —
    # a mutable list on a frozen dataclass let `append('junk')` bypass the
    # TradeResult validation that __post_init__ performs.
    _trades: list[TradeResult] = []
    for d in decisions:
        # AUDIT FIX: a missing zone_id defaulted to "tp" (a WIN), so a typo or an
        # unlabelled trade silently inflated P&L. An unlabelled decision is now
        # a named refusal; an explicitly supplied outcome is required.
        if not d.zone_id:
            raise ValueError(
                f"UNLABELLED_TRADE: {d.pair} {d.direction} has no zone_id, so its "
                f"outcome cannot be resolved (pass a zone_id or an explicit outcome)")
        if d.zone_id not in outcomes:
            raise ValueError(
                f"NO_OUTCOME_FOR_ZONE: {d.zone_id!r} is absent from the outcomes map "
                f"(known: {sorted(outcomes)}) — refusing to assume a win")
        outcome = outcomes[d.zone_id]
        # AUDIT FIX: any typo was silently treated as an SL exit, flipping a
        # winner into a loser. Validate the outcome.
        if outcome not in ("tp", "sl"):
            raise ValueError(f"INVALID_OUTCOME: {outcome!r} for {d.zone_id!r} (want 'tp'|'sl')")
        exit_price = d.tp if outcome == "tp" else d.sl
        fill = Fill(pair=d.pair, direction=d.direction, entry=d.entry,
                    exit=exit_price, units=DEFAULT_UNITS,
                    commission_rate=commission_rate)
        _trades.append(TradeResult(decision=d, fill=fill, outcome=outcome))
    return Portfolio(trades=_trades)


def commission_sensitivity(decisions: list[TradeDecision],
                           rates=(0.0, 0.001, 0.002),
                           outcomes: dict[str, str] | None = None) -> dict[float, dict]:
    """The key analysis: P&L at 0% / 0.1% / 0.2% round-trip commission.

    `outcomes` is REQUIRED (see simulate). It defaults to None only so the
    signature is explicit about the caller having to supply it.
    """
    if outcomes is None:
        raise ValueError(
            "OUTCOMES_REQUIRED: state each trade's outcome — the golden week's "
            "canon record is 'tp' for all, and that must be written down, not assumed")
    out = {}
    for r in rates:
        pf = simulate(decisions, r, outcomes)
        out[r] = {
            "commission_rate": r,
            "net_pips": pf.net_pips_total,
            "gross_pips": pf.gross_pips_total,
            "costs_pips": pf.total_costs,
            "win_rate": pf.win_rate,
            "max_drawdown": pf.max_drawdown,
            "n_trades": len(pf.trades),
            "profitable": pf.net_pips_total > 0,
        }
    return out
