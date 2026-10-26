# 5 Forecast-Only Demo Questions (Chronos-2 backbone — no DB-only, no pure web)
# For CEO rehearsal — each hits ForecastAgent / Chronos-2 / RiskAgent / ScenarioAgent.

1. "Give me the 30-day onion price forecast for Andhra Pradesh and the breach risk."
   → run_forecast(30) + probability_sheet (alert 49.8%, crisis 9.7% verbatim)

2. "What is the 60-day outlook for AP onion prices — point forecast and 80% band?"
   → run_forecast(60) (real Chronos-2, 60-day conditioning context)

3. "If rainfall next month is 150 mm, what happens to AP onion prices over 30 days? Add it as a factor."
   → forecast_with_factor(precipitation_mm=150, horizon=30) + scenario cache
   → expected: Δ ₹5.92/kg (+17.6%), ₹33.65 → ₹39.57

4. "Compare AP's 30-day forecast with Maharashtra — which has the lower crisis breach probability?"
   → run_forecast(AP, 30) + run_forecast(MH, 30) + get_risk (headroom comparison)

5. "Why should I trust the forecast numbers? Show me the model name, the data cutoff, and the backtest selection rule."
   → audit frame inspection (model_name=Amazon Chronos-2, status=CHRONOS2_REAL,
     cutoff=2026-10-15, selection_rule from forecast_metrics.json)
