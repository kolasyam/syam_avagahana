"""
Data Fabric Sources and Ingestion Profiling Endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from app.data.reference_catalog import CONNECTORS_METADATA
from app.domain.schemas import ConnectorHealthOut
from app.analytics.quality_checker import profile_dataset

router = APIRouter()

@router.get("", response_model=List[ConnectorHealthOut])
def get_sources():
    return CONNECTORS_METADATA

@router.post("/profile-upload")
async def upload_and_profile_file(file: UploadFile = File(...)):
    """
    Quarantines and safely inspects an uploaded dataset file (CSV, TSV, XLSX).
    Profiles schema, detects column types, checks null rates, time gaps, and anomalies.
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB limit
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds maximum 10MB limit.")

    result = profile_dataset(content, file.filename)
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid file structure."))

    return result
