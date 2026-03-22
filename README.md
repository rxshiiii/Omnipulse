# OmniPulse

OmniPulse is an AI-native omnichannel customer communication platform prototype for Indian Public Sector Banks.
This hackathon demo includes async FastAPI backend services, LangGraph-based AI pipeline orchestration, PostgreSQL + Redis + RabbitMQ integration, and a React + Tailwind agent console.

## Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy async, LangGraph, Groq APIs
- Data: PostgreSQL (RLS), Redis cache, RabbitMQ queue
- Frontend: React 18, Tailwind CSS 3, React Query, Zustand, Recharts
- Channels: WhatsApp (Meta), SMS/Voice (Twilio), Email (SendGrid), Twitter

## Project Structure

- backend: API server, queue worker, LangGraph nodes, DB models
- frontend: React starter-pack based UI
- seeds: demo data loader
- docker-compose.yml: local infra orchestration

## Setup

1. Clone/open repository at omnipulse.
2. Copy environment file:
   - cp .env.example .env
3. Backend setup:
   - cd backend
   - python3 -m venv .venv
   - source .venv/bin/activate
   - pip install -r requirements.txt
4. Frontend setup:
   - cd ../frontend
   - npm install
5. Start infra and apps:
   - cd ..
   - docker compose up --build
6. Seed demo data:
   - python seeds/demo_data.py

## Environment Variables

| Variable | Purpose |
|---|---|
| GROQ_API_KEY | Groq API key for Llama/Whisper/Kimi/Safety |
| DATABASE_URL | PostgreSQL async URL |
| REDIS_URL | Redis connection URL |
| RABBITMQ_URL | CloudAMQP/local RabbitMQ URL |
| META_VERIFY_TOKEN | WhatsApp webhook verify token |
| META_ACCESS_TOKEN | WhatsApp access token |
| TWILIO_ACCOUNT_SID | Twilio account id |
| TWILIO_AUTH_TOKEN | Twilio auth token |
| SENDGRID_API_KEY | SendGrid API key |
| TWITTER_BEARER_TOKEN | Twitter API bearer token |
| BANK_ID | Tenant identifier alias (union_bank_demo) |
| REACT_APP_API_URL | Frontend API base URL |
| REACT_APP_WS_URL | Frontend WebSocket URL |

## Demo Walkthrough

1. Trigger inbound WhatsApp webhook with a Marathi voice payload at /webhooks/whatsapp.
2. Webhook publishes unified MessageEvent to RabbitMQ queue channel_messages and responds quickly.
3. Consumer resolves identity, loads profile/history from Redis/Postgres, and runs LangGraph pipeline:
   - Whisper transcription
   - translation to English
   - intent + emotional state
   - draft generation (Llama 3.3 70B)
   - safety + compliance checks
   - attribution tracking + orchestration decision
4. Agent dashboard auto-updates over WebSocket with queue and thread updates.
5. Agent sends one-click reply through /api/agents/message/send.
6. Compliance Passport captures audit token and hash-chain verification.

## API Endpoints

### Health

- GET /health

### Webhooks

- GET /webhooks/whatsapp (verify)
- POST /webhooks/whatsapp
- POST /webhooks/sms
- POST /webhooks/email
- POST /webhooks/voice
- POST /webhooks/twitter

### Agent APIs

- GET /api/agents/queue?bank_id=
- GET /api/agents/customer/{customer_id}?bank_id=
- GET /api/agents/customer/{customer_id}/thread?bank_id=
- POST /api/agents/message/send
- POST /api/agents/message/{message_id}/override
- WS /api/agents/ws/{agent_id}

### Compliance APIs

- GET /api/compliance/passport/{bank_id}?from_date=&to_date=&customer_id=&format=json|csv
- GET /api/compliance/verify/{audit_token}
- GET /api/compliance/stats/{bank_id}

### Analytics APIs

- GET /api/analytics/attribution/{bank_id}
- GET /api/analytics/frustration-exits/{bank_id}
- GET /api/analytics/cost-savings/{bank_id}
- GET /api/analytics/channel-performance/{bank_id}

## Notes

- compliance_log is append-only via trigger protection.
- All API queries include bank_id filters for tenant isolation and RLS compatibility.
- Redis profile TTL: 30 minutes, queue TTL: 5 minutes.
