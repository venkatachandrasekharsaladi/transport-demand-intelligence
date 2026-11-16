import { CheckCircle2, CircleAlert, ShieldCheck, BusFront, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dataService } from "../services/dataService";
import { useDashboardData } from "../hooks/useDashboardData";
import { ErrorState, LoadingState } from "../components/States";
import { Notice, Panel, StatCard, ViewHeader, formatCompact, formatNumber } from "../components/Ui";
import type { FleetPlanData } from "../types/data";

export function FleetPlanning() {
  const { data, loading, error } = useDashboardData<FleetPlanData>(dataService.getFleetPlan);
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Fleet plan data is unavailable."} onRetry={() => window.location.reload()} />;
  const chartData = data.route_plan.slice(0, 12);
  const constraint = data.summary.fleet_constraint_satisfied;
  return (
    <>
      <ViewHeader eyebrow="Operations planning agent" title="Fleet planning simulation" description="Translate forecast pressure into a constrained allocation proposal for review. These are not verified MTA dispatch instructions." generatedAt={data.generated_at} />
      <div className="mb-6"><Notice tone="warning"><strong>Simulation assumptions:</strong> {data.assumptions.notice} Capacity is {data.assumptions.bus_capacity} passengers at a {data.assumptions.target_load_factor.toFixed(0)}% target load factor.</Notice></div>
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Available fleet" value={formatNumber(data.assumptions.available_buses)} helper="Assumed total buses" icon={<BusFront className="h-4 w-4" />} />
        <StatCard label="Reserve protected" value={formatNumber(data.assumptions.reserve_buses)} helper={`${formatNumber(data.summary.allocatable_buses)} allocatable`} icon={<ShieldCheck className="h-4 w-4" />} tone="green" />
        <StatCard label="Recommended allocation" value={formatNumber(data.summary.recommended_buses_total)} helper={`${formatNumber(data.summary.unallocated_buses)} unallocated`} icon={<Users className="h-4 w-4" />} tone="blue" />
        <StatCard label="Constraint status" value={constraint ? "Pass" : "Review"} helper={data.summary.planning_status} icon={constraint ? <CheckCircle2 className="h-4 w-4" /> : <CircleAlert className="h-4 w-4" />} tone={constraint ? "green" : "red"} />
      </div>
      <div className="mb-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel title="Priority route allocation" subtitle="Highest forecast requirement routes, ordered by estimated buses required">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#eef1f5" vertical={false} />
                <XAxis dataKey="bus_route" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <Tooltip formatter={(value: number, name) => [formatNumber(value), name === "recommended_buses" ? "Recommended" : "Required"]} />
                <Bar dataKey="estimated_buses_required" fill="#cbd5e1" radius={[5, 5, 0, 0]} />
                <Bar dataKey="recommended_buses" fill="#2563eb" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Constraint validation" subtitle="The allocation is checked before export">
          <div className={`rounded-2xl border p-5 ${constraint ? "border-emerald-200 bg-emerald-50/60" : "border-red-200 bg-red-50/60"}`}>
            <div className="flex items-center gap-3">
              {constraint ? <CheckCircle2 className="h-6 w-6 text-emerald-600" /> : <CircleAlert className="h-6 w-6 text-red-600" />}
              <div><p className="font-bold text-ink">{constraint ? "Fleet constraint satisfied" : "Fleet constraint requires review"}</p><p className="mt-1 text-xs text-slate-600">{data.summary.recommended_buses_total} recommended of {data.summary.allocatable_buses} allocatable buses</p></div>
            </div>
          </div>
          <div className="mt-5 space-y-3 text-sm">
            <SummaryRow label="Estimated requirement" value={formatNumber(data.summary.estimated_buses_required_total)} />
            <SummaryRow label="Routes with shortfall" value={formatNumber(data.summary.routes_with_shortfall)} />
            <SummaryRow label="Human-review status" value="Required" />
          </div>
        </Panel>
      </div>
      <Panel title="Route planning detail" subtitle="Allocation recommendations remain subject to human review">
        <div className="max-h-[440px] overflow-auto">
          <table className="w-full min-w-[800px] text-left text-xs">
            <thead className="sticky top-0 bg-white text-[10px] uppercase tracking-wider text-slate-400"><tr><th className="pb-3 pr-4">Route</th><th className="pb-3 pr-4">Peak forecast</th><th className="pb-3 pr-4">Required</th><th className="pb-3 pr-4">Recommended</th><th className="pb-3 pr-4">Shortfall</th><th className="pb-3">Status</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {data.route_plan.map((row) => <tr key={row.bus_route} className="text-slate-600">
                <td className="py-3 pr-4 font-bold text-ink">{row.bus_route}</td>
                <td className="py-3 pr-4">{formatCompact(row.peak_hourly_forecast)}</td>
                <td className="py-3 pr-4">{row.estimated_buses_required}</td>
                <td className="py-3 pr-4 font-bold text-accent">{row.recommended_buses}</td>
                <td className="py-3 pr-4">{row.estimated_shortfall}</td>
                <td className="py-3"><span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">{row.approval_status}</span></td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">{label}</span><strong className="text-ink">{value}</strong></div>;
}
