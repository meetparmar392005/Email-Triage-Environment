from dataclasses import dataclass, field


# ── Base classes (no openenv-core dependency needed) ─────────────────────────

@dataclass
class Action:
    pass

@dataclass
class Observation:
    pass

@dataclass
class State:
    pass


# ── Our typed models ──────────────────────────────────────────────────────────

@dataclass
class EmailAction(Action):
    action_type: str = ""   # "classify" | "prioritize" | "reply"
    value: str = ""

@dataclass
class EmailObservation(Observation):
    task_id: str = ""
    email: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    step_num: int = 0
    instructions: str = ""

@dataclass
class EmailState(State):
    task_id: str = ""
    step_num: int = 0
    done: bool = False
    cumulative_score: float = 0.0