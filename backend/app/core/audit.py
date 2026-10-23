"""
Immutable Audit Logging Service
Every consequential action, model execution, scenario run, and review decision is immutably logged.
"""

from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.domain.models import AuditEvent

def log_audit_event(
    db: Session,
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str,
    outcome: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> AuditEvent:
    """Record an immutable audit event."""
    event = AuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
        details_json=json.dumps(details or {}),
        correlation_id=correlation_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
