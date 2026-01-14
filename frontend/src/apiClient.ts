// During development we rely on the Vite dev server proxy (see vite.config.ts)
// so calls to `/api/...` are forwarded to the FastAPI backend on port 8000.
const API_BASE_URL = "/api";

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

  ebn0: (payload: { cn0_db_hz: number; data_rate_bps: number }) =>
    request<{ ebn0_db: number }>("/calculations/ebn0", payload),

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
  }) =>
    request<{ azimuth_deg: number }>("/calculations/azimuth", payload)
};


