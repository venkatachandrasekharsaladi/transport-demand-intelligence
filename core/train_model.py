"""Train the notebook-derived forecasting model and save its artifact."""

from __future__ import annotations

from pathlib import Path

from core.data_processing import DEFAULT_DATASET_PATH, load_ridership_data
from core.features import create_model_dataset, split_chronologically
from core.model_training import (
    METADATA_FILENAME,
    MODEL_FILENAME,
    train_and_save_model,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / MODEL_FILENAME
METADATA_PATH = PROJECT_ROOT / "models" / METADATA_FILENAME


def main() -> int:
    """Train and persist the approved notebook model."""
    dataframe = load_ridership_data(DEFAULT_DATASET_PATH)
    split = split_chronologically(create_model_dataset(dataframe))
    metadata = train_and_save_model(split, MODEL_PATH, METADATA_PATH)
    print(f"Saved model artifact to {MODEL_PATH}")
    print(f"Saved model metadata to {METADATA_PATH}")
    print(f"Validation metrics: {metadata['metrics']['validation']}")
    print(f"Test metrics: {metadata['metrics']['test']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
