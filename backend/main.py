import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import init_db
from routers import agents, analytics, compliance, webhooks
from services.queue import start_consumer


app = FastAPI(title="OmniPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "omnipulse-api"}


@app.on_event("startup")
async def startup() -> None:
    await init_db()
    asyncio.create_task(start_consumer())
