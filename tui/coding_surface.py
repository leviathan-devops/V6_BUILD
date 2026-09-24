"""tui/coding_surface.py — the NO-CODING audit (a SUPPLEMENTARY source check).

READ THIS BEFORE TRUSTING OR FIXING THIS FILE.

THE PRIMARY ENFORCEMENT IS NOT HERE. The pin's law is "zero coding capability in
the trading agent — bash REMOVED, code execution DISABLED". That is enforced
MECHANICALLY by `pi --no-builtin-tools`, which removes pi's own read/bash/
powershell/edit/write/grep/find/ls. `pi-harness/prove_zero_coding.py` asserts
that flag is passed and that the extension registers ONLY `plutus_*` tools. That
is the boundary: a flag the runtime honours, not a pattern match.

THIS MODULE IS A SECONDARY CHECK ON THE EXTENSION'S OWN SOURCE. It greps for
spawn/deserialize/write idioms so that a future edit adding one is caught in
review. It is a HEURISTIC, and its limits are real and known:
  - it cannot follow an import alias to its module (a regex has no dataflow), so
    an aliased receiver is reported in the SUSPECT class, not the EXACT class;
  - a determined author can evade any pattern list;
  - the SUSPECT class WILL flag legitimate code (`json.loads`, a db cursor's
    `.execute`), which is the deliberate trade: a false positive costs a review
    item, a missed spawn costs the law.
Its value is CATCHING ACCIDENTS, not stopping an adversary. Treating it as a
security boundary is the mistake that produced five audit criticals across
rounds 1/3/6/7/8 — each one an evasion of a list that cannot be complete.

PIN LAW: "zero coding capability in the trading agent — bash REMOVED, code
execution DISABLED". This module is the mechanical predicate that proves it:
it scans a tree for every capability that would let the agent write or run
code, and returns a NAMED violation list. An empty list is the only pass.

AUDIT FIXES (2026-09-23) — three bypasses in the first version:
  CRITICAL: the write-allowlist was keyed on BASENAME, so any file anywhere
    named after a declared artifact was skipped for ALL capabilities, and a
    process-spawning primitive hidden in such a file passed the scan.
    FIX: the exemption is keyed on the FULL PATH and covers the WRITE
    capability only, never code execution.
  HIGH: the process-spawn pattern was lowercase-only, so importing the
    capitalised class directly evaded it. FIX: match both cases explicitly.
  HIGH: the qualified-builtin guard rejected every dotted call, so a call
    through the builtins module never matched. FIX: match the qualified form
    explicitly instead of blocking every dotted call.
  HIGH: the file-write claim was unenforced (no write-mode patterns existed).
    FIX: a separate WRITE lexicon, exempted only for the declared artifacts.

SELF-SCANNABILITY: the trigger words below are assembled from FRAGMENTS, so
this file's own source never contains them literally. That is what lets the
scanner scan itself with NO self-exemption — an exemption would itself be a
bypass (a spawn primitive hidden here would pass).

PATTERN STYLE: every pattern is a plain character-class alternation. No word
boundaries and no whitespace escapes are used, because a backslash escape
written through a generator layer silently becomes a control character (a
backspace for \\b) and the pattern then matches nothing while LOOKING correct.
"""
from __future__ import annotations
import re
from pathlib import Path


def _f(*parts: str) -> str:
    """Join fragments. The trigger words never appear whole in this source."""
    return "".join(parts)


# The builtins that execute code. `X` is a non-dot, non-word character, so a
# METHOD of the same name (the regex compiler, reached as a dotted call) is
# excluded from the bare form and only matched through its qualified form.
# Lookarounds (not character classes) so the boundary works at a string EDGE:
# a bare import statement puts no character after the module name, and a
# class-based boundary would silently fail there. Neither lookaround needs a
# backslash escape, which a generator layer would turn into a control char.
_PRE = "(?<![0-9A-Za-z_.])"
_POST = "(?![0-9A-Za-z_])"
# AUDIT FIX: a backslash-newline is a valid continuation inside a call, so a
# whitespace class of space/tab alone is evadable with one backslash. The class
# now also matches a newline preceded by a backslash.
_WS = "[ \t]*(?:[" + chr(92) + chr(92) + "][" + chr(10) + chr(13) + "][ \t]*)?"

