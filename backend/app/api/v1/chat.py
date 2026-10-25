"""
Agentic Chat API
================
GET  /api/v1/chat/health   → local LLM readiness
POST /api/v1/chat/stream   → SSE agentic answer stream
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.chat.llm import check_health, warm_model
from app.chat.orchestrator import stream_chat
from app.core.database import get_db

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


@router.get("/health")
def chat_health():
    """Local LLM service + model availability check (for dashboard status chip)."""
    return check_health()


@router.post("/warm")
def chat_warm():
    """Pre-loads the configured model into RAM (call before the demo)."""
    return warm_model()


@router.post("/stream")
def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    history = [h.model_dump() for h in (req.history or [])]
    return StreamingResponse(
        stream_chat(db, req.message, history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
