"""Export real model and agent results for the static React dashboard."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from agents.demand_analysis import DemandAnalysisAgent
from agents.forecasting import ForecastingAgent
from agents.operations_planning import OperationsPlanningAgent
from config import (
    AVAILABLE_BUSES,
    BUS_CAPACITY,
    FORECAST_HORIZON_HOURS,
    RESERVE_BUSES,
    TARGET_LOAD_FACTOR,
)
from core.data_processing import DEFAULT_DATASET_PATH, load_ridership_data, validate_ridership_data
from core.model_training import METADATA_FILENAME, MODEL_FILENAME

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / MODEL_FILENAME
MODEL_METADATA_PATH = PROJECT_ROOT / "models" / METADATA_FILENAME
OUTPUT_DIRECTORY = PROJECT_ROOT / "frontend" / "public" / "data"


def _json_safe(value: Any) -> Any:
    """Convert pandas, NumPy and non-finite values into JSON-safe values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    return _json_safe(dataframe.to_dict(orient="records"))


def _metadata(
    generated_at: str,
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "dataset": {
            "rows": summary["total_rows"],
            "routes": summary["unique_bus_routes"],
            "timestamps": summary["unique_timestamps"],
            "date_range": {
                "start": summary["minimum_timestamp"],
                "end": summary["maximum_timestamp"],
            },
        },
        "source": "MTA ridership CSV and persisted notebook-derived model",
    }


def _write_json(filename: str, payload: dict[str, Any]) -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / filename).write_text(
        json.dumps(_json_safe(payload), indent=2, allow_nan=False),
        encoding="utf-8",
    )


def export_dashboard_data() -> list[Path]:
    """Run agents in order and export the four dashboard response documents."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Required model artifact is missing: {MODEL_PATH}. "
            "Run 'python -m core.train_model' first."
        )
    if not MODEL_METADATA_PATH.is_file():
        raise FileNotFoundError(
            f"Required model metadata is missing: {MODEL_METADATA_PATH}."
        )

    dataframe = load_ridership_data(DEFAULT_DATASET_PATH)
    summary = validate_ridership_data(dataframe)
    generated_at = datetime.now(timezone.utc).isoformat()
    model = joblib.load(MODEL_PATH)
    model_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))

    route_totals = dataframe.groupby("bus_route")["ridership"].sum()
    active_routes = route_totals[route_totals > 0].index
    active_history = dataframe[dataframe["bus_route"].isin(active_routes)]
    forecast = ForecastingAgent(model, active_history).forecast(
        FORECAST_HORIZON_HOURS
    )
    analysis = DemandAnalysisAgent(dataframe, forecast).analyse()
    operations = OperationsPlanningAgent(
        {
            "available_buses": AVAILABLE_BUSES,
            "reserve_buses": RESERVE_BUSES,
            "bus_capacity": BUS_CAPACITY,
            "target_load_factor": TARGET_LOAD_FACTOR,
        }
    ).plan(forecast, analysis)
    if not operations["summary"]["fleet_constraint_satisfied"]:
        raise ValueError("Fleet allocation violates the configured bus constraint.")

    base_metadata = _metadata(generated_at, summary)
    hourly_forecast = (
        forecast.groupby("transit_timestamp", as_index=False)
        .agg(predicted_ridership=("predicted_ridership", "sum"))
        .sort_values("transit_timestamp")
    )
    historical_hourly = (
        dataframe.groupby("transit_timestamp", as_index=False)
        .agg(actual_ridership=("ridership", "sum"))
        .sort_values("transit_timestamp")
        .tail(168)
    )
    route_summary = analysis["route_summary"]
    hourly_summary = analysis["hourly_summary"]
    flagged = analysis["flagged_records"]
    peak_comparison = analysis["peak_comparison"]
    fleet_summary = operations["summary"]

    _write_json(
        "overview.json",
        {
            **base_metadata,
            "forecast_horizon_hours": FORECAST_HORIZON_HOURS,
            "kpis": {
                "total_forecast_ridership": float(
                    forecast["predicted_ridership"].sum()
                ),
                "routes_analysed": int(forecast["bus_route"].nunique()),
                "flagged_demand_periods": int(len(flagged)),
            },
            "hourly_demand": _records(hourly_forecast),
            "top_routes": _records(route_summary.head(10)),
            "peak_comparison": _records(peak_comparison),
            "alerts": {
                "high": int((flagged["priority"] == "high").sum()),
                "elevated": int((flagged["priority"] == "elevated").sum()),
                "basis": "Historical-relative thresholds; not verified overcrowding.",
            },
            "operational_notice": "Fleet values are simulation assumptions requiring human review.",
        },
    )
    _write_json(
        "forecast.json",
        {
            **base_metadata,
            "model": model_metadata,
            "forecast_horizon_hours": FORECAST_HORIZON_HOURS,
            "forecast": _records(forecast),
            "actual_hourly": _records(historical_hourly),
            "explanation": "Recursive forecasts may accumulate error across the horizon.",
        },
    )
    _write_json(
        "demand_analysis.json",
        {
            **base_metadata,
            "route_ranking": _records(route_summary),
            "hourly_ranking": _records(hourly_summary),
            "peak_comparison": _records(peak_comparison),
            "flagged_records": _records(flagged),
            "threshold_notice": "High and elevated flags are historical-relative, not verified overcrowding.",
        },
    )
    _write_json(
        "fleet_plan.json",
        {
            **base_metadata,
            "assumptions": {
                "available_buses": AVAILABLE_BUSES,
                "reserve_buses": RESERVE_BUSES,
                "bus_capacity": BUS_CAPACITY,
                "target_load_factor": TARGET_LOAD_FACTOR,
                "notice": "These are simulation assumptions, not verified MTA operational data.",
            },
            "summary": fleet_summary,
            "route_plan": _records(operations["route_plan"]),
            "planning_status": "Simulation — human approval required",
        },
    )
    return [OUTPUT_DIRECTORY / name for name in (
        "overview.json",
        "forecast.json",
        "demand_analysis.json",
        "fleet_plan.json",
    )]


def main() -> int:
    """Export dashboard documents and report their paths."""
    try:
        for path in export_dashboard_data():
            print(f"Exported {path}")
    except (FileNotFoundError, ValueError, OSError, TypeError) as error:
        print(f"Dashboard export failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
