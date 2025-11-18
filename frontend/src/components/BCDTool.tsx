import React, { useState } from "react";
import { api } from "../apiClient";

export const BCDTool: React.FC = () => {
  const [mode, setMode] = useState<"encode" | "decode">("encode");

  const [value, setValue] = useState(123);
  const [digits, setDigits] = useState(4);
  const [bcdBits, setBcdBits] = useState("0001 0010 0011");

  const [encodeResult, setEncodeResult] = useState<string | null>(null);
  const [decodeResult, setDecodeResult] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleEncode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.bcdEncode({ value, digits });
      setEncodeResult(res.bcd_bits);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.bcdDecode({ bcd_bits: bcdBits });
      setDecodeResult(res.value);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <div className="card-header-row">
        <div>
          <h2>BCD Utility</h2>
          <p className="card-subtitle">Binary Coded Decimal encode/decode.</p>
        </div>
        <div className="segmented-control">
          <button
            type="button"
            className={mode === "encode" ? "active" : ""}
            onClick={() => setMode("encode")}
          >
            Encode
          </button>
          <button
            type="button"
            className={mode === "decode" ? "active" : ""}
            onClick={() => setMode("decode")}
          >
            Decode
          </button>
        </div>
      </div>

      {mode === "encode" ? (
        <form onSubmit={handleEncode} className="form-grid">
          <label>
            Integer Value
            <input
              type="number"
              value={value}
              min={0}
              onChange={(e) => setValue(Number(e.target.value))}
            />
          </label>
          <label>
            Digits
            <input
              type="number"
              value={digits}
              min={1}
              onChange={(e) => setDigits(Number(e.target.value))}
            />
          </label>

          <button type="submit" className="primary" disabled={loading}>
            {loading ? "Encoding..." : "Encode"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleDecode} className="form-grid">
          <label>
            BCD Bits
            <input
              type="text"
              value={bcdBits}
              onChange={(e) => setBcdBits(e.target.value)}
              placeholder="0001 0010 0011"
            />
          </label>

          <button type="submit" className="primary" disabled={loading}>
            {loading ? "Decoding..." : "Decode"}
          </button>
        </form>
      )}

      {error && <p className="error-text">{error}</p>}

      {mode === "encode" && encodeResult && (
        <div className="results">
          <p>
            <strong>BCD:</strong> <code>{encodeResult}</code>
          </p>
        </div>
      )}

      {mode === "decode" && decodeResult !== null && (
        <div className="results">
          <p>
            <strong>Value:</strong> {decodeResult}
          </p>
        </div>
      )}
    </section>
  );
};



