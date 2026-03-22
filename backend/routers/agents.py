from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.compliance_guardian import evaluate_compliance, write_compliance_log_to_db
from config import settings
from database.connection import get_db
from database.models import ComplianceLog, Customer, DeadChannel, LoanJourney, Message
from database.schemas import OverrideRequest, SendMessageRequest
from services.bank import resolve_bank_uuid
from services.cache import invalidate_customer, redis_client


router = APIRouter()
_connections: dict[str, WebSocket] = {}


async def broadcast_event(payload: dict[str, Any]) -> None:
    stale: list[str] = []
    for agent_id, ws in _connections.items():
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(agent_id)
    for agent_id in stale:
        _connections.pop(agent_id, None)


@router.get("/queue")
async def get_queue(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    bank_id = await resolve_bank_uuid(bank_id)
    result = await db.execute(
        select(Customer)
        .where(Customer.bank_id == bank_id)
        .order_by(desc(Customer.frustration_score), asc(Customer.updated_at))
    )
    customers = result.scalars().all()

    data = []
    for c in customers:
        latest = await db.execute(
            select(Message)
            .where(Message.customer_id == c.id, Message.bank_id == bank_id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        msg = latest.scalar_one_or_none()
        wait_minutes = (
            int((datetime.now(timezone.utc) - msg.created_at).total_seconds() / 60)
            if msg and msg.created_at
            else 0
        )
        data.append(
            {
                "id": str(c.id),
                "name": c.name,
                "issue_summary": (msg.content[:80] if msg and msg.content else "No recent issue"),
                "channel": msg.channel if msg else c.preferred_channel,
                "frustration_score": c.frustration_score,
                "exit_risk": c.exit_risk,
                "wait_minutes": wait_minutes,
            }
        )

    if data:
        await redis_client.zadd(
            f"queue:{bank_id}:urgent", {item["id"]: item["frustration_score"] for item in data}
        )
        await redis_client.expire(f"queue:{bank_id}:urgent", 300)
    return {"items": data, "count": len(data)}


@router.get("/customer/{customer_id}")
async def get_customer(customer_id: str, bank_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    bank_id = await resolve_bank_uuid(bank_id)
    customer_result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.bank_id == bank_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")

    journey = await db.execute(
        select(LoanJourney)
        .where(LoanJourney.customer_id == customer_id, LoanJourney.bank_id == bank_id)
        .order_by(LoanJourney.created_at.asc())
    )
    compliance = await db.execute(
        select(ComplianceLog)
        .where(ComplianceLog.customer_id == customer_id, ComplianceLog.bank_id == bank_id)
        .order_by(ComplianceLog.created_at.desc())
        .limit(5)
    )
    active_channels_q = await db.execute(
        select(Message.channel)
        .where(Message.customer_id == customer_id, Message.bank_id == bank_id)
        .distinct()
    )
    dead_channels_q = await db.execute(
        select(DeadChannel)
        .where(DeadChannel.customer_id == customer_id, DeadChannel.bank_id == bank_id)
        .order_by(DeadChannel.buried_at.desc())
    )

    return {
        "profile": {
            "id": str(customer.id),
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "preferred_channel": customer.preferred_channel,
            "frustration_score": customer.frustration_score,
            "emotional_state": customer.emotional_state,
            "exit_risk": customer.exit_risk,
            "attributes": customer.attributes or {},
        },
        "active_channels": [row[0] for row in active_channels_q.all()],
        "dead_channels": [
            {
                "channel": d.channel,
                "reason": d.reason,
                "inactive_days": d.inactive_days,
                "buried_at": d.buried_at,
            }
            for d in dead_channels_q.scalars().all()
        ],
        "loan_journey": [
            {
                "id": str(j.id),
                "department": j.department,
                "stage": j.stage,
                "agent_id": j.agent_id,
                "action_taken": j.action_taken,
                "notes": j.notes,
                "status": j.status,
                "created_at": j.created_at,
            }
            for j in journey.scalars().all()
        ],
        "compliance_summary": [
            {
                "audit_token": str(c.audit_token),
                "overall_result": c.overall_result,
                "fail_reason": c.fail_reason,
                "created_at": c.created_at,
            }
            for c in compliance.scalars().all()
        ],
    }


@router.get("/customer/{customer_id}/thread")
async def get_thread(customer_id: str, bank_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    bank_id = await resolve_bank_uuid(bank_id)
    messages = await db.execute(
        select(Message)
        .where(Message.customer_id == customer_id, Message.bank_id == bank_id)
        .order_by(Message.created_at.asc())
    )
    rows = messages.scalars().all()

    data: list[dict[str, Any]] = []
    for m in rows:
        c = await db.execute(
            select(ComplianceLog.audit_token).where(
                and_(
                    ComplianceLog.message_id == m.id,
                    ComplianceLog.customer_id == customer_id,
                    ComplianceLog.bank_id == bank_id,
                )
            )
        )
        token = c.scalar_one_or_none()
        data.append(
            {
                "id": str(m.id),
                "channel": m.channel,
                "direction": m.direction,
                "content": m.content,
                "translated_content": m.translated_content,
                "original_language": m.original_language,
                "ai_draft": m.ai_draft,
                "agent_id": m.agent_id,
                "created_at": m.created_at,
                "compliance_audit_token": str(token) if token else None,
            }
        )

    return {"messages": data, "count": len(data)}


async def _mock_send_to_channel(channel: str, content: str) -> dict[str, str]:
    return {"channel": channel, "status": "sent", "message": content}


@router.post("/message/send")
async def send_message(req: SendMessageRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    bank_id = await resolve_bank_uuid(req.bank_id)
    customer_res = await db.execute(
        select(Customer).where(Customer.id == req.customer_id, Customer.bank_id == bank_id)
    )
    customer = customer_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="customer not found")

    state = {
        "bank_id": bank_id,
        "customer_id": req.customer_id,
        "customer_profile": {
            "attributes": customer.attributes or {},
            "name": customer.name,
        },
        "ai_draft": req.content,
        "frustration_score": customer.frustration_score,
        "message_type": "transactional",
    }
    compliance_result, details = await evaluate_compliance(state)
    if compliance_result != "PASS":
        return {
            "success": False,
            "audit_token": None,
            "compliance_details": details,
            "reason": "Compliance failed",
        }

    await _mock_send_to_channel(req.channel, req.content)

    msg = Message(
        bank_id=bank_id,
        customer_id=req.customer_id,
        channel=req.channel,
        direction="outbound",
        content=req.content,
        translated_content=req.content,
        sent_content=req.content,
        agent_id=req.agent_id,
        ai_draft=req.content,
        message_type="transactional",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    state["message_id"] = str(msg.id)
    state["compliance_details"] = details
    audit_token = await write_compliance_log_to_db(state)

    await invalidate_customer(req.customer_id)
    await broadcast_event(
        {
            "event": "queue_update",
            "data": {
                "customer_id": req.customer_id,
                "channel": req.channel,
                "content": req.content,
            },
        }
    )

    return {"success": True, "audit_token": audit_token, "compliance_details": details}


@router.post("/message/{message_id}/override")
async def override_and_send(
    message_id: str,
    payload: OverrideRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    bank_id = await resolve_bank_uuid(settings.BANK_ID)
    msg_res = await db.execute(
        select(Message).where(Message.id == message_id, Message.bank_id == bank_id)
    )
    message = msg_res.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="message not found")

    override_note = f"[OVERRIDE by {payload.agent_id}] {payload.override_reason}"
    message.sent_content = (message.sent_content or message.ai_draft or message.content or "") + "\n" + override_note
    message.agent_id = payload.agent_id
    await db.commit()

    state = {
        "message_id": str(message.id),
        "bank_id": str(message.bank_id),
        "customer_id": str(message.customer_id),
        "compliance_details": {
            "dnc_checked": True,
            "dnc_result": "override",
            "consent_valid": True,
            "rbi_content_passed": True,
            "tone_fit_passed": True,
            "safety_check_passed": True,
            "overall_result": "PASS",
            "fail_reason": f"Manual override: {payload.override_reason}",
        },
    }
    audit_token = await write_compliance_log_to_db(state)

    return {"success": True, "message_id": message_id, "audit_token": audit_token}


@router.websocket("/ws/{agent_id}")
async def agents_ws(websocket: WebSocket, agent_id: str) -> None:
    await websocket.accept()
    _connections[agent_id] = websocket
    await websocket.send_json({"event": "connection", "data": {"connected": True}})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.pop(agent_id, None)
