from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from config import settings
from database.schemas import MessageEvent
from services.queue import publish_message


router = APIRouter()


def _base_event(channel: str, raw_payload: dict[str, Any], bank_id: str) -> dict[str, Any]:
    return {
        "customer_phone": None,
        "customer_email": None,
        "channel": channel,
        "content": None,
        "audio_url": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_payload": raw_payload,
        "bank_id": bank_id,
    }


@router.get("/whatsapp")
async def verify_whatsapp(
    mode: str = Query(alias="hub.mode"),
    challenge: str = Query(alias="hub.challenge"),
    verify_token: str = Query(alias="hub.verify_token"),
) -> str:
    if mode == "subscribe" and verify_token == settings.META_VERIFY_TOKEN:
        return challenge
    raise HTTPException(status_code=403, detail="verification failed")


@router.post("/whatsapp")
async def whatsapp_webhook(payload: dict[str, Any]) -> dict[str, str]:
    event = _base_event("whatsapp", payload, payload.get("bank_id", settings.BANK_ID))

    try:
        entries = payload.get("entry", [])
        changes = entries[0].get("changes", []) if entries else []
        value = changes[0].get("value", {}) if changes else {}
        message = (value.get("messages") or [{}])[0]
        contacts = (value.get("contacts") or [{}])[0]

        event["customer_phone"] = contacts.get("wa_id") or message.get("from")
        if message.get("type") == "audio":
            event["audio_url"] = (message.get("audio") or {}).get("url")
        else:
            event["content"] = (message.get("text") or {}).get("body")
    except Exception:
        pass

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/sms")
async def sms_webhook(request: Request) -> dict[str, str]:
    form = await request.form()
    payload = dict(form)
    event = _base_event("sms", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_phone"] = payload.get("From")
    event["content"] = payload.get("Body")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/email")
async def email_webhook(request: Request) -> dict[str, str]:
    form = await request.form()
    payload = dict(form)
    event = _base_event("email", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_email"] = payload.get("from")
    event["content"] = payload.get("text") or payload.get("subject")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/voice")
async def voice_webhook(request: Request) -> dict[str, str]:
    form = await request.form()
    payload = dict(form)
    event = _base_event("voice", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_phone"] = payload.get("From")
    event["content"] = payload.get("TranscriptionText")
    event["audio_url"] = payload.get("RecordingUrl")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/twitter")
async def twitter_webhook(payload: dict[str, Any]) -> dict[str, str]:
    event = _base_event("twitter", payload, payload.get("bank_id", settings.BANK_ID))
    data = payload.get("data", {})
    includes = payload.get("includes", {})
    users = includes.get("users", [{}])
    event["customer_email"] = users[0].get("username") if users else None
    event["content"] = data.get("text")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}
