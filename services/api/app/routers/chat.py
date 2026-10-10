from typing import Literal

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.rag import retrieve, stream_answer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


@router.get("/status")
def status():
    """Lets the UI explain what is missing instead of failing silently."""
    s = get_settings()
    try:
        names = [m["name"] for m in httpx.get(f"{s.ollama_url}/api/tags", timeout=3).json().get("models", [])]
    except (httpx.HTTPError, ValueError):
        return {"ollama": False, "chat_model": False, "embed_model": False}

    def has(name: str) -> bool:
        return any(n == name or n.startswith(name + ":") for n in names)

    return {"ollama": True, "chat_model": has(s.chat_model), "embed_model": has(s.embed_model)}


@router.post("")
def chat(body: ChatRequest, dataset: str = Query(...)):
    messages = [m.model_dump() for m in body.messages]
    if messages[-1]["role"] != "user":
        raise AppError(422, "INVALID_CHAT", "The last message must come from the user.")

    # follow-up questions ("what about its recall?") need the previous question too
    user_texts = [m["content"] for m in messages if m["role"] == "user"]
    context = retrieve(dataset, " ".join(user_texts[-2:]))  # errors here become clean JSON errors

    return StreamingResponse(
        stream_answer(messages, context),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )