import math

# Constants
EARTH_RADIUS_KM = 6371.0
GEO_ALTITUDE_KM = 35786.0
GEO_ORBITAL_RADIUS_KM = EARTH_RADIUS_KM + GEO_ALTITUDE_KM  # ~42164 km


def compute_nadir_angle_deg(
    satellite_longitude_deg: float,
    user_latitude_deg: float,
    user_longitude_deg: float,
) -> float:
    """
    Compute the off-nadir (scan) angle from a GEO satellite to a ground user.

    The nadir angle is the angle at the satellite between the nadir vector
    (pointing to Earth center) and the vector pointing to the ground user.

    Using spherical geometry:
        cos(γ) = cos(φ_user) · cos(ΔL)
        θ_scan = arcsin[(R_E / r_sat) · sin(γ)]

    where:
        φ_user = user latitude
        ΔL = user longitude - satellite longitude
        R_E = Earth radius
        r_sat = GEO orbital radius

    Returns:
        Nadir angle in degrees
    """
    # Convert to radians
    user_lat_rad = math.radians(user_latitude_deg)
    delta_lon_rad = math.radians(user_longitude_deg - satellite_longitude_deg)

    # Central angle from sub-satellite point to user
    cos_gamma = math.cos(user_lat_rad) * math.cos(delta_lon_rad)

    # Clamp to valid range to handle floating point errors
    cos_gamma = max(-1.0, min(1.0, cos_gamma))
    gamma_rad = math.acos(cos_gamma)

    # Check if user is visible from satellite (gamma must be less than Earth edge angle)
    # Maximum visible angle from GEO: arccos(R_E / r_sat) ≈ 81.3°
    max_gamma = math.acos(EARTH_RADIUS_KM / GEO_ORBITAL_RADIUS_KM)
    if gamma_rad > max_gamma:
        raise ValueError(
            f"User location is not visible from the satellite. "
            f"Central angle {math.degrees(gamma_rad):.1f}° exceeds maximum {math.degrees(max_gamma):.1f}°"
        )

    # Nadir angle calculation
    sin_nadir = (EARTH_RADIUS_KM / GEO_ORBITAL_RADIUS_KM) * math.sin(gamma_rad)

    # Clamp to valid range
    sin_nadir = max(-1.0, min(1.0, sin_nadir))
    nadir_angle_rad = math.asin(sin_nadir)

    return math.degrees(nadir_angle_rad)


def compute_scan_loss_db(
    scan_angle_deg: float,
    scan_exponent: float = 1.3,
) -> float:
    """
    Compute ESA scan loss using the cosine^n model.

    L_scan (dB) = -10 · n · log₁₀(cos(θ_scan))

    where:
        θ_scan = scan angle from boresight (nadir)
        n = scan exponent (typically 1.2 to 1.5)

    Args:
        scan_angle_deg: Scan angle in degrees
        scan_exponent: Exponent for cosine model (default 1.3)

    Returns:
        Scan loss in dB (positive value representing loss)
    """
    if scan_exponent <= 0:
        raise ValueError("Scan exponent must be positive")

    if abs(scan_angle_deg) >= 90:
        raise ValueError("Scan angle must be less than 90 degrees")

    scan_angle_rad = math.radians(scan_angle_deg)
    cos_theta = math.cos(scan_angle_rad)

    if cos_theta <= 0:
        raise ValueError("Invalid scan angle results in non-positive cosine")

    # Loss in dB (returned as positive value)
    loss_db = -10.0 * scan_exponent * math.log10(cos_theta)

    return loss_db