# AUDIT FIX: the dotted write form originally required a LITERAL dot, but
# Python permits whitespace around the dot. _DOT tolerates it. (This comment
# shows no call form: the self-scan below runs over this region.)
# AUDIT FIX (round 11): _DOT allowed only space/tab, but _WS also handles a
# BACKSLASH-NEWLINE continuation, which Python's tokenizer ignores — so a dotted
# call split across a line continuation matched neither the dotted rule nor the
# bare/any-receiver forms. _DOT now tolerates the same continuation as _WS.
# AUDIT FIX (round 12): the literal `"[\\]"` is a THREE-character class `[\]`
# (an escaped bracket), NOT a backslash class — so the pattern silently matched
# the wrong characters. Built with chr(92) exactly as _WS is, which removes the
# escaping layer entirely.
_CONT = "[" + chr(92) + chr(92) + "][" + chr(10) + chr(13) + "][ \t]*"
_DOT = "[ \t]*(?:" + _CONT + ")?[.][ \t]*(?:" + _CONT + ")?"


def _bare(word: str) -> str:
    return _PRE + word + _WS + "[(]"


def _qualified(word: str) -> str:
    # AUDIT FIX: the dunder-qualified call form matched NEITHER the bare pattern
    # (a preceding '.' is excluded) nor the plain qualified pattern. Both
    # qualified spellings are now matched.
    # split the "builtins" literal so this source never contains it whole
    bi = _f("buil", "t", "ins")
    return (_f(bi, _DOT, word, _WS, "[(]") + "|"
            + _f("__", bi, "__", _DOT, word, _WS, "[(]"))


# CRITICAL FIX (audit round 7): importing a module UNDER AN ALIAS and calling
# its spawn/deserialize method evaded BOTH branches — the dotted form needs the
# literal module name and the bare form is dot-guarded. A SECOND probe found the
# first fix far too broad (a bare `.loads(` / `.execute(` is an ordinary method
# call). The sound predicate is an ALIAS-SHAPED receiver (one to three chars)
# followed by the method name.
# CRITICAL FIXES (audit round 8) — the previous two attempts were both wrong:
#   1. the receiver was capped at 3 chars, so a LONGER alias evaded it;
#   2. a safe-receiver NAME list (db/cursor/conn/...) excluded by name — but the
#      ALIAS IS CHOSEN BY THE ATTACKER, so naming a process-spawning import
#      after a database handle was treated as safe SQL.
# Both are gone. The predicate is now: ANY receiver, followed by the dangerous
# METHOD name. That WILL flag a legitimate `.loads(` or `.execute(` on some
# object — and that is the correct trade for a read-only audit whose only cost
# is a review item. A false positive is cheap; a missed spawn is not.
# AUDIT FIX (round 10): the receiver pattern ended at a bare literal dot, so it
# matched an adjacent-dot call but MISSED one written with legal Python
# whitespace around the dot — which evaded every -any-receiver rule. _DOT
# tolerates whitespace on both sides, so both spellings match.
# (This comment deliberately shows NO call form: the self-scan below runs over
#  exactly this region, and quoting an evasion here would trip the scan.)
_ALIAS = _f("(?<![", "0-9A-Za-z_.", "])", "[A-Za-z_][A-Za-z0-9_]*", _WS, _DOT)

