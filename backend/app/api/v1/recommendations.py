"""
Decision Briefs & Governed Human-in-the-Loop Approval Workflow
Enforces state machine transitions: Draft -> Submitted -> In Review -> Approved / Rejected.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime, timezone
from app.core.database import get_db
from app.domain.models import DecisionReview
from app.domain.schemas import ReviewOut, ReviewCreateRequest, ReviewTransitionRequest
from app.core.audit import log_audit_event

router = APIRouter()

# Valid role-state transitions
ALLOWED_TRANSITIONS = {
    "DRAFT": {"SUBMIT": "SUBMITTED"},
    "SUBMITTED": {"START_REVIEW": "IN_REVIEW", "REJECT": "REJECTED"},
    "IN_REVIEW": {"APPROVE": "APPROVED", "REJECT": "REJECTED", "RETURN": "DRAFT"}
}

ROLE_PERMISSIONS = {
    "SUBMIT": ["Analyst", "Senior Analyst", "Director of Civil Supplies"],
    "START_REVIEW": ["Director of Civil Supplies", "Civil Supplies Commissioner"],
    "APPROVE": ["Director of Civil Supplies", "Civil Supplies Commissioner", "Hon'ble Minister for Food & Civil Supplies"],
    "REJECT": ["Director of Civil Supplies", "Civil Supplies Commissioner"],
    "RETURN": ["Director of Civil Supplies", "Civil Supplies Commissioner"]
}

@router.get("", response_model=List[ReviewOut])
def get_recommendations(db: Session = Depends(get_db)):
    reviews = db.query(DecisionReview).order_by(DecisionReview.created_at.desc()).all()
    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "scenario_id": r.scenario_id,
            "title": r.title,
            "summary": r.summary,
            "state": r.state,
            "current_reviewer_role": r.current_reviewer_role,
            "comments": json.loads(r.comments_json),
            "version": r.version,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return results

@router.get("/{review_id}", response_model=ReviewOut)
def get_recommendation(review_id: str, db: Session = Depends(get_db)):
    review = db.query(DecisionReview).filter(DecisionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Decision Brief not found.")

    return {
        "id": review.id,
        "scenario_id": review.scenario_id,
        "title": review.title,
        "summary": review.summary,
        "state": review.state,
        "current_reviewer_role": review.current_reviewer_role,
        "comments": json.loads(review.comments_json),
        "version": review.version,
        "created_at": review.created_at,
        "updated_at": review.updated_at
    }

@router.post("/{review_id}/transition", response_model=ReviewOut)
def transition_recommendation(
    review_id: str,
    req: ReviewTransitionRequest,
    db: Session = Depends(get_db)
):
    review = db.query(DecisionReview).filter(DecisionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Decision Brief not found.")

    action = req.action.upper()
    role = req.reviewer_role

    # Check state machine
    current_state = review.state
    if current_state not in ALLOWED_TRANSITIONS or action not in ALLOWED_TRANSITIONS[current_state]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition '{action}' from state '{current_state}'."
        )

    # Check role permission
    allowed_roles = ROLE_PERMISSIONS.get(action, [])
    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not authorized to perform action '{action}' on decision brief."
        )

    next_state = ALLOWED_TRANSITIONS[current_state][action]
    review.state = next_state
    review.updated_at = datetime.now(timezone.utc).isoformat()
    review.current_reviewer_role = role

    # Append comment
    comments = json.loads(review.comments_json)
    comments.append({
        "author": f"{role} (Authorized)",
        "role": role,
        "action": action,
        "timestamp": review.updated_at,
        "text": req.comment
    })
    review.comments_json = json.dumps(comments)
    review.version += 1

    db.commit()
    db.refresh(review)

    # Log immutable audit event
    log_audit_event(
        db=db,
        actor_id=f"user_{role.lower().replace(' ', '_')}",
        actor_role=role,
        action=f"TRANSITION_{action}",
        target_type="DECISION_REVIEW",
        target_id=review.id,
        details={"from_state": current_state, "to_state": next_state, "comment": req.comment}
    )

    return {
        "id": review.id,
        "scenario_id": review.scenario_id,
        "title": review.title,
        "summary": review.summary,
        "state": review.state,
        "current_reviewer_role": review.current_reviewer_role,
        "comments": comments,
        "version": review.version,
        "created_at": review.created_at,
        "updated_at": review.updated_at
    }
