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
- [Step-by-Step Testing](#step-by-step-testing)
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

## Step-by-Step Testing

### 1) Health check
```bash
curl http://127.0.0.1:7860/health
```

### 2) Reset episode
```bash
curl -X POST "http://127.0.0.1:7860/reset?task_id=easy"
```

### 3) Take action
```bash
curl -X POST "http://127.0.0.1:7860/step" \
  -H "Content-Type: application/json" \
  -d "{\"action_type\":\"classify\",\"value\":\"spam\"}"
```

### 4) Inspect state and grader
```bash
curl http://127.0.0.1:7860/state
curl http://127.0.0.1:7860/grader
curl http://127.0.0.1:7860/tasks
```

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

## Deployment Notes

For Round 1 style submission:
- keep `inference.py` at repo root
- keep valid `openenv.yaml`
- ensure Dockerfile builds cleanly
- expose and verify required endpoints

Recommended pre-submit checks:
- `python -m compileall email_triage_env inference.py`
- endpoint smoke tests (`/health`, `/reset`, `/step`, `/tasks`, `/grader`)
- Docker build/run locally

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
