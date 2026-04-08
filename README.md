---
title: Email Triage Environment
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Email Triage Environment

A real-world AI evaluation environment for inbox handling workflows: spam detection, urgency prioritization, and reply drafting.

## Index
- [What This Repository Is](#what-this-repository-is)
- [Why This Matters](#why-this-matters)
- [What It Does](#what-it-does)
- [How Scoring Works](#how-scoring-works)
- [Environment API](#environment-api)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Step-by-Step Local Run](#step-by-step-local-run)
- [Step-by-Step Testing via Swagger UI](#step-by-step-testing-via-swagger-ui)
- [Run Inference Baseline](#run-inference-baseline)
- [Docker Usage](#docker-usage)
- [Deployment Notes](#deployment-notes)
- [What Can Be Added Next](#what-can-be-added-next)
- [Practical Use Cases](#practical-use-cases)
- [Troubleshooting](#troubleshooting)

## What This Repository Is

This repo implements an **email triage simulation environment** where AI agents can be evaluated and improved on realistic tasks using `reset()` / `step()` / `state()` flow.

Instead of a toy game, the environment models an operational workflow teams actually perform daily:
- detect spam
- identify urgent emails
- draft useful replies

## Why This Matters

Email overload is a practical business problem. A good AI assistant should:
- classify reliably
- prioritize based on impact
- reply with context and professional tone

This repository gives you a measurable, repeatable benchmark to test those capabilities.

## What It Does

The environment includes 3 tasks with increasing difficulty:
- `easy`: classify `spam` vs `not_spam`
- `medium`: assign urgency `critical|high|medium|low`
- `hard`: draft a contextual professional reply

Data and task graders are defined in `email_triage_env/server/tasks.py`.

## How Scoring Works

Each `step` returns reward between `0.0` and `1.0`. Final inference score is computed from step rewards in `inference.py`.

Grader behavior:
- Easy:
  - `1.0` for correct class
  - `0.2` for wrong class
  - `0.0` for wrong action type
- Medium:
  - `1.0` exact match
  - partial credit for close priority levels
  - `0.1` for invalid label
- Hard:
  - compositional score from relevance, structure, tone, and substance

Episode ends when:
- perfect score on step (`1.0`), or
- `MAX_STEPS` reached.

## Environment API

Core endpoints:
- `POST /reset?task_id=<easy|medium|hard>`
- `POST /step`
- `GET /state`

Round 1 helper endpoints:
- `GET /tasks`
- `GET /grader`
- `POST /baseline`

Health:
- `GET /health`

Interactive docs:
- `/docs` (Swagger UI)

## Repository Structure

```text
.
├── email_triage_env/
│   ├── models.py                  # Action/Observation/State models
│   ├── client.py                  # HTTP client wrapper
│   └── server/
│       ├── app.py                 # FastAPI endpoints
│       ├── email_environment.py   # Core env logic: reset/step/state
│       ├── tasks.py               # Email pools + graders
│       └── Dockerfile             # Server Docker build
├── inference.py                   # Required Round 1 baseline runner
├── baseline.py                    # Compatibility shim to inference.py
├── openenv.yaml                   # Environment metadata + tasks
├── pyproject.toml                 # Project dependencies
└── Dockerfile                     # Root Dockerfile for deployment/validation
```

## Quick Start

```bash
pip install -e .
uvicorn email_triage_env.server.app:app --host 0.0.0.0 --port 7860
python inference.py --base-url http://localhost:7860
```

## Step-by-Step Local Run

### 1) Clone and enter repo
```bash
git clone <your-repo-url>
cd Email-Triage-Environment
```

### 2) Create virtual environment

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Mac/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies
```bash
python -m pip install --upgrade pip
pip install -e .
```

### 4) Start API server
```bash
uvicorn email_triage_env.server.app:app --host 0.0.0.0 --port 7860
```

### 5) Open API docs
Visit: `http://127.0.0.1:7860/docs`

## Step-by-Step Testing via Swagger UI

After starting the uvicorn server, visit `http://127.0.0.1:7860/docs` to access the interactive Swagger UI. Follow these steps to validate the project:

### Phase 1: Explore Available Tasks

**Step 1: Get List of Available Tasks**
1. Click on **`GET /tasks`** endpoint in Swagger UI
2. Click **"Try it out"** button
3. Click **"Execute"**
4. Review the response showing all 3 task definitions:
   - `easy`: Classify emails as `spam` or `not_spam`
   - `medium`: Assign urgency level (`critical`, `high`, `medium`, `low`)
   - `hard`: Draft a professional reply to the email

**Expected Response:**
```json
{
  "tasks": [
    {
      "id": "easy",
      "instructions": "Classify the email...",
      "action_schema": {
        "action_type": "classify | prioritize | reply",
        "value": "string"
      }
    },
    ...
  ]
}
```

### Phase 2: Test Easy Task (Classification)

**Step 2: Reset with Easy Task**
1. Click on **`POST /reset`** endpoint
2. Click **"Try it out"**
3. In the `task_id` parameter field, enter: `easy`
4. Click **"Execute"**
5. Note the observation object containing:
   - `task_id`: "easy"
   - `email`: Object with `sender`, `subject`, `body`
   - `instructions`: Task instructions
   - `step_num`: Current step (should be 0)

**Step 3: Submit Classification Action**
1. Click on **`POST /step`** endpoint
2. Click **"Try it out"**
3. In the request body, enter:
```json
{
  "action_type": "classify",
  "value": "spam"
}
```
4. Click **"Execute"**
5. Verify response contains:
   - `observation`: Updated observation object
   - `reward`: Should be 1.0 if correct, 0.2 if incorrect, or 0.0 for wrong action type
   - `done`: Boolean indicating if episode is complete

**Step 4: Check Final State and Grader Result**
1. Click on **`GET /state`** endpoint
2. Click **"Try it out"** → **"Execute"**
3. Verify state shows:
   - `task_id`: "easy"
   - `step_num`: Current step count
   - `done`: Whether task is complete
   - `cumulative_score`: Total reward accumulated

4. Click on **`GET /grader`** endpoint
5. Click **"Try it out"** → **"Execute"**
6. Review grader result containing:
   - Correctness metrics
   - Feedback on classification
   - `normalized_score`: Final normalized score

### Phase 3: Test Medium Task (Prioritization)

**Step 5: Reset with Medium Task**
1. Click on **`POST /reset`**
2. Enter `task_id`: `medium`
3. Execute and review the new email
4. Note the instructions asking to assign urgency level

**Step 6: Submit Prioritization Action**
1. Click on **`POST /step`**
2. Enter request body:
```json
{
  "action_type": "prioritize",
  "value": "critical"
}
```
3. Execute and verify reward (1.0 for exact match, partial credit for close levels)
4. Copy the observation for reference

**Step 7: Verify Grader Feedback**
1. Click **`GET /grader`**
2. Review the grader result for:
   - Priority level correctness
   - Partial credit scoring logic
   - Detailed feedback

### Phase 4: Test Hard Task (Reply Generation)

**Step 8: Reset with Hard Task**
1. Click on **`POST /reset`**
2. Enter `task_id`: `hard`
3. Execute and note this task requires composing a reply

**Step 9: Submit Reply Action**
1. Click on **`POST /step`**
2. Enter request body:
```json
{
  "action_type": "reply",
  "value": "Thank you for your message. I have received your inquiry about [topic] and will provide a detailed response by end of business day."
}
```
3. Execute and verify reward (composite score from relevance, structure, tone, substance)

**Step 10: Check Advanced Grader Metrics**
1. Click **`GET /grader`**
2. Review compositional scoring for:
   - Relevance: Does reply address the email?
   - Structure: Is it well-organized?
   - Tone: Is it professional?
   - Substance: Does it provide actionable value?

### Phase 5: System Health & Configuration

**Step 11: Health Check**
1. Click on **`GET /health`** endpoint
2. Click **"Try it out"** → **"Execute"**
3. Verify the server responds with status 200 (healthy)

**Step 12: Reset for Next Episode**
1. Click on **`POST /reset`**
2. Choose a `task_id` parameter
3. Click **"Execute"** to start a fresh episode
4. This clears the previous state and provides a new email

### Phase 6: Complete Multi-Step Episode Testing

**Step 13: Complete Easy Task Episode**
1. Reset with `task_id=easy`
2. Submit 1 step with correct classification
3. Verify `done=true` in response (episode is complete on perfect score)
4. Check `/grader` for final normalized_score

**Step 14: Complete Medium Task Episode (Up to 5 Steps)**
1. Reset with `task_id=medium`
2. Submit step 1: First action
3. If `done=false`, submit step 2: Refine action
4. Continue until either:
   - `done=true` (achieved perfect score)
   - Reach `MAX_STEPS` limit
5. Verify final cumulative rewards and grader feedback

**Step 15: Complete Hard Task Episode**
1. Reset with `task_id=hard`
2. Submit a thoughtful reply with context
3. Check reward score for compositional feedback
4. If `done=false`, refine the reply based on grader feedback
5. Continue until task completes or MAX_STEPS reached

### Phase 7: Error Handling & Edge Cases

**Step 16: Test Invalid Action Type**
1. Reset with `task_id=easy`
2. Submit step with invalid action_type (e.g., "invalid_action")
3. Verify proper error handling in response (should get 0.0 reward)

**Step 17: Test Invalid Values**
1. Reset with `task_id=medium`
2. Submit prioritize action with invalid priority (e.g., "urgent" instead of valid options)
3. Verify grader marks as invalid (0.1 reward)

**Step 18: Test Multiple Resets**
1. Reset with `task_id=easy`
2. Note the email content
3. Reset again with `task_id=easy`
4. Verify different email is presented (demonstrates data randomization)

### Summary Validation Checklist

- ✅ /tasks endpoint returns all task definitions correctly
- ✅ /reset endpoint initializes episodes with valid emails
- ✅ /step endpoint processes actions and returns rewards
- ✅ /state endpoint reflects current episode state
- ✅ /grader endpoint provides accurate scoring feedback
- ✅ Scores range from 0.0 to 1.0
- ✅ `done` flag properly signals episode completion
- ✅ Multiple episodes can be run sequentially
- ✅ Error handling returns appropriate responses
- ✅ All endpoints are documented and functional

## Run Inference Baseline

Set variables first:
- `HF_TOKEN` (required, do not hardcode into files)
- `API_BASE_URL` (optional, has default)
- `MODEL_NAME` (optional, has default)

Example:
```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py --base-url http://localhost:7860
```

Expected logs:
- `[START] ...`
- `[STEP] ...`
- `[END] ...`

## Docker Usage

### Build
```bash
docker build -t email-triage-env:latest .
```

### Run
```bash
docker run --rm -p 7860:7860 email-triage-env:latest
```

Then test:
```bash
curl http://127.0.0.1:7860/health
```

## What Can Be Added Next

To evolve this into a deploy-ready AI email employee:
- Inbox connectors: Gmail/Outlook API ingestion
- Confidence + human-in-loop review queue
- CRM/ticket context retrieval before drafting replies
- Policy filters (PII, compliance, prompt injection defense)
- Multi-model routing (cheap classifier + stronger reply model)
- Monitoring: false-positive spam, urgent miss rate, override rate, latency, cost
- Persistent datastore for audit trails and feedback loops

## Practical Use Cases

- Evaluate different LLMs on realistic email workflows
- Track model quality regressions after prompt changes
- Prototype agent pipelines before production rollout
- Build RL/agentic training loops with partial-credit rewards

## Troubleshooting

- `openenv validate` not found:
  - install the required OpenEnv CLI/core in your environment.
- Docker build fails:
  - ensure Docker Desktop/daemon is running.
- `/baseline` returns missing token error:
  - set `HF_TOKEN` (or `API_KEY`) in shell environment.
- Unexpected poor score:
  - inspect `/grader` output and `history` reasons for step-level feedback.
