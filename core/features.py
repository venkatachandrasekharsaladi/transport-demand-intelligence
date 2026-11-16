"""Feature engineering and chronological splitting for ridership forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "day_of_month",
    "lag_24h",
    "lag_168h",
]
CATEGORICAL_FEATURES = ["bus_route"]
TARGET_COLUMN = "ridership"


@dataclass(frozen=True)
class DatasetSplit:
    """Chronological model split and the complete feature dataset."""

    model_data: pd.DataFrame
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def prepare_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add the calendar features used by the notebook model."""
    data = dataframe[["transit_timestamp", "bus_route", "ridership"]].copy()
    data["transit_timestamp"] = pd.to_datetime(data["transit_timestamp"])
    data["bus_route"] = data["bus_route"].astype(str)
    data = data.sort_values(
        ["transit_timestamp", "bus_route"]
    ).reset_index(drop=True)
    data["hour"] = data["transit_timestamp"].dt.hour
    data["day_of_week"] = data["transit_timestamp"].dt.dayofweek
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)
    data["day_of_month"] = data["transit_timestamp"].dt.day
    return data


def create_model_dataset(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create lagged features for active routes without inventing records."""
    data = prepare_features(dataframe)
    route_totals = data.groupby("bus_route")["ridership"].sum()
    active_routes = route_totals[route_totals > 0].index
    data = data[data["bus_route"].isin(active_routes)].copy()
    data = data.sort_values(
        ["bus_route", "transit_timestamp"]
    ).reset_index(drop=True)
    grouped_ridership = data.groupby("bus_route")["ridership"]
    data["lag_24h"] = grouped_ridership.shift(24)
    data["lag_168h"] = grouped_ridership.shift(168)
    return data.dropna(subset=["lag_24h", "lag_168h"]).reset_index(drop=True)


def split_chronologically(
    model_data: pd.DataFrame,
    train_end: str = "2026-08-25 00:00:00",
    validation_end: str = "2026-09-01 00:00:00",
) -> DatasetSplit:
    """Split model rows by time, preserving chronological ordering."""
    train_boundary = pd.Timestamp(train_end)
    validation_boundary = pd.Timestamp(validation_end)
    train = model_data[model_data["transit_timestamp"] < train_boundary].copy()
    validation = model_data[
        (model_data["transit_timestamp"] >= train_boundary)
        & (model_data["transit_timestamp"] < validation_boundary)
    ].copy()
    test = model_data[
        model_data["transit_timestamp"] >= validation_boundary
    ].copy()

    if train.empty or validation.empty or test.empty:
        raise ValueError("Chronological split produced an empty partition.")
    if train["transit_timestamp"].max() >= validation["transit_timestamp"].min():
        raise ValueError("Training and validation periods overlap.")
    if validation["transit_timestamp"].max() >= test["transit_timestamp"].min():
        raise ValueError("Validation and test periods overlap.")
    return DatasetSplit(model_data, train, validation, test)
