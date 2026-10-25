"""
Reference Catalog for Commodities, Mandis/Districts, and Policy Parameters
All entities strictly in English. Production Grade.
"""

from app.core.config import settings

GEOGRAPHIES = [
    {
        "id": "mandi_kurnool",
        "name": "Kurnool Agricultural Market Yard",
        "district": "Kurnool",
        "state": "Andhra Pradesh",
        "latitude": 15.8281,
        "longitude": 78.0373,
        "market_type": "Primary APMC Hub"
    },
    {
        "id": "mandi_kadapa",
        "name": "Kadapa APMC Mandi",
        "district": "YSR Kadapa",
        "state": "Andhra Pradesh",
        "latitude": 14.4673,
        "longitude": 78.8242,
        "market_type": "Regional Mandi"
    },
    {
        "id": "mandi_vijayawada",
        "name": "Gollapudi Mandi, Vijayawada",
        "district": "NTR District",
        "state": "Andhra Pradesh",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "market_type": "Major Consumption Hub"
    },
    {
        "id": "mandi_tirupati",
        "name": "Tirupati Vegetable Market",
        "district": "Tirupati",
        "state": "Andhra Pradesh",
        "latitude": 13.6288,
        "longitude": 79.4192,
        "market_type": "Regional Hub"
    },
    {
        "id": "mandi_visakhapatnam",
        "name": "MVP Rythu Bazaar / Mandi, Visakhapatnam",
        "district": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "market_type": "Coastal Urban Terminal"
    }
]

COMMODITIES = [
    {
        "id": "onion",
        "name": "Onion (Common Red / Hybrid)",
        "variety": "Nashik Red / Bellary Hybrid",
        "unit": "₹/kg",
        "alert_threshold": 35.0,
        "crisis_threshold": 50.0
    },
    {
        "id": "tomato",
        "name": "Tomato (Hybrid Red)",
        "variety": "Madanapalle Hybrid",
        "unit": "₹/kg",
        "alert_threshold": 40.0,
        "crisis_threshold": 70.0
    },
    {
        "id": "potato",
        "name": "Potato (Table Variety)",
        "variety": "Kufri Jyoti",
        "unit": "₹/kg",
        "alert_threshold": 28.0,
        "crisis_threshold": 42.0
    }
]

CONNECTORS_METADATA = [
    {
        "connector_id": "conn_agmarknet_curated",
        "name": "AGMARKNET — Curated Daily State Series",
        "family": "Market Prices & Arrivals",
        "status": "INGESTED_ACTIVE",
        "freshness_hours": None,
        "records_count": 6851,
        "quality_score": 0.98,
        "mode_label": "Ingested local dataset (2022-01-01 → 2026-10-15, daily)",
        "last_sync": "2026-10-15T00:00:00Z",
        "note": "State aggregates: AP, MH, KA, MP. AP series complete (0 missing modals)."
    },
    {
        "connector_id": "conn_imd_context",
        "name": "IMD — Derived Weather Context",
        "family": "Weather & Climate",
        "status": "INGESTED_ACTIVE",
        "freshness_hours": None,
        "records_count": 6996,
        "quality_score": 0.95,
        "mode_label": "Ingested context series (precipitation, VPD, seasonal rain)",
        "last_sync": "2026-10-15T00:00:00Z",
        "note": "Derived/curated weather series aligned to the price dataset; live IMD telemetry on roadmap."
    },
    {
        "connector_id": "conn_doca_retail",
        "name": "DoCA PMS — Retail Price Lens",
        "family": "Retail Price Monitoring",
        "status": "INGESTED_ACTIVE",
        "freshness_hours": None,
        "records_count": 6750,
        "quality_score": 0.97,
        "mode_label": "Retail reference series ingested alongside mandi modal prices",
        "last_sync": "2026-10-15T00:00:00Z"
    },
    {
        "connector_id": "conn_production_estimates",
        "name": "Production & Supply Context (Horticulture estimates)",
        "family": "Acreage, Production & Stocks",
        "status": "INGESTED_ACTIVE",
        "freshness_hours": None,
        "records_count": 8745,
        "quality_score": 0.90,
        "mode_label": "Standing production estimates (AP/MH/India) + fuel price context",
        "last_sync": "2026-10-15T00:00:00Z"
    },
    {
        "connector_id": "conn_tavily_web",
        "name": "Tavily — Web Fallback (Market Agent escalation)",
        "family": "Web Search Fallback",
        "status": "READY" if settings.TAVILY_API_KEY else "CONFIG_NOT_SET",
        "freshness_hours": 0.0,
        "records_count": 0,
        "quality_score": 0.8,
        "mode_label": "Citation-only web fallback; trust-whitelist filtered; never auto-ingested",
        "last_sync": None,
        "note": "Set TAVILY_API_KEY to enable." if not settings.TAVILY_API_KEY else None
    },
    {
        "connector_id": "conn_district_agmarknet",
        "name": "AGMARKNET — District-Level Pull",
        "family": "Market Prices & Arrivals",
        "status": "ROADMAP_NOT_INGESTED",
        "freshness_hours": None,
        "records_count": 0,
        "quality_score": None,
        "mode_label": "District ingest on roadmap. Registered mandis (Kurnool, Kadapa, "
                      "Vijayawada, Tirupati, Visakhapatnam) are REFERENCE SITES with no price rows; "
                      "district quotes may be fetched via the web-fallback tool with citation.",
        "last_sync": None
    },
]
