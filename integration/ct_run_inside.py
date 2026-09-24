"""integration/ct_run_inside.py — the CONTAINER-SIDE driver (RUNS INSIDE).

WHY THIS FILE EXISTS. The host-side runner shelled out to
`omp ct exec --name omp-ct -- ...`. That is NOT a real CLI: `omp` parses `ct` as
a launch MESSAGE and then rejects `--name` as an unknown flag, so every scenario
returned exit 2 with the extension log as its output. The suite's verdicts could
therefore NOT be reproduced by the runner that claimed them — the artifact was
true but the reproduction path was decorative.

THE SANCTIONED PATH is the container-testing AGENT TOOL. This script is what that
tool EXECUTES; because it already runs INSIDE the container, it invokes the
scenarios with plain `subprocess` and needs no docker and no CLI indirection.

THE SCENARIO AUTHORITY is `run_ct_suite.ADV` / `.HAPPY` — imported, never
duplicated, so the list cannot drift between the runner and the driver.

THE OUTPUT is /work/p3/ct-capture.json (the raw per-scenario records), which the
host-side assembler folds into .trident/ct-results.json.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# AUDIT FIX (round 33): _fail_capture was DEFINED but never called — the import
# below aborted before it could run. The import is now guarded and the failure
# WRITES A CAPTURE, so the host never sees a missing or stale file.
try:
    from run_ct_suite import ADV, HAPPY, EXCLUDED, EXCLUSION_REASON  # noqa: E402
except Exception as _imp_e:                                # noqa: BLE001
    # AUDIT FIX (round 38): this wrote directly, so a missing /work/p3 raised
    # FileNotFoundError (masking the import error) and a kill mid-write left a
    # TRUNCATED capture. Same atomic pattern as main(): mkdir + tmp + replace.
    import json as _j, os as _os
    from pathlib import Path as _P
    try:
        _p = _P("/work/p3/ct-capture.json")
        _p.parent.mkdir(parents=True, exist_ok=True)
        _t = _p.with_suffix(".json.tmp")
        _t.write_text(_j.dumps(
            {"scenarios": [],
             "error": f"AUTHORITY_IMPORT_FAILED: {type(_imp_e).__name__}: {_imp_e}"},
            indent=2))
        _os.replace(_t, _p)
    except Exception as _w:                                # noqa: BLE001
        import sys as _s
        print(f"CAPTURE_WRITE_FAILED: {type(_w).__name__}: {_w}", file=_s.stderr)
    raise SystemExit(2)

CT_DIR = "/work/p3/plutus-ct"
CAPTURE = Path("/work/p3/ct-capture.json")


def _fail_capture(reason: str) -> None:
    """Write a STRUCTURED capture for a pre-flight failure.

    AUDIT FIX (round 32): the authority import sat at MODULE level, so a missing
    or broken `run_ct_suite` exited with a traceback and left the capture MISSING
    or — worse — STALE from a prior run with the same scenario ids, which the host
    assembler would then validate as current. A failure now writes a capture that
    says so.
    """
    import json as _json
    from pathlib import Path as _P
    try:
        _P("/work/p3/ct-capture.json").write_text(_json.dumps(
            {"scenarios": [], "error": reason}, indent=2))
    except Exception as _e:                                # noqa: BLE001
        # AUDIT FIX (round 34): a silent failure here hid the very condition this
        # function exists to report.
        import sys as _s
        print(f"CAPTURE_WRITE_FAILED: {type(_e).__name__}: {_e}", file=_s.stderr)


def _evidence(out: str, token: str, window: int = 1500) -> str:
    """The persisted evidence, GUARANTEED to contain `token` when it is present.

    AUDIT FIX (round 15): a fixed tail slice could cut the deciding line out of
    the record, so the host assembler refused a legitimate PASS. If the token is
    in the output, a window AROUND it is persisted; otherwise the tail is kept.
    """
    i = out.find(token)
    if i < 0:
        return out[-window:]
    lo = max(0, i - window // 3)
    return out[lo: lo + window]


def run(cmd: str, timeout: int = 900) -> tuple[int, str, float]:
    # AUDIT FIX (round 11): `bash -lc` sources login profiles, so PATH and env
    # could differ between hosts and inject noise into token matching; and the
    # clock was `time.time()`, which an NTP step can skew negative. Plain `-c`
    # and a MONOTONIC clock.
    t0 = time.monotonic()
    try:
        p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True,
                           timeout=timeout)
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        # AUDIT FIX (round 11): the partial stdout/stderr ride on the EXCEPTION,
        # and the first version discarded them — losing the evidence of exactly
        # how far a timed-out scenario got.
        # AUDIT FIX (round 12): with text=True the partial output on the
        # exception is STR, so `.decode()` raised AttributeError — inside the
        # exception handler, losing the evidence entirely. Both shapes handled.
        def _as_text(v):
            if v is None:
                return ""
            return v if isinstance(v, str) else v.decode(errors="replace")
        part = _as_text(e.stdout) + _as_text(e.stderr)
        rc = -1
        out = f"EXEC_ERROR: TimeoutExpired after {timeout}s\n{part}"
    except Exception as e:                                     # noqa: BLE001
        rc, out = -1, f"EXEC_ERROR: {type(e).__name__}: {e}"
    return rc, out, round((time.monotonic() - t0) * 1000, 1)


def main() -> int:
    results = []
    # THE ADVERSARIAL SCENARIOS RUN FIRST (the pin's ADVERSARIAL LOOP).
    for _entry in ADV:
        # AUDIT FIX (round 35): a malformed authority entry (wrong arity) aborted
        # main() before the capture was written, discarding every prior result.
        try:
            sid, name, cmd_tpl, pass_tok, fail_tok = _entry
        except (TypeError, ValueError) as e:
            results.append({"id": f"ADV-BAD-{len(results)}", "name": "malformed entry",
                            "kind": "adversarial", "exitCode": -1,
                            "passToken": "", "passTokenMatch": False,
                            "failToken": "", "failTokenAbsent": False,
                            "toolResultContext": f"ENTRY_MALFORMED: {e}",
                            "durationMs": 0.0, "verdict": "FAIL"})
            continue
        # AUDIT FIX (round 13): the % substitution sat OUTSIDE error handling, so
        # a stray '%' in a future heredoc would abort main() before the atomic
        # capture write — discarding every prior scenario AND leaving no capture.
        try:
            cmd = cmd_tpl % CT_DIR
        except (TypeError, ValueError) as e:
            results.append({
                "id": sid, "name": name, "kind": "adversarial", "exitCode": -1,
                "passToken": pass_tok, "passTokenMatch": False,
                "failToken": fail_tok, "failTokenAbsent": False,
                "toolResultContext": f"EXEC_ERROR: template formatting: {e}",
                "durationMs": 0.0, "verdict": "FAIL"})
            continue
        rc, out, ms = run(cmd)
        pm, fa = pass_tok in out, fail_tok not in out
        results.append({
            "id": sid, "name": name, "kind": "adversarial",
            "exitCode": rc, "passToken": pass_tok, "passTokenMatch": pm,
            "failToken": fail_tok, "failTokenAbsent": fa,
            "toolResultContext": _evidence(out, pass_tok), "durationMs": ms,
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})
    # THE HAPPY PATH RUNS LAST (the post-debug confirmation).
    for _entry in HAPPY:
        try:
            sid, name, test = _entry
        except (TypeError, ValueError) as e:
            results.append({"id": f"HAPPY-BAD-{len(results)}", "name": "malformed entry",
                            "kind": "happy_path", "exitCode": -1,
                            "passToken": "", "passTokenMatch": False,
                            "failToken": "", "failTokenAbsent": False,
                            "toolResultContext": f"ENTRY_MALFORMED: {e}",
                            "durationMs": 0.0, "verdict": "FAIL"})
            continue
        rc, out, ms = run(f"cd {CT_DIR} && PLUTUS_PY=python3 bash tests/run.sh {test}")
        # AUDIT FIX (round 15): the verdict was computed on the FULL output while
        # only `out[-1500:]` was persisted, and the host assembler requires the
        # passToken to appear IN the persisted context — so a verbose PASS whose
        # token scrolled out of the tail was rejected as unsupported evidence.
        # The persisted context now GUARANTEES it contains the deciding line.
        pm = f"RESULT: PASS {test}" in out
        # AUDIT FIX (round 11): the failToken was the literal "[TOKEN-ABSENT]",
        # which never appears in real output — so failTokenAbsent was ALWAYS true
        # and the check was vacuous. A real failure marker is now asserted.
        # AUDIT FIX (round 16): `failToken` was a DISPLAY STRING
        # ("RESULT: FAIL | TOKEN-ABSENT | Traceback") that never occurs verbatim,
        # so a downstream `failToken not in context` search always saw it absent —
        # a vacuous pass. The token is now ONE real marker, and the extra checks
        # live in `failTokenAbsent` where they belong.
        fa = ("RESULT: FAIL" not in out and "TOKEN-ABSENT" not in out
              and "Traceback (most recent call last)" not in out)
        results.append({
            "id": sid, "name": name, "kind": "happy_path",
            # AUDIT FIX (round 15): the stored token was the bare test NAME while
            # the verdict matched the full "RESULT: PASS <test>" line — so a
            # FAILURE output mentioning the name would satisfy the downstream
            # evidence check. The stored token is the line that actually decided.
            "exitCode": rc, "passToken": f"RESULT: PASS {test}", "passTokenMatch": pm,
            # the SINGLE marker a downstream substring search can actually use
            "failToken": "RESULT: FAIL",
            "failTokenAbsent": fa,
            "toolResultContext": _evidence(out, f"RESULT: PASS {test}"), "durationMs": ms,
            "verdict": "PASS" if (pm and fa and rc == 0) else "FAIL"})

    # AUDIT FIX (round 11): a kill mid-write left a truncated capture. Write to a
    # temp file in the SAME directory, then os.replace() — atomic on POSIX.
    CAPTURE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "scenarios": results,
        "excludedByName": EXCLUDED,
        "exclusionReason": EXCLUSION_REASON,
    }, indent=2)
    tmp = CAPTURE.with_suffix(".json.tmp")
    tmp.write_text(payload)
    os.replace(tmp, CAPTURE)
    n = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"CT-INSIDE: {n}/{len(results)} PASS -> {CAPTURE}")
    for r in results:
        print(f"  {r['verdict']:4} {r['id']:9} {r['kind']:11} {r['name'][:52]}")
    # AUDIT FIX (round 11): main() always returned 0, so an exit-code caller saw
    # success while scenarios had FAILED. The verdict is now propagated.
    # AUDIT FIX (round 35): an EMPTY suite made `n == len(results)` true (0 == 0)
    # and returned success — masking a broken authority as a pass. The sibling
    # assembler refuses an empty capture; the driver now refuses an empty suite.
    if not results:
        print("CT_SUITE_EMPTY: the authority produced no scenarios — refusing a "
              "vacuous PASS")
        return 2
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
