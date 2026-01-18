import React, { useState } from "react";
import { api } from "../apiClient";

interface BeamState {
  center_lat_deg: number;
  center_lon_deg: number;
  peak_gain_db: number;
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
  const [terminalALat, setTerminalALat] = useState(40);
  const [terminalALon, setTerminalALon] = useState(-5);
  const [terminalAAlt, setTerminalAAlt] = useState(0);
  const [terminalAEirp, setTerminalAEirp] = useState(60);
  const [terminalAGt, setTerminalAGt] = useState(35);
  const [terminalAPointingLoss, setTerminalAPointingLoss] = useState(0.5);
  const [terminalAPolLoss, setTerminalAPolLoss] = useState(0.3);
  // Terminal A HPA
  const [terminalAEirpSaturated, setTerminalAEirpSaturated] = useState<number | null>(null);
  const [terminalAObo, setTerminalAObo] = useState(0);
  const [terminalANpr, setTerminalANpr] = useState<number | null>(null);

  // Terminal B
  const [terminalBLat, setTerminalBLat] = useState(35);
  const [terminalBLon, setTerminalBLon] = useState(10);
  const [terminalBAlt, setTerminalBAlt] = useState(0);
  const [terminalBEirp, setTerminalBEirp] = useState(50);
  const [terminalBGt, setTerminalBGt] = useState(25);
  const [terminalBPointingLoss, setTerminalBPointingLoss] = useState(0.5);
  const [terminalBPolLoss, setTerminalBPolLoss] = useState(0.3);
  // Terminal B HPA
  const [terminalBEirpSaturated, setTerminalBEirpSaturated] = useState<number | null>(null);
  const [terminalBObo, setTerminalBObo] = useState(0);
  const [terminalBNpr, setTerminalBNpr] = useState<number | null>(null);

  // Satellite
  const [satLat, setSatLat] = useState(0);
  const [satLon, setSatLon] = useState(0);
  const [satAlt, setSatAlt] = useState(35786);
  const [fwdUplinkGt, setFwdUplinkGt] = useState(10);
  const [fwdDownlinkEirp, setFwdDownlinkEirp] = useState(45);
  const [retUplinkGt, setRetUplinkGt] = useState(10);
  const [retDownlinkEirp, setRetDownlinkEirp] = useState(45);
  // Satellite transponder (forward downlink)
  const [fwdDownlinkEirpSaturated, setFwdDownlinkEirpSaturated] = useState<number | null>(null);
  const [fwdDownlinkObo, setFwdDownlinkObo] = useState(0);
  const [fwdDownlinkNpr, setFwdDownlinkNpr] = useState<number | null>(null);
  // Satellite transponder (return downlink)
  const [retDownlinkEirpSaturated, setRetDownlinkEirpSaturated] = useState<number | null>(null);
  const [retDownlinkObo, setRetDownlinkObo] = useState(0);
  const [retDownlinkNpr, setRetDownlinkNpr] = useState<number | null>(null);

  // Beams
  const [fwdUplinkBeam, setFwdUplinkBeam] = useState<BeamState>({
    center_lat_deg: 40, center_lon_deg: -5, peak_gain_db: 35, cosine_exponent_n: 1.5
  });
  const [fwdDownlinkBeam, setFwdDownlinkBeam] = useState<BeamState>({
    center_lat_deg: 35, center_lon_deg: 10, peak_gain_db: 35, cosine_exponent_n: 1.5
  });
  const [retUplinkBeam, setRetUplinkBeam] = useState<BeamState>({
    center_lat_deg: 35, center_lon_deg: 10, peak_gain_db: 35, cosine_exponent_n: 1.5
  });
  const [retDownlinkBeam, setRetDownlinkBeam] = useState<BeamState>({
    center_lat_deg: 40, center_lon_deg: -5, peak_gain_db: 35, cosine_exponent_n: 1.5
  });

