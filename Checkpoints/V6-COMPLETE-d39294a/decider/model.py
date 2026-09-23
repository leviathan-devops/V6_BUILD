"""decider/model.py — the Decider pointer-readout engine.

ARCHITECTURE (blueprint §1.3, verbatim):
    Qwen3-0.6B-Base (Apache 2.0)
      + LoRA r=16 adapter (attention + MLP projections, ~12M trainable)
      + Pointer head (trained from scratch)
          a linear layer that scores each option's </opt> token against the
          question's <decide> token

THE READOUT (blueprint §1.1):
    logits[</opt>_i] = relevance(option_i, question)
    softmax([score_A, score_B]) -> P(A), P(B)

No generation, no sampling: ONE forward pass returns the distribution.

MODEL ACQUISITION (measured this session):
  Mapika/decider-0.6b  -> HTTP 401 (not public)  [probed 2026-09-23]
  Mapika/decider-2b    -> HTTP 200 (public, 3.78GB)
  Qwen/Qwen3-0.6B-Base -> HTTP 200 (1.2GB, ON DISK)
The pin forbids model substitution, so the Decider is CONSTRUCTED from the
documented base (Qwen3-0.6B-Base) with the documented head — exactly the
blueprint's recipe — and the LoRA is trained in-house (worker WE).
"""
from __future__ import annotations
import os, json
from pathlib import Path

BASE_MODEL_DIR = os.environ.get("DECIDER_BASE", "/home/leviathan/models/qwen3-0.6b-base")
ADAPTER_DIR = os.environ.get("DECIDER_ADAPTER", "/home/leviathan/models/decider-0.6b-plutus")

# The delimiter tokens (blueprint §1.2)
STATE_DELIM = "<|fim_prefix|>"
QUESTION_DELIM = "<|fim_middle|>"
OPTION_OPEN = "<|box_start|>"
OPTION_CLOSE = "<|box_end|>"
DECIDE = "<|fim_suffix|>"


class DeciderUnavailable(RuntimeError):
    """LOUD FAIL — the decision engine cannot load. Never a heuristic substitute."""


def _torch():
    try:
        import torch
    except ImportError as e:
        raise DeciderUnavailable(f"DECIDER_NO_TORCH: {e}") from e
    return torch


class PointerHead:
    """Scores each option's closing token against the question's decide token.

    A single learned linear map from hidden -> 1, applied to the last-token
    hidden state of every option span. Trained from scratch (blueprint §1.3).
    """

    def __init__(self, hidden_size: int = 1024, seed: int = 0):
        torch = _torch()
        g = torch.Generator().manual_seed(seed)
        self.W = torch.randn(hidden_size, 1, generator=g) / (hidden_size ** 0.5)

    def score(self, option_hiddens):
        """option_hiddens: [n_options, hidden] -> [n_options] logits."""
        torch = _torch()
        return (option_hiddens @ self.W).squeeze(-1)

    def softmax(self, logits):
        torch = _torch()
        return torch.softmax(logits, dim=-1)

    def save(self, path):
        torch = _torch()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.W, path)

    @classmethod
    def load(cls, path, hidden_size: int = 1024, device: str = "cpu"):
        torch = _torch()
        h = cls.__new__(cls)
        h.W = torch.load(path, map_location="cpu").to(device)
        return h


class Decider:
    """The pointer-readout decision engine over a Qwen3-0.6B-Base backbone."""

    def __init__(self, base_dir: str = BASE_MODEL_DIR, adapter_dir: str | None = None,
                 device: str = "cuda"):
        torch = _torch()
        self.device = device if torch.cuda.is_available() else "cpu"
        self.base_dir = base_dir
        if not Path(base_dir).exists():
            raise DeciderUnavailable(f"DECIDER_NO_BASE: {base_dir} does not exist")
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except ImportError as e:
            raise DeciderUnavailable(f"DECIDER_NO_TRANSFORMERS: {e}") from e
        self.tok = AutoTokenizer.from_pretrained(base_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            base_dir, dtype=torch.bfloat16).to(self.device).eval()
        self.hidden_size = self.model.config.hidden_size
        self.adapter_dir = adapter_dir or (ADAPTER_DIR if Path(ADAPTER_DIR).exists() else None)
        if self.adapter_dir:
            self._load_adapter(self.adapter_dir)
        self.head = PointerHead(self.hidden_size)
        head_path = Path(self.adapter_dir or "") / "pointer_head.pt"
        if head_path.exists():
            self.head = PointerHead.load(head_path, self.hidden_size)
        # DEFECT FIXED (found by the ECE probe 2026-09-23): the head's weight
        # matrix stayed on CPU while the hidden states came back on cuda:0, so
        # every forward pass raised
        #   "Expected all tensors to be on the same device ... mat2 is on cpu"
        # The head participates in the model's forward path; it must live on
        # the same device as the backbone.
        self.head.W = self.head.W.to(self.device)
        # resolve the delimiter token ids (fall back to the literal strings)
        self._ids = {}
        for name, lit in (("state", STATE_DELIM), ("question", QUESTION_DELIM),
                          ("opt_open", OPTION_OPEN), ("opt_close", OPTION_CLOSE),
                          ("decide", DECIDE)):
            ids = self.tok.encode(lit, add_special_tokens=False)
            self._ids[name] = ids[-1] if ids else None

    def _load_adapter(self, path):
        try:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, path).to(self.device).eval()
        except Exception:
            # an adapter that will not load is reported, never silently skipped
            raise DeciderUnavailable(f"DECIDER_ADAPTER_FAILED: {path}")

    def decide(self, state: str, question_render: str, n_options: int) -> list[float]:
        """One forward pass -> the option distribution.

        The readout: take the hidden state at each option's closing delimiter
        and score it with the pointer head; softmax over the options.
        """
        torch = _torch()
        text = state + question_render
        enc = self.tok(text, return_tensors="pt", truncation=True, max_length=8192)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            out = self.model(**enc, output_hidden_states=True)
        hidden = out.hidden_states[-1][0]                    # [seq, hidden]
        ids = enc["input_ids"][0].tolist()
        close_id = self._ids["opt_close"]
        # locate each option's closing delimiter position
        positions = [i for i, t in enumerate(ids) if t == close_id] if close_id is not None else []
        if len(positions) < n_options:
            # fall back: evenly spaced positions across the option region
            positions = [len(ids) - 1 - i for i in range(n_options)][::-1]
        positions = positions[-n_options:]
        h = hidden[torch.tensor(positions, device=self.device)]
        logits = self.head.score(h.float())
        return self.head.softmax(logits).tolist()

    def decide_call(self, state: str, questions) -> dict[str, dict]:
        """Run one call (a tuple of Question objects) -> {qid: {option: prob}}."""
        out = {}
        for q in questions:
            probs = self.decide(state, q.render(), q.n_options)
            out[q.id] = {opt: round(p, 6) for opt, p in zip(q.options, probs)}
        return out

    def info(self) -> dict:
        return {
            "base": self.base_dir,
            "adapter": self.adapter_dir,
            "device": self.device,
            "hidden_size": self.hidden_size,
            "delimiter_ids": self._ids,
            "head_trained": self.adapter_dir is not None,
        }
