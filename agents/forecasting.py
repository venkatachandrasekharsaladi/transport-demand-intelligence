"""Recursive route-demand forecasting agent."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.features import CATEGORICAL_FEATURES, FEATURE_COLUMNS


class ForecastingAgent:
    """Generate recursive hourly forecasts from a persisted forecasting model."""

    def __init__(self, model: Any, history: pd.DataFrame) -> None:
        self.model = model
        self.history = history.copy()
        self.history["transit_timestamp"] = pd.to_datetime(
            self.history["transit_timestamp"]
        )
        self.history["bus_route"] = self.history["bus_route"].astype(str)
        self.history = self.history.sort_values(
            ["bus_route", "transit_timestamp"]
        ).reset_index(drop=True)
        self.routes = sorted(self.history["bus_route"].unique())

    def forecast(self, horizon_hours: int = 24) -> pd.DataFrame:
        """Forecast each active route recursively for the requested horizon."""
        if horizon_hours <= 0:
            raise ValueError("Forecast horizon must be positive.")
        values = {
            (row.bus_route, row.transit_timestamp): float(row.ridership)
            for row in self.history.itertuples()
        }
        start = self.history["transit_timestamp"].max() + pd.Timedelta(hours=1)
        output: list[pd.DataFrame] = []

        for offset in range(horizon_hours):
            timestamp = start + pd.Timedelta(hours=offset)
            rows = []
            for route in self.routes:
                rows.append(
                    {
                        "transit_timestamp": timestamp,
                        "bus_route": route,
                        "hour": timestamp.hour,
                        "day_of_week": timestamp.dayofweek,
                        "is_weekend": int(timestamp.dayofweek >= 5),
                        "day_of_month": timestamp.day,
                        "lag_24h": values.get(
                            (route, timestamp - pd.Timedelta(hours=24)),
                            0.0,
                        ),
                        "lag_168h": values.get(
                            (route, timestamp - pd.Timedelta(hours=168)),
                            0.0,
                        ),
                    }
                )
            frame = pd.DataFrame(rows)
            predictions = np.maximum(
                0,
                self.model.predict(
                    frame[FEATURE_COLUMNS + CATEGORICAL_FEATURES]
                ),
            )
            frame["predicted_ridership"] = predictions
            output.append(frame)
            for row in frame.itertuples():
                values[(row.bus_route, row.transit_timestamp)] = float(
                    row.predicted_ridership
                )

        return pd.concat(output, ignore_index=True)
