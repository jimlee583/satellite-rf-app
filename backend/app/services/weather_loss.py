"""
Weather loss (rain attenuation) calculation using simplified ITU-R models.

This module implements rain attenuation calculation based on:
- ITU-R P.838-3: Specific attenuation model for rain
- ITU-R P.618: Propagation data for earth-space telecommunications
- ITU-R P.837: Characteristics of precipitation for propagation modelling
"""

import math
from typing import Tuple

from .azimuth import compute_elevation_deg, EARTH_RADIUS_KM


# GEO satellite altitude in km
GEO_ALTITUDE_KM = 35786.0

# Rain height model constants (simplified ITU-R P.839)
# Mean annual 0°C isotherm height varies by latitude
# This is a simplified approximation
RAIN_HEIGHT_BASE_KM = 5.0  # Approximate rain height at equator


# ITU-R P.838-3 coefficients for specific attenuation
# gamma_R = k * R^alpha (dB/km)
# These are interpolation points for horizontal polarization
# Format: (frequency_ghz, k_h, alpha_h, k_v, alpha_v)
ITU_P838_COEFFICIENTS = [
    (1.0, 0.0000387, 0.912, 0.0000352, 0.880),
    (2.0, 0.000154, 0.963, 0.000138, 0.923),
    (4.0, 0.000650, 1.121, 0.000591, 1.075),
    (6.0, 0.00175, 1.308, 0.00155, 1.265),
    (7.0, 0.00301, 1.332, 0.00265, 1.312),
    (8.0, 0.00454, 1.327, 0.00395, 1.310),
    (10.0, 0.0101, 1.276, 0.00887, 1.264),
    (12.0, 0.0188, 1.217, 0.0168, 1.200),
    (15.0, 0.0367, 1.154, 0.0335, 1.128),
    (20.0, 0.0751, 1.099, 0.0691, 1.065),
    (25.0, 0.124, 1.061, 0.113, 1.030),
    (30.0, 0.187, 1.021, 0.167, 1.000),
    (35.0, 0.263, 0.979, 0.233, 0.963),
    (40.0, 0.350, 0.939, 0.310, 0.929),
    (45.0, 0.442, 0.903, 0.393, 0.897),
    (50.0, 0.536, 0.873, 0.479, 0.868),
    (60.0, 0.707, 0.826, 0.642, 0.824),
    (70.0, 0.851, 0.793, 0.784, 0.793),
    (80.0, 0.975, 0.769, 0.906, 0.769),
    (90.0, 1.06, 0.753, 0.999, 0.754),
    (100.0, 1.12, 0.743, 1.06, 0.744),
]


# Simplified rain rate zones (ITU-R P.837 inspired)
# Maps availability percentage to approximate rain rate (mm/hr) for a "moderate" climate
# These are representative values for temperate regions (similar to ITU Rain Zone K)
RAIN_RATE_BY_AVAILABILITY = {
    97.0: 8.0,     # 3% exceedance
    98.0: 12.0,    # 2% exceedance
    99.0: 22.0,    # 1% exceedance
    99.5: 32.0,    # 0.5% exceedance  
    99.9: 50.0,    # 0.1% exceedance
    99.95: 63.0,   # 0.05% exceedance
    99.99: 83.0,   # 0.01% exceedance
    99.999: 120.0, # 0.001% exceedance
}


def _interpolate_p838_coefficients(frequency_ghz: float) -> Tuple[float, float]:
    """
    Interpolate ITU-R P.838 k and alpha coefficients for a given frequency.
    Uses horizontal polarization values (typical for most applications).
    
    Parameters
    ----------
    frequency_ghz : float
        Frequency in GHz (valid range: 1-100 GHz)
    
    Returns
    -------
    Tuple[float, float]
        (k, alpha) coefficients for specific attenuation calculation
    """
    if frequency_ghz < 1.0:
        raise ValueError("Frequency must be at least 1 GHz for rain attenuation model")
    if frequency_ghz > 100.0:
        raise ValueError("Frequency must not exceed 100 GHz for rain attenuation model")
    
    # Find bracketing points
    for i in range(len(ITU_P838_COEFFICIENTS) - 1):
        f_low, k_h_low, alpha_h_low, _, _ = ITU_P838_COEFFICIENTS[i]
        f_high, k_h_high, alpha_h_high, _, _ = ITU_P838_COEFFICIENTS[i + 1]
        
        if f_low <= frequency_ghz <= f_high:
            # Log-linear interpolation for k, linear for alpha
            t = (frequency_ghz - f_low) / (f_high - f_low)
            
            # Interpolate k in log domain
            log_k = math.log10(k_h_low) + t * (math.log10(k_h_high) - math.log10(k_h_low))
            k = 10 ** log_k
            
            # Linear interpolation for alpha
            alpha = alpha_h_low + t * (alpha_h_high - alpha_h_low)
            
            return k, alpha
    
    # Should not reach here if frequency is in valid range
    raise ValueError(f"Could not interpolate coefficients for {frequency_ghz} GHz")


