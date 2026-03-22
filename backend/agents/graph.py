from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.attribution_tracker import attribution_node
from agents.compliance_guardian import compliance_node, safety_node
from agents.emotion_reader import emotion_node
from agents.intent_detector import intent_node
from agents.orchestrator import orchestrator_node
from agents.response_drafter import draft_node
from agents.vernacular import vernacular_node


class AgentState(TypedDict, total=False):
    message_id: str
    customer_id: str
    bank_id: str
    channel: str
    raw_content: Optional[str]
    audio_url: Optional[str]
    transcribed_text: Optional[str]
    translated_text: Optional[str]
    original_language: Optional[str]
    customer_profile: dict
    conversation_history: list
    intent_label: Optional[str]
    intent_confidence: Optional[float]
    frustration_score: Optional[float]
    emotional_state: Optional[str]
    exit_type: Optional[str]
    ai_draft: Optional[str]
    compliance_result: Optional[str]
    compliance_details: Optional[dict]
    message_type: Optional[str]
    final_action: Optional[str]
    error: Optional[str]


def _should_draft(state: AgentState) -> str:
    intent = state.get("intent_label", "general")
    emotion = state.get("emotional_state", "calm")
    message_type = state.get("message_type", "transactional")

    if intent in ["general", "feedback"]:
        return "skip_draft"
    if emotion == "angry" and message_type == "marketing":
        return "skip_draft"
    return "run_draft"


graph = StateGraph(AgentState)
graph.add_node("vernacular", vernacular_node)
graph.add_node("intent", intent_node)
graph.add_node("emotion", emotion_node)
graph.add_node("draft", draft_node)
graph.add_node("safety", safety_node)
graph.add_node("compliance", compliance_node)
graph.add_node("attribution", attribution_node)
graph.add_node("orchestrator", orchestrator_node)

graph.add_edge(START, "vernacular")
graph.add_edge("vernacular", "intent")
graph.add_edge("intent", "emotion")
graph.add_conditional_edges(
    "emotion",
    _should_draft,
    {
        "run_draft": "draft",
        "skip_draft": "safety",
    },
)
graph.add_edge("draft", "safety")
graph.add_edge("safety", "compliance")
graph.add_edge("compliance", "attribution")
graph.add_edge("attribution", "orchestrator")
graph.add_edge("orchestrator", END)

pipeline = graph.compile()


async def run_pipeline(state: AgentState) -> AgentState:
    return await pipeline.ainvoke(state)
