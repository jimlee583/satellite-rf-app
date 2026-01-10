import React, { useState } from "react";
import { api } from "../apiClient";

export const ScanLossCalculator: React.FC = () => {
  const [satelliteLongitude, setSatelliteLongitude] = useState(-100);
  const [userLatitude, setUserLatitude] = useState(37);
  const [userLongitude, setUserLongitude] = useState(-122);
  const [scanExponent, setScanExponent] = useState(1.3);

  const [scanAngleDeg, setScanAngleDeg] = useState<number | null>(null);
  const [scanLossDb, setScanLossDb] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.scanLoss({
        satellite_longitude_deg: satelliteLongitude,
        user_latitude_deg: userLatitude,
        user_longitude_deg: userLongitude,
        scan_exponent: scanExponent
      });
      setScanAngleDeg(res.scan_angle_deg);
      setScanLossDb(res.scan_loss_db);
    } catch (err) {
      setError((err as Error).message);
      setScanAngleDeg(null);
      setScanLossDb(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>ESA Scan Loss</h2>
      <p className="card-subtitle">
        Calculate scan loss for a satellite-based electronically steered array pointing at a ground user.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Central Angle:</span>
          <span className="formula">
            cos(γ) = cos(φ<sub>user</sub>)·cos(ΔL)
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Nadir Angle:</span>
          <span className="formula">
            θ<sub>scan</sub> = arcsin[(R<sub>E</sub>/r<sub>sat</sub>)·sin(γ)]
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Scan Loss:</span>
          <span className="formula">
            L<sub>scan</sub> = −10·n·log<sub>10</sub>(cos(θ<sub>scan</sub>))
          </span>
        </div>
        <span className="formula-note">
          where ΔL = longitude difference, R<sub>E</sub> = 6371 km, r<sub>sat</sub> = 42164 km
        </span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Sat Long (°)
          <input
            type="number"
            step="any"
            value={satelliteLongitude}
            onChange={(e) => setSatelliteLongitude(Number(e.target.value))}
          />
        </label>
        <label>
          User Lat (°)
          <input
            type="number"
            min={-90}
            max={90}
            step="any"
            value={userLatitude}
            onChange={(e) => setUserLatitude(Number(e.target.value))}
          />
        </label>
        <label>
          User Long (°)
          <input
            type="number"
            min={-180}
            max={180}
            step="any"
            value={userLongitude}
            onChange={(e) => setUserLongitude(Number(e.target.value))}
          />
        </label>
        <label>
          Exponent (n)
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={scanExponent}
            onChange={(e) => setScanExponent(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(scanAngleDeg !== null || scanLossDb !== null) && (
        <div className="results">
          {scanAngleDeg !== null && (
            <p>
              <strong>Scan Angle:</strong> {scanAngleDeg.toFixed(2)}°
            </p>
          )}
          {scanLossDb !== null && (
            <p>
              <strong>Scan Loss:</strong> {scanLossDb.toFixed(2)} dB
            </p>
          )}
        </div>
      )}
    </section>
  );
};
