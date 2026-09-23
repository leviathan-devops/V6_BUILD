"""determinism/determinism.py — architectural determinism.

THE LAW (pin LAWS / W9 gate): sha256(run1) == sha256(run2) byte-identical.

V5 enforced determinism by DISCIPLINE (rule R32). V6 makes it ARCHITECTURAL:
every stage's output is a pure function of its inputs, and the run digest is
computed over the stage outputs — so a nondeterministic stage changes the
digest and the run fails loudly.

The digest deliberately EXCLUDES wall-clock timing (a timing field would make
every run differ for a reason that has nothing to do with the decision).
"""
from __future__ import annotations
import copy, hashlib, json
from dataclasses import dataclass

# Fields that legitimately differ between runs and must NOT enter the digest.
# Fields that legitimately differ between runs and must NOT enter the digest.
# latency_ms / stage_latency are MEASUREMENTS of the run, not decisions the run
# made: including them would make every run differ for a reason that has
# nothing to do with determinism (defect found by the e2e probe 2026-09-23).
VOLATILE = {"ts_wall", "duration_ms", "host", "pid", "started_at", "elapsed",
            "latency_ms", "stage_latency", "timing", "ts"}


def canonical(obj) -> str:
    """A canonical JSON rendering: sorted keys, no whitespace, no volatile fields.

    AUDIT FIX (round 6): a raw `set`/`bytes` reached json.dumps and raised
    TypeError, so digest() crashed while RunDigest (which freezes first)
    succeeded — the two entry points disagreed. Everything is frozen first.
    """
    obj = _freeze(obj)

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in sorted(o.items()) if k not in VOLATILE}
        if isinstance(o, (list, tuple)):
            return [strip(x) for x in o]
        if isinstance(o, float):
            return round(o, 10)
        return o
    return json.dumps(strip(obj), separators=(",", ":"), sort_keys=True)


def digest(stages: dict) -> str:
    """The run digest over the ordered stage outputs.

    DEFECT FIXED (found by the probe 2026-09-23): the volatile filter was
    applied only INSIDE each stage (depth >= 1). A volatile key placed at the
    TOP level therefore became a brand-new stage named "ts_wall", changing the
    digest for a reason that has nothing to do with the decision. The filter
    must apply at EVERY depth, including depth 0.
    """
    h = hashlib.sha256()
    for name in sorted(k for k in stages if k not in VOLATILE):
        h.update(name.encode()); h.update(b"\x00")
        h.update(canonical(stages[name]).encode()); h.update(b"\x1e")
    return h.hexdigest()


class _FrozenDict(dict):
    """A dict that refuses mutation after construction."""

    def _no(self, *a, **k):
        raise TypeError("RunDigest.stages is IMMUTABLE — rebuild the digest instead")

    # AUDIT FIX: `|=` (dict.__ior__) takes its OWN C slot and did not dispatch
    # through __setitem__/update, so `stages |= {...}` mutated in place and left
    # sha stale. __ior__ is blocked explicitly.
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _no
    __ior__ = _no


def _freeze(o):
    # AUDIT FIX: tuples were not recursed (a dict inside a tuple stayed mutable)
    # and sets passed through (mutable AND unserializable by canonical()).
    if isinstance(o, dict):
        return _FrozenDict({k: _freeze(v) for k, v in o.items()})
    if isinstance(o, (list, tuple)):
        return tuple(_freeze(x) for x in o)
    if isinstance(o, (set, frozenset)):
        # AUDIT FIX (round 6): sorted() on heterogeneous members ({1,'a'}) or on
        # dicts/lists raised TypeError. Sort by the CANONICAL RENDERING instead.
        frozen = [_freeze(x) for x in o]
        return tuple(sorted(frozen, key=lambda x: json.dumps(x, sort_keys=True, default=str)))
    if isinstance(o, (bytes, bytearray)):
        return o.decode("utf-8", "backslashreplace")
    return o


@dataclass(frozen=True)
class RunDigest:
    """A FROZEN snapshot of the run.

    AUDIT FIX: the dataclass was mutable and `stages` stayed an aliased
    reference, so a later `stages[...] = ...` left `sha` stale while compare()
    still trusted it — a false match. frozen=True + a copied dict + no
    caller-supplied sha removes the whole class.
    """
    stages: dict
    sha: str = ""

    def __post_init__(self):
        # AUDIT FIX (round 4): frozen=True blocks REBINDING but not IN-PLACE
        # mutation, so `run.stages[k] = v` still left sha stale while compare()
        # trusted it. The stored value is now a DEEP-FROZEN mapping — a
        # MutationAttempt raises instead of silently diverging from the sha.
        object.__setattr__(self, "stages", _freeze(copy.deepcopy(self.stages)))
        object.__setattr__(self, "sha", digest(self.stages))


def compare(a: RunDigest, b: RunDigest) -> dict:
    """Per-stage diff so a divergence NAMES the stage that broke determinism.

    AUDIT FIX: the loop iterated EVERY stage name while digest() EXCLUDED the
    volatile ones, so a volatile-only difference produced match=True with a
    non-empty divergent_stages — the two signals contradicted each other. The
    loop now skips the same names digest() skips.
    """
    diffs = {}
    names = (set(a.stages) | set(b.stages)) - VOLATILE
    for name in sorted(names):
        # AUDIT FIX: `.get` conflated a MISSING stage with an explicit None, so
        # an added/removed None-valued stage changed the sha with no recorded
        # divergence. Membership is checked explicitly.
        in_a, in_b = name in a.stages, name in b.stages
        if in_a != in_b:
            diffs[name] = {"a": "PRESENT" if in_a else "ABSENT",
                           "b": "PRESENT" if in_b else "ABSENT"}
            continue
        ca, cb = canonical(a.stages[name]), canonical(b.stages[name])
        if ca != cb:
            diffs[name] = {"a": ca[:200], "b": cb[:200]}
    return {"match": a.sha == b.sha, "sha_a": a.sha, "sha_b": b.sha,
            "divergent_stages": diffs}


def assert_deterministic(fn, *args, **kw) -> dict:
    """Run `fn` twice and return the comparison."""
    return compare(RunDigest(fn(*args, **kw)), RunDigest(fn(*args, **kw)))
