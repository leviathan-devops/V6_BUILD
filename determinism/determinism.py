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

    def strip(o, depth=0):
        if isinstance(o, dict):
            # AUDIT FIX (round 10): VOLATILE was filtered at EVERY depth, so a
            # legitimate DECISION field named `ts`/`host`/`pid` inside a nested
            # payload was silently discarded and two genuinely different runs
            # digested identically. The run metadata lives at the TOP level, so
            # the filter applies only there.
            drop = VOLATILE if depth == 0 else frozenset()
            # AUDIT FIX (round 15): `str(k)` COLLAPSES distinct keys — {1:'a',
            # '1':'b'} is two entries in Python but one after normalization, so
            # two genuinely different payloads digested identically. JSON cannot
            # represent such a dict, so this is a LOUD refusal, not a silent
            # merge.
            keys = [str(k) for k in o]
            if len(set(keys)) != len(keys):
                raise ValueError(
                    "CANONICAL_KEY_COLLISION: two distinct keys normalize to the "
                    "same string — the payload cannot be rendered deterministically")
            return {str(k): strip(v, depth + 1) for k, v in
                    sorted(o.items(), key=lambda kv: str(kv[0]))
                    if str(k) not in drop}
        if isinstance(o, (list, tuple)):
            # AUDIT FIX (round 14): a stage returning a LIST of dicts put the
            # measurement at depth 1, where `drop` was already empty — so the
            # filter never applied and every run falsely diverged. A list element
            # is still "the top of the payload" for filtering purposes.
            return [strip(x, depth) for x in o]
        if isinstance(o, float):
            # AUDIT FIX (round 17 H5): `round(o, 10)` mapped values differing by
            # less than 1e-10 to the SAME canonical form, so real nondeterminism
            # could digest as a MATCH. The EXACT value is hashed instead — but it
            # must be TAGGED: a bare `repr(1.0)` is the string "1.0", which
            # json.dumps renders identically to the STRING "1.0", so a stage
            # flipping between float and str would still digest the same (my own
            # round-17 regression, caught in round 18). The `f:` prefix makes the
            # type part of the digest.
            return "f:" + repr(o)
        if o is None or isinstance(o, (str, int, bool)):
            return o
        # anything else would reach json.dumps unfreezable
        raise ValueError(f"CANONICAL_UNFREEZABLE: {type(o).__name__} has no "
                         f"deterministic rendering")
    # AUDIT FIX (round 9): a datetime/Decimal/custom object passed _freeze
    # unchanged and then raised TypeError out of json.dumps, so digest() CRASHED
    # where the gate should have produced a digest. `default=str` makes any
    # remaining object render deterministically; a non-str dict KEY is
    # normalised in strip().
    # AUDIT FIX (round 14): `default=str` let an object render via its
    # `__repr__`, which for a default object embeds a HEAP ADDRESS
    # (`<Foo object at 0x7f...>`) — so two logically identical runs digested
    # differently (a false DIVERGENCE). An unfreezable object is now a NAMED
    # refusal, which is the loud-fail contract: the caller must put real data in.
    try:
        return json.dumps(strip(obj), separators=(",", ":"), sort_keys=True)
    except TypeError as e:
        raise ValueError(
            f"CANONICAL_UNFREEZABLE: {e} — the payload carries an object with no "
            f"deterministic rendering; pass plain data (dict/list/str/number/bool/None)") from e


def digest(stages: dict) -> str:
    """The run digest over the ordered stage outputs.

    WHERE THE VOLATILE FILTER APPLIES (corrected in round 11 — the round-6 text
    here claimed "every depth including depth 0", which round 8 deliberately
    reversed and tests/test_determinism_sha_match.py now PINS):
      - AT THE TOP OF each stage's payload (depth 0 of canonical's input):
        VOLATILE is stripped. This is the case the probe found — a stage payload
        like {"decided": 1, "duration_ms": 5} digests identically whatever the
        measurement says.
      - DEEPER than that: NOT stripped. A field named `ts` three levels down is
        hashed, because at that depth the name is as likely to be a decision as
        a measurement.
      - THE ACCEPTED RESIDUAL, stated plainly: a stage payload whose OWN
        top-level field is a legitimate decision named `ts`/`host`/`pid`/
        `timing` IS filtered and therefore unhashed. The names are generic
        enough that this is a real possibility; the fix is for the caller to
        put run metadata in a nested `meta` object, or to rename a decision
        field that collides. This is a deliberate trade, not an oversight.
      - At the TOP level: keys are STAGE NAMES, i.e. labels the caller chose. A
        stage literally named `ts`/`timing` is a REAL stage and IS hashed —
        silently dropping it would hide a stage from the digest.
    A caller holding run metadata puts it INSIDE a payload (where it is
    filtered), never as a top-level key.
    """
    h = hashlib.sha256()
    # AUDIT FIX (round 8): filtering STAGE NAMES by VOLATILE silently dropped a
    # real stage that happened to be named `ts`/`timing`. Volatile filtering
    # belongs INSIDE payloads (canonical does that); a stage name is a label the
    # caller chose and must be hashed.
    for name in sorted(stages):
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
        # AUDIT FIX (round 16): the sort key used `default=str`, so an
        # unfreezable element rendered via its `__repr__` — which embeds a HEAP
        # ADDRESS — and the ORDER varied between runs (the round-14 bug,
        # reintroduced through the sort). Elements are sorted by their canonical
        # RENDERING, which refuses unfreezable values instead of str()-ing them.
        frozen = [_freeze(x) for x in o]
        return tuple(sorted(frozen, key=canonical))
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
    names = set(a.stages) | set(b.stages)
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
    """Run `fn` twice and return the comparison.

    AUDIT FIX (round 8): both runs shared the SAME args/kw objects, so an
    in-place mutation by the first call polluted the second — a false
    divergence for deterministic code, or masked nondeterminism. Each run gets
    its own deep copy.
    """
    a = RunDigest(fn(*copy.deepcopy(args), **copy.deepcopy(kw)))
    b = RunDigest(fn(*copy.deepcopy(args), **copy.deepcopy(kw)))
    return compare(a, b)
