import React, { useState, useEffect, useRef } from "react";
import { api } from "../apiClient";

// Debounce hook - must be defined outside the component
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Skip debounce on first render to set initial value immediately
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Terminal preset definitions
type FrequencyBand = "x" | "ka";

interface TerminalPreset {
  name: string;
  band: FrequencyBand;
  eirp_dbw: number;
  gt_db_per_k: number;
  npr_db: number | null;  // null = ideal/linear
}

const TERMINAL_PRESETS: Record<string, TerminalPreset> = {
  // Custom (default placeholder) - defaults to Ka-band
  "custom": { name: "Custom", band: "ka", eirp_dbw: 50, gt_db_per_k: 20, npr_db: null },

  // Manpack terminals
  "manpack_x": { name: "Manpack (X-band)", band: "x", eirp_dbw: 43, gt_db_per_k: 12, npr_db: 18 },
  "manpack_ka": { name: "Manpack (Ka-band)", band: "ka", eirp_dbw: 40, gt_db_per_k: 14, npr_db: 16 },

  // SNAP 2.0m
  "snap_2m_x": { name: "SNAP 2.0m (X-band)", band: "x", eirp_dbw: 56, gt_db_per_k: 24, npr_db: 20 },
  "snap_2m_ka": { name: "SNAP 2.0m (Ka-band)", band: "ka", eirp_dbw: 52, gt_db_per_k: 28, npr_db: 18 },

  // STT-type
  "stt_x": { name: "STT (X-band)", band: "x", eirp_dbw: 60, gt_db_per_k: 28, npr_db: 22 },
  "stt_ka": { name: "STT (Ka-band)", band: "ka", eirp_dbw: 56, gt_db_per_k: 32, npr_db: 20 },

  // Airborne
  "airborne_ka": { name: "Airborne (Ka-band)", band: "ka", eirp_dbw: 48, gt_db_per_k: 18, npr_db: 16 },

  // Commercial gateway
  "gateway_x": { name: "Commercial Gateway (X-band)", band: "x", eirp_dbw: 72, gt_db_per_k: 36, npr_db: 24 },
  "gateway_ka": { name: "Commercial Gateway (Ka-band)", band: "ka", eirp_dbw: 68, gt_db_per_k: 40, npr_db: 22 },
};

// Default frequencies (GHz) based on band - using midpoint of each band
// X-band: Ground→Sat = 7.9-8.4 GHz (mid: 8.15), Sat→Ground = 7.25-7.75 GHz (mid: 7.5)
// Ka-band: Ground→Sat = 30-31 GHz (mid: 30.5), Sat→Ground = 20.2-21.2 GHz (mid: 20.7)
const FREQUENCY_DEFAULTS: Record<FrequencyBand, { uplink: number; downlink: number }> = {
  x: { uplink: 8.15, downlink: 7.5 },
  ka: { uplink: 30.5, downlink: 20.7 },
};

interface BeamState {
  center_lat_deg: number;
  center_lon_deg: number;
  cosine_exponent_n: number;
}

interface SingleHopResult {
  slant_range_km: number;
  elevation_angle_deg: number;
  off_axis_angle_deg: number;
  fspl_db: number;
  beam_roll_off_db: number;
  weather_atten_db: number;
  pointing_loss_db: number;
  polarization_loss_db: number;
  total_path_loss_db: number;
  cn0_db_hz: number;
  cn_db: number | null;
}

interface LinkDirectionResult {
  uplink: SingleHopResult;
  downlink: SingleHopResult;
  combined_cn0_db_hz: number;
  // Intermodulation
  ci_terminal_hpa_db: number | null;
  ci_satellite_transponder_db: number | null;
  ci_total_db: number | null;
  // Total C/(N+I)
  cnir_db: number | null;
  // DVB-S2 metrics
  combined_cn_db: number | null;
  es_n0_db: number | null;
  channel_bandwidth_mhz: number | null;
}

interface GeometryResult {
  terminal_a_slant_range_km: number;
  terminal_b_slant_range_km: number;
  terminal_a_elevation_deg: number;
  terminal_b_elevation_deg: number;
}

interface ElevationWarning {
  terminal: string;
  elevation_deg: number;
  threshold_deg: number;
  message: string;
}

interface DuplexSatelliteLinkResult {
  forward_link: LinkDirectionResult;
  return_link: LinkDirectionResult;
  geometry: GeometryResult;
  warnings: ElevationWarning[];
}

