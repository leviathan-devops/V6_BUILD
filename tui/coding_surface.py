"""tui/coding_surface.py — the NO-CODING audit.

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


def _bare(word: str) -> str:
    return _PRE + word + _WS + "[(]"


def _qualified(word: str) -> str:
    # AUDIT FIX: the dunder-qualified call form matched NEITHER the bare pattern
    # (a preceding '.' is excluded) nor the plain qualified pattern. Both
    # qualified spellings are now matched.
    # split the "builtins" literal so this source never contains it whole
    bi = _f("buil", "t", "ins")
    return (_f(bi, "[.]", word, _WS, "[(]") + "|"
            + _f("__", bi, "__[.]", word, _WS, "[(]"))


_EXEC_NAMES = [
    (_f("sub", "pro", "cess"),   _f(_PRE, "sub", "pro", "cess", _POST)),
    # AUDIT FIX: the dotted-only forms were bypassed by a from-import
    # (importing the name directly and calling it). Each name now also matches
    # its BARE call form, so the alias/import route is caught too.
    (_f("os.", "sy", "s", "tem"), _f("os[.]", "sy", "s", "tem", _WS, "[(]") + "|"
                                 + _bare(_f("sy", "s", "tem"))),
    (_f("os.", "ex", "ec"),      _f("os[.]", "ex", "ec", "[0-9A-Za-z_]*", _WS, "[(]") + "|"
                                 + _bare(_f("ex", "ec", "l")) + "|" + _bare(_f("ex", "ec", "v"))
                                 + "|" + _bare(_f("ex", "ec", "l", "p"))),
    (_f("os.", "spa", "wn"),     _f("os[.]", "spa", "wn", "[0-9A-Za-z_]*", _WS, "[(]") + "|"
                                 + _bare(_f("spa", "wn")) + "|" + _bare(_f("spa", "wn", "l"))),
    (_f("po", "pen"),            _f("[Pp]", "open", _WS, "[(]")),
    (_f("ev", "al"),             _bare("eval") + "|" + _qualified("eval")),
    (_f("ex", "ec"),             _bare("exec") + "|" + _qualified("exec")),
    (_f("com", "pile"),          _bare("compile") + "|" + _qualified("compile")),
    (_f("__", "imp", "ort", "__"), _f("__", "imp", "ort", "__", _WS, "[(]")),
    (_f("p", "ty"),              _f(_PRE, "p", "ty", _POST)),
    (_f("c", "ty", "pes"),       _f(_PRE, "c", "ty", "pes", _POST)),
    # AUDIT FIX: only load/loads were covered; Unpickler(...).load() and the
    # _pickle alias execute identical deserialization.
    (_f("pickle.", "lo", "ad"),  _f("_?pickle[.](?:lo", "ads?|Unpickler)", _WS, "[(]") + "|"
                                 + _bare(_f("lo", "ads"))),
    (_f("mar", "sh", "al"),      _f(_PRE, "mar", "sh", "al", _POST)),
    (_f("shell", "=True"),       _f("shell", _WS, "=", _WS, "True")),
    (_f("run", "py"),            _f(_PRE, "run", "py", _POST)),
    (_f("importlib.", "import_module"), _f("importlib[.]import_module", _WS, "[(]")),
]
EXEC_FORBIDDEN = {n: p for n, p in _EXEC_NAMES}

# ---- FILE WRITE: exempted ONLY for the declared artifact writers -----------
_WRITE_NAMES = [
    # AUDIT FIX: `[^)]*` could not cross the first ')' so open(get(), "w") was
    # invisible; and r+/w+/a+/x+ were not covered. The arg scan is now
    # non-greedy to the LAST quote, and the mode class includes '+'.
    (_f("open", "-write-mode"),
     _f("open", _WS, "[(].*?['", '"', "][rwax][+]?['", '"', "][ \t]*[,)]")),
    (_f("os.", "wr", "ite"),    _f("os[.]", "wr", "ite", _WS, "[(]")),
    (_f("os.", "op", "en"),     _f("os[.]", "op", "en", _WS, "[(]")),
    (_f("os.", "re", "name"),   _f("os[.]", "re", "name", _WS, "[(]")),
    (_f("os.", "un", "link"),   _f("os[.]", "un", "link", _WS, "[(]")),
    (_f("os.", "re", "move"),   _f("os[.]", "re", "move", _WS, "[(]")),
    (_f("shu", "til"),          _f(_PRE, "shu", "til", _POST)),
    (_f("Path.", "write"),      _f("[.]write_", "text", _WS, "[(]|[.]write_", "bytes", _WS, "[(]")),
    (_f("Named", "TemporaryFile"), _f("Named", "Temporary", "File")),
]
WRITE_FORBIDDEN = {n: p for n, p in _WRITE_NAMES}

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
            out.append({"file": rel,
                        "line": src[:m.start()].count(chr(10)) + 1,
                        "capability": name, "text": m.group(0),
                        "kind": kind, "in_test": is_test})
    return out


def scan_tree(root: str, include_tests: bool = True) -> list:
    """Every code-execution violation in the tree (never exempted), plus write
    violations outside the declared artifact paths."""
    root_p = Path(root)
    violations = []
    for f in sorted(root_p.rglob("*.py")):
        if any(part in (".git", ".venv", "__pycache__", "node_modules")
               for part in f.parts):
            continue
        rel = str(f.relative_to(root_p))
        is_test = bool(TEST_PATH_RE.search(rel))
        if is_test and not include_tests:
            continue
        src = f.read_text(errors="ignore")
        violations += _scan(f, root_p, src, EXEC_FORBIDDEN, "exec")
        if rel not in WRITE_ALLOWED_PATHS and not is_test:
            violations += _scan(f, root_p, src, WRITE_FORBIDDEN, "write")
    return violations


def scan_text(text: str) -> list:
    """Scan a string with the FULL lexicon (used by the negative control)."""
    out = []
    for lexicon in (EXEC_FORBIDDEN, WRITE_FORBIDDEN):
        for name, pat in lexicon.items():
            for m in re.finditer(pat, text):
                out.append({"capability": name, "text": m.group(0)})
    return out


def is_write_allowed(rel_path: str) -> bool:
    return rel_path in WRITE_ALLOWED_PATHS
