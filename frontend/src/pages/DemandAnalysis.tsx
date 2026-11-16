import { useMemo, useState } from "react";
import { AlertTriangle, BarChart3, Filter, Flag, Route } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dataService } from "../services/dataService";
import { useDashboardData } from "../hooks/useDashboardData";
import { ErrorState, LoadingState, EmptyState } from "../components/States";
import { Notice, Panel, StatCard, ViewHeader, formatCompact, formatNumber } from "../components/Ui";
import type { DemandAnalysisData, Priority } from "../types/data";

export function DemandAnalysis() {
  const { data, loading, error } = useDashboardData<DemandAnalysisData>(dataService.getDemandAnalysis);
  const [route, setRoute] = useState("all");
  const [priority, setPriority] = useState<"all" | Priority>("all");
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Demand analysis data is unavailable."} onRetry={() => window.location.reload()} />;
  const routes = [...new Set(data.flagged_records.map((record) => record.bus_route))].sort();
  const filtered = data.flagged_records.filter((record) => (route === "all" || record.bus_route === route) && (priority === "all" || record.priority === priority));
  const hourly = data.hourly_ranking.slice().sort((a, b) => b.predicted_ridership - a.predicted_ridership).slice(0, 12);
  return (
    <>
      <ViewHeader eyebrow="Demand analysis agent" title="Where pressure is building" description="Rank routes and forecast hours, then inspect historical-relative demand signals for prioritisation." generatedAt={data.generated_at} />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Routes ranked" value={formatNumber(data.route_ranking.length)} helper="Active routes in forecast" icon={<Route className="h-4 w-4" />} />
        <StatCard label="Flagged periods" value={formatNumber(data.flagged_records.length)} helper="High or elevated priority" icon={<Flag className="h-4 w-4" />} tone="red" />
        <StatCard label="High priority" value={formatNumber(data.flagged_records.filter((item) => item.priority === "high").length)} helper="Historical-relative threshold" icon={<AlertTriangle className="h-4 w-4" />} tone="amber" />
        <StatCard label="Peak windows" value={formatNumber(data.peak_comparison.length)} helper="Morning, evening and off-peak" icon={<BarChart3 className="h-4 w-4" />} tone="green" />
      </div>
      <div className="mb-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel title="Route ranking" subtitle="Total predicted ridership over the forecast horizon">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.route_ranking.slice(0, 10)} layout="vertical" margin={{ top: 0, right: 14, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="#eef1f5" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="bus_route" width={54} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip formatter={(value: number) => [formatNumber(value), "Predicted ridership"]} />
                <Bar dataKey="total_predicted_ridership" radius={[0, 6, 6, 0]} barSize={20} fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Busiest forecast hours" subtitle="Network-level ranking across the horizon">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourly} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#eef1f5" vertical={false} />
                <XAxis dataKey="hour" tickFormatter={(value) => `${String(value).padStart(2, "0")}:00`} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis tickLine={false} axisLine={false} tickFormatter={formatCompact} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <Tooltip formatter={(value: number) => [formatNumber(value), "Predicted ridership"]} />
                <Bar dataKey="predicted_ridership" radius={[6, 6, 0, 0]}>
                  {hourly.map((item, index) => <Cell key={item.transit_timestamp} fill={index < 3 ? "#f59e0b" : "#93c5fd"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <div className="mb-6 grid gap-4 md:grid-cols-3">
        {data.peak_comparison.map((item, index) => (
          <div key={item.period} className="panel p-5">
            <p className="eyebrow">{item.period}</p>
            <p className="mt-3 text-2xl font-bold text-ink">{formatCompact(item.average_hourly_ridership)}</p>
            <p className="mt-1 text-xs text-slate-500">Average predicted hourly ridership</p>
            <div className={`mt-4 h-1.5 rounded-full ${index === 2 ? "bg-slate-300" : "bg-accent"}`} />
          </div>
        ))}
      </div>
      <Panel title="Demand flags" subtitle="Filter route-hour records by route and priority">
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500"><Filter className="h-4 w-4" /> Filters</div>
          <select value={route} onChange={(event) => setRoute(event.target.value)} className="rounded-lg border border-line bg-white px-3 py-2 text-xs font-semibold text-slate-700 outline-none focus:border-accent">
            <option value="all">All routes</option>
            {routes.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={priority} onChange={(event) => setPriority(event.target.value as "all" | Priority)} className="rounded-lg border border-line bg-white px-3 py-2 text-xs font-semibold capitalize text-slate-700 outline-none focus:border-accent">
            <option value="all">All priorities</option><option value="high">High</option><option value="elevated">Elevated</option>
          </select>
          <span className="text-xs text-slate-400">{filtered.length} matching records</span>
        </div>
        {filtered.length === 0 ? <EmptyState message="No demand flags match the selected filters." /> : (
          <div className="max-h-[420px] overflow-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead className="sticky top-0 bg-white text-[10px] uppercase tracking-wider text-slate-400"><tr><th className="pb-3 pr-4">Timestamp</th><th className="pb-3 pr-4">Route</th><th className="pb-3 pr-4">Priority</th><th className="pb-3 pr-4">Forecast</th><th className="pb-3 pr-4">Historical mean</th><th className="pb-3">Relative ratio</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.slice(0, 300).map((record) => <tr key={`${record.transit_timestamp}-${record.bus_route}`} className="text-slate-600">
                  <td className="py-3 pr-4">{new Date(record.transit_timestamp).toLocaleString()}</td>
                  <td className="py-3 pr-4 font-bold text-ink">{record.bus_route}</td>
                  <td className="py-3 pr-4"><span className={`rounded-full px-2 py-1 text-[10px] font-bold capitalize ${record.priority === "high" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}`}>{record.priority}</span></td>
                  <td className="py-3 pr-4 font-semibold text-accent">{formatNumber(record.predicted_ridership, 1)}</td>
                  <td className="py-3 pr-4">{formatNumber(record.historical_mean, 1)}</td>
                  <td className="py-3">{record.relative_ratio ? `${record.relative_ratio.toFixed(2)}×` : "—"}</td>
                </tr>)}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-5"><Notice>{data.threshold_notice}</Notice></div>
      </Panel>
    </>
  );
}
