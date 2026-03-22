from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import ChannelAttribution, ComplianceLog, Customer, DeadChannel, Message
from services.bank import resolve_bank_uuid


router = APIRouter()


@router.get("/attribution/{bank_id}")
async def attribution(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    bank_id = await resolve_bank_uuid(bank_id)
    rows = (
        await db.execute(select(ChannelAttribution).where(ChannelAttribution.bank_id == bank_id))
    ).scalars().all()
    return {
        "items": [
            {
                "channel": r.channel,
                "weight_percentage": r.touch_weight,
                "total_interactions": r.total_interactions,
            }
            for r in rows
        ]
    }


@router.get("/frustration-exits/{bank_id}")
async def frustration_exits(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    bank_id = await resolve_bank_uuid(bank_id)
    total_exits = (
        await db.execute(
            select(func.count())
            .select_from(Customer)
            .where(Customer.bank_id == bank_id, Customer.exit_risk == "high")
        )
    ).scalar_one()
    proactive_outreach_count = (
        await db.execute(
            select(func.count())
            .select_from(Customer)
            .where(Customer.bank_id == bank_id, Customer.frustration_score >= 8.0)
        )
    ).scalar_one()

    return {
        "total_exits": total_exits,
        "proactive_outreach_count": proactive_outreach_count,
        "ombudsman_prevented": max(0, proactive_outreach_count - 1),
    }


@router.get("/cost-savings/{bank_id}")
async def cost_savings(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    bank_id = await resolve_bank_uuid(bank_id)
    message_count = (
        await db.execute(
            select(func.count()).select_from(Message).where(Message.bank_id == bank_id)
        )
    ).scalar_one()
    switches_eliminated = int(message_count * 0.35)
    agent_minutes_saved = int(switches_eliminated * 2.4)
    cost_saved_inr = int(agent_minutes_saved * 8.5)

    return {
        "switches_eliminated": switches_eliminated,
        "cost_saved_inr": cost_saved_inr,
        "agent_minutes_saved": agent_minutes_saved,
    }


@router.get("/channel-performance/{bank_id}")
async def channel_performance(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    bank_id = await resolve_bank_uuid(bank_id)
    channels = (
        await db.execute(
            select(Message.channel, func.count(Message.id))
            .where(Message.bank_id == bank_id)
            .group_by(Message.channel)
        )
    ).all()

    dead_q = await db.execute(
        select(DeadChannel, Customer.name)
        .join(Customer, and_(Customer.id == DeadChannel.customer_id, Customer.bank_id == bank_id))
        .where(DeadChannel.bank_id == bank_id)
        .order_by(DeadChannel.buried_at.desc())
    )
    dead_rows = dead_q.all()
    dead_count = (
        await db.execute(
            select(func.count()).select_from(DeadChannel).where(DeadChannel.bank_id == bank_id)
        )
    ).scalar_one()

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    trend = (
        await db.execute(
            select(func.date(Message.created_at), func.avg(Customer.frustration_score))
            .join(Customer, and_(Customer.id == Message.customer_id, Customer.bank_id == bank_id))
            .where(Message.bank_id == bank_id, Message.created_at >= thirty_days_ago)
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at).asc())
        )
    ).all()

    violations = (
        await db.execute(
            select(func.count())
            .select_from(ComplianceLog)
            .where(ComplianceLog.bank_id == bank_id, ComplianceLog.overall_result == "FAIL")
        )
    ).scalar_one()

    return {
        "channels": [{"channel": c, "count": n} for c, n in channels],
        "dead_channel_count": dead_count,
        "dead_channels": [
            {
                "customer": name,
                "channel": dead.channel,
                "buried_at": dead.buried_at,
                "inactive_days": dead.inactive_days,
                "reason": dead.reason,
            }
            for dead, name in dead_rows
        ],
        "frustration_trend": [
            {"date": str(day), "score": round(float(avg_score or 0), 2)} for day, avg_score in trend
        ],
        "compliance_violations_prevented": violations,
    }
