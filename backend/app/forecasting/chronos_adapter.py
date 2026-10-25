"""
Amazon Chronos-2 Foundation Model Adapter — REAL MODEL
======================================================
This module runs the actual pretrained Amazon Chronos-2 time-series foundation
model (Apache-2.0 license, production-safe) on the ingested real series.

Dependencies (install first):
    pip install "chronos-forecasting>=2.0" torch
Model weights are fetched once from the Hugging Face hub and cached locally
(pre-download for offline demo):
    huggingface-cli download amazon/chronos-2   (or snapshot_download)

Contract: predict() returns the same point-dictionary schema as
tabular_model.AutoregressiveCovariateModel.predict() so all downstream
consumers (forecast API, agents, risk, tests) keep working:
    {date, predicted_modal, lower_80, upper_80, lower_95, upper_95}

Honesty rules:
  - If weights/package are unavailable, we raise ChronosUnavailableError.
    Callers fall back to the Ridge AR-Lag model and MUST label it as a
    fallback ("AR-Lag (FALLBACK)") — never as Chronos.
  - No synthetic "zero-shot simulation" strings. The model card metadata
    below reflects what actually runs.
"""

import logging
import math
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("chronos_adapter")

MODEL_ID = "amazon/chronos-2"
QUANTILE_LEVELS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

# Inference context cap (days). Chronos-2 handles long histories, but on
# RAM/CPU-constrained demo machines the attention cost grows super-linearly
# with context length. The most recent year is standard zero-shot practice;
# full-context runs can opt out with CHRONOS_MAX_CONTEXT_DAYS=0.
def _context_cap() -> int:
    try:
        return int(os.getenv("CHRONOS_MAX_CONTEXT_DAYS", "365"))
    except ValueError:
        return 365


def _cap_context(df: pd.DataFrame, column: str = "date") -> pd.DataFrame:
    cap = _context_cap()
    if cap and column in df.columns and len(df) > cap:
        return df.tail(cap).reset_index(drop=True)
    return df


def _cap_frame(frame: pd.DataFrame) -> pd.DataFrame:
    cap = _context_cap()
    if cap and "date" in frame.columns:
        # per-item capping for stacked multi-item frames
        capped = frame.groupby("id", sort=False).tail(cap)
        return capped.reset_index(drop=True)
    return frame


