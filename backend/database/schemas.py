from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MessageEvent(BaseModel):
    customer_phone: str | None = None
    customer_email: str | None = None
    customer_ref: str | None = None
    customer_name: str | None = None
    channel: str
    content: str | None = None
    audio_url: str | None = None
    timestamp: str
    raw_payload: dict[str, Any]
    bank_id: str


class SendMessageRequest(BaseModel):
    customer_id: str
    content: str
    channel: str
    agent_id: str
    bank_id: str


class OverrideRequest(BaseModel):
    agent_id: str
    override_reason: str


class QueueItem(BaseModel):
    id: str
    name: str | None
    issue_summary: str
    channel: str
    frustration_score: float
    exit_risk: str
    wait_minutes: int


class ThreadItem(BaseModel):
    id: str
    channel: str
    direction: str
    content: str | None
    translated_content: str | None
    original_language: str | None
    ai_draft: str | None
    agent_id: str | None
    created_at: datetime
    compliance_audit_token: str | None
