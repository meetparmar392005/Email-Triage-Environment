from email_triage_env.models import EmailAction, EmailObservation, EmailState
from .tasks import TASKS


class EmailEnvironment:
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
        """Reset environment with robust error handling."""
        try:
            # Validate task_id
            if not task_id or not isinstance(task_id, str):
                raise ValueError(f"Invalid task_id: {task_id}")
            
            if task_id not in TASKS:
                raise ValueError(f"Unknown task '{task_id}'. Valid: {list(TASKS.keys())}")

            # Reset state
            self._task_id = task_id
            self._step_num = 0
            self._history = []
            self._done = False
            self._cumulative_score = 0.0
            self._last_score = 0.0
            self._last_reason = ""
            
            # Sample email
            task = TASKS[task_id]
            self._email = task.sample_email()
            
            # Validate email
            if not isinstance(self._email, dict):
                raise ValueError("Invalid email format")

            return EmailObservation(
                task_id=task_id,
                email=self._email,
                history=[],
                step_num=0,
                instructions=task.instructions,
            )
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Reset failed: {str(e)}") from e

    def step(self, action: EmailAction) -> tuple[EmailObservation, float, bool]:
        """Execute step with robust error handling."""
        try:
            # Validate episode state
            if self._done:
                raise RuntimeError("Episode is done. Call reset() to start a new one.")
            
            # Validate action
            if not isinstance(action, EmailAction):
                raise TypeError(f"Expected EmailAction, got {type(action)}")
            
            if not hasattr(action, 'action_type') or not hasattr(action, 'value'):
                raise ValueError("Invalid action: missing action_type or value")

            # Get task and grade action
            task = TASKS.get(self._task_id)
            if not task:
                raise RuntimeError(f"Invalid task_id: {self._task_id}")
            
            score, reason = task.grade(action, self._email)
            
            # Ensure score is in valid range (0.01, 0.99) - STRICTLY between 0 and 1
            score = float(score)
            score = min(0.99, max(0.01, score))

            # Update state
            self._step_num += 1
            self._cumulative_score += score
            self._last_score = score
            self._last_reason = str(reason)
            
            # Safely truncate action value
            action_value = str(action.value) if action.value is not None else ""
            self._history.append({
                "step": self._step_num,
                "action_type": str(action.action_type),
                "value": action_value[:100],
                "score": round(score, 4),
                "reason": str(reason),
            })

            # Episode ends on a near-perfect score OR hitting max steps
            done = (score >= 0.95) or (self._step_num >= self.MAX_STEPS)
            self._done = done

            obs = EmailObservation(
                task_id=self._task_id,
                email=self._email,
                history=self._history.copy(),
                step_num=self._step_num,
                instructions=TASKS[self._task_id].instructions,
            )
            return obs, score, done
        except RuntimeError:
            raise
        except Exception as e:
            # Return safe default on error
            self._done = True
            return EmailObservation(
                task_id=self._task_id,
                email=self._email,
                history=self._history.copy(),
                step_num=self._step_num,
                instructions="Error occurred",
            ), 0.0, True

    def state(self) -> EmailState:
        """Get current state with error handling."""
        try:
            return EmailState(
                task_id=str(self._task_id),
                step_num=int(self._step_num),
                done=bool(self._done),
                cumulative_score=round(float(self._cumulative_score), 4),
            )
        except Exception as e:
            # Return safe default state
            return EmailState(
                task_id="error",
                step_num=0,
                done=True,
                cumulative_score=0.0,
            )

    def grader_result(self) -> dict:
        """Get grader result with error handling."""
        try:
            # Safely compute normalized score
            # Use actual steps taken, not MAX_STEPS, to reward efficiency
            actual_steps = max(1, self._step_num)  # At least 1 step
            cumulative = float(self._cumulative_score)
            
            # Normalized score = average reward per step taken
            # Ensure it's strictly between 0 and 1
            normalized = cumulative / float(actual_steps)
            normalized = min(0.99, max(0.01, normalized))
            
            return {
                "task_id": str(self._task_id),
                "done": bool(self._done),
                "step_num": int(self._step_num),
                "last_score": round(float(self._last_score), 4),
                "last_reason": str(self._last_reason),
                "cumulative_score": round(cumulative, 4),
                "max_possible_cumulative": float(self.MAX_STEPS),
                "normalized_score": round(normalized, 4),
                "history": self._history.copy(),
            }
        except Exception as e:
            # Return safe default result
            return {
                "task_id": "error",
                "done": True,
                "step_num": 0,
                "last_score": 0.0,
                "last_reason": f"Error: {str(e)}",
                "cumulative_score": 0.0,
                "max_possible_cumulative": float(self.MAX_STEPS),
                "normalized_score": 0.0,
                "history": [],
            }
