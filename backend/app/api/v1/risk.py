"""
Price Spike Risk API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import json
from app.core.database import get_db
from app.domain.models import RiskAssessment
from app.domain.schemas import RiskAssessmentOut

router = APIRouter()

@router.get("/latest", response_model=RiskAssessmentOut)
def get_latest_risk(
    commodity_id: str = Query("onion"),
    geography_id: str = Query("mandi_kurnool"),
    db: Session = Depends(get_db)
):
    risk = db.query(RiskAssessment).filter(
        RiskAssessment.commodity_id == commodity_id,
        RiskAssessment.geography_id == geography_id
    ).order_by(RiskAssessment.assessment_date.desc()).first()

    if not risk:
        raise HTTPException(status_code=404, detail="No risk assessment found.")

    return {
        "id": risk.id,
        "commodity_id": risk.commodity_id,
        "geography_id": risk.geography_id,
        "assessment_date": risk.assessment_date,
        "horizon_days": risk.horizon_days,
        "spike_probability": risk.spike_probability,
        "threshold_level": risk.threshold_level,
        "primary_drivers": json.loads(risk.primary_drivers_json),
        "narrative": risk.narrative
    }
