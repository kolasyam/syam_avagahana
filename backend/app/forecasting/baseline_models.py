"""
Deterministic Baseline Forecasting Models
Seasonal-Naive, Rolling-Average, and Exponential Smoothing baselines as required by Section 2.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class SeasonalNaiveForecast:
    """Predicts future prices using seasonal repetition (default 7-day week cycle)."""
    def __init__(self, season_length: int = 7):
        self.season_length = season_length

    def predict(self, series: List[float], horizon: int) -> List[float]:
        if len(series) < self.season_length:
            last_val = series[-1] if series else 25.0
            return [last_val] * horizon
            
        preds = []
        recent_season = series[-self.season_length:]
        for i in range(horizon):
            preds.append(recent_season[i % self.season_length])
        return preds

class ExponentialSmoothingForecast:
    """Simple Exponential Smoothing with trend damping."""
    def __init__(self, alpha: float = 0.35, beta: float = 0.15):
        self.alpha = alpha
        self.beta = beta

    def predict(self, series: List[float], horizon: int) -> List[float]:
        if not series:
            return [25.0] * horizon
        if len(series) == 1:
            return [series[0]] * horizon

        level = series[0]
        trend = series[1] - series[0]
        
        for val in series[1:]:
            last_level = level
            level = self.alpha * val + (1 - self.alpha) * (level + trend)
            trend = self.beta * (level - last_level) + (1 - self.beta) * trend

        preds = []
        # Dampen trend over horizon to prevent explosive extrapolation
        damping = 0.90
        for h in range(1, horizon + 1):
            pred = level + trend * sum(damping ** i for i in range(1, h + 1))
            preds.append(round(pred, 2))
        return preds
