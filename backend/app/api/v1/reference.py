"""
Reference Data Endpoints
Returns geographies, commodities, and official metadata.
Strictly English-only.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.domain.models import Geography, Commodity
from app.domain.schemas import GeographyOut, CommodityOut

router = APIRouter()

@router.get("/geographies", response_model=List[GeographyOut])
def get_geographies(db: Session = Depends(get_db)):
    return db.query(Geography).all()

@router.get("/commodities", response_model=List[CommodityOut])
def get_commodities(db: Session = Depends(get_db)):
    return db.query(Commodity).all()
