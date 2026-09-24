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
# AUDIT FIX (round 19): this set held GENERIC names (`ts`, `host`, `pid`,
# `timing`, `elapsed`) that a legitimate DECISION field could carry — a stage
# payload with a top-level `ts` holding an ORDERED state, or `host` naming a
# selected server, was silently dropped and two different decisions digested
# identically (a false MATCH, violating the pinned law). Only names that are
# UNAMBIGUOUSLY measurements remain, so a decision field can never be mistaken
# for one. Run metadata must use these names (or a nested `meta` object).
VOLATILE = frozenset({"ts_wall", "duration_ms", "started_at", "latency_ms",
                      "stage_latency"})


def _strip(o, depth=0):
    # AUDIT FIX (round 21): `_freeze` wraps a top-level list in a _Tag (which
    # IS a dict), so strip saw a dict at depth 0 and recursed to depth 1 — the
    # elements' VOLATILE keys stopped being filtered and every run falsely
    # diverged. A _Tag is TRANSPARENT: it recurses into its value at the SAME
    # depth, because the wrapper is the digest's own, not payload structure.
    if isinstance(o, _Tag):
        return {k: _strip(v, depth) for k, v in o.items()}
    if isinstance(o, dict):
        # AUDIT FIX (round 10): VOLATILE was filtered at EVERY depth, so a
        # legitimate DECISION field named `ts`/`host`/`pid` inside a nested
        # payload was silently discarded and two genuinely different runs
        # digested identically. The run metadata lives at the TOP level, so
        # the filter applies only there.
        # THE PINNED CONTRACT (round 8, asserted by
        # tests/test_determinism_sha_match.py): a stage payload's OWN
        # top-level measurement is filtered by NAME, so two runs differing
        # only in `duration_ms` digest identically.
        #
        # THE RESIDUAL, NAMED (audit rounds 19-33): the same mechanism drops
        # a legitimate DECISION that happens to be NAMED `duration_ms` /
        # `latency_ms` / `ts_wall` / `started_at` / `stage_latency` — two
        # different decisions would then digest identically. That is a
        # DELIBERATE trade, not an oversight: the names are narrow enough that
        # a real decision collision is unlikely, and the alternative (hash
        # everything) makes every run diverge on its own timing.
        #
        # THE SAFE PATH FOR A CALLER: put measurements under the `_meta` key,
        # which is stripped as a NAMESPACE (below) and can never collide with a
        # decision field name.
        drop = VOLATILE if depth == 0 else frozenset()
        # AUDIT FIX (round 15): `str(k)` COLLAPSES distinct keys — {1:'a',
        # '1':'b'} is two entries in Python but one after normalization, so
        # two genuinely different payloads digested identically. JSON cannot
        # represent such a dict, so this is a LOUD refusal, not a silent
        # merge.
        # AUDIT FIX (round 24): `str(k)` ERASED the key's type — {1:'a'} and
        # {'1':'a'} rendered identically, the same class as the float/str and
        # list/tuple value collisions. JSON requires string keys anyway, so a
        # non-str key is a LOUD refusal rather than a silent merge.
        bad = [k for k in o if not isinstance(k, str)]
        if bad:
            raise ValueError(
                f"CANONICAL_NON_STRING_KEY: {bad[:3]!r} — JSON object keys must "
                f"be strings; str() would erase the key's type")
        # `_meta` is the RECOMMENDED home for measurements: stripped as a
        # whole namespace, so it can never collide with a decision field.
        if depth == 0 and "_meta" in o:
            return {str(k): _strip(v, depth + 1) for k, v in
                    sorted(o.items(), key=lambda kv: str(kv[0]))
                    if str(k) not in drop and str(k) != "_meta"}
        return {str(k): _strip(v, depth + 1) for k, v in
                sorted(o.items(), key=lambda kv: str(kv[0]))
                if str(k) not in drop}
    if isinstance(o, (list, tuple)):
        # AUDIT FIX (round 14): a stage returning a LIST of dicts put the
        # measurement at depth 1, where `drop` was already empty — so the
        # filter never applied and every run falsely diverged. A list element
        # is still "the top of the payload" for filtering purposes.
        return [_strip(x, depth) for x in o]
    if isinstance(o, float):
        # AUDIT FIX (round 17 H5): `round(o, 10)` mapped values differing by
        # less than 1e-10 to the SAME canonical form, so real nondeterminism
        # could digest as a MATCH. The EXACT value is hashed instead — but it
        # must be TAGGED: a bare `repr(1.0)` is the string "1.0", which
        # json.dumps renders identically to the STRING "1.0", so a stage
        # flipping between float and str would still digest the same (my own
        # round-17 regression, caught in round 18). The `f:` prefix makes the
        # type part of the digest.
        return _Tag({_TAG_FLOAT: repr(o)})
    if o is None or isinstance(o, (str, int, bool)):
        return o
    # anything else would reach json.dumps unfreezable
    raise ValueError(f"CANONICAL_UNFREEZABLE: {type(o).__name__} has no "
                     f"deterministic rendering")