# TWO CONFIDENCE CLASSES (audit round 8). A regex cannot do the dataflow needed
# to tell `pickle.loads` from `json.loads` when the receiver is an alias — the
# METHOD NAME is the same. So the lexicon carries two classes:
#   EXACT    the literal module name  -> a VIOLATION
#   SUSPECT  any receiver + the method -> a REVIEW ITEM (may be json.loads)
# The scan reports both; the audit asserts zero EXACT violations and lists the
# SUSPECTs. Claiming the SUSPECT class as a violation would fail on legitimate
# code; claiming it as clean would miss the aliased spawn. Both would be wrong.
_ALIASED = [
    (_f("os.system", "-any-receiver"),   _f(_ALIAS, "sys", "tem", _WS, "[(]")),
    (_f("os.exec", "-any-receiver"),     _f(_ALIAS, "ex", "ec", "[0-9A-Za-z_]*", _WS, "[(]")),
    (_f("os.spawn", "-any-receiver"),    _f(_ALIAS, "spa", "wn", "[0-9A-Za-z_]*", _WS, "[(]")),
    (_f("pickle.load", "-any-receiver"), _f(_ALIAS, "lo", "ads?", _WS, "[(]")),
    (_f("importlib", "-any-receiver"),   _f(_ALIAS, "import_module", _WS, "[(]")),
    (_f("builtins.eval", "-any-receiver"), _f(_ALIAS, "ev", "al", _WS, "[(]")),
    (_f("os.write", "-any-receiver"),    _f(_ALIAS, "wr", "ite", _WS, "[(]")),
    (_f("fs.create", "-any-receiver"),   _f(_ALIAS, "mk", "stemp", _WS, "[(]")),
    # AUDIT FIX (round 9): `compile` and `Unpickler` had no any-receiver form,
    # so `import builtins as b; b.compile(...)` and `import pickle as p;
    # p.Unpickler(f)` matched nothing.
    (_f("builtins.compile", "-any-receiver"), _f(_ALIAS, "com", "pile", _WS, "[(]")),
    # AUDIT FIX (round 10): `import builtins as b; b.exec(...)` matched NEITHER
    # the bare form (dot-guarded by _PRE) nor the qualified form (which needs the
    # literal module name), so an aliased exec evaded the scan entirely.
    (_f("builtins.exec", "-any-receiver"), _f(_ALIAS, "ex", "ec", _WS, "[(]")),
    (_f("pickle.Unpickler", "-any-receiver"), _f(_ALIAS, "Un", "pickler", _WS, "[(]")),
    (_f("tempfile", "-any-receiver"),
     _f(_ALIAS, "Temporary", "File", _WS, "[(]")
     + "|" + _f(_ALIAS, "mk", "dtemp", _WS, "[(]")),
]

_EXEC_NAMES = _ALIASED + [
    (_f("sub", "pro", "cess"),   _f(_PRE, "sub", "pro", "cess", _POST)),
    # AUDIT FIX: the dotted-only forms were bypassed by a from-import
    # (importing the name directly and calling it). Each name now also matches
    # its BARE call form, so the alias/import route is caught too.
    # AUDIT FIX (round 10): the literal `os[.]` here required an adjacent dot,
    # so `os . system(...)` evaded it while the neighbouring rules used _DOT.
    (_f("os.", "sy", "s", "tem"), _f("os", _DOT, "sy", "s", "tem", _WS, "[(]") + "|"
                                 + _bare(_f("sy", "s", "tem"))),
    # AUDIT FIX (round 20, CRITICAL): the bare forms enumerated only SIX os.exec
    # variants while the dotted form used `[0-9A-Za-z_]*`. Python's os module
    # also ships execlpe/execvpe, so those evaded BOTH tiers. The bare form now
    # matches the same wildcard the dotted form does.
    # AUDIT FIX (round 20): the DOTTED form may use a wildcard (it requires the
    # `os.` prefix), but the BARE form must not — `exec[a-z]*(` matched
    # `execute(`, a false positive on ordinary code. The real variants are
    # exec{l,v}{p,e}? — that is the suffix, and it covers all eight.
    (_f("os.", "ex", "ec"),      _f("os", _DOT, "ex", "ec", "[0-9A-Za-z_]*", _WS, "[(]") + "|"
                                 + _f(_PRE, "ex", "ec", "[lv][pe]{0,2}", _WS, "[(]")),
    (_f("os.", "spa", "wn"),     _f("os", _DOT, "spa", "wn", "[0-9A-Za-z_]*", _WS, "[(]") + "|"
                                 + _f(_PRE, "spa", "wn", "[lv][pe]{0,2}", _WS, "[(]") + "|"
                                 + "|".join(_bare(_f("spa", "wn") + v)
                                            for v in ("", "l", "v", "lp", "vp"))),
    (_f("po", "pen"),            _f("[Pp]", "open", _WS, "[(]")),
    (_f("ev", "al"),             _bare("eval") + "|" + _qualified("eval")),
    (_f("ex", "ec"),             _bare("exec") + "|" + _qualified("exec")),
    (_f("com", "pile"),          _bare("compile") + "|" + _qualified("compile")),
    (_f("__", "imp", "ort", "__"), _f("__", "imp", "ort", "__", _WS, "[(]")),
    (_f("p", "ty"),              _f(_PRE, "p", "ty", _POST)),
    (_f("c", "ty", "pes"),       _f(_PRE, "c", "ty", "pes", _POST)),
    # AUDIT FIX: only load/loads were covered; Unpickler(...).load() and the
    # _pickle alias execute identical deserialization.
    # CRITICAL FIX (audit round 3): the bare form matched only `loads`, so
    # `from pickle import load; load(...)` executed identical deserialization
    # undetected. Both bare names are matched.
    # CRITICAL FIX (audit round 6): `from pickle import Unpickler; Unpickler(f)`
    # matched NEITHER branch — the qualified form needs a pickle. prefix and the
    # bare forms are dot-guarded. The bare class name is now matched.
    (_f("pickle.", "lo", "ad"),  _f("_?pickle", _DOT, "(?:lo", "ads?|Unpickler)", _WS, "[(]") + "|"
                                 + _bare(_f("lo", "ad")) + "|" + _bare(_f("lo", "ads"))
                                 + "|" + _bare(_f("Un", "pickler"))),
    (_f("mar", "sh", "al"),      _f(_PRE, "mar", "sh", "al", _POST)),
    (_f("shell", "=True"),       _f("shell", "[ \t\n]*=", _WS, "True")),
    (_f("run", "py"),            _f(_PRE, "run", "py", _POST)),
    (_f("importlib.", "import_module"),
     # AUDIT FIX (round 10): same literal-dot defect as os.system above.
     _f("importlib", _DOT, "import_module", _WS, "[(]")
     + "|" + _bare(_f("import_module"))),
]
EXEC_FORBIDDEN = {n: p for n, p in _EXEC_NAMES}

