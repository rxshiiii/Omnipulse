# OmniPulse Backend

FastAPI + LangGraph backend for OmniPulse (AI-native omnichannel communication platform).

## Tech

- Python 3.11
- FastAPI (async)
- SQLAlchemy async + PostgreSQL
- Redis (cache)
- RabbitMQ (queue)
- LangGraph + Groq models

## Project Structure

- `main.py`: FastAPI app entrypoint
- `config.py`: environment config
- `database/`: SQLAlchemy models and DB init
- `routers/`: API routes (`webhooks`, `agents`, `compliance`, `analytics`)
- `services/`: queue, cache, identity helpers
- `agents/`: LangGraph nodes and orchestration

## Local Setup

1. Create and activate Python 3.11 venv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure env variables are configured in root `.env`.
4. Start API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Required Environment Variables

- `GROQ_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `META_VERIFY_TOKEN`
- `META_ACCESS_TOKEN`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `SENDGRID_API_KEY`
- `TWITTER_BEARER_TOKEN`
- `BANK_ID`

## Smoke Tests

- Health:

```bash
curl http://localhost:8000/health
```

- Queue:

```bash
curl "http://localhost:8000/api/agents/queue?bank_id=union_bank_demo"
```

## Deploy Backend on Render

Use a **Web Service** with root directory set to `backend`.

### Render Service Settings

- Runtime: Python
- Root Directory: `backend`
- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Render Environment Variables

Set these in Render dashboard:

- `GROQ_API_KEY`
- `DATABASE_URL` (Render Postgres or external Postgres, asyncpg format)
- `REDIS_URL` (Upstash/Redis Cloud/Railway)
- `RABBITMQ_URL` (CloudAMQP)
- `META_VERIFY_TOKEN`
- `META_ACCESS_TOKEN`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `SENDGRID_API_KEY`
- `TWITTER_BEARER_TOKEN`
- `BANK_ID` (e.g. `union_bank_demo`)

Example Postgres URL format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
```

### Post-Deploy Checks

1. Open `https://<render-service>.onrender.com/health`
2. Verify returns:

```json
{"status":"ok","service":"omnipulse-api"}
```

3. Trigger one webhook and verify queue endpoint responds.

## Notes

- Do not use `localhost` in production env vars for DB/Redis/RabbitMQ.
- Queue consumer starts on app startup.
- Compliance logs are append-only by design.