def get_rain_rate_mm_hr(availability_percent: float) -> float:
    """
    Get the rain rate for a given availability percentage using simplified lookup.
    
    Uses interpolation between standard availability levels for a temperate climate.
    
    Parameters
    ----------
    availability_percent : float
        Link availability percentage (e.g., 99.9 for 99.9% availability)
        Valid range: 99.0 to 99.999
    
    Returns
    -------
    float
        Rain rate in mm/hr exceeded for the given percentage of time
    """
    if availability_percent < 97.0:
        raise ValueError("Availability must be at least 97%")
    if availability_percent > 99.999:
        raise ValueError("Availability must not exceed 99.999%")
    
    # Get sorted availability levels
    avail_levels = sorted(RAIN_RATE_BY_AVAILABILITY.keys())
    
    # Find bracketing levels
    for i in range(len(avail_levels) - 1):
        a_low = avail_levels[i]
        a_high = avail_levels[i + 1]
        
        if a_low <= availability_percent <= a_high:
            # Interpolate rain rate (log-linear in exceedance probability)
            # Convert to exceedance probability
            p_low = 100.0 - a_low
            p_high = 100.0 - a_high
            p_target = 100.0 - availability_percent
            
            r_low = RAIN_RATE_BY_AVAILABILITY[a_low]
            r_high = RAIN_RATE_BY_AVAILABILITY[a_high]
            
            # Log interpolation in probability space
            if p_target <= 0 or p_low <= 0 or p_high <= 0:
                return r_high
            
            log_p_low = math.log10(p_low)
            log_p_high = math.log10(p_high)
            log_p_target = math.log10(p_target)
            
            t = (log_p_target - log_p_low) / (log_p_high - log_p_low)
            
            # Linear interpolation of rain rate
            rain_rate = r_low + t * (r_high - r_low)
            return rain_rate
    
    # Edge case: exactly at a defined level
    if availability_percent in RAIN_RATE_BY_AVAILABILITY:
        return RAIN_RATE_BY_AVAILABILITY[availability_percent]
    
    raise ValueError(f"Could not determine rain rate for {availability_percent}% availability")


def compute_rain_height_km(user_latitude_deg: float) -> float:
    """
    Compute the effective rain height based on latitude.
    Simplified model based on ITU-R P.839.
    
    Parameters
    ----------
    user_latitude_deg : float
        User terminal latitude in degrees
    
    Returns
    -------
    float
        Effective rain height in km
    """
    abs_lat = abs(user_latitude_deg)
    
    # Simplified model: rain height decreases with latitude
    if abs_lat <= 23:
        # Tropical region
        return 5.0
    elif abs_lat <= 35:
        # Subtropical
        return 5.0 - 0.075 * (abs_lat - 23)
    else:
        # Temperate/polar
        return 4.1 - 0.03 * (abs_lat - 35)


def compute_specific_attenuation_db_per_km(
    frequency_ghz: float,
    rain_rate_mm_hr: float,
) -> float:
    """
    Compute specific attenuation using ITU-R P.838 model.
    
    gamma_R = k * R^alpha (dB/km)
    
    Parameters
    ----------
    frequency_ghz : float
        Signal frequency in GHz
    rain_rate_mm_hr : float
        Rain rate in mm/hr
    
    Returns
    -------
    float
        Specific attenuation in dB/km
    """
    if rain_rate_mm_hr <= 0:
        return 0.0
    
    k, alpha = _interpolate_p838_coefficients(frequency_ghz)
    gamma_r = k * (rain_rate_mm_hr ** alpha)
    
    return gamma_r


