class Environment:
    pass
from ..models import EmailAction, EmailObservation, EmailState
from .tasks import TASKS


class EmailEnvironment(Environment):
    MAX_STEPS = 5

    def __init__(self):
        self._task_id: str = "easy"
        self._email: dict = {}
        self._step_num: int = 0
        self._history: list = []
        self._done: bool = False
        self._cumulative_score: float = 0.0
        self._last_score: float = 0.0
        self._last_reason: str = ""

    def reset(self, task_id: str = "easy") -> EmailObservation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task '{task_id}'. Valid: {list(TASKS)}")

        self._task_id = task_id
        self._step_num = 0
        self._history = []
        self._done = False
        self._cumulative_score = 0.0
        self._last_score = 0.0
        self._last_reason = ""
        task = TASKS[task_id]
        self._email = task.sample_email()

        return EmailObservation(
            task_id=task_id,
            email=self._email,
            history=[],
            step_num=0,
            instructions=task.instructions,
        )

    def step(self, action: EmailAction) -> tuple[EmailObservation, float, bool]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        task = TASKS[self._task_id]
        score, reason = task.grade(action, self._email)

        self._step_num += 1
        self._cumulative_score += score
        self._last_score = score
        self._last_reason = reason
        self._history.append({
            "step": self._step_num,
            "action_type": action.action_type,
            "value": action.value[:100],   # truncate for storage
            "score": score,
            "reason": reason,
        })

        # Episode ends on a perfect score OR hitting max steps
        done = (score == 1.0) or (self._step_num >= self.MAX_STEPS)
        self._done = done

        obs = EmailObservation(
            task_id=self._task_id,
            email=self._email,
            history=self._history.copy(),
            step_num=self._step_num,
            instructions=TASKS[self._task_id].instructions,
        )
        return obs, score, done

    def state(self) -> EmailState:
        return EmailState(
            task_id=self._task_id,
            step_num=self._step_num,
            done=self._done,
            cumulative_score=round(self._cumulative_score, 4),
        )

    def grader_result(self) -> dict:
        return {
            "task_id": self._task_id,
            "done": self._done,
            "step_num": self._step_num,
            "last_score": round(self._last_score, 4),
            "last_reason": self._last_reason,
            "cumulative_score": round(self._cumulative_score, 4),
            "max_possible_cumulative": float(self.MAX_STEPS),
            "normalized_score": round(
                min(1.0, max(0.0, self._cumulative_score / float(self.MAX_STEPS))), 4
            ),
            "history": self._history.copy(),
        }
