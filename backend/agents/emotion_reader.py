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


async def emotion_node(state: AgentState) -> AgentState:
    if not settings.GROQ_API_KEY:
        state["frustration_score"] = 3.0
        state["emotional_state"] = "concerned"
        state["exit_type"] = "still_active"
        return state

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    prompt = f"""
You are an emotional intelligence system for Union Bank of India.
Customer message: "{state.get('translated_text', '')}"
Number of contacts for this issue: {len(state.get('conversation_history', []))}
Conversation history: {[m.get('content','')[:100] for m in state.get('conversation_history', [])[-5:]]}

Return ONLY valid JSON:
{{
  "frustration_score": <float 0.0-10.0>,
  "emotional_state": "<calm/concerned/frustrated/angry/distressed>",
  "exit_type": "<natural_resolution/frustrated_exit/still_active>",
  "proactive_outreach_needed": <true/false>,
  "block_promotional": <true/false>
}}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    match = re.search(r"\{.*\}", str(response.content), re.DOTALL)
    if not match:
        state["frustration_score"] = 3.0
        state["emotional_state"] = "concerned"
        state["exit_type"] = "still_active"
        return state

    result = json.loads(match.group())
    state["frustration_score"] = float(result.get("frustration_score", 3.0))
    state["emotional_state"] = result.get("emotional_state", "concerned")
    state["exit_type"] = result.get("exit_type", "still_active")
    return state
