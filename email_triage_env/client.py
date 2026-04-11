import httpx
from dataclasses import dataclass
from .models import EmailAction, EmailObservation, EmailState


@dataclass
class StepResult:
    observation: EmailObservation
    reward: float
    done: bool


class EmailTriageEnv:
    """Email Triage Environment client with robust error handling."""
    
    def __init__(self, base_url: str = "http://localhost:7860"):
        if not base_url:
            raise ValueError("base_url cannot be empty")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def reset(self, task_id: str = "easy") -> EmailObservation:
        """Reset environment with error handling."""
        try:
            if not task_id:
                raise ValueError("task_id cannot be empty")
            
            r = self._client.post(f"{self.base_url}/reset", params={"task_id": task_id})
            r.raise_for_status()
            data = r.json()
            
            if "observation" not in data:
                raise ValueError("Invalid response: missing observation")
            
            return EmailObservation(**data["observation"])
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Reset failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Reset request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Reset failed: {str(e)}")

    def step(self, action: EmailAction) -> StepResult:
        """Execute step with error handling."""
        try:
            if not isinstance(action, EmailAction):
                raise TypeError(f"Expected EmailAction, got {type(action)}")
            
            if not hasattr(action, 'action_type') or not hasattr(action, 'value'):
                raise ValueError("Invalid action: missing action_type or value")
            
            r = self._client.post(f"{self.base_url}/step", json={
                "action_type": str(action.action_type),
                "value": str(action.value) if action.value is not None else "",
            })
            r.raise_for_status()
            data = r.json()
            
            if "observation" not in data or "reward" not in data or "done" not in data:
                raise ValueError("Invalid response: missing required fields")
            
            # Ensure reward is in valid range (0.01, 0.99) - STRICTLY between 0 and 1
            reward = float(data["reward"])
            reward = min(0.99, max(0.01, reward))
            
            return StepResult(
                observation=EmailObservation(**data["observation"]),
                reward=reward,
                done=bool(data["done"]),
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Step failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Step request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Step failed: {str(e)}")

    def state(self) -> EmailState:
        """Get state with error handling."""
        try:
            r = self._client.get(f"{self.base_url}/state")
            r.raise_for_status()
            data = r.json()
            return EmailState(**data)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"State retrieval failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"State request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"State retrieval failed: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        try:
            self._client.close()
        except Exception:
            pass  # Ignore errors during cleanup