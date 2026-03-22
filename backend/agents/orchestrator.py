from __future__ import annotations

from typing import TYPE_CHECKING, Any

from redis.asyncio import Redis

from config import settings

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def flag_proactive_outreach(customer_id: str) -> None:
    await redis_client.set(f"outreach:{customer_id}", "needed", ex=86400)


async def orchestrator_node(state: AgentState) -> AgentState:
    if state.get("compliance_result") == "FAIL":
        state["final_action"] = "route_to_human_review"
    elif state.get("frustration_score", 0) >= 8.0:
        state["final_action"] = "escalate_to_senior_rm"
        await flag_proactive_outreach(state["customer_id"])
    elif state.get("intent_label") in ["urgent_complaint", "fraud_report", "kcc_issue"]:
        state["final_action"] = "escalate_immediate"
    elif state.get("ai_draft") and state.get("compliance_result") == "PASS":
        state["final_action"] = "draft_ready_for_agent"
    else:
        state["final_action"] = "hold_for_manual"
    return state
