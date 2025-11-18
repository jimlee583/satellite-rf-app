import React, { useState } from "react";
import { api } from "../apiClient";

export const EIRPCalculator: React.FC = () => {
  const [txPowerDbw, setTxPowerDbw] = useState(20);
  const [txGainDb, setTxGainDb] = useState(40);
  const [txLossDb, setTxLossDb] = useState(1);

  const [eirpDbw, setEirpDbw] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.eirp({
        tx_power_dbw: txPowerDbw,
        tx_antenna_gain_db: txGainDb,
        tx_losses_db: txLossDb
      });
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
      <p className="card-subtitle">Effective Isotropic Radiated Power.</p>
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
          Tx Antenna Gain (dB)
          <input
            type="number"
            value={txGainDb}
            onChange={(e) => setTxGainDb(Number(e.target.value))}
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

      {eirpDbw !== null && (
        <div className="results">
          <p>
            <strong>EIRP:</strong> {eirpDbw.toFixed(2)} dBW
          </p>
        </div>
      )}
    </section>
  );
};