# ---- FILE WRITE: exempted ONLY for the declared artifact writers -----------
_WRITE_NAMES = [
    # AUDIT FIX: `[^)]*` could not cross the first ')' so open(get(), "w") was
    # invisible; and r+/w+/a+/x+ were not covered. The arg scan is now
    # non-greedy to the LAST quote, and the mode class includes '+'.
    # AUDIT FIX: the mode class now covers b/t/+ flags and the arg scan
    # tolerates a newline inside the parens (a legal, backslash-free split).
    # AUDIT FIX: the mode class `[rwax]` flagged `open(path, "r")` — a READ — as
    # a write violation. Only w/a/x (and the + modes) are writes; a leading 'r'
    # is a read unless followed by '+'.
    # AUDIT FIX (round 22): `(?s:.*?)` with DOTALL crossed `)`, newlines and
    # intervening statements, so `open(a,"r")` followed anywhere later by a `"w"`
    # literal matched as ONE write violation. The arg scan is now bounded to the
    # call: no `)` and no `;` may intervene.
    (_f("open", "-write-mode"),
     # AUDIT FIX (round 6): the mode class required b/t BEFORE +, so the
     # docs-canonical "w+b" never matched, and a leading "b" (rb+/wb+) was missed.
     # The class now accepts the mode letters in any order plus a sign.
     _f("open", _WS, "[(](?s:[^);]*?)['", '"', "][rwaxtb]*[+][rwaxtb]*['", '"', "][ \t\n]*[,)]")
     + "|" + _f("open", _WS, "[(](?s:[^);]*?)['", '"', "][wax][rwaxtb]*['", '"', "][ \t\n]*[,)]")),
    (_f("os.", "wr", "ite"),    _f("os", _DOT, "wr", "ite", _WS, "[(]")),
    (_f("os.", "op", "en"),     _f("os", _DOT, "op", "en", _WS, "[(]")),
    (_f("os.", "re", "name"),   _f("os", _DOT, "re", "name", _WS, "[(]")),
    (_f("os.", "un", "link"),   _f("os", _DOT, "un", "link", _WS, "[(]")),
    (_f("os.", "re", "move"),   _f("os", _DOT, "re", "move", _WS, "[(]")),
    (_f("shu", "til"),          _f(_PRE, "shu", "til", _POST)),
    (_f("Path.", "write"),      _f(_DOT, "write_", "text", _WS, "[(]|", _DOT, "write_", "bytes", _WS, "[(]")),
    (_f("Named", "TemporaryFile"), _f("Named", "Temporary", "File")),
    # AUDIT FIX (round 7): the lexicon covered only NamedTemporaryFile, so
    # TemporaryFile / mkstemp / mkdtemp / mkdir / touch / unlink / replace /
    # symlink / truncate all created files undetected.
    (_f("tempfile", "-creators-bare"),
     _f(_PRE, "Temporary", "File", _WS, "[(]")
     + "|" + _f(_PRE, "mk", "stemp", _WS, "[(]")
     + "|" + _f(_PRE, "mk", "dtemp", _WS, "[(]")),
    (_f("tempfile", "-creators"),
     # AUDIT FIX (round 18): a literal `[.]` required an ADJACENT dot, so a dotted
     # creator written with legal whitespace evaded the scan. Every other dotted
     # rule had migrated to _DOT; this one had not.
     _f("tempfile", _DOT, "Temporary", "File", _WS, "[(]")
     + "|" + _f("tempfile", _DOT, "mk", "stemp", _WS, "[(]")
     + "|" + _f("tempfile", _DOT, "mk", "dtemp", _WS, "[(]")),
    # AUDIT FIX (round 13): the generic bare-form expansion derives a method name
    # by splitting on the dot, which cannot work for these hyphenated
    # multi-method entries — so `from os import mkdir; mkdir(p)` evaded the whole
    # lexicon. The bare forms are listed explicitly.
    # AUDIT FIX (round 14): the dotted forms need the LITERAL `os` prefix and the
    # bare forms are dot-guarded, so `import os as o; o.makedirs(p)` matched
    # NEITHER — the aliased-import evasion the exec lexicon had already closed.
    # Every write primitive now also has an ANY-RECEIVER form (the same _ALIAS
    # the exec lexicon uses), reported as a SUSPECT tier.
    # NOTE: each method needs its OWN _f call — `_f(a, b, c)` CONCATENATES, so a
    # single call with a fragment LIST builds one meaningless string.

    (_f("os.", "fs-creators-bare"),
     # AUDIT FIX (round 13): `_f(w) for w in ("mk","dir")` iterated the fragment
     # TUPLE, so it produced the patterns `mk(` and `dir(` instead of `mkdir(`.
     # The fragments must be joined in ONE _f call.
     _bare(_f("mk", "dir"))
     + "|" + _bare(_f("make", "dirs"))
     + "|" + _bare(_f("re", "place"))
     + "|" + _bare(_f("sym", "link"))
     + "|" + _bare(_f("trun", "cate"))),
    # AUDIT FIX (round 18): `rmdir`/`removedirs`/`renames` (and `Path.rmdir`)
    # evaded the WHOLE lexicon — the remove/rename rules require `[(]` straight
    # after the stem with no suffix wildcard. A deletion is a write.
    (_f("os.", "fs-removers"),
     "|".join(_f("os", _DOT, *frags, _WS, "[(]") for frags in (
         ("rm", "dir"), ("rm", "dirs"), ("remove", "dirs"), ("re", "names"),
         ("re", "move")))),
    (_f("Path.", "rmdir"),
     _f(_DOT, "rm", "dir", _WS, "[(]")),
    # the ALIASED route for the removers: a from-import (`from os import
    # removedirs`) or an aliased module (`import os as o; o.renames(..)`) has no
    # literal `os` at the call site, so it needs the bare + any-receiver forms.
    (_f("os.", "fs-removers-bare"),
     "|".join(_bare(_f(*fr)) for fr in (
         ("rm", "dir"), ("rm", "dirs"), ("remove", "dirs"), ("re", "names")))),
    (_f("os.", "fs-removers-any-receiver"),
     "|".join(_f(_ALIAS, *fr, _WS, "[(]") for fr in (
         ("rm", "dir"), ("rm", "dirs"), ("remove", "dirs"), ("re", "names")))),
    (_f("os.", "fs-creators"),
     _f("os", _DOT, "mk", "dir", _WS, "[(]")
     + "|" + _f("os", _DOT, "make", "dirs", _WS, "[(]")
     + "|" + _f("os", _DOT, "re", "place", _WS, "[(]")
     + "|" + _f("os", _DOT, "sym", "link", _WS, "[(]")
     + "|" + _f("os", _DOT, "trun", "cate", _WS, "[(]")),
    (_f("Path.", "fs-creators"),
     _f(_DOT, "mk", "dir", _WS, "[(]")
     + "|" + _f(_DOT, "touch", _WS, "[(]")
     + "|" + _f(_DOT, "un", "link", _WS, "[(]")
     + "|" + _f(_DOT, "re", "name", _WS, "[(]")),
]
# AUDIT FIX (round 12): the WRITE lexicon carried only DOTTED `os.*` forms, so a
# FROM-IMPORT evaded it — `from os import write; write(...)` has no `os.`
# substring at the call site. _EXEC_NAMES had already closed this hole for the
# exec names; each write name now also matches its BARE call form.
for _n, _pat in list(_WRITE_NAMES):
    if _n.startswith(("os.", "tempfile.")) and "." in _n:
        _word = _n.split(".", 1)[1]
        # AUDIT FIX (round 14): a hyphenated pseudo-entry ("fs-creators") has no
        # single method name, so `_bare("fs-creators")` built a pattern for the
        # literal `fs-creators(` — a rule that can never match. Only real
        # single-identifier method names are expanded.
        if not _word.isidentifier():
            continue
        # AUDIT FIX (round 22): `os.open` expands to the bare word `open`, and a
        # bare `open(` with NO mode check flagged every read as a write — the
        # builtin `open(p, "r")` became a violation. A name whose bare form would
        # be the BUILTIN is skipped: the dotted form already covers os.open, and
        # the builtin's own rule (open-write-mode) already requires a write mode.
        if _word == "open":
            continue
        # AUDIT FIX (round 13): the first list omitted mkdir/makedirs/replace/
        # symlink/truncate, so `from os import mkdir; mkdir(p)` evaded the
        # lexicon entirely. The bare expansion now covers EVERY write name.
        _WRITE_NAMES.append((_n + "-bare", _pat + "|" + _bare(_f(_word))))

