import { AlertTriangle, Bus, Clock3, Route, Sparkles } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { dataService } from "../services/dataService";
import { useDashboardData } from "../hooks/useDashboardData";
import { ErrorState, LoadingState } from "../components/States";
import { Notice, Panel, StatCard, ViewHeader, formatCompact, formatHour, formatNumber } from "../components/Ui";
import type { OverviewData } from "../types/data";

export function Overview() {
  const { data, loading, error } = useDashboardData<OverviewData>(dataService.getOverview);
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Overview data is unavailable."} onRetry={() => window.location.reload()} />;
  const peakChart = data.peak_comparison.map((item) => ({
    ...item,
    label: item.period.replace(" (07:00–09:00)", "").replace(" (16:00–19:00)", ""),
  }));
  return (
    <>
      <ViewHeader
        eyebrow="Network intelligence"
        title="A clear view of demand"
        description="A static, evidence-led view of forecast passenger demand and the operational signals derived from it."
        generatedAt={data.generated_at}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Forecast ridership" value={formatCompact(data.kpis.total_forecast_ridership)} helper="Next 24 hours, all analysed routes" icon={<Sparkles className="h-4 w-4" />} />
        <StatCard label="Routes analysed" value={formatNumber(data.kpis.routes_analysed)} helper={`Of ${formatNumber(data.dataset.routes)} dataset routes`} icon={<Route className="h-4 w-4" />} tone="green" />
        <StatCard label="Forecast horizon" value={`${data.forecast_horizon_hours}h`} helper="Recursive hourly forecast" icon={<Clock3 className="h-4 w-4" />} tone="amber" />
        <StatCard label="Demand alerts" value={formatNumber(data.kpis.flagged_demand_periods)} helper={`${data.alerts.high} high · ${data.alerts.elevated} elevated`} icon={<AlertTriangle className="h-4 w-4" />} tone="red" />
      </div>
      <div className="mb-6 grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <Panel title="Hourly demand trend" subtitle="Aggregated forecast ridership across the next 24 hours">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.hourly_demand} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#eef1f5" vertical={false} />
                <XAxis dataKey="transit_timestamp" tickFormatter={formatHour} tickLine={false} axisLine={false} minTickGap={25} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} tickFormatter={formatCompact} />
                <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} formatter={(value: number) => [formatNumber(value), "Forecast ridership"]} />
                <Line type="monotone" dataKey="predicted_ridership" stroke="#2563eb" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Peak profile" subtitle="Forecast demand by operating window">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={peakChart} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#eef1f5" vertical={false} />
                <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} tickFormatter={formatCompact} />
                <Tooltip formatter={(value: number) => [formatNumber(value), "Average ridership"]} />
                <Bar dataKey="average_hourly_ridership" radius={[6, 6, 0, 0]}>
                  {peakChart.map((entry) => <Cell key={entry.period} fill={entry.label === "Off-peak" ? "#94a3b8" : "#2563eb"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Top routes by forecast demand" subtitle="Prioritised by total predicted ridership over the horizon">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_routes.slice(0, 8)} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 10 }}>
                <CartesianGrid stroke="#eef1f5" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="bus_route" width={54} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip formatter={(value: number) => [formatNumber(value), "Predicted ridership"]} />
                <Bar dataKey="total_predicted_ridership" fill="#2563eb" radius={[0, 6, 6, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Demand alert summary" subtitle="Signals derived from historical-relative thresholds">
          <div className="space-y-3">
            <AlertRow label="High priority periods" value={data.alerts.high} tone="red" />
            <AlertRow label="Elevated periods" value={data.alerts.elevated} tone="amber" />
            <Notice>{data.alerts.basis}</Notice>
            <Notice tone="warning">
              <strong>Operational context:</strong> {data.operational_notice}
            </Notice>
          </div>
        </Panel>
      </div>
    </>
  );
}

function AlertRow({ label, value, tone }: { label: string; value: number; tone: "red" | "amber" }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-line p-4">
      <div className="flex items-center gap-3">
        <span className={`h-2.5 w-2.5 rounded-full ${tone === "red" ? "bg-red-500" : "bg-amber-500"}`} />
        <span className="text-sm font-semibold text-slate-700">{label}</span>
      </div>
      <span className="text-lg font-bold text-ink">{formatNumber(value)}</span>
    </div>
  );
}
