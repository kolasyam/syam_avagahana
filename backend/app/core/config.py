"""
Application Configuration and Constants
AP Essential Commodities Price Intelligence and Stabilisation Platform
Production Configuration
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AP Essential Commodities Price Intelligence & Autonomous Stabilisation"
    PROJECT_VERSION: str = "1.0.0-production"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Production status
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEMO_MODE: bool = False
    DATA_MODE_LABEL: str = "LIVE FEED • AP CIVIL SUPPLIES & APMC INTEGRATED FABRIC"
    
    # Persistence
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ap_commodities.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Domain thresholds (specifically for Onion in Kurnool & AP Mandis)
    ONION_MODAL_BASELINE: float = 24.50     # ₹/kg normal baseline
    ONION_ALERT_THRESHOLD: float = 35.00    # ₹/kg warning threshold (triggers 14-day early alert)
    ONION_CRISIS_THRESHOLD: float = 50.00   # ₹/kg acute crisis threshold
    ONION_MAX_INTERVENTION_CAP: float = 65.00 # ₹/kg runaway threshold
    
    # Target Markets
    PILOT_MARKET_ID: str = "mandi_kurnool"
    PILOT_COMMODITY_ID: str = "onion"
    
    # Model settings
    DEFAULT_FORECAST_HORIZONS: List[int] = [7, 14, 30, 60, 90]
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
