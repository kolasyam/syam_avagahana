"""
Market Observations and Deterministic Analytics Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.domain.models import MarketObservation
from app.domain.schemas import MarketObservationOut
from app.analytics.engine import compute_market_analytics

router = APIRouter()

@router.get("", response_model=List[MarketObservationOut])
def get_observations(
    commodity_id: str = Query("onion"),
    geography_id: str = Query("mandi_kurnool"),
    days: int = Query(60, ge=7, le=365),
    db: Session = Depends(get_db)
):
    cutoff_date = (datetime(2026, 10, 23) - timedelta(days=days)).strftime("%Y-%m-%d")
    records = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == commodity_id,
        MarketObservation.geography_id == geography_id,
        MarketObservation.date >= cutoff_date
    ).order_by(MarketObservation.date.asc()).all()
    return records

@router.get("/analytics")
def get_analytics(
    commodity_id: str = Query("onion"),
    geography_id: str = Query("mandi_kurnool"),
    days: int = Query(90, ge=14, le=365),
    db: Session = Depends(get_db)
):
    cutoff_date = (datetime(2026, 10, 23) - timedelta(days=days)).strftime("%Y-%m-%d")
    records = db.query(MarketObservation).filter(
        MarketObservation.commodity_id == commodity_id,
        MarketObservation.geography_id == geography_id,
        MarketObservation.date >= cutoff_date
    ).order_by(MarketObservation.date.asc()).all()
    
    obs_dicts = [
        {
            "date": o.date,
            "min_price": o.min_price,
            "modal_price": o.modal_price,
            "max_price": o.max_price,
            "arrivals_mt": o.arrivals_mt,
            "source_id": o.source_id
        }
        for o in records
    ]
    
    analytics = compute_market_analytics(obs_dicts)
    return analytics
