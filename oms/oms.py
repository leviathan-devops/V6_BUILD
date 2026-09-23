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
from dataclasses import dataclass, field

PIP = {"EUR/USD": 0.0001, "GBP/USD": 0.0001, "DXY": 0.01}
PIP_VALUE_PER_UNIT = {"EUR/USD": 10.0, "GBP/USD": 10.0, "DXY": 1.0}
DEFAULT_UNITS = 100_000
EQUITY_PER_PIP = 10.0    # $ per pip at 1 standard lot on a 5-digit FX pair


@dataclass
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


@dataclass
class Fill:
    """One executed trade. The pair travels WITH the fill (pip source)."""
    pair: str
    direction: str
    entry: float
    exit: float
    units: int
    commission_rate: float     # round-trip rate, e.g. 0.001

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


@dataclass
class TradeResult:
    decision: TradeDecision
    fill: Fill
    outcome: str            # "tp" | "sl"

    @property
    def gross_pips(self) -> float: return self.fill.gross_pips

    @property
    def cost_pips(self) -> float: return self.fill.cost_pips

    @property
    def net_pips(self) -> float: return self.fill.net_pips


@dataclass
class Portfolio:
    starting_equity: float = 100_000.0
    trades: list[TradeResult] = field(default_factory=list)

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
    pf = Portfolio()
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
        pf.trades.append(TradeResult(decision=d, fill=fill, outcome=outcome))
    return pf


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