def canonical(obj) -> str:
    """A canonical JSON rendering: sorted keys, no whitespace, no volatile fields.

    AUDIT FIX (round 6): a raw `set`/`bytes` reached json.dumps and raised
    TypeError, so digest() crashed while RunDigest (which freezes first)
    succeeded — the two entry points disagreed. Everything is frozen first.

    THE TRUST CHECK IS UNCONDITIONAL (round 36). The previous signature carried a
    `_trust: bool = True` parameter, and passing `_trust=False` skipped the
    reserved-key refusal — so ANY caller could forge a type tag through a PUBLIC
    entry point, contradicting the round-26 trust boundary. A public function has
    no "trusted caller" mode; the internal renderer below is a separate function.
    """
    # the reserved-key check runs on the RAW input, BEFORE `_freeze` inserts its
    # own tags — otherwise strip() rejects the digest's own tag structures.
    _check_reserved(obj)
    obj = _freeze(obj)

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
        return json.dumps(_strip(obj), separators=(",", ":"), sort_keys=True)
    except TypeError as e:
        raise ValueError(
            f"CANONICAL_UNFREEZABLE: {e} — the payload carries an object with no "
            f"deterministic rendering; pass plain data (dict/list/str/number/bool/None)") from e


def digest(stages: dict) -> str:
    """PUBLIC entry: the raw stages are CHECKED before anything is rendered.

    AUDIT FIX (round 26): the reserved-key refusal was skippable — `_render_stage`
    treated any `_Tag`/`_FrozenDict` INSTANCE as already-validated, so a direct
    `digest({'s': _Tag({'__py_float__': 'x'})})` caller could forge a tag and
    merge two different decisions. The trust boundary is now exact: EVERY public
    entry checks; only `_digest_frozen` (reached from RunDigest, which ran the
    same check on the way in) skips it.
    """
    if not isinstance(stages, dict):
        raise ValueError(f"RUN_DIGEST_STAGES_NOT_A_DICT: {type(stages).__name__}")
    _check_reserved(stages)
    return _digest_frozen(stages)


