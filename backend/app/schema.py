from pydantic import BaseModel, Field
from typing import Optional


class LinkBudgetRequest(BaseModel):
    frequency_hz: float = Field(..., description="Carrier frequency in Hz")
    distance_m: float = Field(..., description="Slant range between Tx and Rx in meters")
    tx_power_dbw: float = Field(..., description="Transmit power in dBW")
    tx_antenna_gain_db: float = Field(..., description="Transmit antenna gain in dB")
    rx_antenna_gain_db: float = Field(..., description="Receive antenna gain in dB")
    tx_losses_db: float = Field(0.0, description="Transmit path losses (cables, etc.) in dB")
    rx_losses_db: float = Field(0.0, description="Receive path losses (cables, etc.) in dB")
    other_losses_db: float = Field(0.0, description="Additional propagation losses (rain, pointing, etc.) in dB")


class LinkBudgetResponse(BaseModel):
    fspl_db: float
    received_power_dbw: float
    margin_db: Optional[float] = Field(
        None, description="Optional link margin if a threshold is provided"
    )


class EIRPRequest(BaseModel):
    tx_power_dbw: float = Field(..., description="Transmit power in dBW")
    tx_antenna_gain_db: float = Field(..., description="Transmit antenna gain in dB")
    tx_losses_db: float = Field(0.0, description="Transmit losses in dB")


class EIRPResponse(BaseModel):
    eirp_dbw: float


class GTRequest(BaseModel):
    antenna_gain_db: float = Field(..., description="Receive antenna gain in dB")
    system_noise_temp_k: float = Field(..., description="System noise temperature in Kelvin")


class GTResponse(BaseModel):
    gt_db_per_k: float


class EbN0Request(BaseModel):
    cn0_db_hz: float = Field(..., description="Carrier-to-noise density ratio in dB-Hz")
    data_rate_bps: float = Field(..., description="Information bit rate in bps")


class EbN0Response(BaseModel):
    ebn0_db: float


class PhasedArrayGainRequest(BaseModel):
    element_gain_db: float = Field(..., description="Single element gain in dB")
    num_elements: int = Field(..., gt=0, description="Number of antenna elements in the array")
    array_efficiency: float = Field(
        1.0, ge=0.0, le=1.0, description="Array efficiency factor between 0 and 1"
    )


class PhasedArrayGainResponse(BaseModel):
    array_gain_db: float


class ScanLossRequest(BaseModel):
    satellite_longitude_deg: float = Field(..., description="GEO satellite longitude in degrees")
    user_latitude_deg: float = Field(..., ge=-90, le=90, description="User latitude in degrees")
    user_longitude_deg: float = Field(..., ge=-180, le=180, description="User longitude in degrees")
    scan_exponent: float = Field(1.3, gt=0, description="Scan loss exponent n for cos^n model")


class ScanLossResponse(BaseModel):
    scan_angle_deg: float = Field(..., description="Off-nadir scan angle in degrees")
    scan_loss_db: float = Field(..., description="Scan loss in dB")


class AzimuthRequest(BaseModel):
    start_lat_deg: float = Field(..., ge=-90, le=90, description="Latitude of ground station in degrees")
    start_lon_deg: float = Field(..., ge=-180, le=180, description="Longitude of ground station in degrees")
    end_lat_deg: float = Field(..., ge=-90, le=90, description="Latitude of subsatellite point in degrees")
    end_lon_deg: float = Field(..., ge=-180, le=180, description="Longitude of subsatellite point in degrees")
    satellite_altitude_km: float = Field(
        35786.0, gt=0, description="Satellite altitude above Earth's surface in km (default: GEO)"
    )


class AzimuthResponse(BaseModel):
    azimuth_deg: float = Field(..., description="Initial bearing (azimuth) in degrees [0, 360)")
    elevation_deg: float = Field(..., description="Elevation angle in degrees (negative if below horizon)")
    central_angle_deg: float = Field(..., description="Central angle (lambda) between ground station and subsatellite point in degrees")
    nadir_angle_deg: float = Field(..., description="Nadir angle (eta) at the satellite in degrees")
    terminal_phi_deg: float = Field(..., description="Terminal phi angle (bearing at subsatellite point) in degrees")
    slant_range_km: float = Field(..., description="Slant range (distance) from ground station to satellite in kilometers")


