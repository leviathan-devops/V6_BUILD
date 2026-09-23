"""limite/client.py — the Limite-1B client.

THE LAW: TEMPERATURE=0 on the MPSE path (any temp > 0 = AUTOMATIC-FAIL).
The client hard-codes temperature=0.0 and REFUSES to run if the served model
is unreachable — a loud fail, never a silent fallback to a heuristic.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error

BASE = os.environ.get("LIMITE_BASE", "http://127.0.0.1:8100/v1")
MODEL = os.environ.get("LIMITE_MODEL", "limite-1b")
TEMPERATURE = 0.0     # THE LAW — never change without failing the build


class LimiteUnavailable(RuntimeError):
    """LOUD FAIL: the math engine is down. No fallback, no substitute."""


def health(timeout: float = 5.0) -> dict:
    try:
        with urllib.request.urlopen(f"{BASE}/models", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        raise LimiteUnavailable(f"LIMITE_DOWN: {BASE}/models unreachable — {e}") from e


def complete(prompt: str, max_tokens: int = 512, timeout: float = 120.0) -> str:
    if TEMPERATURE != 0.0:
        raise RuntimeError(f"TEMPERATURE_LAW_VIOLATION: {TEMPERATURE} != 0.0")
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "temperature": TEMPERATURE,
        "top_p": 1.0,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(f"{BASE}/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LimiteUnavailable(f"LIMITE_HTTP_{e.code}: {e.read()[:400]!r}") from e
    except Exception as e:
        raise LimiteUnavailable(f"LIMITE_DOWN: {e}") from e
    return data["choices"][0]["text"]


def ask(query_id: str, **kw) -> tuple[float, str]:
    """Render the query, ask Limite, parse the numeric answer."""
    from math_queries import render, QUERIES
    prompt = render(query_id, **kw)
    raw = complete(prompt)
    return QUERIES[query_id].parse(raw), raw
