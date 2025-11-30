import React, { useState } from "react";
import { api } from "../apiClient";

const LIGHT_SPEED = 299_792_458; // m/s

function parabolicGainDb(efficiency: number, diameterM: number, frequencyGhz: number): number {
  const frequencyHz = frequencyGhz * 1e9;
  const wavelength = LIGHT_SPEED / frequencyHz;
  const gainLinear = efficiency * Math.PI * Math.PI * (diameterM * diameterM) / (wavelength * wavelength);
  return 10 * Math.log10(gainLinear);
}

function beamwidth3dBDeg(diameterM: number, frequencyGhz: number): number {
  // Approximate half-power (3 dB) beamwidth for a circular parabolic reflector:
  // θ_3dB ≈ 70 * λ / D (degrees)
  const frequencyHz = frequencyGhz * 1e9;
  const wavelength = LIGHT_SPEED / frequencyHz;
  return 70 * (wavelength / diameterM);
}

export const GTCalculator: React.FC = () => {
  const [tempK, setTempK] = useState(500);

  // Antenna parameters instead of direct gain
  const [efficiency, setEfficiency] = useState(0.6);
  const [diameterM, setDiameterM] = useState(1.2);
  const [frequencyGhz, setFrequencyGhz] = useState(30);

  const [gtDbPerK, setGtDbPerK] = useState<number | null>(null);
  const [gainDb, setGainDb] = useState<number | null>(null);
  const [beamwidthDeg, setBeamwidthDeg] = useState<number | null>(null);
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
    const computedBeamwidth = beamwidth3dBDeg(diameterM, frequencyGhz);

    try {
      const res = await api.gt({
        antenna_gain_db: computedGainDb,
        system_noise_temp_k: tempK
      });
      setGainDb(computedGainDb);
      setBeamwidthDeg(computedBeamwidth);
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
          Efficiency
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
          Diameter (m)
          <input
            type="number"
            min={0}
            step={0.1}
            value={diameterM}
            onChange={(e) => setDiameterM(Number(e.target.value))}
          />
        </label>
        <label>
          Freq (GHz)
          <input
            type="number"
            min={0}
            step="any"
            value={frequencyGhz}
            onChange={(e) => setFrequencyGhz(Number(e.target.value))}
          />
        </label>
        <label>
          Noise Temp (K)
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

      {(gainDb !== null || gtDbPerK !== null || beamwidthDeg !== null) && (
        <div className="results">
          {gainDb !== null && (
            <p>
              <strong>Antenna Gain:</strong> {gainDb.toFixed(2)} dB
            </p>
          )}
          {beamwidthDeg !== null && (
            <p>
              <strong>3 dB Beamwidth (nadir):</strong> {beamwidthDeg.toFixed(2)}°
            </p>
          )}
          {gtDbPerK !== null && (
            <p>
              <strong>G/T:</strong> {gtDbPerK.toFixed(2)} dB/K
            </p>
          )}
        </div>
      )}
    </section>
  );
};


