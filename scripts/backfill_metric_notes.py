"""
One-off: post-hoc backfill of selection_rule + honest_notes into forecast_metrics.json
(same fields as app.forecasting.backtest now emits on future runs).
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

PATH = r"backend/app/forecasting/forecast_metrics.json"

SEL_RULE = (
    "Champion selection requires calibrated quantile intervals (risk-engine dependency) "
    "alongside competitive point accuracy; point-only models (Seasonal-Naive, Exponential "
    "Smoothing) are excluded from selection by design."
)

with open(PATH, "r", encoding="utf-8") as fh:
    store = json.load(fh)

for geo, geo_block in store.get("by_geography", {}).items():
    for hkey, block in geo_block.items():
        models = block.get("models", [])
        champ = next((m for m in models if m.get("is_champion")), None)
        notes = []
        if models and champ is not None:
            best = min(models, key=lambda m: m["mae"])
            if best["model_name"] != champ["model_name"]:
                notes.append(
                    f"{best['model_name']} posts the lowest point error (MAE "
                    f"₹{best['mae']}/kg vs champion ₹{champ['mae']}/kg) but emits no calibrated "
                    "interval — the production champion must produce quantile bands because "
                    "the risk engine and probability sheet depend on them."
                )
        cov80 = (champ or {}).get("interval_80_coverage_pct")
        if cov80 is not None and cov80 < 70:
            notes.append(
                f"Champion's 80% band under-covered in this fold mix ({cov80}%). For buffer "
                "planning at this horizon, plan on the 95% band until district-level features "
                "enable retraining."
            )
        block["selection_rule"] = SEL_RULE
        block["honest_notes"] = notes
        print(f"{geo} h={hkey} | notes: {len(notes)}")

with open(PATH, "w", encoding="utf-8") as fh:
    json.dump(store, fh, indent=2)

print("patched OK")
