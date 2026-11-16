"""Download the eight-week MTA bus ridership dataset used by the notebook."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from core.data_processing import load_ridership_data, validate_ridership_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "mta_ridership.csv"
API_URL = "https://data.ny.gov/resource/gxb3-akrn.json"
START_DATE = pd.Timestamp("2026-07-14")
END_DATE = pd.Timestamp("2026-09-08")  # Exclusive, as in the notebook.
PAGE_SIZE = 50_000
REQUEST_TIMEOUT_SECONDS = 180
MAX_REQUEST_ATTEMPTS = 3


def _request_page(
    session: requests.Session,
    params: dict[str, Any],
    week_start: pd.Timestamp,
) -> list[dict[str, Any]]:
    """Request one API page, retrying transient failures with clear errors."""
    for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
        try:
            response = session.get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            elif not response.ok:
                raise RuntimeError(
                    f"MTA API rejected the request for week starting "
                    f"{week_start.date()} with HTTP {response.status_code}: "
                    f"{response.text[:300]}"
                )
            payload = response.json()
            if not isinstance(payload, list):
                raise RuntimeError("MTA API returned an unexpected JSON response.")
            return payload
        except (requests.RequestException, ValueError) as error:
            if attempt == MAX_REQUEST_ATTEMPTS:
                raise RuntimeError(
                    f"MTA API request failed after {MAX_REQUEST_ATTEMPTS} attempts "
                    f"for the week starting {week_start.date()}: {error}"
                ) from error
            delay = 2 ** (attempt - 1)
            print(f"  Request failed ({error}); retrying in {delay} second(s).")
            time.sleep(delay)

    raise RuntimeError("MTA API request failed unexpectedly.")


def fetch_week(
    session: requests.Session,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Fetch one weekly window using the notebook's grouped API query."""
    rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "$select": (
                "transit_timestamp, bus_route, "
                "sum(ridership) as ridership"
            ),
            "$where": (
                f"transit_timestamp >= '{start:%Y-%m-%dT%H:%M:%S}' "
                f"AND transit_timestamp < '{end:%Y-%m-%dT%H:%M:%S}'"
            ),
            "$group": "transit_timestamp, bus_route",
            "$order": "transit_timestamp, bus_route",
            "$limit": PAGE_SIZE,
            "$offset": offset,
        }
        batch = _request_page(session, params, start)
        if not batch:
            break

        rows.extend(batch)
        offset += len(batch)
        print(f"  Retrieved {len(rows):,} rows for this week.")

        if len(batch) < PAGE_SIZE:
            break
        time.sleep(0.3)

    return pd.DataFrame(rows)


def download_dataset(output_path: str | Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Download, combine and save the eight-week dataset.

    Existing output is never replaced unless the caller removes it first.
    """
    path = Path(output_path)
    if path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing dataset: {path}. "
            "Move it aside or remove it only after confirming that replacement "
            "is intended."
        )

    weekly_frames: list[pd.DataFrame] = []
    week_start = START_DATE

    with requests.Session() as session:
        while week_start < END_DATE:
            week_end = min(week_start + pd.Timedelta(days=7), END_DATE)
            print(f"Fetching {week_start.date()} to {week_end.date()}.")
            part = fetch_week(session, week_start, week_end)
            if not part.empty:
                weekly_frames.append(part)
            week_start = week_end
            time.sleep(0.5)

    if not weekly_frames:
        raise RuntimeError("MTA API returned no historical records.")

    dataframe = pd.concat(weekly_frames, ignore_index=True)
    dataframe["transit_timestamp"] = pd.to_datetime(
        dataframe["transit_timestamp"], errors="coerce"
    )
    dataframe["bus_route"] = dataframe["bus_route"].astype("string")
    dataframe["ridership"] = pd.to_numeric(
        dataframe["ridership"], errors="coerce"
    )
    dataframe = dataframe.sort_values(
        ["bus_route", "transit_timestamp"]
    ).reset_index(drop=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False)
    print(f"Download completed: {len(dataframe):,} rows saved to {path}.")
    return path


def main() -> int:
    """Download the dataset and run the Stage 1 validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    try:
        output_path = download_dataset(args.output)
        dataframe = load_ridership_data(output_path)
        summary = validate_ridership_data(dataframe)
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Dataset download or validation failed: {error}")
        return 1

    print("\nDownloaded dataset validation completed.")
    print(f"Rows: {summary['total_rows']:,}")
    print(f"Unique routes: {summary['unique_bus_routes']:,}")
    print(f"Unique timestamps: {summary['unique_timestamps']:,}")
    print(f"Date range: {summary['minimum_timestamp']} to {summary['maximum_timestamp']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
