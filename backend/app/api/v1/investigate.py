"""
Conversational Agentic Investigation Endpoint (Server-Sent Events)
Streams multi-agent progress, citations, and decision findings in real-time.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.schemas import InvestigationRequest
from app.agents.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()

@router.post("")
async def start_investigation(
    req: InvestigationRequest,
    db: Session = Depends(get_db)
):
    """
    Initiates the Sense -> Predict -> Simulate -> Act -> Learn workflow
    and streams real agent step updates over Server-Sent Events (SSE).
    """
    stream = orchestrator.stream_investigation(
        query=req.query,
        commodity_id=req.commodity_id,
        geography_id=req.geography_id,
        horizon_days=req.horizon_days,
        db=db
    )

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
