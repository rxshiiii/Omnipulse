from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select

from config import settings
from database.connection import AsyncSessionLocal
from database.models import Customer
from services.bank import resolve_bank_uuid


redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_customer_profile(customer_id: str, bank_id: str) -> dict[str, Any] | None:
    bank_uuid = await resolve_bank_uuid(bank_id)
    key = f"customer:{customer_id}:profile"
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id, Customer.bank_id == bank_uuid)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return None

        payload = {
            "id": str(customer.id),
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "preferred_channel": customer.preferred_channel,
            "frustration_score": customer.frustration_score,
            "emotional_state": customer.emotional_state,
            "exit_risk": customer.exit_risk,
            "attributes": customer.attributes or {},
        }
        await redis_client.set(key, json.dumps(payload), ex=1800)
        return payload


async def invalidate_customer(customer_id: str) -> None:
    keys = await redis_client.keys(f"customer:{customer_id}:*")
    if keys:
        await redis_client.delete(*keys)


async def get_agent_queue(bank_id: str) -> list[dict[str, Any]]:
    key = f"queue:{bank_id}:urgent"
    items = await redis_client.zrevrange(key, 0, -1, withscores=True)
    return [{"customer_id": item[0], "score": float(item[1])} for item in items]
