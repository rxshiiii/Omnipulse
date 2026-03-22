from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    pan_hash: Mapped[str | None] = mapped_column(String(64))
    aadhaar_hash: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(100))
    preferred_channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    frustration_score: Mapped[float] = mapped_column(Float, default=0.0)
    emotional_state: Mapped[str] = mapped_column(String(30), default="neutral")
    exit_risk: Mapped[str] = mapped_column(String(10), default="low")
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    original_language: Mapped[str | None] = mapped_column(String(10))
    translated_content: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(Text)
    intent_label: Mapped[str | None] = mapped_column(String(50))
    intent_confidence: Mapped[float | None] = mapped_column(Float)
    ai_draft: Mapped[str | None] = mapped_column(Text)
    sent_content: Mapped[str | None] = mapped_column(Text)
    agent_id: Mapped[str | None] = mapped_column(String(50))
    message_type: Mapped[str] = mapped_column(String(20), default="transactional")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComplianceLog(Base):
    __tablename__ = "compliance_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))
    audit_token: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    dnc_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    dnc_result: Mapped[str | None] = mapped_column(String(20))
    consent_valid: Mapped[bool | None] = mapped_column(Boolean)
    rbi_content_passed: Mapped[bool | None] = mapped_column(Boolean)
    tone_fit_passed: Mapped[bool | None] = mapped_column(Boolean)
    safety_check_passed: Mapped[bool | None] = mapped_column(Boolean)
    overall_result: Mapped[str | None] = mapped_column(String(10))
    fail_reason: Mapped[str | None] = mapped_column(Text)
    agent_version: Mapped[str | None] = mapped_column(String(20), default="v1.0")
    hash_chain: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoanJourney(Base):
    __tablename__ = "loan_journeys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    department: Mapped[str | None] = mapped_column(String(50))
    stage: Mapped[str | None] = mapped_column(String(50))
    agent_id: Mapped[str | None] = mapped_column(String(50))
    action_taken: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChannelAttribution(Base):
    __tablename__ = "channel_attribution"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(20))
    touch_weight: Mapped[float | None] = mapped_column(Float)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeadChannel(Base):
    __tablename__ = "dead_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(20))
    buried_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)
    inactive_days: Mapped[int | None] = mapped_column(Integer)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("banks.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="agent")
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
