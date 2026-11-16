import { useState } from "react";
import { Shell, type Section } from "./components/Shell";
import { PageErrorBoundary } from "./components/States";
import { DemandAnalysis } from "./pages/DemandAnalysis";
import { FleetPlanning } from "./pages/FleetPlanning";
import { Forecasting } from "./pages/Forecasting";
import { Overview } from "./pages/Overview";

export default function App() {
  const [section, setSection] = useState<Section>("overview");
  return (
    <Shell section={section} onSectionChange={setSection}>
      {section === "overview" && <Overview />}
      {section === "forecasting" && (
        <PageErrorBoundary pageName="Demand forecasting">
          <Forecasting />
        </PageErrorBoundary>
      )}
      {section === "analysis" && <DemandAnalysis />}
      {section === "fleet" && <FleetPlanning />}
    </Shell>
  );
}
