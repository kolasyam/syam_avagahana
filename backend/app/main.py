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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed data
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Agentic workspace for price intelligence, forecasting, and policy intervention simulation for AP Essential Commodities.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
app.include_router(investigate_router, prefix="/api/v1/investigate", tags=["Agentic Investigation"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit Trail"])

# Mount frontend dist static files if they exist
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
