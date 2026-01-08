import React, { useState } from "react";
import { api } from "../apiClient";

// Boltzmann constant in dBW/K/Hz
const K_DBW_PER_K_HZ = -228.6;

export const LinkBudgetCalculator: React.FC = () => {
  // UI in GHz and km, backend expects Hz and m
  const [frequencyGhz, setFrequencyGhz] = useState(30);
  const [distanceKm, setDistanceKm] = useState(40000);
  const [txPowerDbw, setTxPowerDbw] = useState(20);
  const [txGainDb, setTxGainDb] = useState(40);
  const [rxGainDb, setRxGainDb] = useState(40);
  const [txLossDb, setTxLossDb] = useState(1);
  const [rxLossDb, setRxLossDb] = useState(1);
  const [otherLossDb, setOtherLossDb] = useState(0);
  const [systemTempK, setSystemTempK] = useState(800);

  const [fsplDb, setFsplDb] = useState<number | null>(null);
  const [prDbw, setPrDbw] = useState<number | null>(null);
  const [cn0DbHz, setCn0DbHz] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.linkBudget({
        frequency_hz: frequencyGhz * 1e9,
        distance_m: distanceKm * 1e3,
        tx_power_dbw: txPowerDbw,
        tx_antenna_gain_db: txGainDb,
        rx_antenna_gain_db: rxGainDb,
        tx_losses_db: txLossDb,
        rx_losses_db: rxLossDb,
        other_losses_db: otherLossDb
      });
      setFsplDb(res.fspl_db);
      setPrDbw(res.received_power_dbw);
      // C/N0 = Pr - k - 10*log10(Tsys)
      // where k = -228.6 dBW/K/Hz, so C/N0 = Pr + 228.6 - 10*log10(Tsys)
      const cn0 = res.received_power_dbw - K_DBW_PER_K_HZ - 10 * Math.log10(systemTempK);
      setCn0DbHz(cn0);
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
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">FSPL:</span>
          <span className="formula">
            FSPL = 20·log<sub>10</sub>(4πdf/c)
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Received Power:</span>
          <span className="formula">
            P<sub>r</sub> = P<sub>t</sub> + G<sub>t</sub> + G<sub>r</sub> − FSPL − L<sub>tx</sub> − L<sub>rx</sub> − L<sub>other</sub>
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">C/N₀:</span>
          <span className="formula">
            C/N<sub>0</sub> = P<sub>r</sub> − k − 10·log<sub>10</sub>(T)
          </span>
        </div>
        <span className="formula-note">where k = −228.6 dBW/K/Hz</span>
      </div>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Freq (GHz)
          <input
            type="number"
            value={frequencyGhz}
            onChange={(e) => setFrequencyGhz(Number(e.target.value))}
          />
        </label>
        <label>
          Dist (km)
          <input
            type="number"
            value={distanceKm}
            onChange={(e) => setDistanceKm(Number(e.target.value))}
          />
        </label>
        <label>
          Tx Pwr (dBW)
          <input
            type="number"
            value={txPowerDbw}
            onChange={(e) => setTxPowerDbw(Number(e.target.value))}
          />
        </label>
        <label>
          Tx Gain (dB)
          <input
            type="number"
            value={txGainDb}
            onChange={(e) => setTxGainDb(Number(e.target.value))}
          />
        </label>
        <label>
          Rx Gain (dB)
          <input
            type="number"
            value={rxGainDb}
            onChange={(e) => setRxGainDb(Number(e.target.value))}
          />
        </label>
        <label>
          Tx Loss (dB)
          <input
            type="number"
            value={txLossDb}
            onChange={(e) => setTxLossDb(Number(e.target.value))}
          />
        </label>
        <label>
          Rx Loss (dB)
          <input
            type="number"
            value={rxLossDb}
            onChange={(e) => setRxLossDb(Number(e.target.value))}
          />
        </label>
        <label>
          Other Loss (dB)
          <input
            type="number"
            value={otherLossDb}
            onChange={(e) => setOtherLossDb(Number(e.target.value))}
          />
        </label>
        <label>
          Sys Temp (K)
          <input
            type="number"
            min={1}
            value={systemTempK}
            onChange={(e) => setSystemTempK(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {(fsplDb !== null || prDbw !== null || cn0DbHz !== null) && (
        <div className="results">
          {fsplDb !== null && (
            <p>
              <strong>FSPL:</strong> {fsplDb.toFixed(2)} dB
            </p>
          )}
          {prDbw !== null && (
            <p>
              <strong>Received Pwr:</strong> {prDbw.toFixed(2)} dBW
            </p>
          )}
          {cn0DbHz !== null && (
            <p>
              <strong>C/N₀:</strong> {cn0DbHz.toFixed(2)} dB-Hz
            </p>
          )}
        </div>
      )}
    </section>
  );
};


