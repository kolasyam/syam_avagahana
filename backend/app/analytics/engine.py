"""
Deterministic Market Analytics Engine
Calculates moving averages, volatility, mandi price dispersion, arrival-price elasticity,
and statistical anomaly flags without external LLM invention.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd

def compute_market_analytics(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Given a list of chronological daily observations, calculate core analytics."""
    if not observations:
        return {
            "summary": {},
            "moving_averages": [],
            "volatility": 0.0,
            "anomalies": [],
            "arrival_price_correlation": 0.0
        }
    
    df = pd.DataFrame(observations)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # Rolling moving averages
    df["ma_7"] = df["modal_price"].rolling(window=7, min_periods=1).mean().round(2)
    df["ma_14"] = df["modal_price"].rolling(window=14, min_periods=1).mean().round(2)
    df["ma_30"] = df["modal_price"].rolling(window=30, min_periods=1).mean().round(2)
    
    # Volatility (30-day rolling standard deviation)
    df["volatility_30"] = df["modal_price"].rolling(window=14, min_periods=2).std().fillna(0.0).round(2)
    
    # Day-on-day change pct
    df["dod_pct"] = (df["modal_price"].pct_change() * 100).fillna(0.0).round(2)
    
    # Statistical anomaly detection (Z-score on 14-day window or |DoD| > 12%)
    anomalies = []
    window = 14
    for i in range(window, len(df)):
        sub = df["modal_price"].iloc[i-window:i]
        mean = sub.mean()
        std = sub.std()
        curr_price = df["modal_price"].iloc[i]
        curr_date = df["date"].iloc[i].strftime("%Y-%m-%d")
        
        if std > 0:
            z_score = abs(curr_price - mean) / std
            if z_score > 2.5 or abs(df["dod_pct"].iloc[i]) > 14.0:
                anomalies.append({
                    "date": curr_date,
                    "price": float(curr_price),
                    "z_score": round(float(z_score), 2),
                    "dod_change_pct": float(df["dod_pct"].iloc[i]),
                    "severity": "CRITICAL" if z_score > 3.0 else "WARNING",
                    "reason": f"Sudden price deviation of {df['dod_pct'].iloc[i]}% (Z-score: {z_score:.1f})"
                })
    
    # Arrival-Price correlation
    corr = 0.0
    if len(df) > 3 and df["arrivals_mt"].std() > 0 and df["modal_price"].std() > 0:
        corr = float(df["arrivals_mt"].corr(df["modal_price"]))
        corr = round(corr, 3)

    latest = df.iloc[-1]
    prev_week = df.iloc[-8] if len(df) >= 8 else df.iloc[0]
    
    summary = {
        "latest_date": latest["date"].strftime("%Y-%m-%d"),
        "latest_modal_price": float(latest["modal_price"]),
        "latest_min_price": float(latest["min_price"]),
        "latest_max_price": float(latest["max_price"]),
        "latest_arrivals_mt": float(latest["arrivals_mt"]),
        "wow_price_change_pct": round(((latest["modal_price"] - prev_week["modal_price"]) / prev_week["modal_price"]) * 100, 2),
        "wow_arrivals_change_pct": round(((latest["arrivals_mt"] - prev_week["arrivals_mt"]) / prev_week["arrivals_mt"]) * 100, 2) if prev_week["arrivals_mt"] > 0 else 0.0,
        "current_volatility": float(latest["volatility_30"]),
        "period_min": float(df["modal_price"].min()),
        "period_max": float(df["modal_price"].max()),
        "period_mean": round(float(df["modal_price"].mean()), 2)
    }
    
    series_out = []
    for _, row in df.iterrows():
        series_out.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "modal_price": float(row["modal_price"]),
            "arrivals_mt": float(row["arrivals_mt"]),
            "ma_7": float(row["ma_7"]),
            "ma_14": float(row["ma_14"]),
            "ma_30": float(row["ma_30"]),
            "volatility": float(row["volatility_30"])
        })
        
    return {
        "summary": summary,
        "series": series_out,
        "anomalies": anomalies,
        "arrival_price_correlation": corr
    }
