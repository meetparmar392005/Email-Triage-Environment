# Email-Triage-Environment

Email triage is a real-world, high-impact workflow. Knowledge workers spend a large fraction of their week managing inboxes, and poor triage causes missed deadlines, delayed responses, and avoidable operational risk.

This environment trains/evaluates agents on a realistic triage pipeline:
- Easy: classify spam vs non-spam.
- Medium: prioritize urgency by business impact.
- Hard: draft a professional, relevant email reply.

This is intentionally not a toy benchmark. It models practical communication tasks that teams run every day.

## Problem Motivation

Inbox overload is a measurable productivity drain (often cited at roughly 28% of workweek spent on email handling). Good triage requires:
- Fast pattern recognition (spam signals).
- Context-aware risk assessment (urgency and business priority).
- High-quality natural language generation (professional replies).

These tasks create a natural easy -> medium -> hard curriculum for agent development.

## Task Design

The environment exposes 3 tasks with deterministic graders:
- `easy`: classify each email as `spam` or `not_spam`.
- `medium`: assign one of `critical`, `high`, `medium`, `low`.
- `hard`: produce a professional reply to the sender.

Task data and graders are implemented in `email_triage_env/server/tasks.py`.

## Observation Space

Exact fields from `email_triage_env/models.py`:

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Current task identifier (`easy`, `medium`, `hard`) |
| `email` | `dict` | Current email payload (`sender`, `subject`, `body`, etc.) |
| `history` | `list` | Per-step grading trace and prior actions |
| `step_num` | `int` | Current step index in episode |
| `instructions` | `str` | Task-specific instruction shown to the agent |

## Action Space

Exact fields from `email_triage_env/models.py`:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | Expected value depends on task: `classify`, `prioritize`, `reply` |
| `value` | `str` | Agent answer, priority label, or reply text |

## State Space

Exact fields from `email_triage_env/models.py`:

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Active task id |
| `step_num` | `int` | Number of executed steps |
| `done` | `bool` | Episode termination flag |
| `cumulative_score` | `float` | Sum of step rewards accumulated so far |

## Reward Design

Reward is dense and task-aware (0.0 to 1.0 per step), not binary-only terminal reward.

- Easy (`grade_classify`):
  - `1.0` if spam/legit classification is correct.
  - `0.2` on wrong class (still gives corrective signal).
  - `0.0` for wrong action type.
- Medium (`grade_prioritize`):
  - `1.0` exact priority match.
  - Partial credit based on label distance (`critical` <-> `low` gets less than `high` <-> `critical`).
  - `0.1` for invalid priority label.
- Hard (`grade_reply`):
  - Compositional scoring based on usefulness signals:
    - minimum length,
    - acknowledgment/greeting tone,
    - topic overlap with sender request,
    - substantive (non-vague) content.

Episode ends when either:
- perfect step score (`1.0`) is reached, or
- `MAX_STEPS` (`5`) is reached.

### Partial Progress Example

For a medium-priority email where expected label is `critical`:
- Step 1 agent outputs `medium` -> reward around `0.2`
- Step 2 agent outputs `high` -> reward around `0.6`
- Step 3 agent outputs `critical` -> reward `1.0`, episode terminates

The agent receives directional feedback each step, enabling learning from trajectory quality.

## API Endpoints

Core endpoints:
- `POST /reset?task_id=<easy|medium|hard>`
- `POST /step`
- `GET /state`

Round 1 required helper endpoints:
- `GET /tasks`: task list plus action schema
- `GET /grader`: latest grader output (includes normalized score in `[0,1]`)
- `POST /baseline`: runs baseline inference for all 3 tasks using OpenAI-compatible API

Health:
- `GET /health`

## Local Setup

### 1) Install

```bash
pip install -e .
```

### 2) Run server

```bash
uvicorn email_triage_env.server.app:app --host 0.0.0.0 --port 7860
```

### 3) Run required inference script

Set env vars first:
- `HF_TOKEN` (or `API_KEY`) required
- `API_BASE_URL` optional (default provided)
- `MODEL_NAME` optional (default provided)
- `LOCAL_IMAGE_NAME` optional placeholder for checklist compatibility

```bash
python inference.py --base-url http://localhost:7860
```

### 4) Docker

```bash
docker build -t email-triage-env:latest .
docker run --rm -p 7860:7860 email-triage-env:latest
```

## Baseline Scores (Reference)

Illustrative baseline run with `gpt-4o-mini`:

| Task | Expected baseline behavior | Typical normalized score |
|---|---|---|
| Easy (spam) | Usually near-perfect on known spam patterns | `0.90-1.00` |
| Medium (priority) | Good but sometimes underestimates urgency | `0.60-0.80` |
| Hard (reply) | Often generic; misses detailed constraints | `0.35-0.60` |

This pattern is intentional: spam classification is easiest, reply drafting is hardest.

## Repository Structure

```text
.
├── email_triage_env/
│   ├── models.py
│   ├── client.py
│   └── server/
│       ├── app.py
│       ├── email_environment.py
│       ├── tasks.py
│       └── Dockerfile
├── inference.py
├── baseline.py
├── openenv.yaml
├── pyproject.toml
└── Dockerfile
```
