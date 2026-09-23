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

BASE = os.environ.get("DECIDER_URL", "http://127.0.0.1:8008")
TIMEOUT = float(os.environ.get("DECIDER_TIMEOUT", "180"))


class DeciderUnavailable(RuntimeError):
    """LOUD FAIL: the decider cannot be reached. No substitute, ever."""


def health(timeout: float = 10.0) -> dict:
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_DOWN: {BASE}/health unreachable — {e}") from e


def system_one(state, questions: dict, timeout: float = TIMEOUT) -> dict:
    """One forward pass: state + typed questions -> a distribution per question."""
    body = json.dumps({"state": state, "questions": questions}).encode()
    req = urllib.request.Request(f"{BASE}/v1/systemone", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise DeciderUnavailable(f"DECIDER_HTTP_{e.code}: {e.read()[:400]!r}") from e
    except Exception as e:
        raise DeciderUnavailable(f"DECIDER_DOWN: {e}") from e


# ---- the typed question builders (the family's 3 primitives) ----------------
def choice(instructions: str, criteria: dict) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}

def noul(instructions: str) -> dict:
    return {"type": "noul", "instructions": instructions}

def score(instructions: str, criteria: list) -> dict:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


class Decider:
    """The published decider, called over its own wire format."""

    def __init__(self, url: str = BASE):
        global BASE
        BASE = url
        h = health()
        self.model = h.get("model", "?")
        self.device = h.get("device", "?")
        self.url = url

    def decide(self, state, questions: dict) -> dict:
        out = system_one(state, questions)
        return out.get("answers", out)

    def info(self) -> dict:
        return {"url": self.url, "model": self.model, "device": self.device,
                "wire": "POST /v1/systemone (TypeSafe Jev format)"}
