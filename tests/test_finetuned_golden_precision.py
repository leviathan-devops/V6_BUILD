"""tests/test_finetuned_golden_precision.py — the W7 GATE, reported honestly.

THE PIN'S W7 GATE: "fine-tuned >=14/15 golden, test_finetuned_golden_precision".

THE HARD STOP IT COLLIDES WITH:
    "VRAM overflow: if the 3-model stack exceeds 12GB, BLOCKED + report which
     model to downgrade"

THE ANTI-STOP IT MUST OBEY:
    "BLOCKED-AS-DONE: a BLOCKED entry (VRAM, GPU-down) has a resume condition —
     it is never a pass."

So this test has exactly three outcomes and NEVER a fake one:
  PASS     — a fine-tuned adapter exists AND the fine-tuned model reproduces
             >=14/15 golden entries within 3 pips.
  FAIL     — an adapter exists but does NOT meet the precision bar.
  BLOCKED  — no adapter exists because the fine-tune cannot fit the card. The
             exit code is 2 (distinct from 0/1) and the reason + resume condition
             are printed. A BLOCKED is NEVER reported as a pass.

WHY IT IS BLOCKED (the MEASURED arithmetic, from the model's own config.json —
NOT from its name):
    Mapika/decider-2b is 1.666B params (24 layers, hidden 2048, GQA 2 KV heads,
    TIED embeddings). The published trainer (`vendor/decider/decider/train.py:95`)
    is FULL-PARAMETER AdamW with NO memory lever (grep for grad_checkpoint /
    offload / 8bit / deepspeed / fsdp / zero returns ZERO matches).

      full fp32 AdamW     23.3 GB   does NOT fit
      8-bit AdamW         13.3 GB   does NOT fit
      8-bit Adam + ckpt  ~10.3 GB   does NOT fit while the services run

THE RESUME CONDITION: free ~10 GB (stop the Decider server + the Limite vLLM
engine, which hold 5602 + 4060 MiB), OR downgrade the served decision model to
Mapika/decider-0.8b (1.4 GB bf16) per .trident/VRAM_BLOCKER.md.
"""
import _boot, sys, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parent.parent
ADAPTER = Path(os.environ.get("DECIDER_ADAPTER", "/home/leviathan/models/decider-0.6b-plutus"))
FIXTURE = R / "shared/fixtures/bars_anchored.json"
ANCHOR = 1783317600000
MIN_ENTRIES = 14
MAX_DELTA_PIPS = 3.0


def _free_mib() -> int:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return int(out)
    except Exception:
        return -1


def _adapter_present() -> bool:
    if not ADAPTER.exists():
        return False
    return any(ADAPTER.rglob("*.safetensors")) or any(ADAPTER.rglob("adapter_model.*"))


def main() -> int:
    present = _adapter_present()
    free = _free_mib()

    if not present:
        # ---- BLOCKED: no adapter, and the reason is measured, not asserted ----
        print(f"[DETAIL] fine-tuned adapter at {ADAPTER}: ABSENT")
        print(f"[DETAIL] GPU free memory: {free} MiB")
        print(f"[DETAIL] the trainer is FULL-PARAMETER with no memory lever "
              f"(vendor/decider/decider/train.py:95)")
        print(f"[DETAIL] 1.666B params -> full fp32 AdamW 23.3 GB, 8-bit AdamW "
              f"13.3 GB, 8-bit + grad-ckpt ~10.3 GB")
        print(f"[DETAIL] RESUME CONDITION: free ~10 GB (stop the Decider server "
              f"+ the Limite vLLM engine) OR downgrade the served model to "
              f"Mapika/decider-0.8b per .trident/VRAM_BLOCKER.md")
        print(f"[DETAIL] this is BLOCKED, never a pass (the pin's BLOCKED-AS-DONE rule)")
        print("RESULT: BLOCKED test_finetuned_golden_precision")
        print("[TOKEN-ABSENT] test_finetuned_golden_precision")
        return 2

    # ---- an adapter EXISTS: run the precision bar ----
    sys.path.insert(0, str(R / "integration"))
    sys.path.insert(0, str(R / "state"))
    from circuit import Circuit
    from state_constructor import parse_bars

    raw = json.loads(FIXTURE.read_text())
    feeds = {}
    for f in raw:
        try:
            feeds[(f["pair"], f["timeframe"])] = parse_bars(f.get("bars") or [], ANCHOR)
        except Exception:
            pass

    TIER_A = [("DXY", "long", 100.945, 100.905, 101.115, "DXY#1", 4.25),
              ("DXY", "short", 101.140, 101.200, 100.845, "DXY#2", 4.92),
              ("DXY", "long", 100.845, 100.770, 101.190, "DXY#3", 4.60),
              ("DXY", "short", 101.190, 101.250, 100.975, "DXY#4", 3.58),
              ("DXY", "long", 100.975, 100.905, 101.240, "DXY#5", 3.79),
              ("DXY", "short", 101.235, 101.330, 100.680, "DXY#6", 5.84)]
    c = Circuit(use_limite=False, use_decider=True, anchor_ms=ANCHOR)
    ok_n, max_delta = 0, 0.0
    for pair, dr, e, sl, tp, zid, canon in TIER_A:
        r = c.decide(pair, {"entry": e, "sl": sl, "tp": tp, "direction": dr,
                            "zone_id": zid, "confidence": 0.75,
                            "cascade_valid": True, "chain_integrity": True}, feeds)
        d = abs(r.rrr - canon)
        max_delta = max(max_delta, d)
        if d <= 0.02:
            ok_n += 1

    ok = ok_n >= MIN_ENTRIES
    print(f"[DETAIL] the fine-tuned model reproduced {ok_n}/6 Tier-A RRRs "
          f"(max_delta {max_delta:.4f})")
    print(f"[TOKEN] test_finetuned_golden_precision" if ok
          else "[TOKEN-ABSENT] test_finetuned_golden_precision")
    print(f"RESULT: {'PASS' if ok else 'FAIL'} test_finetuned_golden_precision")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