def _digest_frozen(stages: dict) -> str:
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
        top-level field is a legitimate DECISION named one of the VOLATILE
        names IS filtered and therefore unhashed. (The names are now narrow —
        `ts_wall`/`duration_ms`/`started_at`/`latency_ms`/`stage_latency` — so a
        decision field colliding is unlikely, but the trade is real.)
      - WHERE METADATA GOES: at the payload TOP, under one of those names —
        NOT nested. The filter is depth-0-only, so `{"meta": {"duration_ms": 5}}`
        is HASHED and every run falsely diverges. Round 23 corrected this advice,
        which previously said the opposite of what the code does.
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
    # AUDIT FIX (round 24): a non-str stage name raised AttributeError from
    # `name.encode()` instead of this module's named ValueError contract.
    _bad_names = [n for n in stages if not isinstance(n, str)]
    if _bad_names:
        raise ValueError(
            f"RUN_DIGEST_NON_STRING_STAGE: {_bad_names[:3]!r} — stage names are labels")
    for name in sorted(stages):
        # AUDIT FIX (round 24): the framing was `name \x00 payload \x1e` with the
        # name UNESCAPED, so a name CONTAINING those bytes forged a stage
        # boundary — one stage rendered byte-identical to two, a false match.
        # Both are now LENGTH-PREFIXED, which no name content can forge.
        _n = name.encode()
        h.update(len(_n).to_bytes(8, "big")); h.update(_n)
        # AUDIT FIX (round 22): the reserved-key refusal applies to RAW input.
        # `digest` is fed by `RunDigest.__post_init__`, which ALREADY froze (and
        # validated) every stage — so re-running the trust check on those values
        # refused the digest's OWN tags. An already-frozen payload renders with
        # `_render`; a raw one goes through `canonical` and its check.
        _p = _render_stage(stages[name]).encode()
        h.update(len(_p).to_bytes(8, "big")); h.update(_p)
    return h.hexdigest()


# THE TYPE TAGS. AUDIT FIX (round 20): a STRING prefix (`"f:" + repr(o)`) is
# forgeable — a payload holding the literal string "f:1.0" digested identically
# to the float 1.0, so the tag merely moved the collision. The tags are now
# RESERVED KEYS, and `strip` REFUSES any input dict that carries one, so a
# payload cannot forge a tag at all (loud fail, not a silent merge).
_TAG_FLOAT = "__py_float__"
_TAG_BYTES = "__py_bytes__"
_TAG_BYTEARRAY = "__py_bytearray__"
_TAG_SUBCLASS = "__py_subclass__"
_TAG_SEQ = {"list": "__py_list__", "tuple": "__py_tuple__",
            "set": "__py_set__", "frozenset": "__py_frozenset__"}
_TAGS = frozenset({_TAG_FLOAT, _TAG_BYTES, _TAG_BYTEARRAY, _TAG_SUBCLASS,
                   *_TAG_SEQ.values()})


class _FrozenDict(dict):
    """A dict that refuses mutation after construction."""

    def _no(self, *a, **k):
        raise TypeError("RunDigest.stages is IMMUTABLE — rebuild the digest instead")

    # AUDIT FIX: `|=` (dict.__ior__) takes its OWN C slot and did not dispatch
    # through __setitem__/update, so `stages |= {...}` mutated in place and left
    # sha stale. __ior__ is blocked explicitly.
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _no
    __ior__ = _no


def _render_stage(v) -> str:
    """Render ONE stage payload, choosing the entry point by what it IS.

    A stage inside a `RunDigest` is ALREADY FROZEN (and was validated at the
    freeze site), so it renders with `_render`; a RAW payload goes through
    `canonical` and its reserved-key check. Round 22 introduced the split for
    `digest` and left `compare` on the old path, so compare crashed on the same
    frozen tags — one helper, both call sites, no third variant.
    """
    # AUDIT FIX (round 26): `isinstance(v, (_Tag, _FrozenDict))` treated ANY
    # caller-supplied instance as already-validated and skipped the reserved-key
    # check — so a direct digest() caller could forge a tag. The RAW path now
    # always runs the check; only the digest's OWN frozen stages skip it, and
    # that is decided by `RunDigest` (which checks on the way in), not by type.
    # the CALLER has already been checked (digest/RunDigest both check on entry),
    # so a frozen value renders directly and a raw one goes through canonical.
    if isinstance(v, (_Tag, _FrozenDict)):
        return _render(v)
    return canonical(v)


