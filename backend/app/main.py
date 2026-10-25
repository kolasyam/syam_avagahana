"""
FastAPI Application Entry Point
AP Essential Commodities Price Intelligence and Stabilisation Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.data.seed_data import seed_database

# Include v1 API Routers
from app.api.v1.reference import router as reference_router
from app.api.v1.observations import router as observations_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.risk import router as risk_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.sources import router as sources_router
from app.api.v1.investigate import router as investigate_router
from app.api.v1.audit import router as audit_router
from app.api.v1.web_lookup import router as web_lookup_router
from app.api.v1.chat import router as chat_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables, then load data. Synthetic seeding only when explicitly
    # requested (SEED_SYNTHETIC=true); the default path ingests the REAL
    # curated dataset via ingest_real.py.
    Base.metadata.create_all(bind=engine)
    if settings.SEED_SYNTHETIC:
        import logging
        logging.warning("SEED_SYNTHETIC=true — loading DEMO/SYNTHETIC data. "
                        "This flags every row is_demo_data=True. Not for client demos.")
        seed_database()
    else:
        import logging
        from app.data.ingest_real import ensure_real_data
        try:
            summary = ensure_real_data()
            logging.info("Real-data ingestion: %s", summary)
        except Exception as exc:  # hard fail loudly, never silently fake data
            logging.error("REAL-DATA INGESTION FAILED: %s — API will report "
                          "insufficient history rather than fabricate data.", exc)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Agentic workspace for price intelligence, forecasting, and policy intervention simulation for AP Essential Commodities.",
    lifespan=lifespan
)

# CORS configuration — locked to workspace origins in demo mode.
# (was: allow_origins=["*"] with credentials=True — an anti-pattern)
_trusted_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:4173",   # Vite preview / built dist
    "http://127.0.0.1:4173",
    "http://localhost:8000",   # same-origin (served dist)
]
if os.getenv("EXTRA_CORS_ORIGINS"):
    _trusted_origins += [o.strip() for o in os.getenv("EXTRA_CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_trusted_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "demo_mode": settings.DEMO_MODE,
        "environment": settings.ENVIRONMENT
    }

# Mount API Routers
app.include_router(reference_router, prefix="/api/v1/reference", tags=["Reference"])
app.include_router(observations_router, prefix="/api/v1/observations", tags=["Observations"])
app.include_router(forecast_router, prefix="/api/v1/forecast", tags=["Forecast"])
app.include_router(risk_router, prefix="/api/v1/risk", tags=["Risk"])
app.include_router(scenarios_router, prefix="/api/v1/scenarios", tags=["Scenarios"])
app.include_router(recommendations_router, prefix="/api/v1/recommendations", tags=["Recommendations & Approvals"])
app.include_router(sources_router, prefix="/api/v1/sources", tags=["Data Sources"])
app.include_router(web_lookup_router, prefix="/api/v1/web", tags=["Web Fallback"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Agentic Chat"])
app.include_router(investigate_router, prefix="/api/v1/investigate", tags=["Agentic Investigation"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit Trail"])

# Mount frontend dist static files if they exist
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