WRITE_FORBIDDEN = {n: p for n, p in _WRITE_NAMES}

# THE WRITE SUSPECT TIER. AUDIT FIX (round 14): the aliased-import evasion
# (`import os as o; o.makedirs(p)`) is closed with ANY-RECEIVER patterns — but a
# receiver is not provably `os`, so `text.replace(` / `name.remove(` / `f.open(`
# match too. Those are LEGITIMATE calls, so they cannot be VIOLATIONS; they are
# REVIEW ITEMS, exactly like _ALIASED for the exec lexicon. The two tiers keep
# the audit's "zero violations" assertion honest while still surfacing the
# aliased spawn for a human.
WRITE_SUSPECT = [
    (_f("os.", "fs-creators-any-receiver"),
     "|".join(_f(_ALIAS, *frags, _WS, "[(]") for frags in (
         ("mk", "dir"), ("make", "dirs"), ("re", "place"), ("sym", "link"),
         ("trun", "cate")))),
    (_f("os.", "write-any-receiver"),
     "|".join(_f(_ALIAS, *frags, _WS, "[(]") for frags in (
         ("wr", "ite"), ("op", "en"), ("re", "name"), ("un", "link"),
         ("re", "move")))),
]

# FULL-PATH prefixes whose write authority is declared (the artifact writers).
# AUDIT FIX: keyed on the full relative path, never the basename.
WRITE_ALLOWED_PATHS = (
    "report/report.py",
    "corpus/build_corpus.py",
    "memory/memory_store.py",
    "integration/run_container_suite.py",
)