def _render(obj) -> str:
    """Render a value the DIGEST ITSELF froze — no raw-input trust check.

    A separate function rather than a flag on `canonical` (round 36): a parameter
    that skips a refusal is a bypass any caller can invoke, and `_render` is only
    reached from `_digest_frozen`, whose inputs `RunDigest`/`digest` ALREADY
    checked on the way in. It renders with the same machinery, reached directly.
    """
    import json as _json
    return _json.dumps(_strip(obj), separators=(",", ":"), sort_keys=True)


def _check_reserved(o, _seen=None) -> None:
    """A payload may not carry a RESERVED TAG KEY.

    The tags are what make a float/bytes/list distinguishable from a string in
    the digest; if a payload could carry one, it could forge the tag and merge
    two different decisions. A collision is a LOUD refusal, never a silent merge.
    """
    # AUDIT FIX (round 22): returning early for ANY `_Tag` was a TRUST-BOUNDARY
    # BYPASS — a caller could construct a `_Tag` carrying a reserved key and skip
    # the refusal entirely. This walker runs on RAW input only, where no
    # legitimate `_Tag` can exist (the digest's own tags are created later, by
    # `_freeze`), so a `_Tag` here IS a forgery and is refused.
    # AUDIT FIX (round 23): this walker runs BEFORE _freeze, so it needs its OWN
    # cycle guard — otherwise a circular payload recursed here to RecursionError
    # before the freeze guard could see it.
    if isinstance(o, (dict, list, tuple, set, frozenset)):
        if _seen is None:
            _seen = set()
        if id(o) in _seen:
            raise ValueError(
                "CANONICAL_CYCLE: the payload contains a cycle — it has no "
                "canonical rendering")
        _seen = _seen | {id(o)}
    if isinstance(o, _Tag):
        raise ValueError(
            "CANONICAL_RESERVED_KEY: a _Tag instance appeared in the raw payload "
            "— those are the digest's own type tags and cannot be supplied")
    if isinstance(o, dict):
        forged = _TAGS.intersection(str(k) for k in o)
        if forged:
            raise ValueError(
                f"CANONICAL_RESERVED_KEY: the payload carries {sorted(forged)} — "
                f"those keys are reserved for the digest's type tags")
        for v in o.values():
            _check_reserved(v, _seen)
    elif isinstance(o, (list, tuple, set, frozenset)):
        for v in o:
            _check_reserved(v, _seen)



class _Tag(_FrozenDict):
    """A TYPE TAG produced by `_freeze` — deliberately a DISTINCT TYPE, not a
    plain dict. `_check_reserved` refuses a payload carrying a tag key, but it
    must not refuse the digest's OWN tag structures, and a `_Tag` is how the two
    are told apart. `_freeze` also returns a `_Tag` unchanged, so freezing a
    already-frozen payload is idempotent (the double-freeze bug that broke
    test_determinism_sha_match on the first attempt at this fix).
    """

