"""limite/dual_compute.py — LIMITE COMPUTES, CODE VERIFIES.

The verifier runs every math query through BOTH paths:
  - the Limite model (via client.ask)
  - the python shadow (math_queries.code_truth)
and compares |model - code| against the query's tolerance.

On divergence it raises DualComputeDivergence carrying the named token
LIMITE_CODE_DIVERGENCE (the pin's AUTOMATIC-FAIL token). There is no
fallback: a diverging quantity aborts the trade, it does not get averaged.
"""
from __future__ import annotations
from dataclasses import dataclass
from math_queries import QUERIES, code_truth


class DualComputeDivergence(RuntimeError):
    def __init__(self, query_id: str, model: float, code: float, eps: float):
        self.query_id, self.model, self.code, self.eps = query_id, model, code, eps
        try:
            self.delta = abs(model - code)
            detail = (f"|limite {model:.6f} - code {code:.6f}| = {self.delta:.6f} "
                      f"> eps {eps}")
        except (TypeError, ValueError):
            self.delta = float("nan")
            detail = f"non-numeric comparison: limite={model!r} code={code!r}"
        super().__init__(f"LIMITE_CODE_DIVERGENCE [{query_id}]: {detail}")


@dataclass(frozen=True)
class DualResult:
    query_id: str
    model: float
    code: float
    delta: float
    eps: float
    raw: str
    passed: bool

    @property
    def token(self) -> str:
        return "G-DUAL_PASS" if self.passed else "LIMITE_CODE_DIVERGENCE"


def verify(query_id: str, model_value, raw: str = "", **kw) -> DualResult:
    """Verify ONE already-computed answer against the code shadow.

    AUDIT FIX: an unknown query_id raised a raw KeyError and a non-numeric
    model_value raised a raw TypeError, both escaping callers that catch only
    DualComputeDivergence. Both now produce the named divergence token.
    """
    if query_id not in QUERIES:
        raise DualComputeDivergence(query_id, float("nan"), float("nan"), 0.0)
    # AUDIT FIX: OverflowError was not caught (float(10**1000)), and the SHADOW's
    # own failures (TypeError for bad kwargs, UnknownPair, ZeroDivisionError for
    # a zero SL) escaped as raw exceptions instead of the named token.
    try:
        model_value = float(model_value)
    except (TypeError, ValueError, OverflowError):
        raise DualComputeDivergence(query_id, float("nan"), float("nan"), 0.0)
    q = QUERIES[query_id]
    try:
        truth = code_truth(query_id, **kw)
    except Exception as e:
        raise DualComputeDivergence(query_id, model_value, float("nan"), q.tolerance) from e
    delta = abs(model_value - truth)
    return DualResult(query_id, model_value, truth, delta, q.tolerance, raw, delta <= q.tolerance)


def verify_strict(query_id: str, model_value: float, raw: str = "", **kw) -> DualResult:
    """Verify and RAISE on divergence — the production path."""
    r = verify(query_id, model_value, raw, **kw)
    if not r.passed:
        raise DualComputeDivergence(query_id, r.model, r.code, r.eps)
    return r


def verify_live(query_id: str, **kw) -> DualResult:
    """Ask Limite AND verify against the shadow — the full dual path."""
    from limite_client import ask
    model_value, raw = ask(query_id, **kw)
    return verify_strict(query_id, model_value, raw, **kw)
