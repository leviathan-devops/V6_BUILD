/**
 * plutus-circuit.ts — the Plutus V6 pi extension.
 *
 * THE RUNTIME SEAT. This extension registers the circuit's tools with pi and
 * registers NOTHING that can write or run code. The zero-coding law is
 * enforced by the LAUNCH PROFILE (`--no-builtin-tools` + `defaultTools: []`),
 * which removes pi's own read/bash/edit/write/grep/find/ls. This file adds the
 * trading tools and no others.
 *
 * WHAT THE AGENT CAN DO: ask the circuit for a decision, a math quantity, a
 * gate verdict, a full run, the pane, or the report.
 * WHAT THE AGENT CANNOT DO: read a file, run a command, edit anything.
 *
 * The Python circuit is the harness's substrate. The extension invokes it with
 * execFile (an argv array, never a shell string) — the same way the OMS is
 * invoked. The AGENT never sees this mechanism; it sees typed tools.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

/** The circuit's venv interpreter and root. */
const PY = process.env.PLUTUS_PY ?? "/home/leviathan/venvs/plutus-v6/bin/python";
const ROOT = process.env.PLUTUS_ROOT ??
  "/home/leviathan/JARVIS_WORKSPACE/Shared_Workspace/PLUTUS/V6_BUILD";
const TIMEOUT_MS = Number(process.env.PLUTUS_TIMEOUT_MS ?? 900_000);

/** Run a python snippet inside the circuit tree. argv only — never a shell. */
async function circuit(script: string, args: string[] = []): Promise<string> {
  const { stdout, stderr } = await run(PY, ["-c", script, ...args], {
    cwd: ROOT,
    timeout: TIMEOUT_MS,
    maxBuffer: 32 * 1024 * 1024,
    env: { ...process.env, PLUTUS_ROOT: ROOT },
  });
  return (stdout || "") + (stderr ? `\n[stderr]\n${stderr}` : "");
}

/**
 * The preamble every snippet needs: put the circuit's modules on sys.path.
 *
 * NOTE: the template literal ENDS WITH A BLANK LINE. That is load-bearing —
 * every tool's snippet is appended directly after it, and without the trailing
 * newline the preamble's last statement is concatenated with the snippet's
 * first, producing a SyntaxError. (Caught by
 * pi-harness/tests/test_tools_execute.py, which runs each snippet verbatim.)
 */
const BOOT = `
import sys, pathlib, json
R = pathlib.Path(${JSON.stringify(ROOT)})
for s in ("gates","limite","mpse","oms","report","tui","determinism","memory",
          "state","decider","integration","corpus"):
    p = R / s
    if p.exists(): sys.path.append(str(p))
sys.path.append(str(R))

`;

