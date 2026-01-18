import React, { useState } from "react";
import { api } from "../apiClient";

export const AzimuthCalculator: React.FC = () => {
  const [startLatDeg, setStartLatDeg] = useState(51.28);
  const [startLonDeg, setStartLonDeg] = useState(-1.58);
  const [endLatDeg, setEndLatDeg] = useState(0);
  const [endLonDeg, setEndLonDeg] = useState(-1);
  const [altitudeKm, setAltitudeKm] = useState(35786);

  const [azimuthDeg, setAzimuthDeg] = useState<number | null>(null);
  const [elevationDeg, setElevationDeg] = useState<number | null>(null);
  const [centralAngleDeg, setCentralAngleDeg] = useState<number | null>(null);
  const [nadirAngleDeg, setNadirAngleDeg] = useState<number | null>(null);
  const [terminalPhiDeg, setTerminalPhiDeg] = useState<number | null>(null);
  const [slantRangeKm, setSlantRangeKm] = useState<number | null>(null);
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
        end_lon_deg: endLonDeg,
        satellite_altitude_km: altitudeKm
      });
      setAzimuthDeg(res.azimuth_deg);
      setElevationDeg(res.elevation_deg);
      setCentralAngleDeg(res.central_angle_deg);
      setNadirAngleDeg(res.nadir_angle_deg);
      setTerminalPhiDeg(res.terminal_phi_deg);
      setSlantRangeKm(res.slant_range_km);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Azimuth &amp; Elevation</h2>
      <p className="card-subtitle">
        Compute the azimuth (initial bearing) and elevation angle from a ground station
        to a satellite using spherical trigonometry.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Azimuth:</span>
          <span className="formula">
            θ = atan2(sin(Δλ)·cos(φ<sub>2</sub>), cos(φ<sub>1</sub>)·sin(φ<sub>2</sub>) − sin(φ<sub>1</sub>)·cos(φ<sub>2</sub>)·cos(Δλ))
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Elevation:</span>
          <span className="formula">
            El = atan[(cos(λ) − R<sub>E</sub>/(R<sub>E</sub>+h)) / sin(λ)]
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Lambda (λ):</span>
          <span className="formula">
            λ = acos(sin(φ<sub>1</sub>)·sin(φ<sub>2</sub>) + cos(φ<sub>1</sub>)·cos(φ<sub>2</sub>)·cos(Δλ))
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Eta (η):</span>
          <span className="formula">
            η = atan[sin(λ)·r / (1 − cos(λ)·r)]
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Terminal φ:</span>
          <span className="formula">
            φ<sub>t</sub> = acos[(sin(φ<sub>1</sub>) − cos(λ)·sin(φ<sub>2</sub>)) / (sin(λ)·cos(φ<sub>2</sub>))]
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Range:</span>
          <span className="formula">
            d = √[(R<sub>E</sub>+h)² + R<sub>E</sub>² − 2·R<sub>E</sub>·(R<sub>E</sub>+h)·cos(λ)]
          </span>
        </div>
        <span className="formula-note">
          where λ is the central angle, r = R<sub>E</sub>/(R<sub>E</sub>+h), R<sub>E</sub> is Earth radius, h is satellite altitude
        </span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Ground Lat (°)
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
          Ground Lon (°)
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
          Subsat Lat (°)
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
          Subsat Lon (°)
          <input
            type="number"
            min={-180}
            max={180}
            step="any"
            value={endLonDeg}
            onChange={(e) => setEndLonDeg(Number(e.target.value))}
          />
        </label>
        <label>
          Altitude (km)
          <input
            type="number"
            min={0}
            step="any"
            value={altitudeKm}
            onChange={(e) => setAltitudeKm(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(azimuthDeg !== null || elevationDeg !== null || centralAngleDeg !== null || nadirAngleDeg !== null || terminalPhiDeg !== null || slantRangeKm !== null) && (
        <div className="results">
          {azimuthDeg !== null && (
            <p>
              <strong>Azimuth:</strong> {azimuthDeg.toFixed(2)}°
            </p>
          )}
          {elevationDeg !== null && (
            <p>
              <strong>Elevation:</strong> {elevationDeg.toFixed(2)}°
              {elevationDeg < 0 && <span className="warning-text"> (below horizon)</span>}
            </p>
          )}
          {centralAngleDeg !== null && (
            <p>
              <strong>Lambda (λ):</strong> {centralAngleDeg.toFixed(2)}°
            </p>
          )}
          {nadirAngleDeg !== null && (
            <p>
              <strong>Eta (η):</strong> {nadirAngleDeg.toFixed(2)}°
            </p>
          )}
          {terminalPhiDeg !== null && (
            <p>
              <strong>Terminal φ:</strong> {terminalPhiDeg.toFixed(2)}°
            </p>
          )}
          {slantRangeKm !== null && (
            <p>
              <strong>Slant Range:</strong> {slantRangeKm.toFixed(2)} km
            </p>
          )}
        </div>
      )}
    </section>
  );
};
