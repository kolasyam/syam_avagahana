"""
Integration Tests for FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "demo_mode" in data
    assert isinstance(data["demo_mode"], bool)

def test_get_geographies():
    res = client.get("/api/v1/reference/geographies")
    assert res.status_code == 200
    geos = res.json()
    assert len(geos) >= 5
    assert any(g["id"] == "mandi_kurnool" for g in geos)

def test_get_commodities():
    res = client.get("/api/v1/reference/commodities")
    assert res.status_code == 200
    comms = res.json()
    assert any(c["id"] == "onion" for c in comms)

def test_get_observations():
    res = client.get("/api/v1/observations?commodity_id=onion&geography_id=mandi_kurnool&days=30")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    # Last observation should be close to Slide 8 modal price
    assert data[-1]["modal_price"] > 35.0

def test_get_analytics():
    res = client.get("/api/v1/observations/analytics?commodity_id=onion&geography_id=mandi_kurnool&days=60")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "series" in data
    assert "anomalies" in data

def test_get_latest_forecast():
    res = client.get("/api/v1/forecast/latest?commodity_id=onion&geography_id=mandi_kurnool")
    assert res.status_code == 200
    data = res.json()
    assert len(data["forecast_series"]) > 0

def test_get_latest_risk():
    res = client.get("/api/v1/risk/latest?commodity_id=onion&geography_id=mandi_kurnool")
    assert res.status_code == 200
    data = res.json()
    assert data["spike_probability"] > 0.5
    assert len(data["primary_drivers"]) > 0

def test_get_sources():
    res = client.get("/api/v1/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 6
    assert any("AGMARKNET" in s["name"] for s in sources)
