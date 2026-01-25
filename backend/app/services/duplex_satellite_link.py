"""
Duplex Satellite Link Budget Calculator

Computes forward and return link budgets for a bent-pipe satellite relay
between two ground terminals (Terminal A and Terminal B).

Forward Link: Terminal A → Satellite → Terminal B
Return Link:  Terminal B → Satellite → Terminal A

Features:
- Independent beams for each uplink/downlink
- Cosine^n beam roll-off pattern
- Weather attenuation, pointing loss, polarization loss
- Bent-pipe C/N0 combination
- Elevation angle warnings
"""

import math
from typing import Dict, List, Tuple, Any, Optional

from .beam_off_axis import (
    geodetic_to_ecef,
    vector_subtract,
    vector_magnitude,
    vector_dot,
    compute_beam_off_axis_angle_deg,
)
from .link_budget import free_space_path_loss_db

# Constants
BOLTZMANN_DBW_PER_K_HZ = -228.6  # Boltzmann constant in dBW/K/Hz


def compute_operating_eirp(
    eirp_dbw: float,
    eirp_saturated_dbw: Optional[float],
    obo_db: float,
) -> float:
    """
    Compute operating EIRP from saturated EIRP and OBO, or use provided operating EIRP.

    If eirp_saturated_dbw is provided, operating EIRP = saturated - OBO.
    Otherwise, returns the provided eirp_dbw directly.

    Parameters
    ----------
    eirp_dbw : float
        Operating EIRP in dBW (used if saturated not provided)
    eirp_saturated_dbw : float | None
        Saturated EIRP in dBW (if provided, overrides eirp_dbw)
    obo_db : float
        Output Back-Off in dB

    Returns
    -------
    float
        Operating EIRP in dBW
    """
    if eirp_saturated_dbw is not None:
        return eirp_saturated_dbw - obo_db
    return eirp_dbw


def compute_ci_from_npr(npr_db: Optional[float]) -> Optional[float]:
    """
    Compute C/I (carrier-to-intermodulation) from NPR.

    For a simplified model, C/I ≈ NPR.
    More sophisticated models may include OBO adjustments.

    Parameters
    ----------
    npr_db : float | None
        Noise Power Ratio in dB (None means ideal/linear amplifier)

    Returns
    -------
    float | None
        C/I in dB, or None if amplifier is ideal
    """
    if npr_db is None:
        return None
    return npr_db


def combine_ci_sources(*ci_values_db: Optional[float]) -> Optional[float]:
    """
    Combine multiple C/I sources (intermodulation from different amplifiers).

    (C/I)_total^-1 = sum of (C/I)_i^-1 for all sources

    Parameters
    ----------
    *ci_values_db : float | None
        C/I values in dB for each intermod source (None values are ignored)

    Returns
    -------
    float | None
        Combined C/I in dB, or None if no intermod sources
    """
    valid_ci = [ci for ci in ci_values_db if ci is not None]

    if not valid_ci:
        return None

    # Convert to linear and sum reciprocals
    total_reciprocal = sum(10 ** (-ci / 10) for ci in valid_ci)

    return -10.0 * math.log10(total_reciprocal)


def combine_cn_with_ci(cn_db: float, ci_db: Optional[float]) -> float:
    """
    Combine thermal C/N with intermodulation C/I to get C/(N+I).

    (C/(N+I))^-1 = (C/N)^-1 + (C/I)^-1

    Parameters
    ----------
    cn_db : float
        Carrier-to-noise ratio in dB
    ci_db : float | None
        Carrier-to-intermodulation ratio in dB (None = no intermod)

    Returns
    -------
    float
        C/(N+I) in dB
    """
    if ci_db is None:
        return cn_db

    cn_linear = 10 ** (cn_db / 10)
    ci_linear = 10 ** (ci_db / 10)

    cnir_linear = 1.0 / (1.0 / cn_linear + 1.0 / ci_linear)

    return 10.0 * math.log10(cnir_linear)


