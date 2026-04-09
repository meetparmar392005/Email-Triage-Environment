import os
from typing import Any

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from email_triage_env.models import EmailAction
from .email_environment import EmailEnvironment
from .tasks import TASKS

app = FastAPI(title="Email Triage Environment")

# Create a new environment instance for each request to avoid state conflicts
def get_env():
    if not hasattr(app.state, "env"):
        app.state.env = EmailEnvironment()
    return app.state.env


class ActionRequest(BaseModel):
    action_type: str = ""
    value: str = ""


class BaselineRequest(BaseModel):
    model: str | None = None
    max_steps: int = 5


SYSTEM_PROMPT = """You are an email triage assistant.
Return ONLY:
ACTION_TYPE: <classify|prioritize|reply>
VALUE: <answer>
"""


def _parse_llm_response(text: str) -> EmailAction:
    """Parse LLM response with error handling."""
    try:
        action_type = "classify"
        value = ""
        
        if not text:
            return EmailAction(action_type=action_type, value=value)
        
        for line in str(text).strip().splitlines():
            line = line.strip()
            if line.startswith("ACTION_TYPE:"):
                action_type = line.split(":", 1)[1].strip().lower()
            elif line.startswith("VALUE:"):
                value = line.split(":", 1)[1].strip()
        
        return EmailAction(action_type=action_type, value=value)
    except Exception:
        # Return safe default on parse error
        return EmailAction(action_type="classify", value="")


def _build_user_prompt(observation: dict[str, Any], task_id: str) -> str:
    """Build user prompt with error handling."""
    try:
        email = observation.get("email", {})
        if not isinstance(email, dict):
            email = {}
        
        return (
            f"Task ID: {task_id}\n"
            f"Instructions: {observation.get('instructions', '')}\n\n"
            f"From: {email.get('sender', '')}\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Body: {email.get('body', '')}"
        )
    except Exception:
        return f"Task ID: {task_id}\nError building prompt"


def _run_baseline_episode(client: OpenAI, model_name: str, task_id: str, max_steps: int = 5) -> dict:
    """Run baseline episode with comprehensive error handling."""
    try:
        env = get_env()
        obs = env.reset(task_id=task_id).__dict__
        rewards: list[float] = []
        done = False

        for _ in range(max_steps):
            if done:
                break
            
            try:
                user_prompt = _build_user_prompt(obs, task_id)
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                )
                action = _parse_llm_response((completion.choices[0].message.content or "").strip())
                obs_obj, reward, done = env.step(action)
                obs = obs_obj.__dict__
                
                # Ensure reward is in valid range (0.01, 0.99)
                reward = float(reward)
                reward = min(0.99, max(0.01, reward))
                rewards.append(reward)
            except Exception as step_error:
                # Log error but continue
                rewards.append(0.0)
                break

        final = env.grader_result()
        return {
            "task_id": task_id,
            "done": done,
            "steps": len(rewards),
            "rewards": [round(r, 2) for r in rewards],
            "score": final.get("normalized_score", 0.0),
            "grader": final,
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "done": True,
            "steps": 0,
            "rewards": [],
            "score": 0.0,
            "grader": {"error": str(e)},
        }


@app.post("/reset")
def reset(task_id: str = "easy"):
    """Reset endpoint with error handling."""
    try:
        env = get_env()
        obs = env.reset(task_id=task_id)
        return {"observation": obs.__dict__}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/step")
def step(action: ActionRequest):
    """Step endpoint with error handling."""
    try:
        env = get_env()
        
        # Validate action request
        if not action.action_type:
            raise HTTPException(status_code=400, detail="Missing action_type")
        
        act = EmailAction(action_type=action.action_type, value=action.value)
        obs, reward, done = env.step(act)
        
        # Ensure reward is in valid range (0.01, 0.99) - STRICTLY between 0 and 1
        reward = float(reward)
        reward = min(0.99, max(0.01, reward))
        
        return {
            "observation": obs.__dict__,
            "reward": round(reward, 4),
            "done": bool(done)
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")


@app.get("/state")
def state():
    """State endpoint with error handling."""
    try:
        env = get_env()
        return env.state().__dict__
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State retrieval failed: {str(e)}")


@app.get("/grader")
def grader():
    """Grader endpoint with error handling."""
    try:
        env = get_env()
        return env.grader_result()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grader retrieval failed: {str(e)}")


@app.get("/tasks")
def tasks():
    """Tasks endpoint with error handling."""
    try:
        task_payload = []
        for task_id, task in TASKS.items():
            task_payload.append(
                {
                    "id": str(task_id),
                    "instructions": str(task.instructions),
                    "action_schema": {
                        "action_type": "classify | prioritize | reply",
                        "value": "string",
                    },
                }
            )
        return {"tasks": task_payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tasks retrieval failed: {str(e)}")


@app.post("/baseline")
def baseline(request: BaselineRequest):
    api_key = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing HF_TOKEN/API_KEY/OPENAI_API_KEY")

    api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = request.model or os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    max_steps = max(1, min(request.max_steps, EmailEnvironment.MAX_STEPS))

    try:
        client = OpenAI(base_url=api_base_url, api_key=api_key)
        results = {
            task_id: _run_baseline_episode(client, model_name, task_id, max_steps=max_steps)
            for task_id in ["easy", "medium", "hard"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Baseline execution failed: {exc}") from exc

    return {
        "model_name": model_name,
        "api_base_url": api_base_url,
        "results": results,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    """Main entry point for the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
