"""decider/client.py — the client for the PUBLISHED Decider model.

WIRE FORMAT: POST /v1/systemone — TypeSafe Jev's format, the same one the
decider family was trained to serve (MODEL_CARD_0.8B.md: "Same code, same wire
format (POST /v1/systemone, TypeSafe Jev's format), same training recipe").

THE MODEL IS NOT REIMPLEMENTED HERE. It is called. A hand-built head with
untrained weights is not the decider the study trained; the published model is.
(Superseded artifact + its measured ECE: ./SUPERSEDED.md)

THE THREE PRIMITIVES (the family interface):
    choice  — pick one of N described options  -> {choice, confidence, probabilities}
    noul    — probability of yes                -> {noul}
    score   — position on described levels      -> {score, probabilities}

NO SAMPLING: the readout is a softmax over the option logits at the answer
slot; there is no decode, no temperature, no text generation.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error

DEFAULT_BASE = "http://127.0.0.1:8008"


class DeciderUnavailable(RuntimeError):
    """LOUD FAIL: the decider cannot be reached. No substitute, ever."""


def health(url: str | None = None, timeout: float = 10.0) -> dict:
    """AUDIT FIX: url resolves AT CALL TIME (was an import-time default that
    froze a stale BASE)."""
    base = url or os.environ.get("DECIDER_URL", DEFAULT_BASE)
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=timeout) as r:
            raw = r.read()
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_DOWN: {base}/health unreachable — {e}") from e
    # AUDIT FIX: the health payload shape is validated here too — a 200 with a
    # non-object body used to pass through and fail later with AttributeError.
    try:
        data = json.loads(raw)
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_BAD_JSON: {raw[:200]!r}") from e
    if not isinstance(data, dict):
        raise DeciderUnavailable(f"DECIDER_BAD_SHAPE: expected an object, got {type(data).__name__}")
    return data


def system_one(state, questions: dict, timeout: float | None = None,
               url: str | None = None) -> dict:
    """One forward pass: state + typed questions -> a distribution per question."""
    base = url or os.environ.get("DECIDER_URL", DEFAULT_BASE)
    # AUDIT FIX: env parsing and serialization now sit INSIDE the contract — a
    # malformed DECIDER_TIMEOUT or a non-serializable state raised a raw
    # ValueError/TypeError before the try that maps failures to DeciderUnavailable.
    try:
        to = timeout if timeout is not None else float(os.environ.get("DECIDER_TIMEOUT", "180"))
        body = json.dumps({"state": state, "questions": questions}).encode()
    except (TypeError, ValueError) as e:
        raise DeciderUnavailable(f"DECIDER_BAD_REQUEST: {type(e).__name__}: {e}") from e
    req = urllib.request.Request(f"{base}/v1/systemone", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=to) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        # AUDIT FIX: reading the error body can itself fail (a truncated
        # connection), which escaped as a raw URLError instead of DeciderUnavailable.
        try:
            body = e.read()[:400]
        except Exception:
            body = b"<error body unreadable>"
        raise DeciderUnavailable(f"DECIDER_HTTP_{e.code}: {body!r}") from e
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_DOWN: {e}") from e
    # AUDIT FIX: the response shape is validated INSIDE the loud-fail contract.
    try:
        data = json.loads(raw)
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_BAD_JSON: {raw[:300]!r}") from e
    if not isinstance(data, dict):
        raise DeciderUnavailable(f"DECIDER_BAD_SHAPE: expected an object, got {type(data).__name__}")
    if "answers" not in data:
        raise DeciderUnavailable(
            f"DECIDER_NO_ANSWERS: the payload carries no 'answers' key — keys={list(data)}")
    if not isinstance(data["answers"], dict):
        raise DeciderUnavailable(
            f"DECIDER_BAD_ANSWERS: 'answers' must be an object, got "
            f"{type(data['answers']).__name__}")
    return data


# ---- the typed question builders (the family's 3 primitives) ----------------
def choice(instructions: str, criteria: dict) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}

def noul(instructions: str) -> dict:
    return {"type": "noul", "instructions": instructions}

def score(instructions: str, criteria: list) -> dict:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


class Decider:
    """The published decider, called over its own wire format.

    AUDIT FIX: the instance keeps its OWN url. The first version rewrote a
    module global in __init__, so a second instance silently rewired every
    other instance and the module-level functions — and decide() ignored
    self.url entirely, so two instances with different urls both talked to
    whichever was constructed last.
    """

    def __init__(self, url: str | None = None):
        self.url = url or os.environ.get("DECIDER_URL", DEFAULT_BASE)
        h = health(self.url)
        self.model = h.get("model", "?")
        self.device = h.get("device", "?")

    def decide(self, state, questions: dict) -> dict:
        # no fallback: system_one raises DeciderUnavailable on a bad payload
        return system_one(state, questions, url=self.url)["answers"]

    def info(self) -> dict:
        return {"url": self.url, "model": self.model, "device": self.device,
                "wire": "POST /v1/systemone (TypeSafe Jev format)"}