def compute_weather_loss_db(
    satellite_longitude_deg: float,
    user_latitude_deg: float,
    user_longitude_deg: float,
    availability_percent: float,
    frequency_ghz: float,
) -> Tuple[float, float, float]:
    """
    Compute total weather-related signal attenuation (rain fade).
    
    Uses simplified ITU-R models for rain attenuation calculation.
    
    Parameters
    ----------
    satellite_longitude_deg : float
        GEO satellite longitude in degrees
    user_latitude_deg : float
        User terminal latitude in degrees (-90 to 90)
    user_longitude_deg : float
        User terminal longitude in degrees (-180 to 180)
    availability_percent : float
        Required link availability percentage (99.0 to 99.999)
    frequency_ghz : float
        Signal frequency in GHz (1 to 100)
    
    Returns
    -------
    Tuple[float, float, float]
        (elevation_deg, rain_rate_mm_hr, weather_loss_db)
    """
    # Validate inputs
    if not -90 <= user_latitude_deg <= 90:
        raise ValueError("User latitude must be between -90 and 90 degrees")
    if not -180 <= user_longitude_deg <= 180:
        raise ValueError("User longitude must be between -180 and 180 degrees")
    
    # Compute elevation angle (GEO satellite at equator)
    elevation_deg = compute_elevation_deg(
        ground_lat_deg=user_latitude_deg,
        ground_lon_deg=user_longitude_deg,
        subsatellite_lat_deg=0.0,  # GEO satellites are at equator
        subsatellite_lon_deg=satellite_longitude_deg,
        satellite_altitude_km=GEO_ALTITUDE_KM,
    )
    
    if elevation_deg <= 0:
        raise ValueError(
            f"Satellite not visible from this location (elevation: {elevation_deg:.1f}°)"
        )
    
    # Get rain rate for the specified availability
    rain_rate = get_rain_rate_mm_hr(availability_percent)
    
    # Compute rain height
    rain_height = compute_rain_height_km(user_latitude_deg)
    
    # Compute specific attenuation
    gamma_r = compute_specific_attenuation_db_per_km(frequency_ghz, rain_rate)
    
    # Compute effective path length
    l_eff = _compute_effective_path_length_simple(
        elevation_deg=elevation_deg,
        rain_height_km=rain_height,
        frequency_ghz=frequency_ghz,
        rain_rate_mm_hr=rain_rate,
    )
    
    # Total attenuation
    weather_loss_db = gamma_r * l_eff
    
    return elevation_deg, rain_rate, weather_loss_db


def _compute_effective_path_length_simple(
    elevation_deg: float,
    rain_height_km: float,
    frequency_ghz: float,
    rain_rate_mm_hr: float,
    user_altitude_km: float = 0.0,
) -> float:
    """
    Compute effective slant path length through rain with path reduction factor.
    Simplified ITU-R P.618 model.
    """
    if elevation_deg <= 0:
        raise ValueError("Elevation angle must be positive")
    
    # Height difference
    delta_h = rain_height_km - user_altitude_km
    if delta_h <= 0:
        return 0.0
    
    elevation_rad = math.radians(elevation_deg)
    
    # Slant path length
    if elevation_deg >= 5:
        l_s = delta_h / math.sin(elevation_rad)
    else:
        # Low elevation approximation with Earth curvature
        sin_el = math.sin(elevation_rad)
        l_s = 2 * delta_h / (
            math.sqrt(sin_el ** 2 + 2 * delta_h / EARTH_RADIUS_KM) + sin_el
        )
    
    # Horizontal projection
    l_g = l_s * math.cos(elevation_rad)
    
    # Path reduction factor (simplified ITU-R P.618)
    # r = 1 / (1 + 0.78 * sqrt(L_G * gamma / f) - 0.38 * (1 - exp(-2 * L_G)))
    gamma_r = compute_specific_attenuation_db_per_km(frequency_ghz, rain_rate_mm_hr)
    
    if l_g <= 0 or gamma_r <= 0:
        return l_s
    
    term1 = 0.78 * math.sqrt(l_g * gamma_r / frequency_ghz)
    term2 = 0.38 * (1 - math.exp(-2 * l_g))
    
    r = 1.0 / (1.0 + term1 - term2)
    r = max(0.1, min(1.0, r))  # Clamp to reasonable range
    
    l_eff = l_s * r
    
    return l_eff