# Test files exercise writers and legitimately hold canaries.
TEST_PATH_RE = re.compile(_f("(^|/)tests?/|(^|/)test_[^/]*", "[.]py$"))


def _scan(path: Path, root: Path, src: str, lexicon: dict, kind: str) -> list:
    rel = str(path.relative_to(root))
    is_test = bool(TEST_PATH_RE.search(rel))
    out = []
    for name, pat in lexicon.items():
        for m in re.finditer(pat, src):
            # the confidence class is carried in the capability NAME suffix
            confidence = "suspect" if name.endswith("-any-receiver") else "exact"
            out.append({"file": rel,
                        "line": src[:m.start()].count(chr(10)) + 1,
                        "capability": name, "text": m.group(0),
                        "kind": kind, "in_test": is_test,
                        "confidence": confidence})
    return out


def scan_tree(root: str, include_tests: bool = True) -> list:
    """Every code-execution violation in the tree (never exempted), plus write
    violations outside the declared artifact paths."""
    root_p = Path(root)
    # AUDIT FIX (round 20): `rglob` on a NON-EXISTENT path yields empty with no
    # exception, and `[]` is this module's PASS — so a typo in the root silently
    # "proved" zero capability. A missing root is a refusal, never a clean scan.
    if not root_p.is_dir():
        raise ValueError(f"SCAN_ROOT_INVALID: {root!r} is not a directory")
    violations = []
    for f in sorted(root_p.rglob("*.py")):
        if any(part in (".git", ".venv", "__pycache__", "node_modules")
               for part in f.parts):
            continue
        rel = str(f.relative_to(root_p))
        is_test = bool(TEST_PATH_RE.search(rel))
        if is_test and not include_tests:
            continue
        # AUDIT FIX: read_text(errors="ignore") ignores DECODE errors only, so a
        # permission-denied / broken-symlink / raced-delete file raised OSError
        # out of scan_tree and discarded the whole audit. An unreadable file is
        # recorded and skipped.
        try:
            src = f.read_text(errors="ignore")
        except (OSError, UnicodeError) as e:
            # AUDIT FIX (round 18): this record omitted `confidence` while every
            # other finding carries it, so a consumer filtering on confidence
            # crashed on exactly the error path that should be most robust.
            violations.append({"file": rel, "line": 0, "capability": "UNREADABLE",
                               "text": f"{type(e).__name__}: {e}", "kind": "scan",
                               "in_test": is_test, "confidence": "exact"})
            continue
        violations += _scan(f, root_p, src, EXEC_FORBIDDEN, "exec")
        # AUDIT FIX (round 7): a file matching TEST_PATH_RE skipped the WRITE
        # lexicon entirely, so a writer placed at tests/payload.py evaded the
        # audit. The exemption is now limited to the DECLARED artifact paths —
        # a test file is not a licence to write.
        if rel not in WRITE_ALLOWED_PATHS:
            violations += _scan(f, root_p, src, WRITE_FORBIDDEN, "write")
        # AUDIT FIX (round 15): the WRITE_SUSPECT tier was defined but NEVER
        # wired into the tree audit — so the aliased-receiver evasion the
        # round-14 comment claims is closed (`import os as o; o.makedirs(p)`)
        # was still invisible to scan_tree. The suspects are emitted as
        # REVIEW ITEMS (confidence="suspect"), never as violations.
        for name, m in scan_write_suspects(src):
            line = src[:m.start()].count(chr(10)) + 1
            violations.append({
                "file": rel, "line": line, "capability": name, "text": m.group(0),
                "kind": "write", "in_test": is_test, "confidence": "suspect"})
    return violations


