import React, { useState } from "react";
import { api } from "../apiClient";

export const PhasedArrayGainCalculator: React.FC = () => {
  const [elementGainDb, setElementGainDb] = useState(10);
  const [numElements, setNumElements] = useState(64);
  const [efficiency, setEfficiency] = useState(0.9);

  const [arrayGainDb, setArrayGainDb] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.phasedArrayGain({
        element_gain_db: elementGainDb,
        num_elements: numElements,
        array_efficiency: efficiency
      });
      setArrayGainDb(res.array_gain_db);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Phased Array Gain</h2>
      <p className="card-subtitle">Array gain from element gain, count, and efficiency.</p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Elem Gain (dB)
          <input
            type="number"
            value={elementGainDb}
            onChange={(e) => setElementGainDb(Number(e.target.value))}
          />
        </label>
        <label>
          # Elements
          <input
            type="number"
            min={1}
            value={numElements}
            onChange={(e) => setNumElements(Number(e.target.value))}
          />
        </label>
        <label>
          Efficiency
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={efficiency}
            onChange={(e) => setEfficiency(Number(e.target.value))}
          />
        </label>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {arrayGainDb !== null && (
        <div className="results">
          <p>
            <strong>Array Gain:</strong> {arrayGainDb.toFixed(2)} dB
          </p>
        </div>
      )}
    </section>
  );
};



