export type Priority = "high" | "elevated" | "normal";

export interface DatasetMetadata {
  rows: number;
  routes: number;
  timestamps: number;
  date_range: { start: string; end: string };
}

export interface BaseResponse {
  generated_at: string;
  dataset: DatasetMetadata;
  source: string;
}

export interface DemandPoint {
  transit_timestamp: string;
  predicted_ridership: number;
}

export interface RouteSummary {
  bus_route: string;
  total_predicted_ridership: number;
  average_hourly_demand: number;
  peak_hourly_demand: number;
}

export interface PeakComparison {
  period: string;
  total_predicted_ridership: number;
  average_hourly_ridership: number;
  records: number;
}

export interface FlaggedRecord {
  transit_timestamp: string;
  bus_route: string;
  predicted_ridership: number;
  hour: number;
  historical_mean: number;
  historical_std: number;
  relative_ratio: number;
  priority: Priority;
}

export interface FleetRoute {
  bus_route: string;
  peak_hourly_forecast: number;
  estimated_buses_required: number;
  recommended_buses: number;
  estimated_shortfall: number;
  recommendation: string;
  approval_status: string;
}

export interface OverviewData extends BaseResponse {
  forecast_horizon_hours: number;
  kpis: {
    total_forecast_ridership: number;
    routes_analysed: number;
    flagged_demand_periods: number;
  };
  hourly_demand: DemandPoint[];
  top_routes: RouteSummary[];
  peak_comparison: PeakComparison[];
  alerts: { high: number; elevated: number; basis: string };
  operational_notice: string;
}

export interface ForecastRow {
  transit_timestamp: string;
  bus_route: string;
  hour: number;
  day_of_week: number;
  is_weekend: number;
  day_of_month: number;
  lag_24h: number;
  lag_168h: number;
  predicted_ridership: number;
}

export interface ForecastData extends BaseResponse {
  forecast_horizon_hours: number;
  model: {
    model_type: string;
    training_implementation: string;
    metrics: {
      validation: MetricSet;
      test: MetricSet;
      test_observations: number;
      test_actual_total: number;
      test_predicted_total: number;
    };
  };
  forecast: ForecastRow[];
  actual_hourly: { transit_timestamp: string; actual_ridership: number }[];
  explanation: string;
}

export interface MetricSet {
  mae: number;
  rmse: number;
  wape_percent: number;
  bias_percent: number;
}

export interface DemandAnalysisData extends BaseResponse {
  route_ranking: RouteSummary[];
  hourly_ranking: (DemandPoint & { hour: number })[];
  peak_comparison: PeakComparison[];
  flagged_records: FlaggedRecord[];
  threshold_notice: string;
}

export interface FleetPlanData extends BaseResponse {
  assumptions: {
    available_buses: number;
    reserve_buses: number;
    bus_capacity: number;
    target_load_factor: number;
    notice: string;
  };
  summary: {
    routes_planned: number;
    available_buses_assumed: number;
    reserve_buses_protected: number;
    allocatable_buses: number;
    recommended_buses_total: number;
    estimated_buses_required_total: number;
    routes_with_shortfall: number;
    unallocated_buses: number;
    fleet_constraint_satisfied: boolean;
    planning_status: string;
  };
  route_plan: FleetRoute[];
  planning_status: string;
}