def _regularize_daily(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures a contiguous daily grid for Chronos-2's frequency inference.
    AGMARKNET state series miss calendar days (holidays/closures); the DB
    keeps raw gaps, but the MODEL CONTEXT must be regular. Forward-fill
    (standard price-series practice) + backfill for any leading gap.
    """
    if "date" not in frame.columns or frame.empty:
        return frame
    out = frame.drop_duplicates(subset=["date"], keep="first")
    out = (
        out.set_index("date")
        .asfreq("D")
        .assign(price=lambda d: d["price"].ffill().bfill())
        .ffill()
        .bfill()
        .reset_index()
    )
    return out


class ChronosUnavailableError(RuntimeError):
    """Raised when the Chronos-2 package or weights cannot be loaded."""


class Chronos2FoundationModel:
    """
    Adapter for the real Amazon Chronos-2 pretrained model.

    status / candidate flags are now truthful: this is the champion model,
    no longer an 'experimental candidate' facade.
    """

    _pipeline = None   # lazy singleton across the process
    _device = "cpu"

    def __init__(self, model_variant: str = MODEL_ID):
        self.model_variant = model_variant
        self.is_candidate = False
        self.status_label = "PRETRAINED CHRONOS-2 — REAL ZERO-SHOT INFERENCE"
        self.architecture = (
            "Time-series foundation model (T5-style encoder-decoder, patch tokens), "
            "trained on large curated corpora; zero-shot probabilistic inference."
        )

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #

    @classmethod
    def get_pipeline(cls):
        if cls._pipeline is None:
            try:
                import torch
                from chronos import Chronos2Pipeline
            except ImportError as exc:
                raise ChronosUnavailableError(
                    f"chronos-forecasting / torch not installed ({exc}). "
                    'Run: pip install "chronos-forecasting>=2.0" torch'
                ) from exc

            allow_download = os.getenv("CHRONOS_ALLOW_DOWNLOAD", "false").lower() in ("1", "true", "yes")
            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            # Thread cap for low-RAM demo boxes: each native torch thread holds
            # workspace buffers; more threads = more RAM. Override with
            # CHRONOS_TORCH_THREADS (default 4 = balanced CPU inference).
            try:
                torch.set_num_threads(max(1, int(os.getenv("CHRONOS_TORCH_THREADS", "4"))))
            except Exception:
                torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))

            # LOCAL-ONLY first: request paths must never block on a hub download
            # (that froze live endpoints). Pre-cache weights with:
            #   huggingface-cli download amazon/chronos-2
            # Opt-in network fetch with CHRONOS_ALLOW_DOWNLOAD=true.
            load_errors = []
            try:
                try:
                    cls._pipeline = Chronos2Pipeline.from_pretrained(
                        MODEL_ID,
                        local_files_only=True,
                        device_map="cuda" if cls._device == "cuda" else "cpu",
                    )
                except (TypeError, ValueError):
                    cls._pipeline = Chronos2Pipeline.from_pretrained(
                        MODEL_ID, local_files_only=True
                    )
                logger.info("Chronos-2 loaded from local cache (%s).", cls._device)
            except Exception as local_exc:
                load_errors.append(f"local: {local_exc}")
                if allow_download:
                    try:
                        try:
                            cls._pipeline = Chronos2Pipeline.from_pretrained(
                                MODEL_ID,
                                device_map="cuda" if cls._device == "cuda" else "cpu",
                            )
                        except (TypeError, ValueError):
                            cls._pipeline = Chronos2Pipeline.from_pretrained(MODEL_ID)
                        logger.info("Chronos-2 downloaded and loaded (%s).", cls._device)
                    except Exception as net_exc:
                        load_errors.append(f"network: {net_exc}")
                raise ChronosUnavailableError(
                    f"Could not load Chronos-2 weights '{MODEL_ID}' ({'; '.join(load_errors)}). "
                    "Pre-download for offline demo: huggingface-cli download amazon/chronos-2"
                ) from local_exc
        return cls._pipeline

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._pipeline is not None

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    def predict(
        self,
        df: pd.DataFrame,
        horizon: int,
        item_id: str = "onion_ap",
        future_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, object]]:
        """
        Runs REAL Chronos-2 inference on the modal price series.

        df: expects columns ['date' (ISO string or datetime), 'modal_price'].
            Optional known-covariate future can be supplied via future_df
            (used later by the chat add-factor flow).
        horizon: number of daily steps to forecast.
        """
        pipeline = self.get_pipeline()

        context_df = pd.DataFrame({
            "id": item_id,
            "date": pd.to_datetime(df["date"]),
            "price": df["modal_price"].astype(float).values,
        })
        # When conditioning on a covariate (chat add-factor flow), the context
        # must CARRY the historical covariate column so predict_df can align it
        # with the future_df values.
        has_factor = future_df is not None and "factor" in df.columns
        if has_factor:
            context_df["factor"] = df["factor"].astype(float).values
        context_df = _cap_context(context_df, "date")
        context_df = _regularize_daily(context_df)

        kwargs: Dict[str, object] = {
            "prediction_length": int(horizon),
            "quantile_levels": QUANTILE_LEVELS,
        }
        if future_df is not None:
            fdf = future_df.copy()
            fdf["date"] = pd.to_datetime(fdf["date"])
            if "id" not in fdf.columns:
                fdf["id"] = item_id
            kwargs["future_df"] = fdf

        try:
            out = pipeline.predict_df(
                context_df,
                id_column="id",
                timestamp_column="date",
                target="price",
                **kwargs,
            )
        except TypeError:
            # API drift fallback: omit explicit column naming
            out = pipeline.predict_df(context_df, **kwargs)

        quantiles, medians = self._extract_quantile_columns(out, item_id)
        if medians is None or len(medians) < horizon:
            raise ChronosUnavailableError(
                f"Chronos-2 returned unexpected output shape for horizon {horizon}: "
                f"columns={list(out.columns)}"
            )

        # Our own independent date axis: day 1 = last observation + 1
        last_date = pd.to_datetime(df["date"]).max()
        dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

        l05, l10 = quantiles.get(0.05), quantiles.get(0.10)
        l90, l95 = quantiles.get(0.90), quantiles.get(0.95)

        points: List[Dict[str, object]] = []
        for i in range(min(horizon, len(medians))):
            med = float(medians[i])
            lower80 = float(l10[i]) if l10 is not None else med
            upper80 = float(l90[i]) if l90 is not None else med
            lower95 = float(l05[i]) if l05 is not None else lower80
            upper95 = float(l95[i]) if l95 is not None else upper80
            points.append({
                "date": dates[i].strftime("%Y-%m-%d"),
                "predicted_modal": round(med, 2),
                "lower_80": round(lower80, 2),
                "upper_80": round(upper80, 2),
                "lower_95": round(lower95, 2),
                "upper_95": round(upper95, 2),
            })
        return points

    def predict_multi(
        self,
        series_by_id: Dict[str, pd.DataFrame],
        horizon: int,
    ) -> Dict[str, List[Dict[str, object]]]:
        """
        Batched multi-item inference in a single pipeline call
        (context rows stacked long-form with an `id` column each).
        """
        pipeline = self.get_pipeline()
        frames = []
        for item_id, df in series_by_id.items():
            f = pd.DataFrame({
                "id": item_id,
                "date": pd.to_datetime(df["date"]),
                "price": df["modal_price"].astype(float).values,
            })
            f = _cap_context(f, "date")
            f = _regularize_daily(f)
            frames.append(f)
        context_df = pd.concat(frames, ignore_index=True)

        out = pipeline.predict_df(
            context_df,
            prediction_length=int(horizon),
            quantile_levels=QUANTILE_LEVELS,
        )

        results: Dict[str, List[Dict[str, object]]] = {}
        last_dates = {
            item_id: pd.to_datetime(df["date"]).max()
            for item_id, df in series_by_id.items()
        }
        for item_id in series_by_id:
            sub = out[out["id"] == item_id] if "id" in out.columns else out
            quantiles, medians = self._extract_quantile_columns(sub, item_id)
            if medians is None or len(medians) < horizon:
                raise ChronosUnavailableError(
                    f"Chronos-2 batch output invalid for {item_id}: columns={list(sub.columns)}"
                )
            dates = pd.date_range(
                start=last_dates[item_id] + pd.Timedelta(days=1),
                periods=horizon, freq="D",
            )
            l05, l10 = quantiles.get(0.05), quantiles.get(0.10)
            l90, l95 = quantiles.get(0.90), quantiles.get(0.95)
            results[item_id] = [{
                "date": dates[i].strftime("%Y-%m-%d"),
                "predicted_modal": round(float(medians[i]), 2),
                "lower_80": round(float(l10[i]) if l10 is not None else medians[i], 2),
                "upper_80": round(float(l90[i]) if l90 is not None else medians[i], 2),
                "lower_95": round(float(l05[i]) if l05 is not None else (l10[i] if l10 is not None else medians[i]), 2),
                "upper_95": round(float(l95[i]) if l95 is not None else (l90[i] if l90 is not None else medians[i]), 2),
            } for i in range(min(horizon, len(medians)))]
        return results

    # ------------------------------------------------------------------ #
    # Output parsing (robust to API-format drift across releases)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_quantile_columns(
        out: pd.DataFrame, item_id: str
    ):
        """
        Returns ({quantile: np.array}, median_array_or_None).
        Tolerates columns named '0.5', 'q0.5', 'p50', 'median', 'mean'.
        """
        q_map: Dict[float, np.ndarray] = {}
        median_arr = None
        mean_arr = None

        named = {"median": 0.50}
        skip_names = {"id", "target", "date", "timestamp", "item", "step", "obs"}

        for col in out.columns:
            if str(col).lower() in skip_names:
                continue
            try:
                values = np.asarray(out[col], dtype=float)
            except (ValueError, TypeError):
                continue  # non-numeric column (timestamps, labels)
            if np.isnan(values).all() or values.ndim > 1:
                continue
            # explicit float-named quantile columns: "0.05" .. "0.95"
            try:
                q = float(col)
            except (TypeError, ValueError):
                key = str(col).lower().lstrip("qp")
                if str(col).lower() in named:
                    q = named[str(col).lower()]
                elif key.replace(".", "").isdigit() and 0 < float(key) < 1:
                    q = float(key)
                elif str(col).lower() == "median":
                    q = 0.50
                elif str(col).lower() in ("mean", "mean_forecast", "forecast", "point"):
                    mean_arr = values
                    continue
                else:
                    continue
            if 0.0 < q < 1.0:
                q_map[q] = values

        if 0.50 in q_map:
            median_arr = q_map[0.50]
        elif mean_arr is not None:
            median_arr = mean_arr
        elif q_map:
            nearest_q = min(q_map.keys(), key=lambda v: abs(v - 0.5))
            median_arr = q_map[nearest_q]

        return q_map, median_arr


# Backward-compatible alias so existing imports keep working.
Chronos2CandidateAdapter = Chronos2FoundationModel  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Breach probability from the quantile ladder (no extra training required)
# --------------------------------------------------------------------------- #

def estimate_exceedance_probability(
    quantile_ladder: List[tuple],
    threshold: float,
) -> float:
    """
    Estimate P(value > threshold) from a quantile ladder
    [(q, value), ...] ascending in q, e.g. Chronos-2's daily quantile row.

    Method: explain via the crossing quantile — for the q-quantile v_q,
    P(value <= v_q) = q. Linear interpolation between the two ladder
    points that bracket the threshold yields q_cross; P(exceed) = 1 - q_cross.
    """
    if not quantile_ladder:
        return 0.0
    ladder = sorted(quantile_ladder, key=lambda t: t[0])

    # Threshold above the highest quantile value -> exceedance can't be pinned
    # from the ladder; cap at the residual between 1 and top quantile.
    if threshold >= ladder[-1][1]:
        # Above the 0.95 quantile: exceedance <= 0.05, estimate residual/2.
        return round(max(0.0, (1.0 - ladder[-1][0]) / 2.0), 4)
    if threshold <= ladder[0][1]:
        # Below the 0.05 quantile: exceedance >= 0.95 (conservative floor).
        return round(min(1.0, 1.0 - ladder[0][0]), 4)

    for (q0, v0), (q1, v1) in zip(ladder, ladder[1:]):
        if v0 <= threshold <= v1:
            if v1 == v0:
                q_cross = (q0 + q1) / 2
            else:
                q_cross = q0 + (q1 - q0) * (threshold - v0) / (v1 - v0)
            return round(max(0.0, min(1.0, 1.0 - q_cross)), 4)
    return round(0.0 if threshold > ladder[-1][1] else 1.0, 4)


def daily_exceedance_probabilities(
    points: List[Dict[str, object]],
    threshold: float,
) -> List[float]:
    """
    Vector helper: per forecast day, P(price > threshold) using the
    0.05/0.10/median/0.90/0.95 ladder stored in each point dict.
    """
    probs = []
    for pt in points:
        ladder = [
            (0.05, pt.get("lower_95", pt.get("lower_80"))),
            (0.10, pt.get("lower_80")),
            (0.50, pt.get("predicted_modal")),
            (0.90, pt.get("upper_80")),
            (0.95, pt.get("upper_95", pt.get("upper_80"))),
        ]
        ladder = [(q, float(v)) for q, v in ladder if v is not None]
        probs.append(estimate_exceedance_probability(ladder, threshold))
    return probs


def probability_sheet(points: List[Dict[str, object]], alert: float, crisis: float) -> Dict[str, object]:
    """
    Aggregated dynamic risk sheet (replaces old hardcoded 0.88 defaults):
      - alert/crisis exceedance at day 30 and horizon end
      - max daily exceedance within first 30 days, and first median breach day
    """
    if not points:
        return {}

    alert_probs = daily_exceedance_probabilities(points, alert)
    crisis_probs = daily_exceedance_probabilities(points, crisis)
    h = len(points)

    def at_day(probs, day):
        idx = min(day, h) - 1
        return probs[idx]

    first_alert_day = next((i + 1 for i, p in enumerate(alert_probs) if p > 0.5), None)
    first_crisis_day = next((i + 1 for i, p in enumerate(crisis_probs) if p > 0.5), None)

    return {
        "alert_threshold": alert,
        "crisis_threshold": crisis,
        "horizon_days": h,
        "alert_exceedance": {
            "day7": at_day(alert_probs, 7),
            "day30": at_day(alert_probs, 30) if h >= 30 else at_day(alert_probs, h),
            "horizon_end": alert_probs[-1],
            "max_within_30d": max(alert_probs[: min(30, h)], default=0.0),
        },
        "crisis_exceedance": {
            "day7": at_day(crisis_probs, 7),
            "day30": at_day(crisis_probs, 30) if h >= 30 else at_day(crisis_probs, h),
            "horizon_end": crisis_probs[-1],
            "max_within_30d": max(crisis_probs[: min(30, h)], default=0.0),
        },
        "first_median_breach_day_alert": first_alert_day,
        "first_median_breach_day_crisis": first_crisis_day,
        "method": "Quantile-ladder interpolation over Chronos-2 forecast distribution",
    }


# Silence unused-import lint for math (kept for parity with potential future use)
_ = math
