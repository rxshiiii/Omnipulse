from __future__ import annotations

import httpx
from typing import TYPE_CHECKING, Any
from groq import Groq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import settings

if TYPE_CHECKING:
    from agents.graph import AgentState
else:
    AgentState = dict[str, Any]


def _looks_non_english(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)


async def _download_audio(audio_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(audio_url)
        response.raise_for_status()
        return response.content


async def vernacular_node(state: AgentState) -> AgentState:
    client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    if state.get("audio_url") and client:
        audio_data = await _download_audio(state["audio_url"])
        transcription = client.audio.transcriptions.create(
            file=("audio.ogg", audio_data),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )
        state["transcribed_text"] = transcription.text
        state["original_language"] = getattr(transcription, "language", "mr")

    text = state.get("transcribed_text") or state.get("raw_content", "")
    if not text:
        state["translated_text"] = ""
        state["original_language"] = "en"
        return state

    lang = state.get("original_language") or ("mr" if _looks_non_english(text) else "en")
    state["original_language"] = lang

    if lang.lower() not in ["en", "english"] and settings.GROQ_API_KEY:
        llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)
        result = llm.invoke(
            [
                SystemMessage(
                    content="You are a translator. Translate to English accurately. Return ONLY the translation, nothing else."
                ),
                HumanMessage(content=text),
            ]
        )
        state["translated_text"] = str(result.content)
    else:
        state["translated_text"] = text

    return state
