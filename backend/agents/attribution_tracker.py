from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, func, select

from database.connection import AsyncSessionLocal
from database.models import ChannelAttribution, DeadChannel, Message

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


async def get_recent_interactions(customer_id: str, bank_id: str, days: int = 30) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(
                Message.customer_id == customer_id,
                Message.bank_id == bank_id,
                Message.created_at >= since,
            )
            .order_by(Message.created_at.desc())
            .limit(30)
        )
        rows = result.scalars().all()
        return [{"channel": m.channel, "created_at": m.created_at} for m in rows]


async def upsert_attribution(
    customer_id: str,
    bank_id: str,
    current_channel: str,
    channel_weights: dict[str, float],
) -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        for channel, weight in channel_weights.items():
            existing = await session.execute(
                select(ChannelAttribution).where(
                    ChannelAttribution.customer_id == customer_id,
                    ChannelAttribution.bank_id == bank_id,
                    ChannelAttribution.channel == channel,
                )
            )
            record = existing.scalar_one_or_none()
            if record:
                record.touch_weight = weight
                record.total_interactions = (record.total_interactions or 0) + (1 if channel == current_channel else 0)
                record.last_interaction = now if channel == current_channel else record.last_interaction
            else:
                session.add(
                    ChannelAttribution(
                        customer_id=customer_id,
                        bank_id=bank_id,
                        channel=channel,
                        touch_weight=weight,
                        total_interactions=1 if channel == current_channel else 0,
                        last_interaction=now if channel == current_channel else None,
                    )
                )
        await session.commit()


async def check_dead_channels(customer_id: str, bank_id: str) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with AsyncSessionLocal() as session:
        last_seen = await session.execute(
            select(Message.channel, func.max(Message.created_at))
            .where(Message.customer_id == customer_id, Message.bank_id == bank_id)
            .group_by(Message.channel)
        )
        for channel, ts in last_seen.all():
            if ts and ts < cutoff:
                inactive_days = (datetime.now(timezone.utc) - ts).days
                exists = await session.execute(
                    select(DeadChannel).where(
                        and_(
                            DeadChannel.customer_id == customer_id,
                            DeadChannel.bank_id == bank_id,
                            DeadChannel.channel == channel,
                        )
                    )
                )
                if not exists.scalar_one_or_none():
                    session.add(
                        DeadChannel(
                            customer_id=customer_id,
                            bank_id=bank_id,
                            channel=channel,
                            reason="Inactive for over 90 days",
                            inactive_days=inactive_days,
                        )
                    )
        await session.commit()


async def attribution_node(state: AgentState) -> AgentState:
    customer_id = state["customer_id"]
    channel = state["channel"]
    bank_id = state["bank_id"]

    recent = await get_recent_interactions(customer_id, bank_id, days=30)
    channel_weights: dict[str, float] = {}
    for i, interaction in enumerate(sorted(recent, key=lambda x: x["created_at"], reverse=True)[:10]):
        decay = max(0.05, 0.4 * (0.75**i))
        ch = interaction["channel"]
        channel_weights[ch] = channel_weights.get(ch, 0) + decay

    if not channel_weights:
        channel_weights[channel] = 100.0

    total = sum(channel_weights.values()) or 1
    for ch in channel_weights:
        channel_weights[ch] = round(channel_weights[ch] / total * 100, 1)

    await upsert_attribution(customer_id, bank_id, channel, channel_weights)
    await check_dead_channels(customer_id, bank_id)
    return state