class BeamOffAxisRequest(BaseModel):
    sat_lat_deg: float = Field(..., ge=-90, le=90, description="Satellite subsatellite point latitude in degrees")
    sat_lon_deg: float = Field(..., ge=-180, le=180, description="Satellite subsatellite point longitude in degrees")
    sat_alt_km: float = Field(35786.0, gt=0, description="Satellite altitude above Earth's surface in km")
    user_lat_deg: float = Field(..., ge=-90, le=90, description="User terminal latitude in degrees")
    user_lon_deg: float = Field(..., ge=-180, le=180, description="User terminal longitude in degrees")
    user_alt_km: float = Field(0.0, ge=0, description="User terminal altitude in km")
    beam_center_lat_deg: float = Field(..., ge=-90, le=90, description="Beam center latitude in degrees")
    beam_center_lon_deg: float = Field(..., ge=-180, le=180, description="Beam center longitude in degrees")
    beam_center_alt_km: float = Field(0.0, ge=0, description="Beam center altitude in km (typically 0)")


class BeamOffAxisResponse(BaseModel):
    off_axis_angle_deg: float = Field(..., description="Beam off-axis angle in degrees (acos of dot product)")
    
    # Satellite to User Terminal angles
    sat_to_user_lambda_deg: float = Field(..., description="Central angle (lambda) from satellite to user in degrees")
    sat_to_user_eta_deg: float = Field(..., description="Nadir angle (eta) for user direction in degrees")
    sat_to_user_phi_deg: float = Field(..., description="Azimuthal angle (phi) for user direction in degrees")
    sat_to_user_x: float = Field(..., description="Unit vector x = sin(eta)*sin(phi)")
    sat_to_user_y: float = Field(..., description="Unit vector y = sin(eta)*cos(phi)")
    sat_to_user_z: float = Field(..., description="Unit vector z = cos(eta)")
    
    # Satellite to Beam Center angles
    sat_to_beam_lambda_deg: float = Field(..., description="Central angle (lambda) from satellite to beam center in degrees")
    sat_to_beam_eta_deg: float = Field(..., description="Nadir angle (eta) for beam direction in degrees")
    sat_to_beam_phi_deg: float = Field(..., description="Azimuthal angle (phi) for beam direction in degrees")
    sat_to_beam_x: float = Field(..., description="Unit vector x = sin(eta)*sin(phi)")
    sat_to_beam_y: float = Field(..., description="Unit vector y = sin(eta)*cos(phi)")
    sat_to_beam_z: float = Field(..., description="Unit vector z = cos(eta)")
    
    # User terminal geometry
    user_elevation_deg: float = Field(..., description="Elevation angle from user terminal to satellite in degrees")
    user_slant_range_km: float = Field(..., description="Slant range from user terminal to satellite in km")


class WeatherLossRequest(BaseModel):
    satellite_longitude_deg: float = Field(
        ..., ge=-180, le=180, description="GEO satellite longitude in degrees"
    )
    user_latitude_deg: float = Field(
        ..., ge=-90, le=90, description="User terminal latitude in degrees"
    )
    user_longitude_deg: float = Field(
        ..., ge=-180, le=180, description="User terminal longitude in degrees"
    )
    availability_percent: float = Field(
        ..., ge=97.0, le=99.999, description="Required link availability percentage (97.0 to 99.999)"
    )
    frequency_ghz: float = Field(
        ..., gt=1.0, le=100.0, description="Signal frequency in GHz (1 to 100)"
    )


class WeatherLossResponse(BaseModel):
    elevation_deg: float = Field(..., description="Elevation angle to satellite in degrees")
    rain_rate_mm_hr: float = Field(..., description="Rain rate used for calculation in mm/hr")
    weather_loss_db: float = Field(..., description="Total weather attenuation in dB")


# ===========================================================================
# Duplex Satellite Link Budget
# ===========================================================================

