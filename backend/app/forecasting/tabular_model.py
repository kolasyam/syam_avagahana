"""
Autoregressive Tabular Model with Covariates (Arrivals & Weather)
Predicts multi-horizon price points with empirical uncertainty bounds.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

class AutoregressiveCovariateModel:
    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.fitted = False
        self.residual_std = 1.45

    def _build_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Engineers lag and rolling features from historical dataframe."""
        df = df.copy().sort_values("date").reset_index(drop=True)
        prices = df["modal_price"].values
        arrivals = df["arrivals_mt"].values if "arrivals_mt" in df.columns else np.zeros(len(prices))
        
        X, y = [], []
        # Need at least 14 days of history for lag features
        for i in range(14, len(prices)):
            feats = [
                prices[i - 1],             # lag 1
                prices[i - 2],             # lag 2
                prices[i - 7],             # lag 7
                prices[i - 14],            # lag 14
                np.mean(prices[i - 7:i]),   # 7-day mean
                arrivals[i - 1],           # recent arrivals
                arrivals[i - 7] if i >= 7 else arrivals[i - 1], # 7-day prior arrivals
            ]
            X.append(feats)
            y.append(prices[i])
            
        return np.array(X), np.array(y)

    def fit(self, df: pd.DataFrame):
        X, y = self._build_features(df)
        if len(X) >= 10:
            self.model.fit(X, y)
            preds = self.model.predict(X)
            residuals = y - preds
            self.residual_std = max(float(np.std(residuals)), 0.8)
            self.fitted = True

    def predict(self, df: pd.DataFrame, horizon: int) -> List[Dict[str, Any]]:
        """Multi-step recursive forecasting with expanding uncertainty."""
        if not self.fitted:
            self.fit(df)
            
        df = df.copy().sort_values("date").reset_index(drop=True)
        recent_prices = list(df["modal_price"].values)
        recent_arrivals = list(df["arrivals_mt"].values if "arrivals_mt" in df.columns else [300.0] * len(recent_prices))
        
        last_date = pd.to_datetime(df["date"].iloc[-1])
        output = []

        hist_mean = float(np.mean(df["modal_price"].values))

        for step in range(1, horizon + 1):
            target_date = (last_date + pd.Timedelta(days=step)).strftime("%Y-%m-%d")
            
            # Extract features for step
            idx = len(recent_prices)
            feats = np.array([[
                recent_prices[idx - 1],
                recent_prices[idx - 2],
                recent_prices[idx - 7],
                recent_prices[idx - 14],
                np.mean(recent_prices[idx - 7:idx]),
                recent_arrivals[idx - 1],
                recent_arrivals[idx - 7]
            ]])
            
            pred_raw = float(self.model.predict(feats)[0])
            
            # Econometric Damping / Mean-Reversion for Recursive Multi-Step Horizons
            # Short horizons (1-14 days) preserve high local autoregressive fidelity
            # Medium to long horizons (15-90 days) smoothly mean-revert toward seasonal equilibrium
            if step <= 14:
                weight = 1.0 - (step / 80.0)
            else:
                weight = max(0.20, 1.0 - (step / 45.0))
                
            pred = weight * pred_raw + (1.0 - weight) * hist_mean
            pred = round(min(max(pred, 16.0), 52.0), 2)
            
            # Append recursive prediction
            recent_prices.append(pred)
            # Arrivals trend assumption
            recent_arrivals.append(recent_arrivals[-1])
            
            # Uncertainty interval expands with square root of forecast step
            step_uncertainty = self.residual_std * np.sqrt(step)
            unc_80 = round(1.28 * step_uncertainty, 2)
            unc_95 = round(1.96 * step_uncertainty, 2)
            
            output.append({
                "date": target_date,
                "predicted_modal": pred,
                "lower_80": round(max(pred - unc_80, 5.0), 2),
                "upper_80": round(pred + unc_80, 2),
                "lower_95": round(max(pred - unc_95, 5.0), 2),
                "upper_95": round(pred + unc_95, 2),
            })
            
        return output