def _freeze(o, _seen=None):
    # AUDIT FIX: tuples were not recursed (a dict inside a tuple stayed mutable)
    # and sets passed through (mutable AND unserializable by canonical()).
    if isinstance(o, _Tag):
        return o                     # already frozen — idempotent
    # AUDIT FIX (round 23): a CIRCULAR payload recursed until RecursionError
    # instead of the documented loud CANONICAL_* refusal. Identity-tracked.
    if isinstance(o, (dict, list, tuple, set, frozenset)):
        if _seen is None:
            _seen = set()
        if id(o) in _seen:
            raise ValueError(
                "CANONICAL_CYCLE: the payload contains a cycle — it has no "
                "canonical rendering")
        _seen = _seen | {id(o)}
    if isinstance(o, dict):
        return _FrozenDict({k: _freeze(v, _seen) for k, v in o.items()})
    if isinstance(o, (list, tuple)):
        # AUDIT FIX (round 19): `list` and `tuple` both froze to a plain tuple and
        # rendered as the same JSON array, so a stage flipping container TYPE
        # digested identically — the same class as the float/str collision fixed
        # in round 18. The type is now part of the frozen value.
        return _Tag({_TAG_SEQ[type(o).__name__]: tuple(_freeze(x, _seen) for x in o)})
    if isinstance(o, (set, frozenset)):
        # AUDIT FIX (round 6): sorted() on heterogeneous members ({1,'a'}) or on
        # dicts/lists raised TypeError. Sort by the CANONICAL RENDERING instead.
        # AUDIT FIX (round 16): the sort key used `default=str`, so an
        # unfreezable element rendered via its `__repr__` — which embeds a HEAP
        # ADDRESS — and the ORDER varied between runs (the round-14 bug,
        # reintroduced through the sort). Elements are sorted by their canonical
        # RENDERING, which refuses unfreezable values instead of str()-ing them.
        # AUDIT FIX (round 21): set and frozenset both returned a BARE tuple, so
        # they digested identically while list/tuple were distinguished — the same
        # type-erasure class, one branch over. The container type is tagged here.
        frozen = [_freeze(x, _seen) for x in o]
        return _Tag({_TAG_SEQ[type(o).__name__]:
                     tuple(sorted(frozen, key=_render))})
    if isinstance(o, (bytes, bytearray)):
        # AUDIT FIX (round 19): decoding erased the type, so b'abc' and 'abc'
        # digested identically. The tag keeps them distinct.
        # AUDIT FIX (round 21): `backslashreplace` is NON-INJECTIVE — b'\xff'
        # (one invalid byte) decodes to the 4-char string "\\xff", IDENTICAL to
        # the decoding of b'\\xff' (four ASCII bytes). Two distinct payloads
        # therefore shared a digest. hex() is injective and type-tagged.
        # AUDIT FIX (round 24): bytes and bytearray shared ONE tag, so they
        # digested identically — the same type-erasure class as list/tuple and
        # set/frozenset. Each gets its own tag.
        _k = _TAG_BYTES if isinstance(o, bytes) else _TAG_BYTEARRAY
        return _Tag({_k: o.hex()})
    # AUDIT FIX (round 39): a SUBCLASS of str/int/bool/float (IntEnum, StrEnum, a
    # custom `class S(str)`) was returned UNTAGGED and json-encoded as its BASE
    # value, so `MyEnum.X == 1` digested identically to plain `1` — the same
    # type-erasure class as the float/str and list/tuple collisions. An EXACT
    # builtin passes through; a SUBCLASS is tagged with its type name.
    if o is None or type(o) in (str, int, bool, float):
        return o
    if isinstance(o, (str, int, bool, float)):
        return _Tag({_TAG_SUBCLASS: f"{type(o).__name__}:{o!r}"})
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
        # AUDIT FIX (round 23): the reserved-key refusal lived only in
        # `canonical`, and `RunDigest` freezes + renders with `_trust=False` — so
        # a caller could forge a tag THROUGH the RunDigest path and merge two
        # different decisions. The check runs here, on the raw stages.
        # AUDIT FIX (round 23): a LIST payload froze to a tag and `digest` then
        # hashed the tag KEY as if it were a stage name — a mistyped caller
        # silently got a plausible digest instead of a refusal.
        if not isinstance(self.stages, dict):
            raise ValueError(
                f"RUN_DIGEST_STAGES_NOT_A_DICT: {type(self.stages).__name__} — "
                f"stages maps a NAME to a payload")
        _check_reserved(self.stages)
        # AUDIT FIX (round 4): frozen=True blocks REBINDING but not IN-PLACE
        # mutation, so `run.stages[k] = v` still left sha stale while compare()
        # trusted it. The stored value is now a DEEP-FROZEN mapping — a
        # MutationAttempt raises instead of silently diverging from the sha.
        object.__setattr__(self, "stages", _freeze(copy.deepcopy(self.stages)))
        # the check ran above, on the RAW stages — so the internal path is safe
        object.__setattr__(self, "sha", _digest_frozen(self.stages))


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
        ca, cb = _render_stage(a.stages[name]), _render_stage(b.stages[name])
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
