from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from config import settings

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


async def intent_node(state: AgentState) -> AgentState:
    if not settings.GROQ_API_KEY:
        state["intent_label"] = "general"
        state["intent_confidence"] = 0.5
        return state

    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)
    prompt = f"""
You are a banking intent classifier for Union Bank of India.
Customer message: "{state.get('translated_text', '')}"
Recent history (last 3): {[m.get('content','') for m in state.get('conversation_history', [])[-3:]]}

Return ONLY valid JSON, no explanation:
{{
  "intent_label": "<one of: complaint, query, urgent_complaint, transaction_issue, loan_query, kcc_issue, fraud_report, feedback, account_issue, general>",
  "confidence": <float 0.0-1.0>,
  "sub_category": "<specific issue>",
  "requires_response": <true/false>,
  "urgency": "<low/medium/high/critical>"
}}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    match = re.search(r"\{.*\}", str(response.content), re.DOTALL)
    if not match:
        state["intent_label"] = "general"
        state["intent_confidence"] = 0.5
        return state

    result = json.loads(match.group())
    state["intent_label"] = result.get("intent_label", "general")
    state["intent_confidence"] = float(result.get("confidence", 0.5))
    return state
