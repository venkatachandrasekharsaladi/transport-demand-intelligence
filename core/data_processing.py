"""Load and validate the hourly MTA bus ridership dataset."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {"transit_timestamp", "bus_route", "ridership"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "mta_ridership.csv"


def load_ridership_data(file_path: str | Path) -> pd.DataFrame:
    """Load and clean a ridership CSV without dropping any records."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Ridership dataset not found: {path}")

    try:
        dataframe = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as error:
        raise ValueError(f"Could not read ridership dataset '{path}': {error}") from error

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Ridership dataset is missing required column(s): {missing}")

    try:
        dataframe["transit_timestamp"] = pd.to_datetime(
            dataframe["transit_timestamp"], errors="raise"
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Column 'transit_timestamp' contains values that cannot be parsed as datetimes."
        ) from error

    dataframe["ridership"] = pd.to_numeric(dataframe["ridership"], errors="coerce")
    if dataframe["ridership"].isna().any():
        raise ValueError("Column 'ridership' contains missing or non-numeric values.")

    return dataframe


def get_dataset_summary(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Return calculated statistics for a validated-schema ridership DataFrame."""
    missing_values = {
        column: int(dataframe[column].isna().sum()) for column in REQUIRED_COLUMNS
    }
    duplicate_records = int(
        dataframe.duplicated(subset=["transit_timestamp", "bus_route"]).sum()
    )
    route_totals = dataframe.groupby("bus_route", dropna=False)["ridership"].sum()

    return {
        "total_rows": int(len(dataframe)),
        "unique_bus_routes": int(dataframe["bus_route"].nunique(dropna=True)),
        "unique_timestamps": int(dataframe["transit_timestamp"].nunique(dropna=True)),
        "minimum_timestamp": dataframe["transit_timestamp"].min(),
        "maximum_timestamp": dataframe["transit_timestamp"].max(),
        "missing_values": missing_values,
        "negative_ridership_records": int((dataframe["ridership"] < 0).sum()),
        "duplicate_route_hour_records": duplicate_records,
        "zero_ridership_records": int((dataframe["ridership"] == 0).sum()),
        "routes_with_zero_total_ridership": int((route_totals == 0).sum()),
    }


def validate_ridership_data(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Calculate data-quality checks and warn about issues without deleting data."""
    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"DataFrame is missing required column(s): {missing}")

    summary = get_dataset_summary(dataframe)
    quality_issues = [
        (
            summary["missing_values"],
            "Missing values found in required columns: "
            f"{summary['missing_values']}",
        ),
        (
            summary["negative_ridership_records"],
            f"Found {summary['negative_ridership_records']} negative ridership record(s).",
        ),
        (
            summary["duplicate_route_hour_records"],
            "Found "
            f"{summary['duplicate_route_hour_records']} duplicate route-hour record(s).",
        ),
    ]
    for issue_count, message in quality_issues:
        has_issue = any(issue_count.values()) if isinstance(issue_count, dict) else issue_count > 0
        if has_issue:
            warnings.warn(message, UserWarning, stacklevel=2)

    if summary["routes_with_zero_total_ridership"] > 0:
        warnings.warn(
            f"Found {summary['routes_with_zero_total_ridership']} route(s) with zero "
            "total ridership; records have been preserved.",
            UserWarning,
            stacklevel=2,
        )

    return summary


def _format_summary(summary: dict[str, Any]) -> str:
    """Format summary values for command-line output."""
    lines = [
        "Dataset summary",
        "---------------",
        f"Total rows: {summary['total_rows']:,}",
        f"Unique bus routes: {summary['unique_bus_routes']:,}",
        f"Unique timestamps: {summary['unique_timestamps']:,}",
        f"Minimum timestamp: {summary['minimum_timestamp']}",
        f"Maximum timestamp: {summary['maximum_timestamp']}",
        f"Missing values: {summary['missing_values']}",
        f"Negative ridership records: {summary['negative_ridership_records']:,}",
        "Duplicate route-hour records: "
        f"{summary['duplicate_route_hour_records']:,}",
        f"Zero-ridership records: {summary['zero_ridership_records']:,}",
        "Routes with zero total ridership: "
        f"{summary['routes_with_zero_total_ridership']:,}",
    ]
    return "\n".join(lines)


def main() -> int:
    """Run dataset loading and validation from the project root."""
    try:
        dataframe = load_ridership_data(DEFAULT_DATASET_PATH)
        summary = validate_ridership_data(dataframe)
    except (FileNotFoundError, ValueError) as error:
        print(f"Dataset validation failed: {error}", file=sys.stderr)
        return 1

    print(_format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
