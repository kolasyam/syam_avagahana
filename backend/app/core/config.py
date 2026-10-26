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
    DATA_MODE_LABEL: str = "REAL INGESTED DATA • AGMARKNET-derived AP state series (2022-2026), IMD weather context"
    
    # Persistence — ABSOLUTE path anchored to the backend/ directory so any
    # process (uvicorn, scripts, notebooks) resolves the SAME SQLite file
    # regardless of the working directory it was launched from.
    _BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(_BACKEND_DIR, "ap_commodities.db").replace("\\", "/")
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Domain thresholds (specifically for Onion in Kurnool & AP Mandis)
    ONION_MODAL_BASELINE: float = 24.50     # ₹/kg normal baseline
    ONION_ALERT_THRESHOLD: float = 35.00    # ₹/kg warning threshold (triggers 14-day early alert)
    ONION_CRISIS_THRESHOLD: float = 50.00   # ₹/kg acute crisis threshold
    ONION_MAX_INTERVENTION_CAP: float = 65.00 # ₹/kg runaway threshold
    
    # Pilot geography = the real ingested state series (district data is a
    # roadmap item; mandi_kurnool remains registered as a reference site).
    PILOT_MARKET_ID: str = "state_andhra_pradesh"
    PILOT_COMMODITY_ID: str = "onion"

    # --- Real data & demo-mode settings -----------------------------------
    # Synthetic seeding is OFF by default: startup ingests the real curated
    # dataset instead (see app/data/ingest_real.py).
    SEED_SYNTHETIC: bool = os.getenv("SEED_SYNTHETIC", "false").lower() in ("1", "true", "yes")
    REAL_DATA_CSV: str = os.getenv(
        "REAL_DATA_CSV",
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop",
                     "AP_Onion_Dataset_2022_2026_Production.csv")
    )

    # --- LLM provider (agentic chat) ---------------------------------------
    # Primary = OSS-20B over an OpenAI-compatible API; local Ollama is the
    # automatic fallback so the demo survives an API hiccup. The rule-based
    # deterministic path is the last resort (honest, labelled, never fake).
    # Set LLM_PROVIDER=ollama to force local-only (offline rehearsal).
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai_api")  # "openai_api" | "ollama"
    LLM_FALLBACK_TO_OLLAMA: bool = os.getenv(
        "LLM_FALLBACK_TO_OLLAMA", "true"
    ).lower() in ("1", "true", "yes")

    # Primary: OpenAI-compatible API serving an open-weight OSS model.
    # Default = Groq (openai/gpt-oss-20b, ~1000 tps). Works with any
    # /chat/completions endpoint — swap base+model for OpenAI, OpenRouter,
    # Together, Fireworks, vLLM, etc.
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.groq.com/openai/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", os.getenv("GROQ_API_KEY", ""))
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")

    # NOTE: OLLAMA_MODEL must fit the demo machine's RAM. 14B needs ~10GB and
    # crashed on a 7.5GB box (CPU_REPACK alloc failure) — 3B (~2.3GB) is safe.
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")

    # --- Web fallback (Market Agent escalation) -----------------------------
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    WEB_TRUST_DOMAINS: List[str] = [
        # Government / official market data
        "agmarknet.gov.in", "dfpd.gov.in", "consumeraffairs.nic.in",
        "imdagrimet.gov.in", "maurdyog.mahaonline.gov.in",
        "nafed-india.com", "pib.gov.in",
        # News-of-record national outlets (current market context tier)
        "business-standard.com", "economictimes.indiatimes.com",
        "livemint.com", "moneycontrol.com", "thehindubusinessline.com",
        "newindianexpress.com", "downtoearth.org.in",
    ]
    
    # Model settings
    DEFAULT_FORECAST_HORIZONS: List[int] = [7, 14, 30, 60, 90]
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