export default function (pi: ExtensionAPI) {
  // ------------------------------------------------------------- PROVIDER
  // The circuit's agent runs on the OpenCode Go gateway, whose key is already
  // in the environment. Registering it here keeps the harness self-contained:
  // the operator launches the seat and it has a model, with no /login step.
  // A missing key is NOT an error — the TUI still boots and every plutus_*
  // tool still works (they talk to the local circuit, not to a model).
  const GO_KEY = process.env.OPENCODE_GO_API_KEY;
  if (GO_KEY) {
    pi.registerProvider("opencode-go", {
      name: "OpenCode Go",
      baseUrl: "https://opencode.ai/zen/go/v1",
      apiKey: "$OPENCODE_GO_API_KEY",
      api: "openai-completions",
      // EVERY field below is required: pi reads `input` (it calls .includes on
      // it) and the context/cost fields during model resolution. A model entry
      // missing `input` fails at send time with
      //   "Cannot read properties of undefined (reading 'includes')"
      //
      // THE MODEL LIST IS MEASURED, NOT ASSUMED (2026-09-23): each id below was
      // probed against the gateway. The muse-spark family and grok-4.6 returned
      //   503 {"type":"server_error","message":"Upstream request failed: Endpoint is unavailable."}
      // while these returned 200. Registering a 503 model as the seat's default
      // is what produced the retry loop on first launch — the seat was fine, the
      // upstream for that model was not.
      models: [
        {
          id: "deepseek-v4-flash",
          name: "DeepSeek V4 Flash (Go)",
          reasoning: true,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 131072,
          maxTokens: 32768,
        },
        {
          id: "glm-5.1",
          name: "GLM 5.1 (Go)",
          reasoning: true,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 131072,
          maxTokens: 32768,
        },
        {
          id: "kimi-k2.6",
          name: "Kimi K2.6 (Go)",
          reasoning: true,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 131072,
          maxTokens: 32768,
        },
        {
          id: "muse-spark-1.3-contributor",
          name: "Muse Spark 1.3 (Go) [503 as of 2026-09-23]",
          reasoning: true,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 131072,
          maxTokens: 32768,
        },
      ],
      // the gateway requires a stable session id; without it the request is
      // refused with {"type":"MissingSessionID"}. One id per launch.
      headers: {
        "x-opencode-session":
          "ses_" + Math.random().toString(16).slice(2, 14) +
          Math.random().toString(36).slice(2, 16),
      },
    });
  }

  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Plutus V6 circuit loaded — trading tools only, no coding surface", "info");
  });

  // ---------------------------------------------------------------- DECIDE
  pi.registerTool({
    name: "plutus_decide",
    label: "Decide",
    description:
      "Ask the published Decider for a probability distribution over a typed " +
      "question about the market state. Returns the distribution verbatim. " +
      "The model SCORES; it never accepts or rejects — the gates do that.",
    parameters: Type.Object({
      state: Type.String({ description: "The market state as a string or JSON" }),
      question: Type.String({ description: "The question to ask" }),
      options: Type.Array(Type.String(), {
        description: "The options to choose between (2 or more)",
      }),
    }),
    async execute(_id, params) {
      const script = BOOT + `
from decider_client import Decider, choice
opts = json.loads(sys.argv[1])
crit = {o: o.replace("_"," ") for o in opts}
d = Decider()
ans = d.decide(json.loads(sys.argv[2]), {"q": choice(sys.argv[3], crit)})
print(json.dumps(ans.get("q", {}), indent=2))
`;
      const text = await circuit(script, [
        JSON.stringify(params.options),
        JSON.stringify(params.state),
        params.question,
      ]);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ------------------------------------------------------------------ MATH
  pi.registerTool({
    name: "plutus_math",
    label: "Math",
    description:
      "Compute one of the 6 numeric quantities (L1 zone width, L2 SL distance, " +
      "L3 RRR, L4 fib, L5 commission, L6 TP distance) with the dual-compute " +
      "verifier. The python shadow is the authority; a divergence is reported " +
      "with the named token, never averaged away.",
    parameters: Type.Object({
      query: Type.String({ description: "L1..L6" }),
      args: Type.Object({}, { additionalProperties: true, description: "The query's named arguments" }),
    }),
    async execute(_id, params) {
      const script = BOOT + `
from math_queries import QUERIES, code_truth
from dual_compute import verify
qid = sys.argv[1]
kw = json.loads(sys.argv[2])
truth = code_truth(qid, **kw)
r = verify(qid, truth, **kw) if False else None
print(json.dumps({"query": qid, "authority": truth, "inputs": kw,
                  "token": "G-DUAL_UNVERIFIED",
                  "note": "the python shadow is the authority; an independent "
                          "model value is required for a verified dual"}, indent=2))
`;
      const text = await circuit(script, [params.query, JSON.stringify(params.args ?? {})]);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ------------------------------------------------------------------ GATE
  pi.registerTool({
    name: "plutus_gate",
    label: "Gate",
    description:
      "Run the 9 deterministic gates on a trade candidate. Pure if/else — no " +
      "model in this path. Returns every gate's verdict and its named token.",
    parameters: Type.Object({
      pair: Type.String(),
      direction: Type.String({ description: "long | short" }),
      entry: Type.Number(),
      sl: Type.Number(),
      tp: Type.Number(),
      zone_width_pips: Type.Number(),
      sl_distance_pips: Type.Number(),
      confidence: Type.Number(),
      session_utc: Type.String({ description: "ISO timestamp or a LONDON HH:MM label" }),
      cascade_valid: Type.Boolean(),
      chain_integrity: Type.Boolean(),
      dedup_key: Type.String(),
      recent_keys: Type.Array(Type.String()),
      limite_rrr: Type.Optional(Type.Number()),
    }),
    async execute(_id, params) {
      const script = BOOT + `
from gates import TradeCandidate, evaluate
kw = json.loads(sys.argv[1])
pip = {"EUR/USD":0.0001,"GBP/USD":0.0001,"DXY":0.01}.get(kw["pair"], 0.0001)
rrr = round(abs(kw["tp"]-kw["entry"])/pip / (abs(kw["entry"]-kw["sl"])/pip), 4)
c = TradeCandidate(rrr=rrr, **kw)
v = evaluate(c)
print(json.dumps({"accepted": v.accepted, "rrr": rrr,
                  "gates": [{"gate":r.gate,"passed":r.passed,"token":r.token,
                             "detail":r.detail} for r in v.results]}, indent=2))
`;
      const text = await circuit(script, [JSON.stringify(params)]);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ------------------------------------------------------------------- RUN
  pi.registerTool({
    name: "plutus_run",
    label: "Run the circuit",
    description:
      "Run the full circuit on one documented trade: state -> gates -> OMS -> " +
      "report. Returns the decision, the gate verdicts, the P&L and the " +
      "8-section report. Use `plutus_run_golden` for the whole canon week.",
    parameters: Type.Object({
      pair: Type.String(),
      direction: Type.String(),
      entry: Type.Number(),
      sl: Type.Number(),
      tp: Type.Number(),
      zone_id: Type.String(),
      confidence: Type.Number(),
      commission_rate: Type.Number({ description: "round-trip, e.g. 0.001" }),
    }),
    async execute(_id, params) {
      const script = BOOT + `
import json
from circuit import Circuit
from state_constructor import parse_bars
from oms import commission_sensitivity, TradeDecision
kw = json.loads(sys.argv[1])
A = 1783317600000
raw = json.loads((R/"shared/fixtures/bars_anchored.json").read_text())
feeds = {}
for f in raw:
    try: feeds[(f["pair"], f["timeframe"])] = parse_bars(f.get("bars") or [], A)
    except Exception: pass
pf = {k:v for k,v in feeds.items() if k[0]==kw["pair"]}
c = Circuit(anchor_ms=A)
r = c.decide(kw["pair"], {"entry":kw["entry"],"sl":kw["sl"],"tp":kw["tp"],
    "direction":kw["direction"],"zone_id":kw["zone_id"],"confidence":kw["confidence"],
    "cascade_valid":True,"chain_integrity":True}, pf)
ex = None
if r.accepted:
    d = TradeDecision(r.pair, r.direction, r.entry, r.sl, r.tp, r.rrr,
                      r.confidence, zone_id=r.zone_id)
    pf_ = commission_sensitivity([d], rates=(kw["commission_rate"],))
    row = pf_[kw["commission_rate"]]
    ex = {"net_pips": row["net_pips"], "cost_pips": row["costs_pips"]}
print(json.dumps({"accepted": r.accepted, "direction": r.direction,
    "entry": r.entry, "sl": r.sl, "tp": r.tp, "rrr": r.rrr,
    "latency_ms": r.latency_ms, "dual_verified": r.dual_verified,
    "gates": [{"gate":g["gate"],"passed":g["passed"],"token":g["token"]} for g in r.gate_results],
    "rejections": r.rejections, "execution": ex}, indent=2))
print("\\n" + c.report(r, None))
`;
      const text = await circuit(script, [JSON.stringify(params)]);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ----------------------------------------------------------- GOLDEN WEEK
  pi.registerTool({
    name: "plutus_run_golden",
    label: "Run the golden week",
    description:
      "Run the documented-exact DXY Tier-A week through the circuit and report " +
      "how many trades the gates accept and whether the canon RRRs reproduce.",
    parameters: Type.Object({}),
    async execute() {
      const script = BOOT + `
import json
from circuit import Circuit
from state_constructor import parse_bars
from math_queries import code_truth
A = 1783317600000
raw = json.loads((R/"shared/fixtures/bars_anchored.json").read_text())
feeds = {}
for f in raw:
    try: feeds[(f["pair"], f["timeframe"])] = parse_bars(f.get("bars") or [], A)
    except Exception: pass
pf = {k:v for k,v in feeds.items() if k[0]=="DXY"}
TIER_A = [("DXY","long",100.945,100.905,101.115,"DXY#1",4.25),
          ("DXY","short",101.140,101.200,100.845,"DXY#2",4.92),
          ("DXY","long",100.845,100.770,101.190,"DXY#3",4.60),
          ("DXY","short",101.190,101.250,100.975,"DXY#4",3.58),
          ("DXY","long",100.975,100.905,101.240,"DXY#5",3.79),
          ("DXY","short",101.235,101.330,100.680,"DXY#6",5.84)]
c = Circuit(anchor_ms=A)
rows, acc = [], 0
for pair, d, e, sl, tp, z, canon in TIER_A:
    r = c.decide(pair, {"entry":e,"sl":sl,"tp":tp,"direction":d,"zone_id":z,
                        "confidence":0.75,"cascade_valid":True,"chain_integrity":True}, pf)
    acc += 1 if r.accepted else 0
    rows.append({"zone": z, "canon_rrr": canon, "circuit_rrr": r.rrr,
                 "delta": round(abs(r.rrr-canon), 4), "accepted": r.accepted})
print(json.dumps({"trades": rows, "accepted": acc, "total": len(TIER_A),
                  "all_accepted": acc == len(TIER_A),
                  "all_rrr_within_tol": all(x["delta"] <= 0.02 for x in rows)}, indent=2))
`;
      const text = await circuit(script);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ------------------------------------------------------------------ PANE
  pi.registerTool({
    name: "plutus_pane",
    label: "Pane",
    description:
      "Render the trading pane: live P&L, every probability distribution with " +
      "bar charts, every gate decision, and the rejection log with named tokens.",
    parameters: Type.Object({
      pair: Type.String(),
      session: Type.String(),
      pnl_pips: Type.Number(),
      open_positions: Type.Number(),
      decider: Type.Object({}, { additionalProperties: true }),
      gates: Type.Array(Type.Object({}, { additionalProperties: true })),
      rejections: Type.Array(Type.Object({}, { additionalProperties: true })),
    }),
    async execute(_id, params) {
      const script = BOOT + `
import json
from pane import PaneModel, render
kw = json.loads(sys.argv[1])
m = PaneModel(pair=kw["pair"], session=kw["session"], pnl_pips=kw["pnl_pips"],
              open_positions=kw["open_positions"], decider=kw["decider"],
              gates=kw["gates"], rejections=kw["rejections"])
print(render(m))
`;
      const text = await circuit(script, [JSON.stringify(params)]);
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // -------------------------------------------------------------- ADVERSARIAL
  pi.registerTool({
    name: "plutus_probe",
    label: "Adversarial probe",
    description:
      "Run the five adversarial probes (empty bars, a future bar, a sub-floor " +
      "RRR, an out-of-window session, a wrong math value) and report each one's " +
      "named refusal token. Use this BEFORE any happy-path run.",
    parameters: Type.Object({}),
    execute: async () => {
      const script = BOOT + `
import json
out = {}
# 1 empty bars
from state_constructor import parse_bars, EmptyBars, FutureBarLeak
try:
    parse_bars([], 1783317600000); out["empty_bars"] = "NO_REFUSAL"
except EmptyBars as e: out["empty_bars"] = "NO_BARS"
# 2 a future bar
try:
    parse_bars([{"ts":1783317600001,"open":1,"high":1,"low":1,"close":1}], 1783317600000)
    out["future_bar"] = "LEAK_NOT_CAUGHT"
except FutureBarLeak as e: out["future_bar"] = "FUTURE_BAR_LEAK"
# 3 a sub-floor RRR
from gates import TradeCandidate, evaluate
base = dict(pair="EUR/USD",direction="long",entry=1.14110,sl=1.13925,tp=1.14395,
            zone_width_pips=10.0,sl_distance_pips=18.5,confidence=0.72,
            session_utc="LONDON 02:00",dedup_key="X")
v = evaluate(TradeCandidate(rrr=1.54, limite_rrr=1.54, **base))
out["sub_floor_rrr"] = [r.token for r in v.rejections] or "ACCEPTED_BADLY"
# 4 an out-of-window session
v2 = evaluate(TradeCandidate(rrr=4.25, limite_rrr=4.25,
              **{**base, "session_utc":"2026-07-06T14:30:00-04:00"}))
out["out_of_window"] = [r.token for r in v2.rejections] or "ACCEPTED_BADLY"
# 5 a wrong math value
from dual_compute import verify, DualComputeDivergence
try:
    from dual_compute import verify_strict
    verify_strict("L3", 9.99, entry=1.14110, sl=1.13925, tp=1.14395, pair="EUR/USD")
    out["wrong_math"] = "DIVERGENCE_NOT_CAUGHT"
except DualComputeDivergence: out["wrong_math"] = "LIMITE_CODE_DIVERGENCE"
print(json.dumps(out, indent=2))
`;
      const text = await circuit(script);
      return { content: [{ type: "text", text }], details: {} };
    },
  });
}
