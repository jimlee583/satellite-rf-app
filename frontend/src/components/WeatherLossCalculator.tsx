import React, { useState } from "react";
import { api } from "../apiClient";

export const WeatherLossCalculator: React.FC = () => {
  const [satelliteLongitude, setSatelliteLongitude] = useState(-100);
  const [userLatitude, setUserLatitude] = useState(40);
  const [userLongitude, setUserLongitude] = useState(-100);
  const [availabilityPercent, setAvailabilityPercent] = useState(99.5);
  const [frequencyGhz, setFrequencyGhz] = useState(30);

  const [elevationDeg, setElevationDeg] = useState<number | null>(null);
  const [rainRateMmHr, setRainRateMmHr] = useState<number | null>(null);
  const [weatherLossDb, setWeatherLossDb] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.weatherLoss({
        satellite_longitude_deg: satelliteLongitude,
        user_latitude_deg: userLatitude,
        user_longitude_deg: userLongitude,
        availability_percent: availabilityPercent,
        frequency_ghz: frequencyGhz
      });
      setElevationDeg(res.elevation_deg);
      setRainRateMmHr(res.rain_rate_mm_hr);
      setWeatherLossDb(res.weather_loss_db);
    } catch (err) {
      setError((err as Error).message);
      setElevationDeg(null);
      setRainRateMmHr(null);
      setWeatherLossDb(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Weather Loss</h2>
      <p className="card-subtitle">
        Calculate rain attenuation for a given availability using simplified ITU-R models.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Specific Atten:</span>
          <span className="formula">
            γ<sub>R</sub> = k·R<sup>α</sup> (dB/km)
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Total Loss:</span>
          <span className="formula">
            A = γ<sub>R</sub>·L<sub>eff</sub>
          </span>
        </div>
        <span className="formula-note">
          ITU-R P.838 coefficients; R = rain rate for availability %
        </span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Sat Long (°)
          <input
            type="number"
            min={-180}
            max={180}
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
          Availability (%)
          <input
            type="number"
            min={97}
            max={99.999}
            step={0.001}
            value={availabilityPercent}
            onChange={(e) => setAvailabilityPercent(Number(e.target.value))}
          />
        </label>
        <label>
          Freq (GHz)
          <input
            type="number"
            min={1}
            max={100}
            step="any"
            value={frequencyGhz}
            onChange={(e) => setFrequencyGhz(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(elevationDeg !== null || rainRateMmHr !== null || weatherLossDb !== null) && (
        <div className="results">
          {elevationDeg !== null && (
            <p>
              <strong>Elevation:</strong> {elevationDeg.toFixed(2)}°
            </p>
          )}
          {rainRateMmHr !== null && (
            <p>
              <strong>Rain Rate:</strong> {rainRateMmHr.toFixed(1)} mm/hr
            </p>
          )}
          {weatherLossDb !== null && (
            <p>
              <strong>Weather Loss:</strong> {weatherLossDb.toFixed(2)} dB
            </p>
          )}
        </div>
      )}
    </section>
  );
};
