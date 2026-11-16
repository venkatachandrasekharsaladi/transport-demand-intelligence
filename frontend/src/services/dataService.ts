import type {
  DemandAnalysisData,
  FleetPlanData,
  ForecastData,
  OverviewData,
} from "../types/data";

const dataPath = (filename: string) =>
  `${import.meta.env.BASE_URL}data/${filename}`;

async function fetchJson<T>(filename: string): Promise<T> {
  const response = await fetch(dataPath(filename));
  if (!response.ok) {
    throw new Error(`Could not load ${filename} (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export const dataService = {
  getOverview: () => fetchJson<OverviewData>("overview.json"),
  getForecast: () => fetchJson<ForecastData>("forecast.json"),
  getDemandAnalysis: () =>
    fetchJson<DemandAnalysisData>("demand_analysis.json"),
  getFleetPlan: () => fetchJson<FleetPlanData>("fleet_plan.json"),
};