def scan_write_suspects(src: str) -> list:
    """The WRITE review tier: an aliased receiver calling a write primitive.
    Reported, never asserted against (see WRITE_SUSPECT)."""
    # AUDIT FIX (round 16, CRITICAL): this returned `(name, str)` while the
    # caller (scan_tree) treats the second element as a Match — so the FIRST
    # write-suspect hit crashed the whole tree audit with AttributeError. A
    # helper and its consumer must agree on the shape; it returns Matches.
    out = []
    for name, pat in WRITE_SUSPECT:
        for m in re.finditer(pat, src):
            out.append((name, m))
    return out


def scan_text(text: str) -> list:
    """Scan a string with the FULL lexicon (used by the negative control).

    AUDIT FIX (round 17 H4): the docstring said FULL but it scanned only
    EXEC_FORBIDDEN + WRITE_FORBIDDEN — omitting the WRITE_SUSPECT tier that
    scan_tree reports — and it returned no `confidence`, so a caller could not
    tell an EXACT violation from a SUSPECT. Both are now carried, so the
    negative control covers what the tree audit covers.
    """
    out = []
    for lexicon in (EXEC_FORBIDDEN, WRITE_FORBIDDEN):
        for name, pat in lexicon.items():
            for m in re.finditer(pat, text):
                out.append({"capability": name, "text": m.group(0),
                            "confidence": "suspect" if name.endswith("-any-receiver")
                            else "exact"})
    for name, m in scan_write_suspects(text):
        out.append({"capability": name, "text": m.group(0), "confidence": "suspect"})
    return out


def is_write_allowed(rel_path: str) -> bool:
    return rel_path in WRITE_ALLOWED_PATHS