def cn0_to_cn(cn0_db_hz: float, bandwidth_hz: float) -> float:
    """
    Convert C/N0 (dB-Hz) to C/N (dB) given channel bandwidth.

    C/N = C/N0 - 10*log10(B)

    Parameters
    ----------
    cn0_db_hz : float
        Carrier-to-noise density ratio in dB-Hz
    bandwidth_hz : float
        Channel bandwidth in Hz

    Returns
    -------
    float
        C/N in dB
    """
    return cn0_db_hz - 10.0 * math.log10(bandwidth_hz)


def cn0_to_es_n0(cn0_db_hz: float, symbol_rate_hz: float) -> float:
    """
    Convert C/N0 (dB-Hz) to Es/N0 (dB) given symbol rate.

    Es/N0 = C/N0 - 10*log10(Rs)

    Parameters
    ----------
    cn0_db_hz : float
        Carrier-to-noise density ratio in dB-Hz
    symbol_rate_hz : float
        Symbol rate in Hz

    Returns
    -------
    float
        Es/N0 in dB
    """
    return cn0_db_hz - 10.0 * math.log10(symbol_rate_hz)


def compute_slant_range_km(
    terminal_lat_deg: float,
    terminal_lon_deg: float,
    terminal_alt_km: float,
    sat_lat_deg: float,
    sat_lon_deg: float,
    sat_alt_km: float,
) -> float:
    """
    Compute slant range (distance) between a ground terminal and satellite.

    Parameters
    ----------
    terminal_lat_deg : float
        Terminal latitude in degrees
    terminal_lon_deg : float
        Terminal longitude in degrees
    terminal_alt_km : float
        Terminal altitude above sea level in km
    sat_lat_deg : float
        Satellite subsatellite point latitude in degrees
    sat_lon_deg : float
        Satellite subsatellite point longitude in degrees
    sat_alt_km : float
        Satellite altitude above Earth's surface in km

    Returns
    -------
    float
        Slant range in kilometers
    """
    terminal_ecef = geodetic_to_ecef(terminal_lat_deg, terminal_lon_deg, terminal_alt_km)
    sat_ecef = geodetic_to_ecef(sat_lat_deg, sat_lon_deg, sat_alt_km)
    vec = vector_subtract(sat_ecef, terminal_ecef)
    return vector_magnitude(vec)


def compute_elevation_angle_deg(
    terminal_lat_deg: float,
    terminal_lon_deg: float,
    terminal_alt_km: float,
    sat_lat_deg: float,
    sat_lon_deg: float,
    sat_alt_km: float,
) -> float:
    """
    Compute elevation angle from a ground terminal to a satellite.

    Uses the local radial direction as the "up" vector and computes
    the angle between the horizontal plane and the satellite direction.

    Parameters
    ----------
    terminal_lat_deg : float
        Terminal latitude in degrees
    terminal_lon_deg : float
        Terminal longitude in degrees
    terminal_alt_km : float
        Terminal altitude above sea level in km
    sat_lat_deg : float
        Satellite subsatellite point latitude in degrees
    sat_lon_deg : float
        Satellite subsatellite point longitude in degrees
    sat_alt_km : float
        Satellite altitude above Earth's surface in km

    Returns
    -------
    float
        Elevation angle in degrees (negative if satellite is below horizon)
    """
    terminal_ecef = geodetic_to_ecef(terminal_lat_deg, terminal_lon_deg, terminal_alt_km)
    sat_ecef = geodetic_to_ecef(sat_lat_deg, sat_lon_deg, sat_alt_km)

    # Vector from terminal to satellite
    to_sat = vector_subtract(sat_ecef, terminal_ecef)
    to_sat_mag = vector_magnitude(to_sat)

    if to_sat_mag < 1e-9:
        return 90.0  # Satellite at terminal location (degenerate case)

    # Local "up" vector at terminal (radial direction from Earth center)
    terminal_mag = vector_magnitude(terminal_ecef)
    if terminal_mag < 1e-9:
        return 0.0  # Terminal at Earth center (degenerate case)

    up_vector = (
        terminal_ecef[0] / terminal_mag,
        terminal_ecef[1] / terminal_mag,
        terminal_ecef[2] / terminal_mag,
    )

    # Unit vector from terminal to satellite
    to_sat_unit = (
        to_sat[0] / to_sat_mag,
        to_sat[1] / to_sat_mag,
        to_sat[2] / to_sat_mag,
    )

    # Elevation = arcsin(dot(to_sat_unit, up_vector))
    sin_elevation = vector_dot(to_sat_unit, up_vector)
    sin_elevation = max(-1.0, min(1.0, sin_elevation))  # Clamp for numerical safety

    elevation_rad = math.asin(sin_elevation)
    return math.degrees(elevation_rad)