export const DuplexSatelliteLinkCalculator: React.FC = () => {
  // Terminal A
  const [terminalAPreset, setTerminalAPreset] = useState("custom");
  const [terminalABand, setTerminalABand] = useState<FrequencyBand>("ka");
  const [terminalALat, setTerminalALat] = useState(40);
  const [terminalALon, setTerminalALon] = useState(-5);
  const [terminalAAlt, setTerminalAAlt] = useState(0);
  const [terminalAEirp, setTerminalAEirp] = useState(60);
  const [terminalAGt, setTerminalAGt] = useState(35);
  const [terminalAPointingLoss, setTerminalAPointingLoss] = useState(0.5);
  const [terminalAPolLoss, setTerminalAPolLoss] = useState(0.3);
  const [terminalANpr, setTerminalANpr] = useState<number | null>(null);

  // Terminal B
  const [terminalBPreset, setTerminalBPreset] = useState("custom");
  const [terminalBBand, setTerminalBBand] = useState<FrequencyBand>("ka");
  const [terminalBLat, setTerminalBLat] = useState(35);
  const [terminalBLon, setTerminalBLon] = useState(10);
  const [terminalBAlt, setTerminalBAlt] = useState(0);
  const [terminalBEirp, setTerminalBEirp] = useState(50);
  const [terminalBGt, setTerminalBGt] = useState(25);
  const [terminalBPointingLoss, setTerminalBPointingLoss] = useState(0.5);
  const [terminalBPolLoss, setTerminalBPolLoss] = useState(0.3);
  const [terminalBNpr, setTerminalBNpr] = useState<number | null>(null);

  // Satellite
  const [satLat, setSatLat] = useState(0);
  const [satLon, setSatLon] = useState(0);
  const [satAlt, setSatAlt] = useState(35786);
  // X-band antenna parameters
  const [xBandEirp, setXBandEirp] = useState(45);
  const [xBandGt, setXBandGt] = useState(10);
  const [xBandNpr, setXBandNpr] = useState<number | null>(null);
  // Ka-band antenna parameters
  const [kaBandEirp, setKaBandEirp] = useState(50);
  const [kaBandGt, setKaBandGt] = useState(15);
  const [kaBandNpr, setKaBandNpr] = useState<number | null>(null);

  // Beams
  const [fwdUplinkBeam, setFwdUplinkBeam] = useState<BeamState>({
    center_lat_deg: 40, center_lon_deg: -5, cosine_exponent_n: 1.5
  });
  const [fwdDownlinkBeam, setFwdDownlinkBeam] = useState<BeamState>({
    center_lat_deg: 35, center_lon_deg: 10, cosine_exponent_n: 1.5
  });
  const [retUplinkBeam, setRetUplinkBeam] = useState<BeamState>({
    center_lat_deg: 35, center_lon_deg: 10, cosine_exponent_n: 1.5
  });
  const [retDownlinkBeam, setRetDownlinkBeam] = useState<BeamState>({
    center_lat_deg: 40, center_lon_deg: -5, cosine_exponent_n: 1.5
  });

  // Link Parameters - frequencies default based on terminal bands
  const [fwdUplinkFreq, setFwdUplinkFreq] = useState(FREQUENCY_DEFAULTS.ka.uplink);
  const [fwdDownlinkFreq, setFwdDownlinkFreq] = useState(FREQUENCY_DEFAULTS.ka.downlink);
  const [retUplinkFreq, setRetUplinkFreq] = useState(FREQUENCY_DEFAULTS.ka.uplink);
  const [retDownlinkFreq, setRetDownlinkFreq] = useState(FREQUENCY_DEFAULTS.ka.downlink);

  const [weatherFwdUplink, setWeatherFwdUplink] = useState(2);
  const [weatherFwdDownlink, setWeatherFwdDownlink] = useState(1);
  const [weatherRetUplink, setWeatherRetUplink] = useState(2);
  const [weatherRetDownlink, setWeatherRetDownlink] = useState(1);

  // Channel bandwidth (for C/N and Es/N0)
  const [symbolRateMsps, setSymbolRateMsps] = useState<number | null>(27.5);
  const [rollOffFactor, setRollOffFactor] = useState(0.20);

  const [minElevWarning, setMinElevWarning] = useState(5);

  // Collapsible sections
  const [expandedSections, setExpandedSections] = useState({
    terminalA: true,
    terminalB: true,
    satellite: true,
    beams: false,
    linkParams: false,
  });

  // Results
  const [result, setResult] = useState<DuplexSatelliteLinkResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Weather loss auto-calculation state
  interface WeatherLossResult {
    elevation_deg: number;
    rain_rate_mm_hr: number;
    weather_loss_db: number;
  }

  interface HopWeatherLoss {
    97: WeatherLossResult | null;
    98: WeatherLossResult | null;
    99: WeatherLossResult | null;
  }

  interface AutoWeatherLossState {
    fwdUplink: HopWeatherLoss;
    fwdDownlink: HopWeatherLoss;
    retUplink: HopWeatherLoss;
    retDownlink: HopWeatherLoss;
  }

  const [autoWeatherLoss, setAutoWeatherLoss] = useState<AutoWeatherLossState | null>(null);
  const [weatherLossLoading, setWeatherLossLoading] = useState(false);
  const [weatherLossError, setWeatherLossError] = useState<string | null>(null);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const updateBeam = (
    setter: React.Dispatch<React.SetStateAction<BeamState>>,
    field: keyof BeamState,
    value: number
  ) => {
    setter(prev => ({ ...prev, [field]: value }));
  };

  // Update frequencies when Terminal A band changes
  // Terminal A affects: Forward Uplink (A→Sat) and Return Downlink (Sat→A)
  useEffect(() => {
    setFwdUplinkFreq(FREQUENCY_DEFAULTS[terminalABand].uplink);
    setRetDownlinkFreq(FREQUENCY_DEFAULTS[terminalABand].downlink);
  }, [terminalABand]);

  // Update frequencies when Terminal B band changes
  // Terminal B affects: Forward Downlink (Sat→B) and Return Uplink (B→Sat)
  useEffect(() => {
    setFwdDownlinkFreq(FREQUENCY_DEFAULTS[terminalBBand].downlink);
    setRetUplinkFreq(FREQUENCY_DEFAULTS[terminalBBand].uplink);
  }, [terminalBBand]);

  // Debounced inputs for weather loss calculation
  // Use a string key to ensure proper comparison (objects create new refs every render)
  const weatherLossInputKey = `${terminalALat},${terminalALon},${terminalBLat},${terminalBLon},${satLon},${fwdUplinkFreq},${fwdDownlinkFreq},${retUplinkFreq},${retDownlinkFreq}`;
  const debouncedWeatherInputKey = useDebounce(weatherLossInputKey, 500);

  // Auto-calculate weather loss when inputs change
  useEffect(() => {
    // Parse the debounced key string back into values
    const parts = debouncedWeatherInputKey.split(",").map(Number);
    const [aLat, aLon, bLat, bLon, sLon, fwdUp, fwdDown, retUp, retDown] = parts;

    // Validate coordinates and frequencies
    const validCoords =
      aLat >= -90 && aLat <= 90 &&
      aLon >= -180 && aLon <= 180 &&
      bLat >= -90 && bLat <= 90 &&
      bLon >= -180 && bLon <= 180 &&
      sLon >= -180 && sLon <= 180;
    const validFreqs = fwdUp > 0 && fwdDown > 0 && retUp > 0 && retDown > 0;

    if (!validCoords || !validFreqs) {
      return;
    }

    const availabilities = [97, 98, 99] as const;

    // Define the 4 hops with their terminal locations and frequencies
    const hops = [
      { key: "fwdUplink" as const, lat: aLat, lon: aLon, freq: fwdUp },
      { key: "fwdDownlink" as const, lat: bLat, lon: bLon, freq: fwdDown },
      { key: "retUplink" as const, lat: bLat, lon: bLon, freq: retUp },
      { key: "retDownlink" as const, lat: aLat, lon: aLon, freq: retDown },
    ];

    const fetchWeatherLoss = async () => {
      setWeatherLossLoading(true);
      setWeatherLossError(null);

      try {
        // Create all 12 API calls (4 hops x 3 availability levels)
        const calls = hops.flatMap((hop) =>
          availabilities.map((avail) =>
            api
              .weatherLoss({
                satellite_longitude_deg: sLon,
                user_latitude_deg: hop.lat,
                user_longitude_deg: hop.lon,
                availability_percent: avail,
                frequency_ghz: hop.freq,
              })
              .then((result) => ({ hop: hop.key, avail, result }))
              .catch((err) => ({ hop: hop.key, avail, error: err.message }))
          )
        );

        const results = await Promise.all(calls);

        // Check for any errors (e.g., satellite not visible)
        const errors = results.filter((r) => "error" in r);
        if (errors.length > 0) {
          // Find unique error messages
          const errorMessages = [...new Set(errors.map((e) => (e as { error: string }).error))];
          setWeatherLossError(errorMessages.join("; "));
          setAutoWeatherLoss(null);
          return;
        }

        // Build the state object
        const newState: AutoWeatherLossState = {
          fwdUplink: { 97: null, 98: null, 99: null },
          fwdDownlink: { 97: null, 98: null, 99: null },
          retUplink: { 97: null, 98: null, 99: null },
          retDownlink: { 97: null, 98: null, 99: null },
        };

        for (const r of results) {
          if ("result" in r) {
            newState[r.hop][r.avail] = r.result;
          }
        }

        setAutoWeatherLoss(newState);
      } catch (err) {
        setWeatherLossError((err as Error).message);
        setAutoWeatherLoss(null);
      } finally {
        setWeatherLossLoading(false);
      }
    };

    fetchWeatherLoss();
  }, [debouncedWeatherInputKey]);

  const handleTerminalAPresetChange = (presetKey: string) => {
    setTerminalAPreset(presetKey);
    const preset = TERMINAL_PRESETS[presetKey];
    if (preset) {
      setTerminalABand(preset.band);
      if (presetKey !== "custom") {
        setTerminalAEirp(preset.eirp_dbw);
        setTerminalAGt(preset.gt_db_per_k);
        setTerminalANpr(preset.npr_db);
      }
    }
  };

  const handleTerminalBPresetChange = (presetKey: string) => {
    setTerminalBPreset(presetKey);
    const preset = TERMINAL_PRESETS[presetKey];
    if (preset) {
      setTerminalBBand(preset.band);
      if (presetKey !== "custom") {
        setTerminalBEirp(preset.eirp_dbw);
        setTerminalBGt(preset.gt_db_per_k);
        setTerminalBNpr(preset.npr_db);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.duplexSatelliteLink({
        terminal_a: {
          lat_deg: terminalALat,
          lon_deg: terminalALon,
          alt_km: terminalAAlt,
          band: terminalABand,
          eirp_dbw: terminalAEirp,
          gt_db_per_k: terminalAGt,
          pointing_loss_db: terminalAPointingLoss,
          polarization_loss_db: terminalAPolLoss,
          hpa_npr_db: terminalANpr,
        },
        terminal_b: {
          lat_deg: terminalBLat,
          lon_deg: terminalBLon,
          alt_km: terminalBAlt,
          band: terminalBBand,
          eirp_dbw: terminalBEirp,
          gt_db_per_k: terminalBGt,
          pointing_loss_db: terminalBPointingLoss,
          polarization_loss_db: terminalBPolLoss,
          hpa_npr_db: terminalBNpr,
        },
        satellite: {
          lat_deg: satLat,
          lon_deg: satLon,
          alt_km: satAlt,
          x_band_eirp_dbw: xBandEirp,
          x_band_gt_db_per_k: xBandGt,
          x_band_npr_db: xBandNpr,
          ka_band_eirp_dbw: kaBandEirp,
          ka_band_gt_db_per_k: kaBandGt,
          ka_band_npr_db: kaBandNpr,
          fwd_uplink_beam: fwdUplinkBeam,
          fwd_downlink_beam: fwdDownlinkBeam,
          ret_uplink_beam: retUplinkBeam,
          ret_downlink_beam: retDownlinkBeam,
        },
        link_params: {
          fwd_uplink_freq_ghz: fwdUplinkFreq,
          fwd_downlink_freq_ghz: fwdDownlinkFreq,
          ret_uplink_freq_ghz: retUplinkFreq,
          ret_downlink_freq_ghz: retDownlinkFreq,
          weather_atten_fwd_uplink_db: weatherFwdUplink,
          weather_atten_fwd_downlink_db: weatherFwdDownlink,
          weather_atten_ret_uplink_db: weatherRetUplink,
          weather_atten_ret_downlink_db: weatherRetDownlink,
          symbol_rate_msps: symbolRateMsps,
          roll_off_factor: rollOffFactor,
          min_elevation_warning_deg: minElevWarning,
        },
      });
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const renderHopResult = (hop: SingleHopResult, label: string) => (
    <div className="hop-result">
      <h5>{label}</h5>
      <div className="hop-metrics">
        <p><strong>C/N₀:</strong> {hop.cn0_db_hz.toFixed(2)} dB-Hz</p>
        {hop.cn_db !== null && (
          <p><strong>C/N:</strong> {hop.cn_db.toFixed(2)} dB</p>
        )}
        <p><strong>Off-axis:</strong> {hop.off_axis_angle_deg.toFixed(2)}°</p>
      </div>
      <details className="loss-details">
        <summary>Loss Breakdown</summary>
        <ul>
          <li>FSPL: {hop.fspl_db.toFixed(2)} dB</li>
          <li>Beam Roll-off: {hop.beam_roll_off_db.toFixed(2)} dB</li>
          <li>Weather: {hop.weather_atten_db.toFixed(2)} dB</li>
          <li>Pointing: {hop.pointing_loss_db.toFixed(2)} dB</li>
          <li>Polarization: {hop.polarization_loss_db.toFixed(2)} dB</li>
          <li><strong>Total Path Loss: {hop.total_path_loss_db.toFixed(2)} dB</strong></li>
        </ul>
      </details>
    </div>
  );

  return (
    <section className="card card-wide">
      <h2>Duplex Satellite Link Budget</h2>
      <p className="card-subtitle">
        Compute forward (A→Sat→B) and return (B→Sat→A) link budgets for a bent-pipe satellite relay.
      </p>
      <div className="formula-box">
        <div className="formula-row">
          <span className="formula-label">Single Hop C/N₀:</span>
          <span className="formula">
            C/N<sub>0</sub> = EIRP + G/T − FSPL − L<sub>weather</sub> − L<sub>point</sub> − L<sub>pol</sub> − k
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Bent-pipe Combined:</span>
          <span className="formula">
            (C/N<sub>0</sub>)<sup>−1</sup><sub>total</sub> = (C/N<sub>0</sub>)<sup>−1</sup><sub>up</sub> + (C/N<sub>0</sub>)<sup>−1</sup><sub>down</sub>
          </span>
        </div>
        <div className="formula-row">
          <span className="formula-label">Beam Roll-off:</span>
          <span className="formula">
            G(θ) = G<sub>peak</sub> + 10·n·log<sub>10</sub>(cos θ)
          </span>
        </div>
        <span className="formula-note">where k = −228.6 dBW/K/Hz</span>
      </div>

      <form onSubmit={handleSubmit} className="duplex-form">
        {/* Terminal A */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("terminalA")} className="clickable-legend">
            {expandedSections.terminalA ? "▼" : "▶"} Terminal A
          </legend>
          {expandedSections.terminalA && (
            <div className="fieldset-content">
              <div className="input-row">
                <label>
                  Terminal Type
                  <select value={terminalAPreset} onChange={(e) => handleTerminalAPresetChange(e.target.value)}>
                    <option value="custom">Custom</option>
                    <optgroup label="Manpack">
                      <option value="manpack_x">Manpack (X-band)</option>
                      <option value="manpack_ka">Manpack (Ka-band)</option>
                    </optgroup>
                    <optgroup label="SNAP 2.0m">
                      <option value="snap_2m_x">SNAP 2.0m (X-band)</option>
                      <option value="snap_2m_ka">SNAP 2.0m (Ka-band)</option>
                    </optgroup>
                    <optgroup label="STT">
                      <option value="stt_x">STT (X-band)</option>
                      <option value="stt_ka">STT (Ka-band)</option>
                    </optgroup>
                    <optgroup label="Airborne">
                      <option value="airborne_ka">Airborne (Ka-band)</option>
                    </optgroup>
                    <optgroup label="Commercial Gateway">
                      <option value="gateway_x">Gateway (X-band)</option>
                      <option value="gateway_ka">Gateway (Ka-band)</option>
                    </optgroup>
                  </select>
                </label>
                <label>
                  Band
                  <select value={terminalABand} onChange={(e) => setTerminalABand(e.target.value as FrequencyBand)}>
                    <option value="x">X-Band</option>
                    <option value="ka">Ka-Band</option>
                  </select>
                </label>
              </div>
              <div className="input-row">
                <label>
                  Lat (°)
                  <input type="number" step="any" value={terminalALat} onChange={(e) => setTerminalALat(Number(e.target.value))} />
                </label>
                <label>
                  Lon (°)
                  <input type="number" step="any" value={terminalALon} onChange={(e) => setTerminalALon(Number(e.target.value))} />
                </label>
                <label>
                  Alt (km)
                  <input type="number" step="any" min={0} value={terminalAAlt} onChange={(e) => setTerminalAAlt(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  EIRP (dBW)
                  <input type="number" step="any" value={terminalAEirp} onChange={(e) => setTerminalAEirp(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={terminalANpr ?? ""} placeholder="Ideal" onChange={(e) => setTerminalANpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  G/T (dB/K)
                  <input type="number" step="any" value={terminalAGt} onChange={(e) => setTerminalAGt(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  Pointing Loss (dB)
                  <input type="number" step="any" min={0} value={terminalAPointingLoss} onChange={(e) => setTerminalAPointingLoss(Number(e.target.value))} />
                </label>
                <label>
                  Pol Loss (dB)
                  <input type="number" step="any" min={0} value={terminalAPolLoss} onChange={(e) => setTerminalAPolLoss(Number(e.target.value))} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        {/* Terminal B */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("terminalB")} className="clickable-legend">
            {expandedSections.terminalB ? "▼" : "▶"} Terminal B
          </legend>
          {expandedSections.terminalB && (
            <div className="fieldset-content">
              <div className="input-row">
                <label>
                  Terminal Type
                  <select value={terminalBPreset} onChange={(e) => handleTerminalBPresetChange(e.target.value)}>
                    <option value="custom">Custom</option>
                    <optgroup label="Manpack">
                      <option value="manpack_x">Manpack (X-band)</option>
                      <option value="manpack_ka">Manpack (Ka-band)</option>
                    </optgroup>
                    <optgroup label="SNAP 2.0m">
                      <option value="snap_2m_x">SNAP 2.0m (X-band)</option>
                      <option value="snap_2m_ka">SNAP 2.0m (Ka-band)</option>
                    </optgroup>
                    <optgroup label="STT">
                      <option value="stt_x">STT (X-band)</option>
                      <option value="stt_ka">STT (Ka-band)</option>
                    </optgroup>
                    <optgroup label="Airborne">
                      <option value="airborne_ka">Airborne (Ka-band)</option>
                    </optgroup>
                    <optgroup label="Commercial Gateway">
                      <option value="gateway_x">Gateway (X-band)</option>
                      <option value="gateway_ka">Gateway (Ka-band)</option>
                    </optgroup>
                  </select>
                </label>
                <label>
                  Band
                  <select value={terminalBBand} onChange={(e) => setTerminalBBand(e.target.value as FrequencyBand)}>
                    <option value="x">X-Band</option>
                    <option value="ka">Ka-Band</option>
                  </select>
                </label>
              </div>
              <div className="input-row">
                <label>
                  Lat (°)
                  <input type="number" step="any" value={terminalBLat} onChange={(e) => setTerminalBLat(Number(e.target.value))} />
                </label>
                <label>
                  Lon (°)
                  <input type="number" step="any" value={terminalBLon} onChange={(e) => setTerminalBLon(Number(e.target.value))} />
                </label>
                <label>
                  Alt (km)
                  <input type="number" step="any" min={0} value={terminalBAlt} onChange={(e) => setTerminalBAlt(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  EIRP (dBW)
                  <input type="number" step="any" value={terminalBEirp} onChange={(e) => setTerminalBEirp(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={terminalBNpr ?? ""} placeholder="Ideal" onChange={(e) => setTerminalBNpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  G/T (dB/K)
                  <input type="number" step="any" value={terminalBGt} onChange={(e) => setTerminalBGt(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  Pointing Loss (dB)
                  <input type="number" step="any" min={0} value={terminalBPointingLoss} onChange={(e) => setTerminalBPointingLoss(Number(e.target.value))} />
                </label>
                <label>
                  Pol Loss (dB)
                  <input type="number" step="any" min={0} value={terminalBPolLoss} onChange={(e) => setTerminalBPolLoss(Number(e.target.value))} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        {/* Satellite */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("satellite")} className="clickable-legend">
            {expandedSections.satellite ? "▼" : "▶"} Satellite
          </legend>
          {expandedSections.satellite && (
            <div className="fieldset-content">
              <div className="input-row">
                <label>
                  Lat (°)
                  <input type="number" step="any" value={satLat} onChange={(e) => setSatLat(Number(e.target.value))} />
                </label>
                <label>
                  Lon (°)
                  <input type="number" step="any" value={satLon} onChange={(e) => setSatLon(Number(e.target.value))} />
                </label>
                <label>
                  Alt (km)
                  <input type="number" step="any" min={0} value={satAlt} onChange={(e) => setSatAlt(Number(e.target.value))} />
                </label>
              </div>
              <h4 className="subsection-title">X-Band Antenna</h4>
              <div className="input-row">
                <label>
                  EIRP (dBW)
                  <input type="number" step="any" value={xBandEirp} onChange={(e) => setXBandEirp(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={xBandNpr ?? ""} placeholder="Ideal" onChange={(e) => setXBandNpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  G/T (dB/K)
                  <input type="number" step="any" value={xBandGt} onChange={(e) => setXBandGt(Number(e.target.value))} />
                </label>
              </div>
              <h4 className="subsection-title">Ka-Band Antenna</h4>
              <div className="input-row">
                <label>
                  EIRP (dBW)
                  <input type="number" step="any" value={kaBandEirp} onChange={(e) => setKaBandEirp(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={kaBandNpr ?? ""} placeholder="Ideal" onChange={(e) => setKaBandNpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  G/T (dB/K)
                  <input type="number" step="any" value={kaBandGt} onChange={(e) => setKaBandGt(Number(e.target.value))} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        {/* Beams */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("beams")} className="clickable-legend">
            {expandedSections.beams ? "▼" : "▶"} Beams (Advanced)
          </legend>
          {expandedSections.beams && (
            <div className="fieldset-content">
              {/* Forward Uplink Beam */}
              <h4 className="subsection-title">Forward Uplink Beam (receives from A)</h4>
              <div className="input-row">
                <label>
                  Center Lat (°)
                  <input type="number" step="any" value={fwdUplinkBeam.center_lat_deg} onChange={(e) => updateBeam(setFwdUplinkBeam, "center_lat_deg", Number(e.target.value))} />
                </label>
                <label>
                  Center Lon (°)
                  <input type="number" step="any" value={fwdUplinkBeam.center_lon_deg} onChange={(e) => updateBeam(setFwdUplinkBeam, "center_lon_deg", Number(e.target.value))} />
                </label>
                <label>
                  Cosine n
                  <input type="number" step="any" min={0.1} value={fwdUplinkBeam.cosine_exponent_n} onChange={(e) => updateBeam(setFwdUplinkBeam, "cosine_exponent_n", Number(e.target.value))} />
                </label>
              </div>

              {/* Forward Downlink Beam */}
              <h4 className="subsection-title">Forward Downlink Beam (transmits to B)</h4>
              <div className="input-row">
                <label>
                  Center Lat (°)
                  <input type="number" step="any" value={fwdDownlinkBeam.center_lat_deg} onChange={(e) => updateBeam(setFwdDownlinkBeam, "center_lat_deg", Number(e.target.value))} />
                </label>
                <label>
                  Center Lon (°)
                  <input type="number" step="any" value={fwdDownlinkBeam.center_lon_deg} onChange={(e) => updateBeam(setFwdDownlinkBeam, "center_lon_deg", Number(e.target.value))} />
                </label>
                <label>
                  Cosine n
                  <input type="number" step="any" min={0.1} value={fwdDownlinkBeam.cosine_exponent_n} onChange={(e) => updateBeam(setFwdDownlinkBeam, "cosine_exponent_n", Number(e.target.value))} />
                </label>
              </div>

              {/* Return Uplink Beam */}
              <h4 className="subsection-title">Return Uplink Beam (receives from B)</h4>
              <div className="input-row">
                <label>
                  Center Lat (°)
                  <input type="number" step="any" value={retUplinkBeam.center_lat_deg} onChange={(e) => updateBeam(setRetUplinkBeam, "center_lat_deg", Number(e.target.value))} />
                </label>
                <label>
                  Center Lon (°)
                  <input type="number" step="any" value={retUplinkBeam.center_lon_deg} onChange={(e) => updateBeam(setRetUplinkBeam, "center_lon_deg", Number(e.target.value))} />
                </label>
                <label>
                  Cosine n
                  <input type="number" step="any" min={0.1} value={retUplinkBeam.cosine_exponent_n} onChange={(e) => updateBeam(setRetUplinkBeam, "cosine_exponent_n", Number(e.target.value))} />
                </label>
              </div>

              {/* Return Downlink Beam */}
              <h4 className="subsection-title">Return Downlink Beam (transmits to A)</h4>
              <div className="input-row">
                <label>
                  Center Lat (°)
                  <input type="number" step="any" value={retDownlinkBeam.center_lat_deg} onChange={(e) => updateBeam(setRetDownlinkBeam, "center_lat_deg", Number(e.target.value))} />
                </label>
                <label>
                  Center Lon (°)
                  <input type="number" step="any" value={retDownlinkBeam.center_lon_deg} onChange={(e) => updateBeam(setRetDownlinkBeam, "center_lon_deg", Number(e.target.value))} />
                </label>
                <label>
                  Cosine n
                  <input type="number" step="any" min={0.1} value={retDownlinkBeam.cosine_exponent_n} onChange={(e) => updateBeam(setRetDownlinkBeam, "cosine_exponent_n", Number(e.target.value))} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        {/* Link Parameters */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("linkParams")} className="clickable-legend">
            {expandedSections.linkParams ? "▼" : "▶"} Link Parameters (Advanced)
          </legend>
          {expandedSections.linkParams && (
            <div className="fieldset-content">
              <h4 className="subsection-title">Frequencies (GHz)</h4>
              <div className="input-row">
                <label>
                  Fwd Uplink
                  <input type="number" step="any" min={0.1} value={fwdUplinkFreq} onChange={(e) => setFwdUplinkFreq(Number(e.target.value))} />
                </label>
                <label>
                  Fwd Downlink
                  <input type="number" step="any" min={0.1} value={fwdDownlinkFreq} onChange={(e) => setFwdDownlinkFreq(Number(e.target.value))} />
                </label>
                <label>
                  Ret Uplink
                  <input type="number" step="any" min={0.1} value={retUplinkFreq} onChange={(e) => setRetUplinkFreq(Number(e.target.value))} />
                </label>
                <label>
                  Ret Downlink
                  <input type="number" step="any" min={0.1} value={retDownlinkFreq} onChange={(e) => setRetDownlinkFreq(Number(e.target.value))} />
                </label>
              </div>

              <h4 className="subsection-title">Weather Attenuation (dB)</h4>
              <div className="input-row">
                <label>
                  Fwd Uplink
                  <input type="number" step="any" min={0} value={weatherFwdUplink} onChange={(e) => setWeatherFwdUplink(Number(e.target.value))} />
                </label>
                <label>
                  Fwd Downlink
                  <input type="number" step="any" min={0} value={weatherFwdDownlink} onChange={(e) => setWeatherFwdDownlink(Number(e.target.value))} />
                </label>
                <label>
                  Ret Uplink
                  <input type="number" step="any" min={0} value={weatherRetUplink} onChange={(e) => setWeatherRetUplink(Number(e.target.value))} />
                </label>
                <label>
                  Ret Downlink
                  <input type="number" step="any" min={0} value={weatherRetDownlink} onChange={(e) => setWeatherRetDownlink(Number(e.target.value))} />
                </label>
              </div>

              {/* Weather Loss Reference Table */}
              <div className="weather-loss-reference">
                <div className="weather-loss-header">
                  <span className="weather-loss-title">ITU-R Calculated Values (click to copy)</span>
                  {weatherLossLoading && <span className="weather-loss-loading">Calculating...</span>}
                </div>
                {weatherLossError && (
                  <div className="weather-loss-error">{weatherLossError}</div>
                )}
                {autoWeatherLoss && !weatherLossError && (
                  <table className="weather-loss-table">
                    <thead>
                      <tr>
                        <th>Hop</th>
                        <th>Terminal</th>
                        <th>Elev</th>
                        <th>97%</th>
                        <th>98%</th>
                        <th>99%</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Fwd Uplink</td>
                        <td>A</td>
                        <td>{autoWeatherLoss.fwdUplink[97]?.elevation_deg.toFixed(1)}°</td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdUplink[97] && setWeatherFwdUplink(Math.round(autoWeatherLoss.fwdUplink[97].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdUplink[97]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdUplink[98] && setWeatherFwdUplink(Math.round(autoWeatherLoss.fwdUplink[98].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdUplink[98]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdUplink[99] && setWeatherFwdUplink(Math.round(autoWeatherLoss.fwdUplink[99].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdUplink[99]?.weather_loss_db.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td>Fwd Downlink</td>
                        <td>B</td>
                        <td>{autoWeatherLoss.fwdDownlink[97]?.elevation_deg.toFixed(1)}°</td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdDownlink[97] && setWeatherFwdDownlink(Math.round(autoWeatherLoss.fwdDownlink[97].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdDownlink[97]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdDownlink[98] && setWeatherFwdDownlink(Math.round(autoWeatherLoss.fwdDownlink[98].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdDownlink[98]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.fwdDownlink[99] && setWeatherFwdDownlink(Math.round(autoWeatherLoss.fwdDownlink[99].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.fwdDownlink[99]?.weather_loss_db.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td>Ret Uplink</td>
                        <td>B</td>
                        <td>{autoWeatherLoss.retUplink[97]?.elevation_deg.toFixed(1)}°</td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retUplink[97] && setWeatherRetUplink(Math.round(autoWeatherLoss.retUplink[97].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retUplink[97]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retUplink[98] && setWeatherRetUplink(Math.round(autoWeatherLoss.retUplink[98].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retUplink[98]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retUplink[99] && setWeatherRetUplink(Math.round(autoWeatherLoss.retUplink[99].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retUplink[99]?.weather_loss_db.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td>Ret Downlink</td>
                        <td>A</td>
                        <td>{autoWeatherLoss.retDownlink[97]?.elevation_deg.toFixed(1)}°</td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retDownlink[97] && setWeatherRetDownlink(Math.round(autoWeatherLoss.retDownlink[97].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retDownlink[97]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retDownlink[98] && setWeatherRetDownlink(Math.round(autoWeatherLoss.retDownlink[98].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retDownlink[98]?.weather_loss_db.toFixed(2)}
                        </td>
                        <td
                          className="clickable-value"
                          onClick={() => autoWeatherLoss.retDownlink[99] && setWeatherRetDownlink(Math.round(autoWeatherLoss.retDownlink[99].weather_loss_db * 100) / 100)}
                          title="Click to use this value"
                        >
                          {autoWeatherLoss.retDownlink[99]?.weather_loss_db.toFixed(2)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                )}
              </div>

              <h4 className="subsection-title">Channel Bandwidth (DVB-S2)</h4>
              <div className="input-row">
                <label>
                  Symbol Rate (Msps)
                  <input type="number" step="any" min={0.1} value={symbolRateMsps ?? ""} placeholder="For C/N" onChange={(e) => setSymbolRateMsps(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  Roll-off (α)
                  <select value={rollOffFactor} onChange={(e) => setRollOffFactor(Number(e.target.value))}>
                    <option value={0.20}>0.20</option>
                    <option value={0.25}>0.25</option>
                    <option value={0.35}>0.35</option>
                  </select>
                </label>
              </div>

              <h4 className="subsection-title">Warnings</h4>
              <div className="input-row">
                <label>
                  Min Elevation Warning (°)
                  <input type="number" step="any" min={0} max={90} value={minElevWarning} onChange={(e) => setMinElevWarning(Number(e.target.value))} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {result && (
        <div className="results duplex-results">
          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div className="warnings-section">
              {result.warnings.map((w, i) => (
                <div key={i} className="warning-item">
                  ⚠️ {w.message}
                </div>
              ))}
            </div>
          )}

          {/* Geometry Summary */}
          <div className="geometry-summary">
            <h3>Geometry</h3>
            <div className="geometry-grid">
              <div>
                <p><strong>Terminal A → Sat:</strong></p>
                <p>Range: {result.geometry.terminal_a_slant_range_km.toFixed(1)} km</p>
                <p>Elevation: {result.geometry.terminal_a_elevation_deg.toFixed(2)}°</p>
              </div>
              <div>
                <p><strong>Terminal B → Sat:</strong></p>
                <p>Range: {result.geometry.terminal_b_slant_range_km.toFixed(1)} km</p>
                <p>Elevation: {result.geometry.terminal_b_elevation_deg.toFixed(2)}°</p>
              </div>
            </div>
          </div>

          {/* Forward Link */}
          <div className="link-result-section">
            <h3>Forward Link (A → Sat → B)</h3>
            <div className="link-summary">
              <p className="combined-cn0">
                <strong>Combined C/N₀:</strong> {result.forward_link.combined_cn0_db_hz.toFixed(2)} dB-Hz
              </p>
              {result.forward_link.combined_cn_db !== null && (
                <p><strong>Combined C/N:</strong> {result.forward_link.combined_cn_db.toFixed(2)} dB</p>
              )}
              {result.forward_link.es_n0_db !== null && (
                <p><strong>Es/N₀:</strong> {result.forward_link.es_n0_db.toFixed(2)} dB</p>
              )}
              {result.forward_link.ci_total_db !== null && (
                <p><strong>C/I (total):</strong> {result.forward_link.ci_total_db.toFixed(2)} dB</p>
              )}
              {result.forward_link.cnir_db !== null && (
                <p className="cnir-highlight"><strong>C/(N+I):</strong> {result.forward_link.cnir_db.toFixed(2)} dB</p>
              )}
              {result.forward_link.channel_bandwidth_mhz !== null && (
                <p className="bandwidth-info">BW: {result.forward_link.channel_bandwidth_mhz.toFixed(2)} MHz</p>
              )}
            </div>
            {(result.forward_link.ci_terminal_hpa_db !== null || result.forward_link.ci_satellite_transponder_db !== null) && (
              <details className="intermod-details">
                <summary>Intermodulation Breakdown</summary>
                <ul>
                  {result.forward_link.ci_terminal_hpa_db !== null && (
                    <li>Terminal A HPA C/I: {result.forward_link.ci_terminal_hpa_db.toFixed(2)} dB</li>
                  )}
                  {result.forward_link.ci_satellite_transponder_db !== null && (
                    <li>Satellite Transponder C/I: {result.forward_link.ci_satellite_transponder_db.toFixed(2)} dB</li>
                  )}
                </ul>
              </details>
            )}
            <div className="hops-grid">
              {renderHopResult(result.forward_link.uplink, "Uplink (A → Sat)")}
              {renderHopResult(result.forward_link.downlink, "Downlink (Sat → B)")}
            </div>
          </div>

          {/* Return Link */}
          <div className="link-result-section">
            <h3>Return Link (B → Sat → A)</h3>
            <div className="link-summary">
              <p className="combined-cn0">
                <strong>Combined C/N₀:</strong> {result.return_link.combined_cn0_db_hz.toFixed(2)} dB-Hz
              </p>
              {result.return_link.combined_cn_db !== null && (
                <p><strong>Combined C/N:</strong> {result.return_link.combined_cn_db.toFixed(2)} dB</p>
              )}
              {result.return_link.es_n0_db !== null && (
                <p><strong>Es/N₀:</strong> {result.return_link.es_n0_db.toFixed(2)} dB</p>
              )}
              {result.return_link.ci_total_db !== null && (
                <p><strong>C/I (total):</strong> {result.return_link.ci_total_db.toFixed(2)} dB</p>
              )}
              {result.return_link.cnir_db !== null && (
                <p className="cnir-highlight"><strong>C/(N+I):</strong> {result.return_link.cnir_db.toFixed(2)} dB</p>
              )}
              {result.return_link.channel_bandwidth_mhz !== null && (
                <p className="bandwidth-info">BW: {result.return_link.channel_bandwidth_mhz.toFixed(2)} MHz</p>
              )}
            </div>
            {(result.return_link.ci_terminal_hpa_db !== null || result.return_link.ci_satellite_transponder_db !== null) && (
              <details className="intermod-details">
                <summary>Intermodulation Breakdown</summary>
                <ul>
                  {result.return_link.ci_terminal_hpa_db !== null && (
                    <li>Terminal B HPA C/I: {result.return_link.ci_terminal_hpa_db.toFixed(2)} dB</li>
                  )}
                  {result.return_link.ci_satellite_transponder_db !== null && (
                    <li>Satellite Transponder C/I: {result.return_link.ci_satellite_transponder_db.toFixed(2)} dB</li>
                  )}
                </ul>
              </details>
            )}
            <div className="hops-grid">
              {renderHopResult(result.return_link.uplink, "Uplink (B → Sat)")}
              {renderHopResult(result.return_link.downlink, "Downlink (Sat → A)")}
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
