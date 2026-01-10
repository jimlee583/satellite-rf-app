import React from "react";
import { LinkBudgetCalculator } from "./components/LinkBudgetCalculator";
import { EIRPCalculator } from "./components/EIRPCalculator";
import { GTCalculator } from "./components/GTCalculator";
import { EbN0Calculator } from "./components/EbN0Calculator";
import { PhasedArrayGainCalculator } from "./components/PhasedArrayGainCalculator";
import { ScanLossCalculator } from "./components/ScanLossCalculator";

const App: React.FC = () => {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Satellite RF Communications Calculator</h1>
          <p className="app-subtitle">
            Quick evaluations of link budgets, EIRP, G/T, Eb/N0, phased arrays, and ESA scan loss.
          </p>
        </div>
        <span className="app-badge">FastAPI · React · TypeScript</span>
      </header>

      <main className="app-main">
        <div className="cards-grid">
          <LinkBudgetCalculator />
          <EIRPCalculator />
          <GTCalculator />
          <EbN0Calculator />
          <PhasedArrayGainCalculator />
          <ScanLossCalculator />
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Backend at <code>http://localhost:8000/api</code>, frontend at{" "}
          <code>http://localhost:3000</code>.
        </p>
      </footer>
    </div>
  );
};

export default App;