def compute_beam_roll_off_db(off_axis_angle_deg: float, cosine_exponent_n: float) -> float:
    """
    Compute antenna gain roll-off using cos^n pattern.

    G(θ) = G_peak * cos^n(θ)
    Roll-off in dB = 10 * n * log10(cos(θ))

    Parameters
    ----------
    off_axis_angle_deg : float
        Off-axis angle from beam center in degrees
    cosine_exponent_n : float
        Exponent n in the cos^n pattern (higher = sharper roll-off)

    Returns
    -------
    float
        Roll-off in dB (0 at beam center, negative for off-axis)
    """
    if off_axis_angle_deg >= 90.0:
        return -100.0  # Effectively no gain beyond 90°

    theta_rad = math.radians(abs(off_axis_angle_deg))
    cos_theta = math.cos(theta_rad)

    if cos_theta <= 0:
        return -100.0

    return 10.0 * cosine_exponent_n * math.log10(cos_theta)


def compute_single_hop_cn0(
    tx_eirp_dbw: float,
    rx_gt_db_per_k: float,
    frequency_hz: float,
    slant_range_m: float,
    beam_roll_off_db: float,
    weather_atten_db: float,
    pointing_loss_db: float,
    polarization_loss_db: float,
) -> Tuple[float, Dict[str, float]]:
    """
    Compute C/N0 for a single hop (uplink or downlink).

    C/N0 = EIRP + G/T + beam_roll_off - FSPL - weather - pointing - polarization - k

    Note: beam_roll_off is typically negative (loss), so we add it.
    The roll-off is already applied to either EIRP (downlink) or G/T (uplink).

    Parameters
    ----------
    tx_eirp_dbw : float
        Transmitter EIRP in dBW (including any beam roll-off for Tx side)
    rx_gt_db_per_k : float
        Receiver G/T in dB/K (including any beam roll-off for Rx side)
    frequency_hz : float
        Carrier frequency in Hz
    slant_range_m : float
        Slant range in meters
    beam_roll_off_db : float
        Beam roll-off in dB (already included in EIRP or G/T, kept for reporting)
    weather_atten_db : float
        Weather attenuation in dB
    pointing_loss_db : float
        Antenna pointing loss in dB
    polarization_loss_db : float
        Polarization mismatch loss in dB

    Returns
    -------
    Tuple[float, Dict[str, float]]
        (cn0_db_hz, losses_breakdown)
    """
    fspl_db = free_space_path_loss_db(frequency_hz, slant_range_m)

    # Total losses (excluding beam roll-off which is in EIRP/GT)
    total_path_loss_db = fspl_db + weather_atten_db + pointing_loss_db + polarization_loss_db

    # C/N0 = EIRP + G/T - losses - k
    # Note: -k because k is negative (-228.6), so subtracting it adds 228.6
    cn0_db_hz = tx_eirp_dbw + rx_gt_db_per_k - total_path_loss_db - BOLTZMANN_DBW_PER_K_HZ

    losses_breakdown = {
        "fspl_db": fspl_db,
        "beam_roll_off_db": beam_roll_off_db,
        "weather_atten_db": weather_atten_db,
        "pointing_loss_db": pointing_loss_db,
        "polarization_loss_db": polarization_loss_db,
        "total_path_loss_db": total_path_loss_db,
    }

    return cn0_db_hz, losses_breakdown


