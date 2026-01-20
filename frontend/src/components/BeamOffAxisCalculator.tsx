import React, { useState } from "react";
import { api } from "../apiClient";

export const BeamOffAxisCalculator: React.FC = () => {
  // Satellite position (GEO at 0° longitude by default)
  const [satLatDeg, setSatLatDeg] = useState(0);
  const [satLonDeg, setSatLonDeg] = useState(0);
  const [satAltKm, setSatAltKm] = useState(35786);

  // User terminal position
  const [userLatDeg, setUserLatDeg] = useState(40);
  const [userLonDeg, setUserLonDeg] = useState(-5);
  const [userAltKm, setUserAltKm] = useState(0);

  // Beam center position
  const [beamCenterLatDeg, setBeamCenterLatDeg] = useState(45);
  const [beamCenterLonDeg, setBeamCenterLonDeg] = useState(0);
  const [beamCenterAltKm, setBeamCenterAltKm] = useState(0);

  const [result, setResult] = useState<{
    off_axis_angle_deg: number;
    sat_to_user_lambda_deg: number;
    sat_to_user_eta_deg: number;
    sat_to_user_phi_deg: number;
    sat_to_user_x: number;
    sat_to_user_y: number;
    sat_to_user_z: number;
    sat_to_beam_lambda_deg: number;
    sat_to_beam_eta_deg: number;
    sat_to_beam_phi_deg: number;
    sat_to_beam_x: number;
    sat_to_beam_y: number;
    sat_to_beam_z: number;
    user_elevation_deg: number;
    user_slant_range_km: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.beamOffAxis({
        sat_lat_deg: satLatDeg,
        sat_lon_deg: satLonDeg,
        sat_alt_km: satAltKm,
        user_lat_deg: userLatDeg,
        user_lon_deg: userLonDeg,
        user_alt_km: userAltKm,
        beam_center_lat_deg: beamCenterLatDeg,
        beam_center_lon_deg: beamCenterLonDeg,
        beam_center_alt_km: beamCenterAltKm
      });
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Beam Off-Axis Angle</h2>
      <p className="card-subtitle">
        Compute the angle between the satellite-to-beam-center and satellite-to-user
        vectors using the 3D vector method.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Off-Axis Angle:</span>
          <span className="formula">
            θ = arccos[(V<sub>beam</sub> · V<sub>user</sub>) / (|V<sub>beam</sub>| · |V<sub>user</sub>|)]
          </span>
        </div>
        <span className="formula-note">
          Positions converted to ECEF coordinates using WGS84 ellipsoid
        </span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <fieldset>
          <legend>Satellite</legend>
          <label>
            Lat (°)
            <input
              type="number"
              min={-90}
              max={90}
              step="any"
              value={satLatDeg}
              onChange={(e) => setSatLatDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Lon (°)
            <input
              type="number"
              min={-180}
              max={180}
              step="any"
              value={satLonDeg}
              onChange={(e) => setSatLonDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Alt (km)
            <input
              type="number"
              min={0}
              step="any"
              value={satAltKm}
              onChange={(e) => setSatAltKm(Number(e.target.value))}
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>User Terminal</legend>
          <label>
            Lat (°)
            <input
              type="number"
              min={-90}
              max={90}
              step="any"
              value={userLatDeg}
              onChange={(e) => setUserLatDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Lon (°)
            <input
              type="number"
              min={-180}
              max={180}
              step="any"
              value={userLonDeg}
              onChange={(e) => setUserLonDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Alt (km)
            <input
              type="number"
              min={0}
              step="any"
              value={userAltKm}
              onChange={(e) => setUserAltKm(Number(e.target.value))}
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Beam Center</legend>
          <label>
            Lat (°)
            <input
              type="number"
              min={-90}
              max={90}
              step="any"
              value={beamCenterLatDeg}
              onChange={(e) => setBeamCenterLatDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Lon (°)
            <input
              type="number"
              min={-180}
              max={180}
              step="any"
              value={beamCenterLonDeg}
              onChange={(e) => setBeamCenterLonDeg(Number(e.target.value))}
            />
          </label>
          <label>
            Alt (km)
            <input
              type="number"
              min={0}
              step="any"
              value={beamCenterAltKm}
              onChange={(e) => setBeamCenterAltKm(Number(e.target.value))}
            />
          </label>
        </fieldset>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {result !== null && (
        <div className="results">
          <h3>Off-Axis Angle (dot product)</h3>
          <p><strong>θ:</strong> {result.off_axis_angle_deg.toFixed(4)}°</p>

          <h3>User Terminal → Satellite</h3>
          <p><strong>Elevation Angle:</strong> {result.user_elevation_deg.toFixed(4)}°</p>
          <p><strong>Slant Range:</strong> {result.user_slant_range_km.toFixed(2)} km</p>

          <h3>Satellite → User Terminal</h3>
          <p><strong>λ (lambda):</strong> {result.sat_to_user_lambda_deg.toFixed(4)}°</p>
          <p><strong>η (eta):</strong> {result.sat_to_user_eta_deg.toFixed(4)}°</p>
          <p><strong>φ (phi):</strong> {result.sat_to_user_phi_deg.toFixed(4)}°</p>
          <p>
            <strong>Unit Vector (x, y, z):</strong> ({result.sat_to_user_x.toFixed(6)}, {result.sat_to_user_y.toFixed(6)}, {result.sat_to_user_z.toFixed(6)})
          </p>

          <h3>Satellite → Beam Center</h3>
          <p><strong>λ (lambda):</strong> {result.sat_to_beam_lambda_deg.toFixed(4)}°</p>
          <p><strong>η (eta):</strong> {result.sat_to_beam_eta_deg.toFixed(4)}°</p>
          <p><strong>φ (phi):</strong> {result.sat_to_beam_phi_deg.toFixed(4)}°</p>
          <p>
            <strong>Unit Vector (x, y, z):</strong> ({result.sat_to_beam_x.toFixed(6)}, {result.sat_to_beam_y.toFixed(6)}, {result.sat_to_beam_z.toFixed(6)})
          </p>
        </div>
      )}
    </section>
  );
};
