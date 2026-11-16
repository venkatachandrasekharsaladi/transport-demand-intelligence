"""Simulation-only fleet planning agent."""

from __future__ import annotations

import numpy as np
import pandas as pd


class OperationsPlanningAgent:
    """Allocate a constrained simulated fleet by forecast priority."""

    def __init__(self, config: dict[str, float | int]) -> None:
        self.config = config.copy()
        self._validate_config()

    def _validate_config(self) -> None:
        required = {
            "available_buses",
            "reserve_buses",
            "bus_capacity",
            "target_load_factor",
        }
        if not required.issubset(self.config):
            raise ValueError("Operations configuration is incomplete.")
        if not 0 <= self.config["reserve_buses"] <= self.config["available_buses"]:
            raise ValueError("Reserve buses must be between zero and available buses.")
        if self.config["bus_capacity"] <= 0 or not 0 < self.config["target_load_factor"] <= 1:
            raise ValueError("Bus capacity and target load factor are invalid.")

    def plan(
        self,
        forecast_data: pd.DataFrame,
        demand_results: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Return route requirements and a fleet-constrained allocation."""
        if forecast_data.empty:
            raise ValueError("Cannot plan a fleet for an empty forecast.")
        peak = (
            forecast_data.groupby("bus_route", as_index=False)
            .agg(peak_hourly_forecast=("predicted_ridership", "max"))
        )
        effective_capacity = (
            float(self.config["bus_capacity"])
            * float(self.config["target_load_factor"])
        )
        peak["estimated_buses_required"] = np.ceil(
            peak["peak_hourly_forecast"] / effective_capacity
        ).astype(int)
        if demand_results and "route_summary" in demand_results:
            route_summary = demand_results["route_summary"]
            if isinstance(route_summary, pd.DataFrame):
                peak = peak.merge(
                    route_summary[["bus_route", "forecast_total", "demand_rank"]],
                    on="bus_route",
                    how="left",
                )
        sort_columns = ["estimated_buses_required", "peak_hourly_forecast"]
        peak = peak.sort_values(sort_columns, ascending=False).reset_index(drop=True)
        allocatable = int(self.config["available_buses"] - self.config["reserve_buses"])
        peak["recommended_buses"] = 0
        baseline_routes = min(len(peak), allocatable)
        if baseline_routes:
            peak.loc[: baseline_routes - 1, "recommended_buses"] = 1
        remaining = allocatable - baseline_routes
        while remaining > 0:
            peak["remaining_need"] = (
                peak["estimated_buses_required"] - peak["recommended_buses"]
            )
            eligible = peak[peak["remaining_need"] > 0]
            if eligible.empty:
                break
            index = eligible.sort_values(
                ["remaining_need", "peak_hourly_forecast"],
                ascending=False,
            ).index[0]
            peak.loc[index, "recommended_buses"] += 1
            remaining -= 1
        peak = peak.drop(columns=["remaining_need"], errors="ignore")
        peak["estimated_shortfall"] = (
            peak["estimated_buses_required"] - peak["recommended_buses"]
        ).clip(lower=0)
        peak["recommendation"] = np.where(
            peak["estimated_shortfall"] > 0,
            "Estimated shortfall — review alternatives",
            "Within simulated allocation",
        )
        peak["approval_status"] = "Pending human review"
        summary = {
            "routes_planned": int(len(peak)),
            "available_buses_assumed": int(self.config["available_buses"]),
            "reserve_buses_protected": int(self.config["reserve_buses"]),
            "allocatable_buses": allocatable,
            "recommended_buses_total": int(peak["recommended_buses"].sum()),
            "estimated_buses_required_total": int(
                peak["estimated_buses_required"].sum()
            ),
            "routes_with_shortfall": int((peak["estimated_shortfall"] > 0).sum()),
            "routes_with_zero_allocation": int(
                peak["recommended_buses"].eq(0).sum()
            ),
            "unallocated_buses": int(
                allocatable - peak["recommended_buses"].sum()
            ),
            "fleet_constraint_satisfied": bool(
                peak["recommended_buses"].sum() <= allocatable
            ),
            "planning_status": "Simulation — human approval required",
        }
        return {"route_plan": peak, "summary": summary}