class TerminalInput(BaseModel):
    """Ground terminal parameters"""
    lat_deg: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon_deg: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    alt_km: float = Field(0.0, ge=0, description="Altitude above sea level in km")

    eirp_dbw: float = Field(..., description="Effective Isotropic Radiated Power in dBW (operating, after back-off)")
    gt_db_per_k: float = Field(..., description="Figure of merit G/T in dB/K")
    pointing_loss_db: float = Field(0.0, ge=0, description="Antenna pointing loss in dB")
    polarization_loss_db: float = Field(0.0, ge=0, description="Polarization mismatch loss in dB")

    # HPA non-linearity parameters (optional)
    eirp_saturated_dbw: Optional[float] = Field(None, description="Saturated EIRP in dBW (if provided, eirp_dbw is ignored and computed from this minus OBO)")
    hpa_obo_db: float = Field(0.0, ge=0, description="HPA Output Back-Off in dB")
    hpa_npr_db: Optional[float] = Field(None, description="HPA Noise Power Ratio in dB at operating point (None = ideal/linear, no intermod)")


class BeamInput(BaseModel):
    """Satellite beam parameters"""
    center_lat_deg: float = Field(..., ge=-90, le=90, description="Beam center latitude")
    center_lon_deg: float = Field(..., ge=-180, le=180, description="Beam center longitude")
    cosine_exponent_n: float = Field(1.0, gt=0, description="Exponent n in cos^n(θ) pattern")


class SatelliteInput(BaseModel):
    """Satellite parameters"""
    lat_deg: float = Field(0.0, ge=-90, le=90, description="Subsatellite point latitude")
    lon_deg: float = Field(..., ge=-180, le=180, description="Subsatellite point longitude")
    alt_km: float = Field(35786.0, gt=0, description="Altitude above Earth surface in km")

    # Forward link (A → Sat → B)
    fwd_uplink_gt_db_per_k: float = Field(..., description="Satellite G/T for forward uplink")
    fwd_downlink_eirp_dbw: float = Field(..., description="Satellite EIRP for forward downlink (operating, after back-off)")

    # Return link (B → Sat → A)
    ret_uplink_gt_db_per_k: float = Field(..., description="Satellite G/T for return uplink")
    ret_downlink_eirp_dbw: float = Field(..., description="Satellite EIRP for return downlink (operating, after back-off)")

    # Four independent beams
    fwd_uplink_beam: BeamInput
    fwd_downlink_beam: BeamInput
    ret_uplink_beam: BeamInput
    ret_downlink_beam: BeamInput

    # Transponder non-linearity parameters (optional)
    # Forward downlink transponder
    fwd_downlink_eirp_saturated_dbw: Optional[float] = Field(None, description="Forward downlink saturated EIRP in dBW")
    fwd_downlink_obo_db: float = Field(0.0, ge=0, description="Forward downlink transponder Output Back-Off in dB")
    fwd_downlink_npr_db: Optional[float] = Field(None, description="Forward downlink transponder NPR in dB (None = ideal)")

    # Return downlink transponder
    ret_downlink_eirp_saturated_dbw: Optional[float] = Field(None, description="Return downlink saturated EIRP in dBW")
    ret_downlink_obo_db: float = Field(0.0, ge=0, description="Return downlink transponder Output Back-Off in dB")
    ret_downlink_npr_db: Optional[float] = Field(None, description="Return downlink transponder NPR in dB (None = ideal)")


class LinkParametersInput(BaseModel):
    """Link frequency and loss parameters"""
    # Ka-band defaults: 30 GHz up, 20 GHz down
    fwd_uplink_freq_ghz: float = Field(30.0, gt=0, description="Forward uplink frequency in GHz")
    fwd_downlink_freq_ghz: float = Field(20.0, gt=0, description="Forward downlink frequency in GHz")
    ret_uplink_freq_ghz: float = Field(30.0, gt=0, description="Return uplink frequency in GHz")
    ret_downlink_freq_ghz: float = Field(20.0, gt=0, description="Return downlink frequency in GHz")

    # Weather attenuation (user-provided)
    weather_atten_fwd_uplink_db: float = Field(0.0, ge=0, description="Forward uplink weather attenuation in dB")
    weather_atten_fwd_downlink_db: float = Field(0.0, ge=0, description="Forward downlink weather attenuation in dB")
    weather_atten_ret_uplink_db: float = Field(0.0, ge=0, description="Return uplink weather attenuation in dB")
    weather_atten_ret_downlink_db: float = Field(0.0, ge=0, description="Return downlink weather attenuation in dB")

    # Channel bandwidth parameters (for C/N and Es/N0 calculation)
    symbol_rate_msps: Optional[float] = Field(None, gt=0, description="Symbol rate in Msps (required for C/N calculation)")
    roll_off_factor: float = Field(0.20, ge=0.0, le=1.0, description="DVB-S2 roll-off factor (0.20, 0.25, or 0.35)")

    # Elevation angle warning threshold
    min_elevation_warning_deg: float = Field(5.0, ge=0, le=90, description="Minimum elevation warning threshold in degrees")


