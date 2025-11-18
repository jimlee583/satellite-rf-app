import React, { useState } from "react";
import { api } from "../apiClient";

export const GTCalculator: React.FC = () => {
  const [gainDb, setGainDb] = useState(40);
  const [tempK, setTempK] = useState(500);

  const [gtDbPerK, setGtDbPerK] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
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
      <p className="card-subtitle">Antenna gain to noise temperature.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Antenna Gain (dB)
          <input
            type="number"
            value={gainDb}
            onChange={(e) => setGainDb(Number(e.target.value))}
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



