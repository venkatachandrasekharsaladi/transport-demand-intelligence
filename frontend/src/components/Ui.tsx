import type { ReactNode } from "react";
import { ArrowUpRight, Info } from "lucide-react";

export function Panel({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel p-5 sm:p-6 ${className}`}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold text-ink">{title}</h2>
          {subtitle && <p className="mt-1 text-xs leading-5 text-slate-500">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function StatCard({
  label,
  value,
  helper,
  icon,
  tone = "blue",
}: {
  label: string;
  value: string;
  helper: string;
  icon: ReactNode;
  tone?: "blue" | "green" | "amber" | "red";
}) {
  const tones = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-red-50 text-red-600",
  };
  return (
    <div className="panel flex min-h-36 flex-col justify-between p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="eyebrow">{label}</span>
        <span className={`rounded-xl p-2.5 ${tones[tone]}`}>{icon}</span>
      </div>
      <div>
        <p className="mt-3 text-2xl font-bold tracking-tight text-ink">{value}</p>
        <p className="mt-1 text-xs text-slate-500">{helper}</p>
      </div>
    </div>
  );
}

export function Notice({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: "info" | "warning";
}) {
  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 text-xs leading-5 ${
        tone === "warning"
          ? "border-amber-200 bg-amber-50 text-amber-800"
          : "border-blue-100 bg-blue-50/70 text-blue-800"
      }`}
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

export function ViewHeader({
  eyebrow,
  title,
  description,
  generatedAt,
}: {
  eyebrow: string;
  title: string;
  description: string;
  generatedAt?: string;
}) {
  return (
    <header className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{description}</p>
      </div>
      {generatedAt && (
        <div className="rounded-xl border border-line bg-white px-3 py-2 text-xs text-slate-500 shadow-sm">
          Generated <span className="font-semibold text-slate-700">{new Date(generatedAt).toLocaleString()}</span>
        </div>
      )}
    </header>
  );
}

export function LinkHint({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-semibold text-accent">
      {label} <ArrowUpRight className="h-3.5 w-3.5" />
    </span>
  );
}

export const formatNumber = (value: number, digits = 0) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);

export const formatCompact = (value: number) =>
  new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);

export const formatHour = (value: string) =>
  new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