class DuplexSatelliteLinkRequest(BaseModel):
    """Top-level request for duplex satellite link budget"""
    terminal_a: TerminalInput
    terminal_b: TerminalInput
    satellite: SatelliteInput
    link_params: LinkParametersInput


class SingleHopResult(BaseModel):
    """Results for one hop (uplink or downlink)"""
    slant_range_km: float = Field(..., description="Slant range in km")
    elevation_angle_deg: float = Field(..., description="Elevation angle in degrees")
    off_axis_angle_deg: float = Field(..., description="Off-axis angle from beam center in degrees")

    # Loss breakdown
    fspl_db: float = Field(..., description="Free space path loss in dB")
    beam_roll_off_db: float = Field(..., description="Beam roll-off loss in dB")
    weather_atten_db: float = Field(..., description="Weather attenuation in dB")
    pointing_loss_db: float = Field(..., description="Pointing loss in dB")
    polarization_loss_db: float = Field(..., description="Polarization loss in dB")
    total_path_loss_db: float = Field(..., description="Total path loss in dB")

    # Performance
    cn0_db_hz: float = Field(..., description="Carrier-to-noise density ratio in dB-Hz")
    cn_db: Optional[float] = Field(None, description="Carrier-to-noise ratio in dB (if symbol rate provided)")


class LinkDirectionResult(BaseModel):
    """Results for one link direction (forward or return)"""
    uplink: SingleHopResult
    downlink: SingleHopResult
    combined_cn0_db_hz: float = Field(..., description="Combined thermal C/N0 for bent-pipe in dB-Hz")

    # Intermodulation (if NPR values provided)
    ci_terminal_hpa_db: Optional[float] = Field(None, description="C/I from uplink terminal HPA in dB")
    ci_satellite_transponder_db: Optional[float] = Field(None, description="C/I from satellite transponder in dB")
    ci_total_db: Optional[float] = Field(None, description="Combined C/I from all intermod sources in dB")

    # Total C/(N+I) including intermodulation
    cnir_db: Optional[float] = Field(None, description="Total C/(N+I) including thermal noise and intermod in dB")

    # DVB-S2 metrics (if symbol rate provided)
    combined_cn_db: Optional[float] = Field(None, description="Combined C/N in dB (from C/N0 - 10*log10(bandwidth))")
    es_n0_db: Optional[float] = Field(None, description="Es/N0 in dB (from C/N0 - 10*log10(symbol_rate))")
    channel_bandwidth_mhz: Optional[float] = Field(None, description="Occupied channel bandwidth in MHz")


class GeometryResult(BaseModel):
    """Geometry summary"""
    terminal_a_slant_range_km: float = Field(..., description="Terminal A to satellite slant range in km")
    terminal_b_slant_range_km: float = Field(..., description="Terminal B to satellite slant range in km")
    terminal_a_elevation_deg: float = Field(..., description="Terminal A elevation angle in degrees")
    terminal_b_elevation_deg: float = Field(..., description="Terminal B elevation angle in degrees")


class ElevationWarning(BaseModel):
    """Warning for low elevation angles"""
    terminal: str = Field(..., description="Terminal identifier (A or B)")
    elevation_deg: float = Field(..., description="Actual elevation angle in degrees")
    threshold_deg: float = Field(..., description="Warning threshold in degrees")
    message: str = Field(..., description="Warning message")


class DuplexSatelliteLinkResponse(BaseModel):
    """Complete response for duplex satellite link budget"""
    forward_link: LinkDirectionResult = Field(..., description="Forward link (A → Sat → B) results")
    return_link: LinkDirectionResult = Field(..., description="Return link (B → Sat → A) results")
    geometry: GeometryResult = Field(..., description="Geometry summary")
    warnings: list[ElevationWarning] = Field(default_factory=list, description="Elevation angle warnings")