def combine_cn0_bent_pipe(uplink_cn0_db_hz: float, downlink_cn0_db_hz: float) -> float:
    """
    Combine uplink and downlink C/N0 for a bent-pipe (transparent) transponder.

    For bent-pipe: (C/N0)_total^-1 = (C/N0)_up^-1 + (C/N0)_down^-1

    Parameters
    ----------
    uplink_cn0_db_hz : float
        Uplink C/N0 in dB-Hz
    downlink_cn0_db_hz : float
        Downlink C/N0 in dB-Hz

    Returns
    -------
    float
        Combined C/N0 in dB-Hz
    """
    up_linear = 10 ** (uplink_cn0_db_hz / 10)
    down_linear = 10 ** (downlink_cn0_db_hz / 10)

    total_linear = 1.0 / (1.0 / up_linear + 1.0 / down_linear)

    return 10.0 * math.log10(total_linear)


def check_elevation_warnings(
    terminal_a_elev_deg: float,
    terminal_b_elev_deg: float,
    threshold_deg: float,
) -> List[Dict[str, Any]]:
    """
    Check for low elevation angle warnings.

    Parameters
    ----------
    terminal_a_elev_deg : float
        Terminal A elevation angle in degrees
    terminal_b_elev_deg : float
        Terminal B elevation angle in degrees
    threshold_deg : float
        Warning threshold in degrees

    Returns
    -------
    List[Dict[str, Any]]
        List of warning dictionaries
    """
    warnings = []

    # Check for below-horizon (critical)
    if terminal_a_elev_deg < 0:
        warnings.append({
            "terminal": "A",
            "elevation_deg": terminal_a_elev_deg,
            "threshold_deg": 0.0,
            "message": f"Terminal A cannot see satellite (elevation {terminal_a_elev_deg:.1f}° is below horizon).",
        })
    elif terminal_a_elev_deg < threshold_deg:
        warnings.append({
            "terminal": "A",
            "elevation_deg": terminal_a_elev_deg,
            "threshold_deg": threshold_deg,
            "message": f"Terminal A elevation ({terminal_a_elev_deg:.1f}°) is below minimum threshold ({threshold_deg}°). Link may be degraded.",
        })

    if terminal_b_elev_deg < 0:
        warnings.append({
            "terminal": "B",
            "elevation_deg": terminal_b_elev_deg,
            "threshold_deg": 0.0,
            "message": f"Terminal B cannot see satellite (elevation {terminal_b_elev_deg:.1f}° is below horizon).",
        })
    elif terminal_b_elev_deg < threshold_deg:
        warnings.append({
            "terminal": "B",
            "elevation_deg": terminal_b_elev_deg,
            "threshold_deg": threshold_deg,
            "message": f"Terminal B elevation ({terminal_b_elev_deg:.1f}°) is below minimum threshold ({threshold_deg}°). Link may be degraded.",
        })

    return warnings


