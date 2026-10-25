"""
Market Agent Web-Fallback Lookup Endpoint
=========================================
Thin API over tools/web_trust.py for the chat sources panel.

GET /api/v1/web/lookup?q=...
Returns citation-only web results (trust-filtered, never auto-ingested).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.tools.web_trust import web_search_lookup
from app.core.database import get_db
from app.core.audit import log_audit_event

router = APIRouter()


@router.get("/lookup")
def lookup(
    q: str = Query(..., min_length=2, max_length=300),
    max_results: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    result = web_search_lookup(q, max_results=max_results)
    if result["status"] == "WEB_RESULTS":
        try:
            log_audit_event(
                db,
                actor_id="market_agent",
                actor_role="Agent",
                action="WEB_FALLBACK_LOOKUP",
                target_type="WebSearch",
                target_id=q[:120],
                details={
                    "trust_summary": result.get("trust_summary"),
                    "ingested_into_model": False,
                },
            )
        except Exception:
            pass  # audit logging must never break the user-facing tool path
    return result
