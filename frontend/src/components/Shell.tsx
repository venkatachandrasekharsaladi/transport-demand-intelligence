import { useState } from "react";
import {
  Activity,
  BarChart3,
  BusFront,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Menu,
  X,
} from "lucide-react";

export type Section = "overview" | "forecasting" | "analysis" | "fleet";

const navigation: { id: Section; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "forecasting", label: "Demand forecasting", icon: Activity },
  { id: "analysis", label: "Demand analysis", icon: BarChart3 },
  { id: "fleet", label: "Fleet planning", icon: BusFront },
];

export function Shell({
  section,
  onSectionChange,
  children,
}: {
  section: Section;
  onSectionChange: (section: Section) => void;
  children: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="min-h-screen bg-mist">
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden border-r border-line bg-white transition-all duration-200 lg:block ${
          collapsed ? "w-[76px]" : "w-64"
        }`}
      >
        <SidebarContent
          collapsed={collapsed}
          section={section}
          onSectionChange={onSectionChange}
        />
        <button
          onClick={() => setCollapsed((value) => !value)}
          className="absolute -right-3 top-8 rounded-full border border-line bg-white p-1.5 text-slate-500 shadow-sm hover:text-accent"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-navy/30" onClick={() => setMobileOpen(false)} aria-label="Close menu" />
          <aside className="relative h-full w-72 border-r border-line bg-white">
            <button className="absolute right-4 top-4 text-slate-500" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
              <X className="h-5 w-5" />
            </button>
            <SidebarContent
              collapsed={false}
              section={section}
              onSectionChange={(next) => {
                onSectionChange(next);
                setMobileOpen(false);
              }}
            />
          </aside>
        </div>
      )}
      <div className={`transition-all duration-200 ${collapsed ? "lg:pl-[76px]" : "lg:pl-64"}`}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white/90 px-4 backdrop-blur sm:px-7">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>
            <div className="lg:hidden">
              <p className="text-sm font-bold text-ink">Transport Intelligence</p>
              <p className="text-[10px] uppercase tracking-widest text-slate-400">Analytics workspace</p>
            </div>
            <div className="hidden items-center gap-2 text-sm text-slate-500 lg:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Static intelligence layer connected
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-semibold text-slate-500 sm:inline-flex">
              Stage 2 prototype
            </span>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy text-xs font-bold text-white">TI</span>
          </div>
        </header>
        <main className="mx-auto max-w-[1600px] px-4 py-7 sm:px-7 lg:px-10">{children}</main>
      </div>
    </div>
  );
}

function SidebarContent({
  collapsed,
  section,
  onSectionChange,
}: {
  collapsed: boolean;
  section: Section;
  onSectionChange: (section: Section) => void;
}) {
  return (
    <div className="flex h-full flex-col px-3 py-6">
      <div className={`mb-10 flex items-center gap-3 px-2 ${collapsed ? "justify-center" : ""}`}>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-navy text-white">
          <BusFront className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-sm font-bold text-ink">Transport</p>
            <p className="text-sm font-bold text-accent">Intelligence</p>
          </div>
        )}
      </div>
      {!collapsed && <p className="eyebrow mb-3 px-3">Workspace</p>}
      <nav className="space-y-1">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onSectionChange(id)}
            title={collapsed ? label : undefined}
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-semibold transition ${
              section === id ? "bg-blue-50 text-accent" : "text-slate-500 hover:bg-slate-50 hover:text-ink"
            } ${collapsed ? "justify-center" : ""}`}
          >
            <Icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && label}
          </button>
        ))}
      </nav>
      <div className="mt-auto">
        {!collapsed && (
          <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-4">
            <p className="text-xs font-bold text-blue-900">Research prototype</p>
            <p className="mt-2 text-[11px] leading-5 text-blue-800/75">
              Forecasts and fleet values are generated from the project’s static Python intelligence layer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
