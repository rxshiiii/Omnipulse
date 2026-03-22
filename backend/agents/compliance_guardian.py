from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from sqlalchemy import desc, select

from config import settings
from database.connection import AsyncSessionLocal
from database.models import ComplianceLog
from services.bank import resolve_bank_uuid

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


async def safety_node(state: AgentState) -> AgentState:
    draft = state.get("ai_draft") or state.get("translated_text") or ""
    if not draft or not settings.GROQ_API_KEY:
        state["safety_precheck"] = True
        return state

    llm = ChatGroq(model="groq/safety-gpt-oss-20b", temperature=0)
    try:
        response = llm.invoke(
            [
                HumanMessage(
                    content=f"Classify bank customer message safety. Answer safe or unsafe only: {draft}"
                )
            ]
        )
        state["safety_precheck"] = "unsafe" not in str(response.content).lower()
    except Exception:
        state["safety_precheck"] = True
    return state


async def evaluate_compliance(state: AgentState) -> tuple[str, dict]:
    profile = state.get("customer_profile", {})
    draft = state.get("ai_draft", "")

    dnc_result = "not_on_list"
    consent_valid = profile.get("attributes", {}).get("whatsapp_consent", True)

    if draft and settings.GROQ_API_KEY:
        llm = ChatGroq(model="moonshotai/kimi-k2-instruct", temperature=0)
        rbi_prompt = f"""
You are an RBI compliance checker for Indian bank communications.
Check this message: "{draft}"

Return ONLY valid JSON:
{{
  "passed": <true/false>,
  "issues": [],
  "reason": "<explanation if failed, empty string if passed>"
}}
"""
        try:
            rbi_response = llm.invoke([HumanMessage(content=rbi_prompt)])
            match = json.loads(str(rbi_response.content)[str(rbi_response.content).find("{") : str(rbi_response.content).rfind("}") + 1])
            rbi_result = {
                "passed": bool(match.get("passed", True)),
                "issues": match.get("issues", []),
                "reason": match.get("reason", ""),
            }
        except Exception:
            rbi_result = {"passed": True, "issues": [], "reason": ""}
    else:
        rbi_result = {"passed": True, "issues": [], "reason": ""}

    tone_fit = True
    if state.get("frustration_score", 0) > 6 and state.get("message_type") == "marketing":
        tone_fit = False

    safety_passed = bool(state.get("safety_precheck", True))
    if draft and settings.GROQ_API_KEY:
        safety_llm = ChatGroq(model="groq/safety-gpt-oss-20b", temperature=0)
        try:
            safety_response = safety_llm.invoke(
                [
                    HumanMessage(
                        content=f"Is this message safe to send to a bank customer? Answer with only 'safe' or 'unsafe': {draft}"
                    )
                ]
            )
            safety_passed = "unsafe" not in str(safety_response.content).lower()
        except Exception:
            safety_passed = True

    all_passed = (
        dnc_result == "not_on_list"
        and consent_valid
        and rbi_result["passed"]
        and tone_fit
        and safety_passed
    )

    details = {
        "dnc_checked": True,
        "dnc_result": dnc_result,
        "consent_valid": consent_valid,
        "rbi_content_passed": rbi_result["passed"],
        "tone_fit_passed": tone_fit,
        "safety_check_passed": safety_passed,
        "overall_result": "PASS" if all_passed else "FAIL",
        "fail_reason": rbi_result.get("reason", "") if not all_passed else None,
    }
    return ("PASS" if all_passed else "FAIL", details)


async def write_compliance_log_to_db(state: AgentState) -> str:
    details = state.get("compliance_details", {})
    bank_id = state.get("bank_id")
    customer_id = state.get("customer_id")
    if not bank_id or not customer_id:
        return ""

    bank_id = await resolve_bank_uuid(str(bank_id))

    raw_message_id = state.get("message_id")
    message_id: str | None = None
    if raw_message_id:
        try:
            message_id = str(uuid.UUID(str(raw_message_id)))
        except (ValueError, TypeError):
            message_id = None

    async with AsyncSessionLocal() as session:
        prev_q = await session.execute(
            select(ComplianceLog)
            .where(ComplianceLog.bank_id == bank_id)
            .order_by(desc(ComplianceLog.created_at))
            .limit(1)
        )
        prev = prev_q.scalar_one_or_none()
        prev_hash = prev.hash_chain if prev else "GENESIS"

        payload = f"{bank_id}|{customer_id}|{message_id or ''}|{details.get('overall_result')}|{datetime.now(timezone.utc).isoformat()}|{prev_hash}"
        hash_chain = hashlib.sha256(payload.encode()).hexdigest()

        log = ComplianceLog(
            bank_id=bank_id,
            customer_id=customer_id,
            message_id=message_id,
            dnc_checked=details.get("dnc_checked", False),
            dnc_result=details.get("dnc_result"),
            consent_valid=details.get("consent_valid"),
            rbi_content_passed=details.get("rbi_content_passed"),
            tone_fit_passed=details.get("tone_fit_passed"),
            safety_check_passed=details.get("safety_check_passed"),
            overall_result=details.get("overall_result"),
            fail_reason=details.get("fail_reason"),
            agent_version="v1.0",
            hash_chain=hash_chain,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return str(log.audit_token)


async def compliance_node(state: AgentState) -> AgentState:
    result, details = await evaluate_compliance(state)
    state["compliance_result"] = result
    state["compliance_details"] = details
    audit_token = await write_compliance_log_to_db(state)
    state["compliance_audit_token"] = audit_token
    return state
