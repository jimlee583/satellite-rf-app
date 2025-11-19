import React, { useState } from "react";
import { api } from "../apiClient";

const LIGHT_SPEED = 299_792_458; // m/s

function parabolicGainDb(efficiency: number, diameterM: number, frequencyGhz: number): number {
  const frequencyHz = frequencyGhz * 1e9;
  const wavelength = LIGHT_SPEED / frequencyHz;
  const gainLinear = efficiency * Math.PI * Math.PI * (diameterM * diameterM) / (wavelength * wavelength);
  return 10 * Math.log10(gainLinear);
}

export const GTCalculator: React.FC = () => {
  const [tempK, setTempK] = useState(500);

  // Antenna parameters instead of direct gain
  const [efficiency, setEfficiency] = useState(0.6);
  const [diameterM, setDiameterM] = useState(1.2);
  const [frequencyGhz, setFrequencyGhz] = useState(12);

  const [gtDbPerK, setGtDbPerK] = useState<number | null>(null);
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

    const gainDb = parabolicGainDb(efficiency, diameterM, frequencyGhz);

    try {
      const res = await api.gt({
        antenna_gain_db: gainDb,
        system_noise_temp_k: tempK
      });
      setGtDbPerK(res.gt_db_per_k);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>G/T</h2>
      <p className="card-subtitle">
        Antenna gain-to-noise temperature using reflector efficiency, diameter, and frequency.
      </p>
      <form onSubmit={handleSubmit} className="form-grid">
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
            step={0.01}
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
          System Noise Temp (K)
          <input
            type="number"
            value={tempK}
            onChange={(e) => setTempK(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {gtDbPerK !== null && (
        <div className="results">
          <p>
            <strong>G/T:</strong> {gtDbPerK.toFixed(2)} dB/K
          </p>
        </div>
      )}
    </section>
  );
};


