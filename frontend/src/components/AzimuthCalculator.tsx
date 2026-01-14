import React, { useState } from "react";
import { api } from "../apiClient";

export const AzimuthCalculator: React.FC = () => {
  const [startLatDeg, setStartLatDeg] = useState(40.7128);
  const [startLonDeg, setStartLonDeg] = useState(-74.006);
  const [endLatDeg, setEndLatDeg] = useState(51.5074);
  const [endLonDeg, setEndLonDeg] = useState(-0.1278);

  const [azimuthDeg, setAzimuthDeg] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.azimuth({
        start_lat_deg: startLatDeg,
        start_lon_deg: startLonDeg,
        end_lat_deg: endLatDeg,
        end_lon_deg: endLonDeg
      });
      setAzimuthDeg(res.azimuth_deg);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Azimuth (Initial Bearing)</h2>
      <p className="card-subtitle">
        Compute the initial bearing from one point to another on a sphere using the
        spherical law of cosines.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Azimuth:</span>
          <span className="formula">
            θ = atan2(sin(Δλ)·cos(φ<sub>2</sub>), cos(φ<sub>1</sub>)·sin(φ<sub>2</sub>) − sin(φ<sub>1</sub>)·cos(φ<sub>2</sub>)·cos(Δλ))
          </span>
        </div>
        <span className="formula-note">
          where φ<sub>1</sub>, φ<sub>2</sub> are latitudes and Δλ = λ<sub>2</sub> − λ<sub>1</sub>
        </span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Start Lat (°)
          <input
            type="number"
            min={-90}
            max={90}
            step="any"
            value={startLatDeg}
            onChange={(e) => setStartLatDeg(Number(e.target.value))}
          />
        </label>
        <label>
          Start Lon (°)
          <input
            type="number"
            min={-180}
            max={180}
            step="any"
            value={startLonDeg}
            onChange={(e) => setStartLonDeg(Number(e.target.value))}
          />
        </label>
        <label>
          End Lat (°)
          <input
            type="number"
            min={-90}
            max={90}
            step="any"
            value={endLatDeg}
            onChange={(e) => setEndLatDeg(Number(e.target.value))}
          />
        </label>
        <label>
          End Lon (°)
          <input
            type="number"
            min={-180}
            max={180}
            step="any"
            value={endLonDeg}
            onChange={(e) => setEndLonDeg(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {azimuthDeg !== null && (
        <div className="results">
          <p>
            <strong>Azimuth:</strong> {azimuthDeg.toFixed(2)}°
          </p>
        </div>
      )}
    </section>
  );
};
