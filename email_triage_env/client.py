import httpx
from dataclasses import dataclass
from .models import EmailAction, EmailObservation, EmailState


@dataclass
class StepResult:
    observation: EmailObservation
    reward: float
    done: bool


class EmailTriageEnv:
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client()

    def reset(self, task_id: str = "easy") -> EmailObservation:
        r = self._client.post(f"{self.base_url}/reset", params={"task_id": task_id})
        r.raise_for_status()
        return EmailObservation(**r.json()["observation"])

    def step(self, action: EmailAction) -> StepResult:
        r = self._client.post(f"{self.base_url}/step", json={
            "action_type": action.action_type,
            "value": action.value,
        })
        r.raise_for_status()
        data = r.json()
        return StepResult(
            observation=EmailObservation(**data["observation"]),
            reward=data["reward"],
            done=data["done"],
        )

    def state(self) -> EmailState:
        r = self._client.get(f"{self.base_url}/state")
        r.raise_for_status()
        return EmailState(**r.json())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()