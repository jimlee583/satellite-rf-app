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
    off_axis_angle_deg: float = Field(..., description="Beam off-axis angle in degrees")
