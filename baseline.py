"""
Baseline inference script.
Usage:
  export OPENAI_API_KEY=sk-...
  python baseline.py --base-url http://localhost:7860
"""

import os
import argparse
import asyncio
from openai import OpenAI
from email_triage_env import EmailTriageEnv, EmailAction

SYSTEM_PROMPT = """You are an email triage assistant. You will receive an email and a task.
Respond ONLY in this exact format (no other text):
ACTION_TYPE: <classify|prioritize|reply>
VALUE: <your answer>
"""

def parse_response(text: str) -> EmailAction:
    action_type, value = "classify", ""
    for line in text.strip().splitlines():
        if line.startswith("ACTION_TYPE:"):
            action_type = line.split(":", 1)[1].strip().lower()
        elif line.startswith("VALUE:"):
            value = line.split(":", 1)[1].strip()
    return EmailAction(action_type=action_type, value=value)


async def run_task(client: OpenAI, env_client, task_id: str) -> float:
    print(f"\n{'='*50}")
    print(f"Task: {task_id.upper()}")

    result = await env_client.reset(task_id=task_id)
    obs = result.observation
    total_reward = 0.0

    for step in range(5):
        email = obs.email
        prompt = (
            f"Task: {obs.instructions}\n\n"
            f"From: {email.get('sender')}\n"
            f"Subject: {email.get('subject')}\n"
            f"Body: {email.get('body')}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        action = parse_response(raw)

        print(f"  Step {step+1}: action_type={action.action_type}, value={action.value[:60]!r}")

        result = await env_client.step(action)
        total_reward += result.reward
        print(f"  → reward={result.reward:.2f}, done={result.done}")

        if result.done:
            break
        obs = result.observation

    print(f"  Total reward: {total_reward:.2f}")
    return total_reward


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:7860")
    args = parser.parse_args()

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    scores = {}
    async with EmailTriageEnv(base_url=args.base_url) as env_client:
        for task_id in ["easy", "medium", "hard"]:
            scores[task_id] = await run_task(openai_client, env_client, task_id)

    print("\n" + "="*50)
    print("BASELINE SCORES")
    print("="*50)
    for task_id, score in scores.items():
        print(f"  {task_id:<10} {score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())