"""
Reference Catalog for Commodities, Mandis/Districts, and Policy Parameters
All entities strictly in English. Production Grade.
"""

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
        "connector_id": "conn_agmarknet",
        "name": "AGMARKNET / APMC Mandi Feeds",
        "family": "Market Prices & Arrivals",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 1.2,
        "records_count": 48200,
        "quality_score": 0.98,
        "mode_label": "Live Ingestion (AGMARKNET Daily Gateway)",
        "last_sync": "2026-10-23T18:00:00Z"
    },
    {
        "connector_id": "conn_enam",
        "name": "e-NAM Unified Trade Platform",
        "family": "Electronic Mandi Trades",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 2.5,
        "records_count": 31400,
        "quality_score": 0.96,
        "mode_label": "Production Gateway (e-NAM Integration)",
        "last_sync": "2026-10-23T17:30:00Z"
    },
    {
        "connector_id": "conn_doca",
        "name": "Department of Consumer Affairs (DoCA PMS)",
        "family": "Retail & Wholesale Price Monitoring",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 3.0,
        "records_count": 18200,
        "quality_score": 0.99,
        "mode_label": "Production Gateway (DoCA Real-Time API)",
        "last_sync": "2026-10-23T16:00:00Z"
    },
    {
        "connector_id": "conn_ap_horticulture",
        "name": "AP Department of Horticulture & Agriculture",
        "family": "Acreage, Crop Stage & Yield",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 12.0,
        "records_count": 1250,
        "quality_score": 0.94,
        "mode_label": "Integrated SCM (State Horticulture Dept)",
        "last_sync": "2026-10-23T06:00:00Z"
    },
    {
        "connector_id": "conn_imd",
        "name": "India Meteorological Department (IMD)",
        "family": "Weather, Monsoon & Extreme Rainfall",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 2.0,
        "records_count": 14600,
        "quality_score": 0.97,
        "mode_label": "Automated Telemetry (IMD Radar Grid)",
        "last_sync": "2026-10-23T18:30:00Z"
    },
    {
        "connector_id": "conn_nafed",
        "name": "NAFED / NCCF Central Buffer Stock",
        "family": "Price Stabilisation Fund (PSF)",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 4.5,
        "records_count": 480,
        "quality_score": 0.99,
        "mode_label": "Verified Ledger (NAFED/NCCF PSF Buffer)",
        "last_sync": "2026-10-23T15:00:00Z"
    },
    {
        "connector_id": "conn_civil_supplies",
        "name": "AP Civil Supplies SCM & ePOS Rythu Bazaars",
        "family": "Public Distribution & Subsidised Counters",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 1.5,
        "records_count": 62000,
        "quality_score": 0.99,
        "mode_label": "Active SCM (AP ePOS Rythu Bazaars)",
        "last_sync": "2026-10-23T18:15:00Z"
    },
    {
        "connector_id": "conn_logistics",
        "name": "South Central Railway & Interstate Freight TMS",
        "family": "Freight Rakes & Truck Convoys",
        "status": "ONLINE_ACTIVE",
        "freshness_hours": 2.8,
        "records_count": 8900,
        "quality_score": 0.95,
        "mode_label": "Live Waybills (South Central Railway Freight)",
        "last_sync": "2026-10-23T17:00:00Z"
    }
]
