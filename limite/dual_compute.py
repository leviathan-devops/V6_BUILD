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
        self.delta = abs(model - code)
        super().__init__(
            f"LIMITE_CODE_DIVERGENCE [{query_id}]: |limite {model:.6f} - code {code:.6f}| "
            f"= {self.delta:.6f} > eps {eps}")


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


def verify(query_id: str, model_value: float, raw: str = "", **kw) -> DualResult:
    """Verify ONE already-computed answer against the code shadow."""
    q = QUERIES[query_id]
    truth = code_truth(query_id, **kw)
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
