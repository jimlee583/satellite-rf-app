// API base URL is read from VITE_API_BASE_URL at build time.
//   - Local dev: leave VITE_API_BASE_URL unset. Calls are sent to relative
//     `/api/...` paths and the Vite dev-server proxy (see vite.config.ts)
//     forwards them to the FastAPI backend on port 8000.
//   - Production build: VITE_API_BASE_URL points at the Cloud Run backend
//     (see frontend/.env.production). Calls go directly to that origin.
const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/+$/, "");
const API_BASE_URL = `${API_ORIGIN}/api`;

async function request<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export const api = {
  linkBudget: (payload: {
    frequency_hz: number;
    distance_m: number;
    tx_power_dbw: number;
    tx_antenna_gain_db: number;
    rx_antenna_gain_db: number;
    tx_losses_db?: number;
    rx_losses_db?: number;
    other_losses_db?: number;
  }) =>
    request<{ fspl_db: number; received_power_dbw: number }>("/calculations/link-budget", payload),

  eirp: (payload: { tx_power_dbw: number; tx_antenna_gain_db: number; tx_losses_db?: number }) =>
    request<{ eirp_dbw: number }>("/calculations/eirp", payload),

  gt: (payload: { antenna_gain_db: number; system_noise_temp_k: number }) =>
    request<{ gt_db_per_k: number }>("/calculations/gt", payload),

  phasedArrayGain: (payload: {
    element_gain_db: number;
    num_elements: number;
    array_efficiency?: number;
  }) =>
    request<{ array_gain_db: number }>("/calculations/phased-array-gain", payload),

  scanLoss: (payload: {
    satellite_longitude_deg: number;
    user_latitude_deg: number;
    user_longitude_deg: number;
    scan_exponent?: number;
  }) =>
    request<{ scan_angle_deg: number; scan_loss_db: number }>("/calculations/scan-loss", payload),

  azimuth: (payload: {
    start_lat_deg: number;
    start_lon_deg: number;
    end_lat_deg: number;
    end_lon_deg: number;
    satellite_altitude_km?: number;
  }) =>
    request<{ azimuth_deg: number; elevation_deg: number; central_angle_deg: number; nadir_angle_deg: number; terminal_phi_deg: number; slant_range_km: number }>("/calculations/azimuth", payload),

  beamOffAxis: (payload: {
    sat_lat_deg: number;
    sat_lon_deg: number;
    sat_alt_km?: number;
    user_lat_deg: number;
    user_lon_deg: number;
    user_alt_km?: number;
    beam_center_lat_deg: number;
    beam_center_lon_deg: number;
    beam_center_alt_km?: number;
  }) =>
    request<{
      off_axis_angle_deg: number;
      sat_to_user_lambda_deg: number;
      sat_to_user_eta_deg: number;
      sat_to_user_phi_deg: number;
      sat_to_user_x: number;
      sat_to_user_y: number;
      sat_to_user_z: number;
      sat_to_beam_lambda_deg: number;
      sat_to_beam_eta_deg: number;
      sat_to_beam_phi_deg: number;
      sat_to_beam_x: number;
      sat_to_beam_y: number;
      sat_to_beam_z: number;
    }>("/calculations/beam-off-axis", payload),

  weatherLoss: (payload: {
    satellite_longitude_deg: number;
    user_latitude_deg: number;
    user_longitude_deg: number;
    availability_percent: number;
    frequency_ghz: number;
  }) =>
    request<{ elevation_deg: number; rain_rate_mm_hr: number; weather_loss_db: number }>(
      "/calculations/weather-loss",
      payload
    ),

  duplexSatelliteLink: (payload: {
    terminal_a: {
      lat_deg: number;
      lon_deg: number;
      alt_km?: number;
      band: "x" | "ka";
      eirp_dbw: number;
      gt_db_per_k: number;
      pointing_loss_db?: number;
      polarization_loss_db?: number;
      hpa_npr_db?: number | null;
    };
    terminal_b: {
      lat_deg: number;
      lon_deg: number;
      alt_km?: number;
      band: "x" | "ka";
      eirp_dbw: number;
      gt_db_per_k: number;
      pointing_loss_db?: number;
      polarization_loss_db?: number;
      hpa_npr_db?: number | null;
    };
    satellite: {
      lat_deg?: number;
      lon_deg: number;
      alt_km?: number;
      // X-band antenna
      x_band_eirp_dbw: number;
      x_band_gt_db_per_k: number;
      x_band_npr_db?: number | null;
      // Ka-band antenna
      ka_band_eirp_dbw: number;
      ka_band_gt_db_per_k: number;
      ka_band_npr_db?: number | null;
      // Beams
      fwd_uplink_beam: {
        center_lat_deg: number;
        center_lon_deg: number;
        cosine_exponent_n?: number;
      };
      fwd_downlink_beam: {
        center_lat_deg: number;
        center_lon_deg: number;
        cosine_exponent_n?: number;
      };
      ret_uplink_beam: {
        center_lat_deg: number;
        center_lon_deg: number;
        cosine_exponent_n?: number;
      };
      ret_downlink_beam: {
        center_lat_deg: number;
        center_lon_deg: number;
        cosine_exponent_n?: number;
      };
    };
    link_params: {
      fwd_uplink_freq_ghz?: number;
      fwd_downlink_freq_ghz?: number;
      ret_uplink_freq_ghz?: number;
      ret_downlink_freq_ghz?: number;
      weather_atten_fwd_uplink_db?: number;
      weather_atten_fwd_downlink_db?: number;
      weather_atten_ret_uplink_db?: number;
      weather_atten_ret_downlink_db?: number;
      symbol_rate_msps?: number | null;
      roll_off_factor?: number;
      min_elevation_warning_deg?: number;
    };
  }) =>
    request<{
      forward_link: {
        uplink: {
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
        };
        downlink: {
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
        };
        combined_cn0_db_hz: number;
        ci_terminal_hpa_db: number | null;
        ci_satellite_transponder_db: number | null;
        ci_total_db: number | null;
        cnir_db: number | null;
        combined_cn_db: number | null;
        es_n0_db: number | null;
        channel_bandwidth_mhz: number | null;
        selected_modcod: string | null;
        spectral_efficiency: number | null;
      };
      return_link: {
        uplink: {
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
        };
        downlink: {
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
        };
        combined_cn0_db_hz: number;
        ci_terminal_hpa_db: number | null;
        ci_satellite_transponder_db: number | null;
        ci_total_db: number | null;
        cnir_db: number | null;
        combined_cn_db: number | null;
        es_n0_db: number | null;
        channel_bandwidth_mhz: number | null;
        selected_modcod: string | null;
        spectral_efficiency: number | null;
      };
      geometry: {
        terminal_a_slant_range_km: number;
        terminal_b_slant_range_km: number;
        terminal_a_elevation_deg: number;
        terminal_b_elevation_deg: number;
      };
      warnings: Array<{
        terminal: string;
        elevation_deg: number;
        threshold_deg: number;
        message: string;
      }>;
    }>("/calculations/duplex-satellite-link", payload)
};


