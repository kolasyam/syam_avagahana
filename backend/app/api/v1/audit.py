"""
Audit Events Query API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from app.core.database import get_db
from app.domain.models import AuditEvent

router = APIRouter()

@router.get("/events")
def get_audit_events(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    results = []
    for e in events:
        results.append({
            "id": e.id,
            "timestamp": e.timestamp,
            "actor_id": e.actor_id,
            "actor_role": e.actor_role,
            "action": e.action,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "outcome": e.outcome,
            "details": json.loads(e.details_json or "{}"),
            "correlation_id": e.correlation_id
        })
    return results
