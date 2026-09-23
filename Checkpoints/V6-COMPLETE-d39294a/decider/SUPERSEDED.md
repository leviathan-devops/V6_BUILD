# SUPERSEDED — the hand-built pointer head (2026-09-23)

`model.py` in this directory constructs a Decider from scratch: Qwen3-0.6B-Base
+ a hand-initialised `PointerHead` + a delimiter-scan readout.

**IT IS SUPERSEDED AND MUST NOT BE USED FOR DECISIONS.** Why:

1. The real Decider is PUBLISHED and AVAILABLE ON THIS HOST. Probe results:
     - `Mapika/decider-0.8b`   base Qwen3.5-0.8B-Base, 1.4 GB bf16  (smallest)
     - `Mapika/decider-2b`     base Qwen3.5-2B-Base,   3.5 GB bf16  (the default)
     - `Mapika/decider-4b`     base Qwen3.5-4B-Base,   8.4 GB bf16
   Source: JevManager/vendor/decider/MODEL_CARD_0.8B.md (the family table).
2. It is SERVED already: `uvicorn decider.serve:app` on 127.0.0.1:8008,
   `/health` -> {"ok":true,"model":"Mapika/decider-2b","device":"cuda"},
   `POST /v1/systemone` in TypeSafe Jev's exact wire format.
3. A hand-built head has UNTRAINED weights. The ECE probe measured 0.3858 on it
   against a 0.05 gate — an uncalibrated head is not the decider the study
   trained (0.809 on the single-run protocol).

The hand-built head was built on the assumption that no published Decider was
reachable (`Mapika/decider-0.6b` returns HTTP 401; `decider-2b` was reachable
but I did not check for a local implementation). That assumption was WRONG and
the artifact is retained only as a record of the wrong path.

THE REAL PATH: `decider/client.py` -> POST /v1/systemone -> the published model.
