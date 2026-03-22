from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from config import settings

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


async def draft_node(state: AgentState) -> AgentState:
    if state.get("intent_label") in ["general", "feedback"]:
        return state

    if not settings.GROQ_API_KEY:
        state["ai_draft"] = "Thank you for your message. We have raised your request and our team will update you within 24 hours. — Priya, Union Bank Support"
        return state

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
    profile = state.get("customer_profile", {})
    history_text = "\n".join(
        [
            f"{m.get('direction','')}: {m.get('translated_content') or m.get('content','')}"
            for m in state.get("conversation_history", [])[-8:]
        ]
    )

    prompt = f"""
You are a Union Bank of India customer service agent named Priya.

CUSTOMER NAME: {profile.get('name', 'Customer')}
ISSUE: {state.get('intent_label', 'query')} — {state.get('translated_text', '')}
EMOTIONAL STATE: {state.get('emotional_state', 'calm')} (frustration: {state.get('frustration_score', 0)}/10)
ACCOUNT ATTRIBUTES: {profile.get('attributes', {})}
CONVERSATION HISTORY:
{history_text}

Write a professional empathetic response that:
1. Addresses customer by name
2. Acknowledges their specific issue
3. References relevant history
4. Gives concrete next step with realistic timeline
5. Is empathetic if frustration score > 6
6. Is under 80 words
7. Ends with: — Priya, Union Bank Support

Return the message text only.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    state["ai_draft"] = str(response.content).strip()
    return state
