"""Demand analysis agent for forecast rankings and historical-relative alerts."""

from __future__ import annotations

import numpy as np
import pandas as pd


class DemandAnalysisAgent:
    """Analyse forecast demand without claiming verified overcrowding."""

    def __init__(
        self,
        historical_data: pd.DataFrame,
        forecast_data: pd.DataFrame,
    ) -> None:
        self.historical_data = historical_data.copy()
        self.forecast_data = forecast_data.copy()
        self.historical_data["transit_timestamp"] = pd.to_datetime(
            self.historical_data["transit_timestamp"]
        )
        self.forecast_data["transit_timestamp"] = pd.to_datetime(
            self.forecast_data["transit_timestamp"]
        )
        self._validate_data()

    def _validate_data(self) -> None:
        required_history = {"transit_timestamp", "bus_route", "ridership"}
        required_forecast = {
            "transit_timestamp",
            "bus_route",
            "predicted_ridership",
        }
        if not required_history.issubset(self.historical_data.columns):
            raise ValueError("Historical data is missing required analysis columns.")
        if not required_forecast.issubset(self.forecast_data.columns):
            raise ValueError("Forecast data is missing required analysis columns.")
        if self.forecast_data.empty:
            raise ValueError("Forecast data is empty.")
        if self.forecast_data["predicted_ridership"].isna().any():
            raise ValueError("Forecast contains missing predictions.")
        if (self.forecast_data["predicted_ridership"] < 0).any():
            raise ValueError("Forecast contains negative ridership.")

    def analyse(self) -> dict[str, pd.DataFrame]:
        """Return route/hour rankings, peak comparisons and alert records."""
        forecast = self.forecast_data.copy()
        history = self.historical_data.copy()
        forecast["hour"] = forecast["transit_timestamp"].dt.hour
        forecast["day_of_week"] = forecast["transit_timestamp"].dt.dayofweek
        forecast["hour_of_week"] = forecast["day_of_week"] * 24 + forecast["hour"]
        route_stats = (
            forecast.groupby("bus_route", as_index=False)
            .agg(
                forecast_total=("predicted_ridership", "sum"),
                forecast_average=("predicted_ridership", "mean"),
                forecast_peak=("predicted_ridership", "max"),
            )
            .sort_values("forecast_total", ascending=False)
        )
        route_stats["demand_rank"] = (
            route_stats["forecast_total"]
            .rank(method="dense", ascending=False)
            .astype(int)
        )
        route_stats["total_predicted_ridership"] = route_stats["forecast_total"]
        route_stats["average_hourly_demand"] = route_stats["forecast_average"]
        route_stats["peak_hourly_demand"] = route_stats["forecast_peak"]
        hourly_stats = (
            forecast.groupby(["transit_timestamp", "hour"], as_index=False)
            .agg(
                total_forecast=("predicted_ridership", "sum"),
                average_route_demand=("predicted_ridership", "mean"),
            )
            .sort_values("total_forecast", ascending=False)
        )
        hourly_stats["predicted_ridership"] = hourly_stats["total_forecast"]
        history["hour"] = history["transit_timestamp"].dt.hour
        history["day_of_week"] = history["transit_timestamp"].dt.dayofweek
        history["hour_of_week"] = history["day_of_week"] * 24 + history["hour"]
        baseline = history.groupby(["bus_route", "hour_of_week"])["ridership"].agg(
            historical_mean="mean",
            historical_std="std",
            historical_median="median",
        ).reset_index()
        flagged = forecast.merge(
            baseline,
            on=["bus_route", "hour_of_week"],
            how="left",
        )
        flagged["historical_ratio"] = flagged["predicted_ridership"] / flagged[
            "historical_mean"
        ].clip(lower=1)
        flagged["demand_flag"] = np.select(
            [
                flagged["historical_ratio"] >= 1.5,
                flagged["historical_ratio"] >= 1.2,
            ],
            ["High relative to historical profile", "Elevated relative to historical profile"],
            default="Within historical-relative range",
        )
        flagged = flagged[
            flagged["demand_flag"] != "Within historical-relative range"
        ].copy()
        flagged["relative_ratio"] = flagged["historical_ratio"]
        flagged["priority"] = np.where(
            flagged["historical_ratio"] >= 1.5,
            "high",
            "elevated",
        )
        period_summary = _peak_comparison(forecast)
        return {
            "route_summary": route_stats,
            "hourly_summary": hourly_stats,
            "flagged_records": flagged.sort_values(
                "historical_ratio",
                ascending=False,
            ),
            "peak_comparison": period_summary,
        }


def _peak_comparison(forecast: pd.DataFrame) -> pd.DataFrame:
    """Compare the requested morning, evening and off-peak windows."""
    data = forecast.copy()
    data["hour"] = data["transit_timestamp"].dt.hour
    windows = {
        "Morning peak": data["hour"].between(7, 9),
        "Evening peak": data["hour"].between(16, 19),
        "Off-peak": ~data["hour"].between(7, 9) & ~data["hour"].between(16, 19),
    }
    rows = []
    for label, mask in windows.items():
        subset = data.loc[mask, "predicted_ridership"]
        rows.append(
            {
                "period": label,
                "total_predicted_ridership": float(subset.sum()),
                "average_hourly_ridership": float(subset.mean()),
                "records": int(len(subset)),
            }
        )
    return pd.DataFrame(rows)