def compute_duplex_satellite_link(
    terminal_a: Dict[str, Any],
    terminal_b: Dict[str, Any],
    satellite: Dict[str, Any],
    link_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute duplex bent-pipe satellite link budget.

    Forward Link: Terminal A → Satellite → Terminal B
    Return Link:  Terminal B → Satellite → Terminal A

    Parameters
    ----------
    terminal_a : Dict
        Terminal A parameters (position, EIRP, G/T, losses, HPA NPR)
    terminal_b : Dict
        Terminal B parameters (position, EIRP, G/T, losses, HPA NPR)
    satellite : Dict
        Satellite parameters (position, EIRP, G/T for each direction, beams, transponder NPR)
    link_params : Dict
        Link parameters (frequencies, weather attenuation, threshold, symbol rate)

    Returns
    -------
    Dict[str, Any]
        Complete link budget results including thermal C/N, intermod C/I, and total C/(N+I)
    """
    # Extract satellite position
    sat_lat = satellite["lat_deg"]
    sat_lon = satellite["lon_deg"]
    sat_alt = satellite["alt_km"]

    # =========================================================================
    # TERMINAL BANDS AND EIRP
    # =========================================================================

    terminal_a_band = terminal_a["band"]  # "x" or "ka"
    terminal_b_band = terminal_b["band"]  # "x" or "ka"

    terminal_a_eirp = terminal_a["eirp_dbw"]
    terminal_b_eirp = terminal_b["eirp_dbw"]

    # =========================================================================
    # SATELLITE PARAMETERS (selected based on terminal bands)
    # =========================================================================

    # Helper to get satellite params for a given band
    def get_sat_params_for_band(band: str) -> tuple:
        """Returns (eirp_dbw, gt_db_per_k, npr_db) for the specified band."""
        if band == "x":
            return (
                satellite["x_band_eirp_dbw"],
                satellite["x_band_gt_db_per_k"],
                satellite.get("x_band_npr_db"),
            )
        else:  # ka
            return (
                satellite["ka_band_eirp_dbw"],
                satellite["ka_band_gt_db_per_k"],
                satellite.get("ka_band_npr_db"),
            )

    # Forward link (A → Sat → B):
    # - Uplink: Satellite receives from A, use G/T for A's band
    # - Downlink: Satellite transmits to B, use EIRP/NPR for B's band
    _, sat_fwd_uplink_gt, _ = get_sat_params_for_band(terminal_a_band)
    sat_fwd_down_eirp, _, sat_fwd_down_npr = get_sat_params_for_band(terminal_b_band)

    # Return link (B → Sat → A):
    # - Uplink: Satellite receives from B, use G/T for B's band
    # - Downlink: Satellite transmits to A, use EIRP/NPR for A's band
    _, sat_ret_uplink_gt, _ = get_sat_params_for_band(terminal_b_band)
    sat_ret_down_eirp, _, sat_ret_down_npr = get_sat_params_for_band(terminal_a_band)

    # =========================================================================
    # BANDWIDTH PARAMETERS (for C/N and Es/N0)
    # =========================================================================

    symbol_rate_msps = link_params.get("symbol_rate_msps")
    roll_off_factor = link_params.get("roll_off_factor", 0.20)

    # Calculate bandwidth and symbol rate in Hz
    symbol_rate_hz = symbol_rate_msps * 1e6 if symbol_rate_msps else None
    bandwidth_hz = symbol_rate_hz * (1 + roll_off_factor) if symbol_rate_hz else None
    bandwidth_mhz = bandwidth_hz / 1e6 if bandwidth_hz else None

    # =========================================================================
    # GEOMETRY: Compute slant ranges and elevation angles
    # =========================================================================

    range_a_km = compute_slant_range_km(
        terminal_a["lat_deg"], terminal_a["lon_deg"], terminal_a["alt_km"],
        sat_lat, sat_lon, sat_alt,
    )
    range_b_km = compute_slant_range_km(
        terminal_b["lat_deg"], terminal_b["lon_deg"], terminal_b["alt_km"],
        sat_lat, sat_lon, sat_alt,
    )

    elev_a_deg = compute_elevation_angle_deg(
        terminal_a["lat_deg"], terminal_a["lon_deg"], terminal_a["alt_km"],
        sat_lat, sat_lon, sat_alt,
    )
    elev_b_deg = compute_elevation_angle_deg(
        terminal_b["lat_deg"], terminal_b["lon_deg"], terminal_b["alt_km"],
        sat_lat, sat_lon, sat_alt,
    )

    # =========================================================================
    # FORWARD LINK: Terminal A → Satellite → Terminal B
    # =========================================================================

    # Forward Uplink: A transmits → Satellite receives
    fwd_up_beam = satellite["fwd_uplink_beam"]
    fwd_up_off_axis = compute_beam_off_axis_angle_deg(
        sat_lat, sat_lon, sat_alt,
        terminal_a["lat_deg"], terminal_a["lon_deg"], terminal_a["alt_km"],
        fwd_up_beam["center_lat_deg"], fwd_up_beam["center_lon_deg"], 0.0,
    )
    fwd_up_roll_off = compute_beam_roll_off_db(fwd_up_off_axis, fwd_up_beam["cosine_exponent_n"])

    # For uplink, beam roll-off applies to satellite receive gain (G/T)
    fwd_up_cn0, fwd_up_losses = compute_single_hop_cn0(
        tx_eirp_dbw=terminal_a_eirp,
        rx_gt_db_per_k=sat_fwd_uplink_gt + fwd_up_roll_off,
        frequency_hz=link_params["fwd_uplink_freq_ghz"] * 1e9,
        slant_range_m=range_a_km * 1e3,
        beam_roll_off_db=fwd_up_roll_off,
        weather_atten_db=link_params["weather_atten_fwd_uplink_db"],
        pointing_loss_db=terminal_a["pointing_loss_db"],
        polarization_loss_db=terminal_a["polarization_loss_db"],
    )

    # Forward Downlink: Satellite transmits → B receives
    fwd_down_beam = satellite["fwd_downlink_beam"]
    fwd_down_off_axis = compute_beam_off_axis_angle_deg(
        sat_lat, sat_lon, sat_alt,
        terminal_b["lat_deg"], terminal_b["lon_deg"], terminal_b["alt_km"],
        fwd_down_beam["center_lat_deg"], fwd_down_beam["center_lon_deg"], 0.0,
    )
    fwd_down_roll_off = compute_beam_roll_off_db(fwd_down_off_axis, fwd_down_beam["cosine_exponent_n"])

    # For downlink, beam roll-off applies to satellite transmit EIRP
    fwd_down_cn0, fwd_down_losses = compute_single_hop_cn0(
        tx_eirp_dbw=sat_fwd_down_eirp + fwd_down_roll_off,
        rx_gt_db_per_k=terminal_b["gt_db_per_k"],
        frequency_hz=link_params["fwd_downlink_freq_ghz"] * 1e9,
        slant_range_m=range_b_km * 1e3,
        beam_roll_off_db=fwd_down_roll_off,
        weather_atten_db=link_params["weather_atten_fwd_downlink_db"],
        pointing_loss_db=terminal_b["pointing_loss_db"],
        polarization_loss_db=terminal_b["polarization_loss_db"],
    )

    # Combined forward link thermal C/N0 (bent-pipe)
    fwd_combined_cn0 = combine_cn0_bent_pipe(fwd_up_cn0, fwd_down_cn0)

    # Forward link C/N (per-hop, if bandwidth provided)
    fwd_up_cn = cn0_to_cn(fwd_up_cn0, bandwidth_hz) if bandwidth_hz else None
    fwd_down_cn = cn0_to_cn(fwd_down_cn0, bandwidth_hz) if bandwidth_hz else None
    fwd_combined_cn = cn0_to_cn(fwd_combined_cn0, bandwidth_hz) if bandwidth_hz else None

    # Forward link intermodulation
    fwd_ci_terminal_hpa = compute_ci_from_npr(terminal_a.get("hpa_npr_db"))
    fwd_ci_satellite = compute_ci_from_npr(sat_fwd_down_npr)
    fwd_ci_total = combine_ci_sources(fwd_ci_terminal_hpa, fwd_ci_satellite)

    # Forward link total C/(N+I)
    fwd_cnir = combine_cn_with_ci(fwd_combined_cn, fwd_ci_total) if fwd_combined_cn is not None else None

    # Forward link Es/N0
    fwd_es_n0 = cn0_to_es_n0(fwd_combined_cn0, symbol_rate_hz) if symbol_rate_hz else None

    # =========================================================================
    # RETURN LINK: Terminal B → Satellite → Terminal A
    # =========================================================================

    # Return Uplink: B transmits → Satellite receives
    ret_up_beam = satellite["ret_uplink_beam"]
    ret_up_off_axis = compute_beam_off_axis_angle_deg(
        sat_lat, sat_lon, sat_alt,
        terminal_b["lat_deg"], terminal_b["lon_deg"], terminal_b["alt_km"],
        ret_up_beam["center_lat_deg"], ret_up_beam["center_lon_deg"], 0.0,
    )
    ret_up_roll_off = compute_beam_roll_off_db(ret_up_off_axis, ret_up_beam["cosine_exponent_n"])

    ret_up_cn0, ret_up_losses = compute_single_hop_cn0(
        tx_eirp_dbw=terminal_b_eirp,
        rx_gt_db_per_k=sat_ret_uplink_gt + ret_up_roll_off,
        frequency_hz=link_params["ret_uplink_freq_ghz"] * 1e9,
        slant_range_m=range_b_km * 1e3,
        beam_roll_off_db=ret_up_roll_off,
        weather_atten_db=link_params["weather_atten_ret_uplink_db"],
        pointing_loss_db=terminal_b["pointing_loss_db"],
        polarization_loss_db=terminal_b["polarization_loss_db"],
    )

    # Return Downlink: Satellite transmits → A receives
    ret_down_beam = satellite["ret_downlink_beam"]
    ret_down_off_axis = compute_beam_off_axis_angle_deg(
        sat_lat, sat_lon, sat_alt,
        terminal_a["lat_deg"], terminal_a["lon_deg"], terminal_a["alt_km"],
        ret_down_beam["center_lat_deg"], ret_down_beam["center_lon_deg"], 0.0,
    )
    ret_down_roll_off = compute_beam_roll_off_db(ret_down_off_axis, ret_down_beam["cosine_exponent_n"])

    ret_down_cn0, ret_down_losses = compute_single_hop_cn0(
        tx_eirp_dbw=sat_ret_down_eirp + ret_down_roll_off,
        rx_gt_db_per_k=terminal_a["gt_db_per_k"],
        frequency_hz=link_params["ret_downlink_freq_ghz"] * 1e9,
        slant_range_m=range_a_km * 1e3,
        beam_roll_off_db=ret_down_roll_off,
        weather_atten_db=link_params["weather_atten_ret_downlink_db"],
        pointing_loss_db=terminal_a["pointing_loss_db"],
        polarization_loss_db=terminal_a["polarization_loss_db"],
    )

    # Combined return link thermal C/N0 (bent-pipe)
    ret_combined_cn0 = combine_cn0_bent_pipe(ret_up_cn0, ret_down_cn0)

    # Return link C/N (per-hop, if bandwidth provided)
    ret_up_cn = cn0_to_cn(ret_up_cn0, bandwidth_hz) if bandwidth_hz else None
    ret_down_cn = cn0_to_cn(ret_down_cn0, bandwidth_hz) if bandwidth_hz else None
    ret_combined_cn = cn0_to_cn(ret_combined_cn0, bandwidth_hz) if bandwidth_hz else None

    # Return link intermodulation
    ret_ci_terminal_hpa = compute_ci_from_npr(terminal_b.get("hpa_npr_db"))
    ret_ci_satellite = compute_ci_from_npr(sat_ret_down_npr)
    ret_ci_total = combine_ci_sources(ret_ci_terminal_hpa, ret_ci_satellite)

    # Return link total C/(N+I)
    ret_cnir = combine_cn_with_ci(ret_combined_cn, ret_ci_total) if ret_combined_cn is not None else None

    # Return link Es/N0
    ret_es_n0 = cn0_to_es_n0(ret_combined_cn0, symbol_rate_hz) if symbol_rate_hz else None

    # =========================================================================
    # WARNINGS
    # =========================================================================

    warnings = check_elevation_warnings(
        elev_a_deg, elev_b_deg,
        link_params["min_elevation_warning_deg"],
    )

    # =========================================================================
    # BUILD RESPONSE
    # =========================================================================

    return {
        "forward_link": {
            "uplink": {
                "slant_range_km": range_a_km,
                "elevation_angle_deg": elev_a_deg,
                "off_axis_angle_deg": fwd_up_off_axis,
                "fspl_db": fwd_up_losses["fspl_db"],
                "beam_roll_off_db": fwd_up_losses["beam_roll_off_db"],
                "weather_atten_db": fwd_up_losses["weather_atten_db"],
                "pointing_loss_db": fwd_up_losses["pointing_loss_db"],
                "polarization_loss_db": fwd_up_losses["polarization_loss_db"],
                "total_path_loss_db": fwd_up_losses["total_path_loss_db"],
                "cn0_db_hz": fwd_up_cn0,
                "cn_db": fwd_up_cn,
            },
            "downlink": {
                "slant_range_km": range_b_km,
                "elevation_angle_deg": elev_b_deg,
                "off_axis_angle_deg": fwd_down_off_axis,
                "fspl_db": fwd_down_losses["fspl_db"],
                "beam_roll_off_db": fwd_down_losses["beam_roll_off_db"],
                "weather_atten_db": fwd_down_losses["weather_atten_db"],
                "pointing_loss_db": fwd_down_losses["pointing_loss_db"],
                "polarization_loss_db": fwd_down_losses["polarization_loss_db"],
                "total_path_loss_db": fwd_down_losses["total_path_loss_db"],
                "cn0_db_hz": fwd_down_cn0,
                "cn_db": fwd_down_cn,
            },
            "combined_cn0_db_hz": fwd_combined_cn0,
            "ci_terminal_hpa_db": fwd_ci_terminal_hpa,
            "ci_satellite_transponder_db": fwd_ci_satellite,
            "ci_total_db": fwd_ci_total,
            "combined_cn_db": fwd_combined_cn,
            "cnir_db": fwd_cnir,
            "es_n0_db": fwd_es_n0,
            "channel_bandwidth_mhz": bandwidth_mhz,
        },
        "return_link": {
            "uplink": {
                "slant_range_km": range_b_km,
                "elevation_angle_deg": elev_b_deg,
                "off_axis_angle_deg": ret_up_off_axis,
                "fspl_db": ret_up_losses["fspl_db"],
                "beam_roll_off_db": ret_up_losses["beam_roll_off_db"],
                "weather_atten_db": ret_up_losses["weather_atten_db"],
                "pointing_loss_db": ret_up_losses["pointing_loss_db"],
                "polarization_loss_db": ret_up_losses["polarization_loss_db"],
                "total_path_loss_db": ret_up_losses["total_path_loss_db"],
                "cn0_db_hz": ret_up_cn0,
                "cn_db": ret_up_cn,
            },
            "downlink": {
                "slant_range_km": range_a_km,
                "elevation_angle_deg": elev_a_deg,
                "off_axis_angle_deg": ret_down_off_axis,
                "fspl_db": ret_down_losses["fspl_db"],
                "beam_roll_off_db": ret_down_losses["beam_roll_off_db"],
                "weather_atten_db": ret_down_losses["weather_atten_db"],
                "pointing_loss_db": ret_down_losses["pointing_loss_db"],
                "polarization_loss_db": ret_down_losses["polarization_loss_db"],
                "total_path_loss_db": ret_down_losses["total_path_loss_db"],
                "cn0_db_hz": ret_down_cn0,
                "cn_db": ret_down_cn,
            },
            "combined_cn0_db_hz": ret_combined_cn0,
            "ci_terminal_hpa_db": ret_ci_terminal_hpa,
            "ci_satellite_transponder_db": ret_ci_satellite,
            "ci_total_db": ret_ci_total,
            "combined_cn_db": ret_combined_cn,
            "cnir_db": ret_cnir,
            "es_n0_db": ret_es_n0,
            "channel_bandwidth_mhz": bandwidth_mhz,
        },
        "geometry": {
            "terminal_a_slant_range_km": range_a_km,
            "terminal_b_slant_range_km": range_b_km,
            "terminal_a_elevation_deg": elev_a_deg,
            "terminal_b_elevation_deg": elev_b_deg,
        },
        "warnings": warnings,
    }
