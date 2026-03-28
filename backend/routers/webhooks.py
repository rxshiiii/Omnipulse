from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from config import settings
from database.schemas import MessageEvent
from services.queue import publish_message


router = APIRouter()


def _stringify_payload_values(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[key] = value
        else:
            normalized[key] = str(value)
    return normalized


async def _read_request_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        payload = await request.json()
        if isinstance(payload, dict):
            return _stringify_payload_values(payload)
        return {}

    form = await request.form()
    return _stringify_payload_values(dict(form))


def _first_non_empty(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _base_event(channel: str, raw_payload: dict[str, Any], bank_id: str) -> dict[str, Any]:
    return {
        "customer_phone": None,
        "customer_email": None,
        "customer_ref": None,
        "customer_name": None,
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
    event["customer_ref"] = _first_non_empty(
        payload,
        "customer_ref",
        "customer_id",
        "external_customer_id",
        "crm_customer_id",
    )
    event["customer_name"] = _first_non_empty(payload, "customer_name", "name")

    try:
        entries = payload.get("entry", [])
        changes = entries[0].get("changes", []) if entries else []
        value = changes[0].get("value", {}) if changes else {}
        message = (value.get("messages") or [{}])[0]
        contacts = (value.get("contacts") or [{}])[0]

        event["customer_phone"] = contacts.get("wa_id") or message.get("from")
        if not event["customer_name"]:
            profile = contacts.get("profile") if isinstance(contacts, dict) else {}
            if isinstance(profile, dict):
                event["customer_name"] = profile.get("name")
        if not event["customer_ref"]:
            event["customer_ref"] = contacts.get("wa_id") or message.get("from")
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
    payload = await _read_request_payload(request)
    event = _base_event("sms", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_ref"] = _first_non_empty(
        payload,
        "customer_ref",
        "customer_id",
        "external_customer_id",
        "crm_customer_id",
    )
    event["customer_name"] = _first_non_empty(payload, "customer_name", "name")
    event["customer_phone"] = _first_non_empty(payload, "From", "from", "phone", "customer_phone")
    event["content"] = _first_non_empty(payload, "Body", "body", "message", "content", "text")

    if not event["customer_phone"]:
        raise HTTPException(status_code=400, detail="Missing customer phone in SMS payload")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/email")
async def email_webhook(request: Request) -> dict[str, str]:
    payload = await _read_request_payload(request)
    event = _base_event("email", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_ref"] = _first_non_empty(
        payload,
        "customer_ref",
        "customer_id",
        "external_customer_id",
        "crm_customer_id",
    )
    event["customer_name"] = _first_non_empty(payload, "customer_name", "name", "sender_name")
    event["customer_email"] = _first_non_empty(
        payload,
        "from",
        "From",
        "email",
        "customer_email",
        "sender",
    )
    event["content"] = _first_non_empty(
        payload,
        "text",
        "plain",
        "body",
        "message",
        "content",
        "subject",
    )

    if not event["customer_email"]:
        raise HTTPException(status_code=400, detail="Missing customer email in Email payload")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/voice")
async def voice_webhook(request: Request) -> dict[str, str]:
    payload = await _read_request_payload(request)
    event = _base_event("voice", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_ref"] = _first_non_empty(
        payload,
        "customer_ref",
        "customer_id",
        "external_customer_id",
        "crm_customer_id",
    )
    event["customer_name"] = _first_non_empty(payload, "customer_name", "name")
    event["customer_phone"] = _first_non_empty(payload, "From", "from", "phone", "customer_phone")
    event["content"] = _first_non_empty(
        payload,
        "TranscriptionText",
        "transcription_text",
        "SpeechResult",
        "body",
        "message",
        "content",
    )
    event["audio_url"] = _first_non_empty(payload, "RecordingUrl", "recording_url", "audio_url")

    if not event["customer_phone"]:
        raise HTTPException(status_code=400, detail="Missing customer phone in Voice payload")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}


@router.post("/twitter")
async def twitter_webhook(payload: dict[str, Any]) -> dict[str, str]:
    event = _base_event("twitter", payload, payload.get("bank_id", settings.BANK_ID))
    event["customer_ref"] = _first_non_empty(
        payload,
        "customer_ref",
        "customer_id",
        "external_customer_id",
        "crm_customer_id",
    )
    event["customer_name"] = _first_non_empty(payload, "customer_name", "name")
    data = payload.get("data", {})
    includes = payload.get("includes", {})
    users = includes.get("users", [{}])
    event["customer_email"] = users[0].get("username") if users else None
    if not event["customer_name"] and users:
        event["customer_name"] = users[0].get("name") or users[0].get("username")
    if not event["customer_ref"]:
        event["customer_ref"] = data.get("author_id") or (users[0].get("id") if users else None)
    event["content"] = data.get("text")

    parsed = MessageEvent(**event)
    await publish_message(parsed.model_dump())
    return {"status": "accepted"}
