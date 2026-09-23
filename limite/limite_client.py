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
            raw = r.read()
    except urllib.error.HTTPError as e:
        try:
            body = e.read()[:400]
        except Exception:
            body = b"<error body unreadable>"
        raise LimiteUnavailable(f"LIMITE_HTTP_{e.code}: {body!r}") from e
    except Exception as e:
        raise LimiteUnavailable(f"LIMITE_DOWN: {e}") from e
    # AUDIT FIX: the shape check lives INSIDE the loud-fail contract. The first
    # version indexed choices[0].text outside the try, so a malformed payload
    # raised a raw KeyError/IndexError instead of LimiteUnavailable.
    try:
        data = json.loads(raw)
        text = data["choices"][0]["text"]
    except Exception as e:
        raise LimiteUnavailable(
            f"LIMITE_BAD_RESPONSE: {type(e).__name__} on {raw[:300]!r}") from e
    if not isinstance(text, str):
        # AUDIT FIX: a payload with `"text": null` passed the shape check and
        # failed later in parse() with a raw AttributeError.
        raise LimiteUnavailable(
            f"LIMITE_BAD_TEXT: expected a string, got {type(text).__name__}")
    return text


def ask(query_id: str, **kw) -> tuple[float, str]:
    """Render the query, ask Limite, parse the numeric answer.

    AUDIT FIX: an unknown query_id raised a raw KeyError and a model reply with
    no ANSWER tag raised a raw ValueError, both escaping the loud-fail contract.
    """
    from math_queries import render, QUERIES
    if query_id not in QUERIES:
        raise LimiteUnavailable(
            f"LIMITE_UNKNOWN_QUERY: {query_id!r} (known: {sorted(QUERIES)})")
    prompt = render(query_id, **kw)
    raw = complete(prompt)
    try:
        return QUERIES[query_id].parse(raw), raw
    except Exception as e:
        raise LimiteUnavailable(
            f"LIMITE_UNPARSEABLE: {type(e).__name__}: {e}") from e
