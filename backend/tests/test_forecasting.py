"""
Unit Tests for Forecasting Models and Backtesting
"""

import pytest
import pandas as pd
import numpy as np
from app.forecasting.baseline_models import SeasonalNaiveForecast, ExponentialSmoothingForecast
from app.forecasting.tabular_model import AutoregressiveCovariateModel
from app.forecasting.chronos_adapter import Chronos2CandidateAdapter
from app.forecasting.backtest import evaluate_models_backtest

def test_seasonal_naive():
    model = SeasonalNaiveForecast(season_length=7)
    history = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0] * 3
    preds = model.predict(history, horizon=14)
    assert len(preds) == 14
    assert preds[0] == 20.0
    assert preds[6] == 26.0
    assert preds[7] == 20.0

def test_exponential_smoothing():
    model = ExponentialSmoothingForecast()
    history = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
    preds = model.predict(history, horizon=7)
    assert len(preds) == 7
    assert all(p > 0 for p in preds)
    # Upward trend should be preserved
    assert preds[-1] >= preds[0]

def test_autoregressive_covariate_model():
    model = AutoregressiveCovariateModel()
    dates = pd.date_range("2026-06-01", periods=60)
    prices = [22.0 + np.sin(i / 5.0) * 3.0 + (i * 0.1) for i in range(60)]
    arrivals = [350.0 - (i * 1.5) for i in range(60)]
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "modal_price": prices, "arrivals_mt": arrivals})

    preds = model.predict(df, horizon=14)
    assert len(preds) == 14
    for p in preds:
        assert "predicted_modal" in p
        assert p["lower_80"] <= p["predicted_modal"] <= p["upper_80"]
        assert p["lower_95"] <= p["lower_80"]
        assert p["upper_95"] >= p["upper_80"]

def test_chronos_adapter_contract():
    """The adapter is the REAL pretrained Chronos-2 model (no more fake candidate
    facade). Real inference requires locally cached weights; the contract test
    skips gracefully when they're absent (CI-safe), never fakes output."""
    adapter = Chronos2CandidateAdapter()  # alias of Chronos2FoundationModel
    # Honesty contract: this is a real model now, no "experimental candidate" theater
    assert adapter.is_candidate is False
    assert "candidate" not in adapter.status_label.lower()

    pytest.importorskip("chronos")
    pytest.importorskip("torch")
    dates = pd.date_range("2026-06-01", periods=30)
    prices = [25.0 + (i * 0.2) for i in range(30)]
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "modal_price": prices, "arrivals_mt": [300.0]*30})
    try:
        res = adapter.predict(df, horizon=7)
    except Exception as exc:
        if "weights" in str(exc).lower() or "load" in str(exc).lower() or "Could not load" in str(exc):
            pytest.skip(f"Chronos-2 weights not cached locally: {exc}")
        raise
    assert len(res) == 7
    for p in res:
        assert "date" in p and "predicted_modal" in p
        assert p["lower_80"] <= p["predicted_modal"] <= p["upper_80"]
        assert p["lower_95"] <= p["lower_80"]
        assert p["upper_95"] >= p["upper_80"]

def test_rolling_origin_backtest():
    dates = pd.date_range("2026-06-01", periods=50)
    prices = [20.0 + (i * 0.15) for i in range(50)]
    obs = [{"date": d.strftime("%Y-%m-%d"), "modal_price": p, "arrivals_mt": 300.0} for d, p in zip(dates, prices)]
    report = evaluate_models_backtest(obs, horizon=7)
    assert report["status"] == "COMPLETED"
    assert len(report["models"]) >= 2
    for m in report["models"]:
        assert m["mae"] >= 0.0
        assert m["rmse"] >= 0.0
