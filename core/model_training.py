"""Train, evaluate and persist the notebook's latest Random Forest pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from core.features import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    DatasetSplit,
)

MODEL_FILENAME = "forecasting_random_forest.joblib"
METADATA_FILENAME = "forecasting_random_forest_metadata.json"


def build_model() -> Pipeline:
    """Build the one-hot route pipeline from notebook cell 26."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "route",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", FEATURE_COLUMNS),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=40,
                    max_depth=18,
                    min_samples_leaf=5,
                    max_features=0.8,
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ]
    )


def calculate_metrics(
    actual: pd.Series | np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate the notebook's MAE, RMSE and WAPE metrics."""
    clipped = np.maximum(0, predicted)
    actual_array = np.asarray(actual)
    return {
        "mae": round(float(mean_absolute_error(actual_array, clipped)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(actual_array, clipped))), 3),
        "wape_percent": round(
            float(
                np.abs(actual_array - clipped).sum()
                / max(actual_array.sum(), 1)
                * 100
            ),
            3,
        ),
        "bias_percent": round(
            float(
                (clipped.sum() - actual_array.sum())
                / max(actual_array.sum(), 1)
                * 100
            ),
            3,
        ),
    }


def evaluate_model(model: Pipeline, split: DatasetSplit) -> dict[str, Any]:
    """Evaluate validation and test performance without retraining."""
    validation_pred = model.predict(
        split.validation[FEATURE_COLUMNS + CATEGORICAL_FEATURES]
    )
    test_pred = model.predict(split.test[FEATURE_COLUMNS + CATEGORICAL_FEATURES])
    return {
        "validation": calculate_metrics(split.validation[TARGET_COLUMN], validation_pred),
        "test": calculate_metrics(split.test[TARGET_COLUMN], test_pred),
        "test_observations": int(len(split.test)),
        "test_actual_total": int(split.test[TARGET_COLUMN].sum()),
        "test_predicted_total": int(np.maximum(0, test_pred).sum()),
    }


def train_and_save_model(
    split: DatasetSplit,
    model_path: str | Path,
    metadata_path: str | Path,
) -> dict[str, Any]:
    """Train on the notebook's bounded sample and persist model metadata."""
    model = build_model()
    sample = split.train.sample(
        n=min(100_000, len(split.train)),
        random_state=42,
    )
    model.fit(
        sample[FEATURE_COLUMNS + CATEGORICAL_FEATURES],
        sample[TARGET_COLUMN],
    )
    metrics = evaluate_model(model, split)
    metadata: dict[str, Any] = {
        "model_type": "RandomForestRegressor",
        "training_implementation": "Notebook cell 26 one-hot pipeline",
        "training_rows": int(len(sample)),
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "target_column": TARGET_COLUMN,
        "train_end": str(split.train["transit_timestamp"].max()),
        "validation_end": str(split.validation["transit_timestamp"].max()),
        "test_start": str(split.test["transit_timestamp"].min()),
        "metrics": metrics,
    }
    model_file = Path(model_path)
    metadata_file = Path(metadata_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_file)
    metadata_file.write_text(
        __import__("json").dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return metadata
