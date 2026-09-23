"""decider/calibration.py — the post-hoc confidence calibration layer.

THE FINDING THIS ANSWERS (measured 2026-09-23): on the DXY trading domain the
published Decider is 12/12 CORRECT but states only 0.59-0.96 confidence, so its
raw ECE is 0.18. When accuracy is 1.0, ANY stated probability below 1.0
contributes |1 - p| to the ECE by construction. The model is UNDER-CONFIDENT.

THE METHOD: temperature scaling. A single scalar T maps a stated probability to
a calibrated one:
    p' = sigmoid( logit(p) / T )
T > 1 SOFTENS (for over-confidence), T < 1 SHARPENS (for under-confidence).
T is fitted by minimising the negative log-likelihood on a FIT set and is then
applied unchanged to a HELD-OUT set where the ECE is measured.

THE LAW THIS MODULE OBEYS: the calibration is fitted on data the measurement
does not see. Fitting and measuring on the same rows is the circular-fixture
error — a number that proves nothing.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


def _logit(p: float) -> float:
    """The log-odds of a probability.

    AUDIT FIX (round 7): out-of-range and NaN values were silently CLIPPED, so
    p=2.0, p=-1.0 and p=nan all produced plausible-looking metrics. A
    calibration input outside [0,1] is a caller error, not a value to clip.
    """
    try:
        p = float(p)
    except (TypeError, ValueError, OverflowError) as e:
        raise ValueError(f"INVALID_PROBABILITY: {p!r} is not a number") from e
    if p != p or p in (float("inf"), float("-inf")):
        raise ValueError(f"INVALID_PROBABILITY: {p!r} is not finite")
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"INVALID_PROBABILITY: {p} is outside [0, 1]")
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    """A SATURATING sigmoid.

    AUDIT FIX: the naive `1/(1+exp(-x))` raises OverflowError for large |x|
    (e.g. p=0.1 with T=0.001 -> x ~ -2200). The two-branch form saturates at
    0 and 1 instead of crashing, which is what a calibration layer must do.
    """
    if x >= 0:
        z = math.exp(-x) if x < 700 else 0.0
        return 1 / (1 + z)
    z = math.exp(x) if x > -700 else 0.0
    return z / (1 + z)


def apply_T(p: float, T: float) -> float:
    """Calibrate one stated probability with temperature T."""
    # AUDIT FIX (round 7): `T <= 0` is False for NaN, so apply_T(p, nan) silently
    # returned 0.0 and apply_T(p, inf) returned 0.5. Both are validated now.
    if T != T or T in (float("inf"), float("-inf")) or T <= 0:
        raise ValueError(f"INVALID_TEMPERATURE: {T!r} (want a finite T > 0)")
    return _sigmoid(_logit(p) / T)


def nll(pairs, T: float = 1.0) -> float:
    """Mean negative log-likelihood of [(p_hat, correct)] under temperature T."""
    if not pairs:
        return float("inf")
    total = 0.0
    for p, correct in pairs:
        q = apply_T(p, T)
        total -= math.log(max(q, 1e-9)) if correct else math.log(max(1 - q, 1e-9))
    return total / len(pairs)


def ece(pairs, T: float = 1.0, n_bins: int = 10) -> float | None:
    """Expected Calibration Error of [(p_hat, correct)] under temperature T."""
    if not pairs:
        return None
    if not isinstance(n_bins, int) or n_bins < 1:
        raise ValueError(f"INVALID_N_BINS: {n_bins!r} (want an int >= 1)")
    bins = [[] for _ in range(n_bins)]
    for p, correct in pairs:
        q = apply_T(p, T)
        bins[min(n_bins - 1, max(0, int(q * n_bins)))].append((q, correct))
    n, total = len(pairs), 0.0
    for b in bins:
        if not b:
            continue
        conf = sum(q for q, _ in b) / len(b)
        acc = sum(1 for _, c in b if c) / len(b)
        total += (len(b) / n) * abs(acc - conf)
    return total


@dataclass(frozen=True)
class FittedTemperature:
    T: float
    fit_nll: float
    baseline_nll: float
    fit_n: int
    clipped: bool = False      # True when the minimum sits on the grid bound

    @property
    def improves(self) -> bool:
        return self.fit_nll < self.baseline_nll


def fit(pairs, lo: float = 0.05, hi: float = 5.0, steps: int = 500) -> FittedTemperature:
    """Fit T by minimising the NLL on `pairs` (the FIT set)."""
    if not pairs:
        raise ValueError("NO_FIT_DATA: cannot fit a temperature on an empty set")
    # AUDIT FIX: a zero/negative range silently divided by zero, and a grid that
    # CLIPS at its bounds reported an endpoint T as if it were the minimum.
    if lo <= 0 or hi <= lo or steps < 1:
        raise ValueError(f"INVALID_FIT_GRID: lo={lo} hi={hi} steps={steps}")
    # AUDIT FIX (round 6): seeding best at T=1.0 could return a T OUTSIDE
    # [lo,hi] when the grid excludes 1.0, and report it as unclipped. The seed
    # is now a grid point.
    best_T, best = lo, nll(pairs, lo)
    for i in range(steps + 1):
        T = lo + (hi - lo) * i / steps
        v = nll(pairs, T)
        if v < best:
            best_T, best = T, v
    # AUDIT FIX: report when the minimum sits ON a bound — the fitted T is then
    # an artefact of the grid, not the data's minimum.
    at_bound = abs(best_T - lo) < 1e-9 or abs(best_T - hi) < 1e-9
    return FittedTemperature(best_T, best, nll(pairs, 1.0), len(pairs),
                             clipped=at_bound)


def split(rows, seed: int = 20260923, fit_frac: float = 0.5):
    """A deterministic fit/eval split. Returns (fit_rows, eval_rows)."""
    import random
    r = list(rows)
    random.Random(seed).shuffle(r)
    # AUDIT FIX: a degenerate split (an empty eval partition) silently broke the
    # fit/eval separation the module's own docstring requires.
    if len(r) < 2:
        raise ValueError(f"SPLIT_TOO_SMALL: need >= 2 rows, got {len(r)}")
    # AUDIT FIX (round 7): fit_frac outside (0,1) was silently clamped, hiding
    # a caller error and breaking the fit/eval separation this module promises.
    if not (0.0 < fit_frac < 1.0):
        raise ValueError(f"INVALID_FIT_FRAC: {fit_frac} (want 0 < f < 1)")
    k = max(1, min(len(r) - 1, int(len(r) * fit_frac)))
    return r[:k], r[k:]
