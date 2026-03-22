from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import aio_pika
from sqlalchemy import select

from agents.graph import run_pipeline
from config import settings
from database.connection import AsyncSessionLocal
from database.models import Customer, Message
from services.cache import get_customer_profile, invalidate_customer, redis_client
from services.identity import resolve_customer


QUEUE_NAME = "channel_messages"
logger = logging.getLogger(__name__)


async def publish_message(event: dict[str, Any]) -> None:
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=QUEUE_NAME,
        )


async def _get_history(customer_id: str, bank_id: str) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.customer_id == customer_id, Message.bank_id == bank_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        rows = list(reversed(result.scalars().all()))
        return [
            {
                "id": str(r.id),
                "direction": r.direction,
                "channel": r.channel,
                "content": r.content,
                "translated_content": r.translated_content,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


async def _save_message_and_updates(event: dict[str, Any], state: dict[str, Any]) -> str:
    async with AsyncSessionLocal() as session:
        msg = Message(
            bank_id=state["bank_id"],
            customer_id=state["customer_id"],
            channel=event["channel"],
            direction="inbound",
            content=event.get("content"),
            original_language=state.get("original_language"),
            translated_content=state.get("translated_text"),
            audio_url=event.get("audio_url"),
            intent_label=state.get("intent_label"),
            intent_confidence=state.get("intent_confidence"),
            ai_draft=state.get("ai_draft"),
            message_type=state.get("message_type", "transactional"),
        )
        session.add(msg)

        customer = await session.get(Customer, state["customer_id"])
        if customer and str(customer.bank_id) == state["bank_id"]:
            customer.frustration_score = float(state.get("frustration_score", customer.frustration_score))
            customer.emotional_state = state.get("emotional_state", customer.emotional_state)
            customer.exit_risk = "high" if customer.frustration_score >= 8 else ("medium" if customer.frustration_score >= 5 else "low")

        await session.commit()
        await session.refresh(msg)
        return str(msg.id)


async def _broadcast(event_name: str, payload: dict[str, Any]) -> None:
    try:
        from routers.agents import broadcast_event

        await broadcast_event({"event": event_name, "data": payload})
    except Exception:
        pass


async def _process_event(event: dict[str, Any]) -> None:
    customer = await resolve_customer(
        event["bank_id"],
        phone=event.get("customer_phone"),
        email=event.get("customer_email"),
        channel=event["channel"],
    )

    profile = await get_customer_profile(customer["id"], event["bank_id"])
    if not profile:
        profile = customer

    history = await _get_history(customer["id"], customer["bank_id"])

    state: dict[str, Any] = {
        "message_id": "",
        "customer_id": customer["id"],
        "bank_id": customer["bank_id"],
        "channel": event["channel"],
        "raw_content": event.get("content"),
        "audio_url": event.get("audio_url"),
        "customer_profile": profile,
        "conversation_history": history,
        "message_type": "transactional",
    }

    result = await run_pipeline(state)
    message_id = await _save_message_and_updates(event, result)
    result["message_id"] = message_id

    queue_key = f"queue:{customer['bank_id']}:urgent"
    await redis_client.zadd(queue_key, {customer["id"]: float(result.get("frustration_score", 0.0))})
    await redis_client.expire(queue_key, 300)

    await _broadcast(
        "new_message",
        {
            "customer_id": customer["id"],
            "channel": event["channel"],
            "content": event.get("content") or result.get("translated_text"),
            "frustration_score": result.get("frustration_score", 0),
        },
    )
    await _broadcast(
        "frustration_update",
        {
            "customer_id": customer["id"],
            "score": result.get("frustration_score", 0),
            "exit_type": result.get("exit_type", "still_active"),
        },
    )
    await _broadcast(
        "queue_update",
        {
            "customer_id": customer["id"],
            "frustration_score": result.get("frustration_score", 0),
            "channel": event["channel"],
        },
    )
    await _broadcast(
        "compliance_alert",
        {
            "customer_id": customer["id"],
            "message": result.get("ai_draft") or result.get("translated_text") or "",
            "result": result.get("compliance_result", "UNKNOWN"),
        },
    )

    await invalidate_customer(customer["id"])


async def start_consumer() -> None:
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)

            async with queue.iterator() as iterator:
                async for message in iterator:
                    async with message.process():
                        payload = json.loads(message.body.decode("utf-8"))
                        try:
                            await _process_event(payload)
                        except Exception as exc:
                            logger.exception("Queue event processing failed: %s", exc)
        except Exception as exc:
            logger.exception("Queue consumer reconnecting after error: %s", exc)
            await asyncio.sleep(3)
