import React, { useState } from "react";
import { api } from "../apiClient";

const LIGHT_SPEED = 299_792_458; // m/s

function parabolicGainDb(efficiency: number, diameterM: number, frequencyGhz: number): number {
  const frequencyHz = frequencyGhz * 1e9;
  const wavelength = LIGHT_SPEED / frequencyHz;
  const gainLinear = efficiency * Math.PI * Math.PI * (diameterM * diameterM) / (wavelength * wavelength);
  return 10 * Math.log10(gainLinear);
}

export const EIRPCalculator: React.FC = () => {
  const [txPowerDbw, setTxPowerDbw] = useState(20);
  const [txLossDb, setTxLossDb] = useState(1);

  // Antenna parameters instead of direct gain
  const [efficiency, setEfficiency] = useState(0.6);
  const [diameterM, setDiameterM] = useState(1.2);
  const [frequencyGhz, setFrequencyGhz] = useState(12);

  const [gainDb, setGainDb] = useState<number | null>(null);
  const [eirpDbw, setEirpDbw] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (efficiency <= 0 || efficiency > 1 || diameterM <= 0 || frequencyGhz <= 0) {
      setLoading(false);
      setError("Efficiency must be in (0,1], and diameter/frequency must be positive.");
      return;
    }

    const computedGainDb = parabolicGainDb(efficiency, diameterM, frequencyGhz);

    try {
      const res = await api.eirp({
        tx_power_dbw: txPowerDbw,
        tx_antenna_gain_db: computedGainDb,
        tx_losses_db: txLossDb
      });
      setGainDb(computedGainDb);
      setEirpDbw(res.eirp_dbw);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>EIRP</h2>
      <p className="card-subtitle">
        Effective Isotropic Radiated Power using reflector efficiency, diameter, and frequency.
      </p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Tx Power (dBW)
          <input
            type="number"
            value={txPowerDbw}
            onChange={(e) => setTxPowerDbw(Number(e.target.value))}
          />
        </label>
        <label>
          Antenna Efficiency (0–1)
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={efficiency}
            onChange={(e) => setEfficiency(Number(e.target.value))}
          />
        </label>
        <label>
          Reflector Diameter (m)
          <input
            type="number"
            min={0}
            step={0.1}
            value={diameterM}
            onChange={(e) => setDiameterM(Number(e.target.value))}
          />
        </label>
        <label>
          Frequency (GHz)
          <input
            type="number"
            min={0}
            step={1}
            value={frequencyGhz}
            onChange={(e) => setFrequencyGhz(Number(e.target.value))}
          />
        </label>
        <label>
          Tx Losses (dB)
          <input
            type="number"
            value={txLossDb}
            onChange={(e) => setTxLossDb(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(eirpDbw !== null || gainDb !== null) && (
        <div className="results">
          {gainDb !== null && (
            <p>
              <strong>Antenna Gain:</strong> {gainDb.toFixed(2)} dB
            </p>
          )}
          {eirpDbw !== null && (
            <p>
              <strong>EIRP:</strong> {eirpDbw.toFixed(2)} dBW
            </p>
          )}
        </div>
      )}
    </section>
  );
};


