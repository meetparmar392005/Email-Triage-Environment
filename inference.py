"""
Round 1 inference script for Email-Triage-Environment.

Required environment variables:
  HF_TOKEN (or API_KEY)

Defaulted environment variables:
  API_BASE_URL (default: https://router.huggingface.co/v1)
  MODEL_NAME (default: Qwen/Qwen2.5-72B-Instruct)

Optional:
  LOCAL_IMAGE_NAME (kept for checklist compatibility when using from_docker_image)
"""

import os
import argparse
from typing import Optional

from openai import OpenAI

from email_triage_env import EmailAction, EmailTriageEnv

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")


LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

TASKS = ["easy", "medium", "hard"]
MAX_STEPS = 5
SUCCESS_SCORE_THRESHOLD = 0.6

SYSTEM_PROMPT = """You are an email triage assistant.
You must output exactly:
ACTION_TYPE: <classify|prioritize|reply>
VALUE: <your answer>
"""


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_value = _normalize_text(error) if error else "null"
    action_value = _normalize_text(action).replace("\n", " ")
    print(
        f"[STEP] step={step} action={action_value} reward={reward:.2f} done={str(done).lower()} error={error_value}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def parse_response(text: str, fallback_task: str) -> EmailAction:
    """Parse LLM response with robust error handling."""
    try:
        action_type = {
            "easy": "classify",
            "medium": "prioritize",
            "hard": "reply",
        }.get(fallback_task, "classify")
        value = ""

        if not text:
            return EmailAction(action_type=action_type, value=value)
        
        for line in str(text).strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("ACTION_TYPE:"):
                parsed_type = line.split(":", 1)[1].strip().lower()
                if parsed_type:  # Only update if non-empty
                    action_type = parsed_type
            elif line.startswith("VALUE:"):
                value = line.split(":", 1)[1].strip()

        return EmailAction(action_type=action_type, value=value)
    except Exception as e:
        # Return safe default on any error
        default_type = {
            "easy": "classify",
            "medium": "prioritize",
            "hard": "reply",
        }.get(fallback_task, "classify")
        return EmailAction(action_type=default_type, value="")


def build_prompt(task_id: str, instructions: str, email: dict) -> str:
    return (
        f"Task ID: {task_id}\n"
        f"Instructions: {instructions}\n\n"
        f"From: {email.get('sender', '')}\n"
        f"Subject: {email.get('subject', '')}\n"
        f"Body: {email.get('body', '')}"
    )


def get_action(client: OpenAI, task_id: str, instructions: str, email: dict) -> EmailAction:
    """Get action from LLM with error handling."""
    try:
        prompt = build_prompt(task_id, instructions, email)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            timeout=30.0,
        )
        raw = (response.choices[0].message.content or "").strip()
        return parse_response(raw, fallback_task=task_id)
    except Exception as e:
        # Return safe default action on error
        default_type = {
            "easy": "classify",
            "medium": "prioritize",
            "hard": "reply",
        }.get(task_id, "classify")
        return EmailAction(action_type=default_type, value="")


def run_task(client: OpenAI, env: EmailTriageEnv, task_id: str) -> dict:
    """Run task with comprehensive error handling."""
    rewards: list[float] = []
    steps = 0
    done = False
    error: Optional[str] = None

    log_start(task=task_id, env="email-triage-env", model=MODEL_NAME)

    try:
        obs = env.reset(task_id=task_id)
        for step in range(1, MAX_STEPS + 1):
            if done:
                break
            
            try:
                action = get_action(client, task_id, obs.instructions, obs.email)
                action_str = f"{action.action_type}:{action.value}"
                result = env.step(action)
                
                # Ensure reward is in valid range (0.01, 0.99) - STRICTLY between 0 and 1
                reward = float(result.reward or 0.01)
                reward = min(0.99, max(0.01, reward))
                
                done = bool(result.done)
                rewards.append(reward)
                steps = step
                log_step(step=step, action=action_str, reward=reward, done=done, error=None)
                obs = result.observation
            except Exception as step_exc:
                error = str(step_exc)
                log_step(
                    step=step,
                    action="error",
                    reward=0.0,
                    done=True,
                    error=error,
                )
                done = True
                break
    except Exception as exc:
        error = str(exc)
        log_step(
            step=max(steps, 1),
            action="error",
            reward=0.0,
            done=True,
            error=error,
        )
        done = True

    # Ensure we have at least one reward
    if not rewards:
        rewards = [0.01]
    
    total = sum(rewards)
    episode_steps = max(1, len(rewards))
    score = total / float(episode_steps)
    # Ensure score is in valid range (0.01, 0.99) - STRICTLY between 0 and 1
    score = min(0.99, max(0.01, score))
    
    success = score >= SUCCESS_SCORE_THRESHOLD and error is None
    log_end(success=success, steps=steps, score=score, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps": steps, "rewards": rewards}


def main() -> None:
    """Main function with error handling."""
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--base-url", default="http://localhost:7860")
        args = parser.parse_args()

        if not HF_TOKEN:
            raise RuntimeError("HF_TOKEN (or API_KEY) is required for inference.")
        
        if not args.base_url:
            raise ValueError("base_url cannot be empty")

        openai_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN, timeout=30.0)

        with EmailTriageEnv(base_url=args.base_url) as env:
            for task_id in TASKS:
                try:
                    run_task(openai_client, env, task_id)
                except Exception as task_error:
                    print(f"[ERROR] Task {task_id} failed: {str(task_error)}", flush=True)
                    # Continue with next task
    except Exception as e:
        print(f"[FATAL] Inference failed: {str(e)}", flush=True)
        raise


if __name__ == "__main__":
    main()
