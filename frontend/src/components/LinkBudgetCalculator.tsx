import React, { useState } from "react";
import { api } from "../apiClient";

export const LinkBudgetCalculator: React.FC = () => {
  const [frequencyHz, setFrequencyHz] = useState(12e9);
  const [distanceM, setDistanceM] = useState(3.6e7);
  const [txPowerDbw, setTxPowerDbw] = useState(20);
  const [txGainDb, setTxGainDb] = useState(40);
  const [rxGainDb, setRxGainDb] = useState(40);
  const [txLossDb, setTxLossDb] = useState(1);
  const [rxLossDb, setRxLossDb] = useState(1);
  const [otherLossDb, setOtherLossDb] = useState(0);

  const [fsplDb, setFsplDb] = useState<number | null>(null);
  const [prDbw, setPrDbw] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.linkBudget({
        frequency_hz: frequencyHz,
        distance_m: distanceM,
        tx_power_dbw: txPowerDbw,
        tx_antenna_gain_db: txGainDb,
        rx_antenna_gain_db: rxGainDb,
        tx_losses_db: txLossDb,
        rx_losses_db: rxLossDb,
        other_losses_db: otherLossDb
      });
      setFsplDb(res.fspl_db);
      setPrDbw(res.received_power_dbw);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Link Budget</h2>
      <p className="card-subtitle">Compute received power and free-space path loss.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Frequency (Hz)
          <input
            type="number"
            value={frequencyHz}
            onChange={(e) => setFrequencyHz(Number(e.target.value))}
          />
        </label>
        <label>
          Distance (m)
          <input
            type="number"
            value={distanceM}
            onChange={(e) => setDistanceM(Number(e.target.value))}
          />
        </label>
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
          Rx Antenna Gain (dB)
          <input
            type="number"
            value={rxGainDb}
            onChange={(e) => setRxGainDb(Number(e.target.value))}
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
        <label>
          Rx Losses (dB)
          <input
            type="number"
            value={rxLossDb}
            onChange={(e) => setRxLossDb(Number(e.target.value))}
          />
        </label>
        <label>
          Other Losses (dB)
          <input
            type="number"
            value={otherLossDb}
            onChange={(e) => setOtherLossDb(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(fsplDb !== null || prDbw !== null) && (
        <div className="results">
          {fsplDb !== null && (
            <p>
              <strong>FSPL:</strong> {fsplDb.toFixed(2)} dB
            </p>
          )}
          {prDbw !== null && (
            <p>
              <strong>Received Power:</strong> {prDbw.toFixed(2)} dBW
            </p>
          )}
        </div>
      )}
    </section>
  );
};


