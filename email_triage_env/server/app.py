from fastapi import FastAPI
from pydantic import BaseModel
from .email_environment import EmailEnvironment

app = FastAPI(title="Email Triage Environment")
env = EmailEnvironment()


class ActionRequest(BaseModel):
    action_type: str = ""
    value: str = ""


@app.post("/reset")
def reset(task_id: str = "easy"):
    obs = env.reset(task_id=task_id)
    return {"observation": obs.__dict__}


@app.post("/step")
def step(action: ActionRequest):
    from email_triage_env.models import EmailAction
    act = EmailAction(action_type=action.action_type, value=action.value)
    obs, reward, done = env.step(act)
    return {"observation": obs.__dict__, "reward": reward, "done": done}


@app.get("/state")
def state():
    return env.state().__dict__


@app.get("/health")
def health():
    return {"status": "ok"}