  // Link Parameters
  const [fwdUplinkFreq, setFwdUplinkFreq] = useState(30);
  const [fwdDownlinkFreq, setFwdDownlinkFreq] = useState(20);
  const [retUplinkFreq, setRetUplinkFreq] = useState(30);
  const [retDownlinkFreq, setRetDownlinkFreq] = useState(20);

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
          eirp_dbw: terminalAEirp,
          gt_db_per_k: terminalAGt,
          pointing_loss_db: terminalAPointingLoss,
          polarization_loss_db: terminalAPolLoss,
          eirp_saturated_dbw: terminalAEirpSaturated,
          hpa_obo_db: terminalAObo,
          hpa_npr_db: terminalANpr,
        },
        terminal_b: {
          lat_deg: terminalBLat,
          lon_deg: terminalBLon,
          alt_km: terminalBAlt,
          eirp_dbw: terminalBEirp,
          gt_db_per_k: terminalBGt,
          pointing_loss_db: terminalBPointingLoss,
          polarization_loss_db: terminalBPolLoss,
          eirp_saturated_dbw: terminalBEirpSaturated,
          hpa_obo_db: terminalBObo,
          hpa_npr_db: terminalBNpr,
        },
        satellite: {
          lat_deg: satLat,
          lon_deg: satLon,
          alt_km: satAlt,
          fwd_uplink_gt_db_per_k: fwdUplinkGt,
          fwd_downlink_eirp_dbw: fwdDownlinkEirp,
          ret_uplink_gt_db_per_k: retUplinkGt,
          ret_downlink_eirp_dbw: retDownlinkEirp,
          fwd_uplink_beam: fwdUplinkBeam,
          fwd_downlink_beam: fwdDownlinkBeam,
          ret_uplink_beam: retUplinkBeam,
          ret_downlink_beam: retDownlinkBeam,
          fwd_downlink_eirp_saturated_dbw: fwdDownlinkEirpSaturated,
          fwd_downlink_obo_db: fwdDownlinkObo,
          fwd_downlink_npr_db: fwdDownlinkNpr,
          ret_downlink_eirp_saturated_dbw: retDownlinkEirpSaturated,
          ret_downlink_obo_db: retDownlinkObo,
          ret_downlink_npr_db: retDownlinkNpr,
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
            {expandedSections.terminalA ? "▼" : "▶"} Terminal A (Gateway)
          </legend>
          {expandedSections.terminalA && (
            <div className="fieldset-content">
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
              <h4 className="subsection-title">HPA Non-Linearity (Optional)</h4>
              <div className="input-row">
                <label>
                  Sat. EIRP (dBW)
                  <input type="number" step="any" value={terminalAEirpSaturated ?? ""} placeholder="Optional" onChange={(e) => setTerminalAEirpSaturated(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  OBO (dB)
                  <input type="number" step="any" min={0} value={terminalAObo} onChange={(e) => setTerminalAObo(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={terminalANpr ?? ""} placeholder="Ideal" onChange={(e) => setTerminalANpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
              </div>
            </div>
          )}
        </fieldset>

        {/* Terminal B */}
        <fieldset className="collapsible-fieldset">
          <legend onClick={() => toggleSection("terminalB")} className="clickable-legend">
            {expandedSections.terminalB ? "▼" : "▶"} Terminal B (User)
          </legend>
          {expandedSections.terminalB && (
            <div className="fieldset-content">
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
              <h4 className="subsection-title">HPA Non-Linearity (Optional)</h4>
              <div className="input-row">
                <label>
                  Sat. EIRP (dBW)
                  <input type="number" step="any" value={terminalBEirpSaturated ?? ""} placeholder="Optional" onChange={(e) => setTerminalBEirpSaturated(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  OBO (dB)
                  <input type="number" step="any" min={0} value={terminalBObo} onChange={(e) => setTerminalBObo(Number(e.target.value))} />
                </label>
                <label>
                  NPR (dB)
                  <input type="number" step="any" value={terminalBNpr ?? ""} placeholder="Ideal" onChange={(e) => setTerminalBNpr(e.target.value ? Number(e.target.value) : null)} />
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
              <h4 className="subsection-title">Forward Link (A → Sat → B)</h4>
              <div className="input-row">
                <label>
                  Uplink G/T (dB/K)
                  <input type="number" step="any" value={fwdUplinkGt} onChange={(e) => setFwdUplinkGt(Number(e.target.value))} />
                </label>
                <label>
                  Downlink EIRP (dBW)
                  <input type="number" step="any" value={fwdDownlinkEirp} onChange={(e) => setFwdDownlinkEirp(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  Fwd Sat. EIRP (dBW)
                  <input type="number" step="any" value={fwdDownlinkEirpSaturated ?? ""} placeholder="Optional" onChange={(e) => setFwdDownlinkEirpSaturated(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  Fwd OBO (dB)
                  <input type="number" step="any" min={0} value={fwdDownlinkObo} onChange={(e) => setFwdDownlinkObo(Number(e.target.value))} />
                </label>
                <label>
                  Fwd NPR (dB)
                  <input type="number" step="any" value={fwdDownlinkNpr ?? ""} placeholder="Ideal" onChange={(e) => setFwdDownlinkNpr(e.target.value ? Number(e.target.value) : null)} />
                </label>
              </div>
              <h4 className="subsection-title">Return Link (B → Sat → A)</h4>
              <div className="input-row">
                <label>
                  Uplink G/T (dB/K)
                  <input type="number" step="any" value={retUplinkGt} onChange={(e) => setRetUplinkGt(Number(e.target.value))} />
                </label>
                <label>
                  Downlink EIRP (dBW)
                  <input type="number" step="any" value={retDownlinkEirp} onChange={(e) => setRetDownlinkEirp(Number(e.target.value))} />
                </label>
              </div>
              <div className="input-row">
                <label>
                  Ret Sat. EIRP (dBW)
                  <input type="number" step="any" value={retDownlinkEirpSaturated ?? ""} placeholder="Optional" onChange={(e) => setRetDownlinkEirpSaturated(e.target.value ? Number(e.target.value) : null)} />
                </label>
                <label>
                  Ret OBO (dB)
                  <input type="number" step="any" min={0} value={retDownlinkObo} onChange={(e) => setRetDownlinkObo(Number(e.target.value))} />
                </label>
                <label>
                  Ret NPR (dB)
                  <input type="number" step="any" value={retDownlinkNpr ?? ""} placeholder="Ideal" onChange={(e) => setRetDownlinkNpr(e.target.value ? Number(e.target.value) : null)} />
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
                  Peak Gain (dB)
                  <input type="number" step="any" value={fwdUplinkBeam.peak_gain_db} onChange={(e) => updateBeam(setFwdUplinkBeam, "peak_gain_db", Number(e.target.value))} />
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
                  Peak Gain (dB)
                  <input type="number" step="any" value={fwdDownlinkBeam.peak_gain_db} onChange={(e) => updateBeam(setFwdDownlinkBeam, "peak_gain_db", Number(e.target.value))} />
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
                  Peak Gain (dB)
                  <input type="number" step="any" value={retUplinkBeam.peak_gain_db} onChange={(e) => updateBeam(setRetUplinkBeam, "peak_gain_db", Number(e.target.value))} />
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
                  Peak Gain (dB)
                  <input type="number" step="any" value={retDownlinkBeam.peak_gain_db} onChange={(e) => updateBeam(setRetDownlinkBeam, "peak_gain_db", Number(e.target.value))} />
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
