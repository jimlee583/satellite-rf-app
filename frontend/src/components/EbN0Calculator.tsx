import React, { useState } from "react";
import { api } from "../apiClient";

export const EbN0Calculator: React.FC = () => {
  const [cn0DbHz, setCn0DbHz] = useState(80);
  const [dataRateBps, setDataRateBps] = useState(1e6);

  const [ebn0Db, setEbn0Db] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.ebn0({
        cn0_db_hz: cn0DbHz,
        data_rate_bps: dataRateBps
      });
      setEbn0Db(res.ebn0_db);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Eb/N0</h2>
      <p className="card-subtitle">Energy per bit to noise spectral density.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          C/N₀ (dB-Hz)
          <input
            type="number"
            value={cn0DbHz}
            onChange={(e) => setCn0DbHz(Number(e.target.value))}
          />
        </label>
        <label>
          Rate (bps)
          <input
            type="number"
            value={dataRateBps}
            onChange={(e) => setDataRateBps(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {ebn0Db !== null && (
        <div className="results">
          <p>
            <strong>Eb/N0:</strong> {ebn0Db.toFixed(2)} dB
          </p>
        </div>
      )}
    </section>
  );
};



