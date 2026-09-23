"""decider/question_templates.py — the 17 typed questions in 4 calls.

THE PACKING GRAMMAR (blueprint §1.2):
  <|fim_prefix|> STATE <|fim_middle|> QUESTION <|box_start|> OPTION <|box_end|> ... <|fim_suffix|>

Three primitives (blueprint §1.4):
  CHOICE  — pick one from N options
  NOUL    — binary yes/no
  SCORE   — position on an ordered scale

4 CALLS (blueprint §1.7):
  CALL 1 E1 PRESSURE  : 5 questions
  CALL 2 E2 STORYLINE : 4 questions
  CALL 3 E3 TRADE     : 5 questions
  CALL 4 PVE SCORING  : 3 questions
  TOTAL: 17 questions
"""
from __future__ import annotations
from dataclasses import dataclass, field

STATE_DELIM = "<|fim_prefix|>"
QUESTION_DELIM = "<|fim_middle|>"
OPTION_OPEN = "<|box_start|>"
OPTION_CLOSE = "<|box_end|>"
DECIDE = "<|fim_suffix|>"

CHOICE, NOUL, SCORE = "choice", "noul", "score"


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    kind: str
    options: tuple[str, ...]
    call: str

    def render(self) -> str:
        opts = "".join(f"{OPTION_OPEN}{o}{OPTION_CLOSE}" for o in self.options)
        return f"{QUESTION_DELIM}{self.text}{opts}{DECIDE}"

    @property
    def n_options(self) -> int:
        return len(self.options)


# ---- CALL 1: E1 PRESSURE (5) -----------------------------------------------
E1 = (
    Question("E1.Q1", "What is the zone type at this level?",
             CHOICE, ("BoM", "MoM", "PHANTOM", "LQZ"), "E1"),
    Question("E1.Q2", "Does this zone pass the OBCV displacement gate?",
             NOUL, ("pass", "fail"), "E1"),
    Question("E1.Q3", "What is the mitigation state?",
             CHOICE, ("unmitigated", "1x", "2x", "3x_deployed"), "E1"),
    Question("E1.Q4", "What is the pressure classification?",
             CHOICE, ("strong_demand", "weak_demand", "neutral",
                      "weak_supply", "strong_supply"), "E1"),
    Question("E1.Q5", "Is this a FORTRESS zone (4+ defense events)?",
             NOUL, ("no", "yes"), "E1"),
)

# ---- CALL 2: E2 STORYLINE (4) ----------------------------------------------
E2 = (
    Question("E2.Q1", "What shape is forming on the day element?",
             CHOICE, ("BS", "WL", "RWL", "R", "SS", "consolidation"), "E2"),
    Question("E2.Q2", "What is the day element designation?",
             CHOICE, ("BS_day", "WL_day", "R_day"), "E2"),
    Question("E2.Q3", "Is the cascade valid?",
             CHOICE, ("valid", "invalid", "partial"), "E2"),
    Question("E2.Q4", "What is the freshness state?",
             CHOICE, ("unmitigated", "1x_80", "2x_50", "3x_deployed"), "E2"),
)

# ---- CALL 3: E3 TRADE (5) --------------------------------------------------
E3 = (
    Question("E3.Q1", "What is the trade direction?",
             CHOICE, ("long", "short", "no_trade"), "E3"),
    Question("E3.Q2", "What is the quality grade?",
             SCORE, ("F", "C", "B", "A", "Aplus"), "E3"),
    Question("E3.Q3", "Is the session valid for entry?",
             NOUL, ("yes", "no"), "E3"),
    Question("E3.Q4", "Is the SL inside the envelope?",
             NOUL, ("yes", "no"), "E3"),
    Question("E3.Q5", "Is there shield coverage on the entry path?",
             NOUL, ("yes", "no"), "E3"),
)

# ---- CALL 4: PVE SCORING (3) -----------------------------------------------
PVE = (
    Question("PVE.Q1", "What is the TP hit probability?",
             SCORE, ("very_low", "low", "medium", "high", "very_high"), "PVE"),
    Question("PVE.Q2", "Is the entry reachable from here?",
             NOUL, ("yes", "no"), "PVE"),
    Question("PVE.Q3", "What is the confidence grade?",
             SCORE, ("F", "C", "B", "A", "Aplus"), "PVE"),
)

CALLS = {"E1": E1, "E2": E2, "E3": E3, "PVE": PVE}
ALL_QUESTIONS = E1 + E2 + E3 + PVE           # 17

# The confidence grade -> numeric mapping the gate layer consumes.
GRADE_VALUE = {"F": 0.45, "C": 0.55, "B": 0.65, "A": 0.75, "Aplus": 0.85}
SCORE_LEVELS = {"E3.Q2": ("F", "C", "B", "A", "Aplus"),
                "PVE.Q1": ("very_low", "low", "medium", "high", "very_high"),
                "PVE.Q3": ("F", "C", "B", "A", "Aplus")}


def render_call(call: str, state: str) -> str:
    """Pack the state + one call's questions into a single Decider input."""
    qs = CALLS[call]
    return state + "".join(q.render() for q in qs)


def expected_level(probs: dict[str, float], levels: tuple[str, ...]) -> float:
    """The score primitive's expected level: sum(i * p_i), 1-INDEXED.

    The blueprint §1.4 states the formula and its worked value explicitly:
      Output [0.02, 0.08, 0.25, 0.45, 0.20] -> expected level = 3.73
    1*0.02 + 2*0.08 + 3*0.25 + 4*0.45 + 5*0.20 = 3.73  (1-indexed)
    0*0.02 + 1*0.08 + 2*0.25 + 3*0.45 + 4*0.20 = 2.73  (0-indexed -- WRONG)
    The blueprint is the authority: 1-index the scale.
    """
    return round(sum((i + 1) * probs.get(lv, 0.0) for i, lv in enumerate(levels)), 4)


def grade_from_probs(probs: dict[str, float]) -> tuple[str, float]:
    """Map an E3.Q2/PVE.Q3 distribution to (grade, confidence value).

    The expected level is 1-indexed, so index = round(expected) - 1.
    """
    lv = SCORE_LEVELS["PVE.Q3"]
    exp = expected_level(probs, lv)
    idx = max(0, min(len(lv) - 1, int(round(exp)) - 1))
    grade = lv[idx]
    return grade, GRADE_VALUE[grade]


assert len(ALL_QUESTIONS) == 17, f"expected 17 questions, got {len(ALL_QUESTIONS)}"
assert len(E1) == 5 and len(E2) == 4 and len(E3) == 5 and len(PVE) == 3
