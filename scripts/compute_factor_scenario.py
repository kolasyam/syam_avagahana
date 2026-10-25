"""
Isolated factor-scenario compute worker
=======================================
Runs the REAL covariate-conditioned Chronos-2 re-forecast in a SEPARATE
process. Reason (demo-critical): on the 7.3 GB demo box a native torch
crash under RAM pressure killed the whole uvicorn server mid-SSE twice.
By isolating inference, a crash costs only this worker — the API server
and the chat session stay alive, and the tool reports an honest PARTIAL.

    python scripts/compute_factor_scenario.py \
        --geography state_andhra_pradesh \
        --variable precipitation_mm \
        --future-value 150 \
        --horizon 30 \
        --out "<path-to-result.json>"

Writes the scenario result dict as JSON to --out (never stdout: torch /
transformers emit noise on stdout). Exit code 1 + PARTIAL JSON on any
failure, so the caller can still surface a truthful reason.
"""

import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Offline + safe threading: the child must not touch the network and must
# not multiply native thread buffers on the low-RAM demo box.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("CHRONOS_TORCH_THREADS", "4")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geography", required=True)
    parser.add_argument("--variable", required=True)
    parser.add_argument("--future-value", type=float, required=True)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    fail = {"status": "PARTIAL", "reason": None, "variable": args.variable,
            "future_value": args.future_value, "geography_id": args.geography,
            "isolated": True}
    try:
        import gc
        import pandas as pd

        from app.core.database import SessionLocal
        from app.core.config import settings
        from app.domain.models import ExternalObservation, MarketObservation
        from app.forecasting.chronos_adapter import Chronos2FoundationModel
        from app.chat.tools import _served_forecast

        result = {
            "status": "OK",
            "source": f"Chronos-2 re-forecast conditioned on {args.variable}={args.future_value} (real model)",
            "variable": args.variable,
            "future_value": args.future_value,
            "geography_id": args.geography,
            "isolated": True,
        }
        with SessionLocal() as db:
            served = _served_forecast(db, args.geography, min(args.horizon, 30)) \
                or _served_forecast(db, args.geography, 30)
            rows = db.query(MarketObservation).filter(
                MarketObservation.commodity_id == settings.PILOT_COMMODITY_ID,
                MarketObservation.geography_id == args.geography,
            ).order_by(MarketObservation.date.asc()).all()
            hist = db.query(ExternalObservation).filter(
                ExternalObservation.geography_id == args.geography,
                ExternalObservation.variable_name == args.variable,
            ).order_by(ExternalObservation.date.asc()).all()

        if served is None:
            fail["reason"] = "No cached baseline forecast to diff against."
            raise RuntimeError(fail["reason"])
        if not rows:
            fail["reason"] = f"No ingested price rows for {args.geography}."
            raise RuntimeError(fail["reason"])
        if not hist:
            fail["reason"] = f"No history rows for {args.variable} in {args.geography}."
            raise RuntimeError(fail["reason"])

        # Same RAM guard as before: 300-day conditioning context is enough for
        # a what-if sensitivity and keeps native memory far below the crash
        # cliff observed with the full multi-year frame.
        rows = rows[-300:]
        price_df = pd.DataFrame([{"date": r.date, "modal_price": r.modal_price} for r in rows])
        factor_df = pd.DataFrame([{"date": h.date, "factor": h.value} for h in hist])
        merged = price_df.merge(factor_df, on="date", how="left")
        merged["factor"] = merged["factor"].ffill().bfill().fillna(merged["factor"].median())

        last_date = pd.to_datetime(merged["date"]).max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1), periods=args.horizon, freq="D")
        future_df = pd.DataFrame(
            {"date": future_dates.strftime("%Y-%m-%d"), "factor": float(args.future_value)})

        gc.collect()
        adapter = Chronos2FoundationModel()
        points = adapter.predict(merged, args.horizon, future_df=future_df)

        baseline_points = served["points"]
        n = min(len(baseline_points), args.horizon)
        baseline = [p["predicted_modal"] for p in baseline_points[:n]]
        scenario = [p["predicted_modal"] for p in points[:n]]
        deltas = [round(s - b, 2) for s, b in zip(scenario, baseline)]
        avg_delta = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
        base_avg = round(sum(baseline) / len(baseline), 2)
        scen_avg = round(sum(scenario) / len(scenario), 2)
        pct = round(avg_delta / max(1e-9, sum(baseline) / len(baseline)) * 100.0, 1)

        result.update({
            "baseline_avg_modal": base_avg,
            "scenario_avg_modal": scen_avg,
            "avg_delta_inr_kg": avg_delta,
            "avg_delta_pct": pct,
            "scenario_points": points,
            "presentation_hints": {
                "summary": (
                    f"Quote exactly: conditioned on {args.variable}={args.future_value}, the "
                    f"{args.horizon}-day ONION modal-price scenario average moves from "
                    f"₹{base_avg}/kg (baseline) to ₹{scen_avg}/kg — "
                    f"Δ ₹{avg_delta}/kg ({pct}%), from a real Chronos-2 re-forecast. "
                    "Mention onion only."
                ),
            },
            "note": "What-if sensitivity using the real foundation model; not a socio-economic guarantee.",
        })
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return 0

    except BaseException as exc:  # noqa: BLE001 — the worker must always leave a truthful receipt
        fail["reason"] = f"{type(exc).__name__}: {exc}"
        fail["answer_protocol"] = (
            "Report the PARTIAL status and reason only. You must NOT claim any numeric "
            "effect on the forecast."
        )
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(fail, f, ensure_ascii=False)
        except OSError:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
