import math

# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0


def compute_azimuth_deg(
    start_lat_deg: float,
    start_lon_deg: float,
    end_lat_deg: float,
    end_lon_deg: float,
) -> float:
    """
    Compute the initial bearing (azimuth) from start point to end point
    on a sphere using the spherical law of cosines formula.

    θ = atan2(sin(Δλ)·cos(φ₂), cos(φ₁)·sin(φ₂) − sin(φ₁)·cos(φ₂)·cos(Δλ))

    Parameters
    ----------
    start_lat_deg : float
        Latitude of start point in degrees (-90 to 90)
    start_lon_deg : float
        Longitude of start point in degrees (-180 to 180)
    end_lat_deg : float
        Latitude of end point in degrees (-90 to 90)
    end_lon_deg : float
        Longitude of end point in degrees (-180 to 180)

    Returns
    -------
    float
        Initial bearing (azimuth) in degrees, normalized to [0, 360)
    """
    # Convert to radians
    phi1 = math.radians(start_lat_deg)
    phi2 = math.radians(end_lat_deg)
    delta_lambda = math.radians(end_lon_deg - start_lon_deg)

    # Spherical law of cosines for azimuth
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    theta_rad = math.atan2(x, y)

    # Convert to degrees and normalize to [0, 360)
    theta_deg = math.degrees(theta_rad)
    azimuth_deg = (theta_deg + 360) % 360

    return azimuth_deg


def compute_central_angle_deg(
    start_lat_deg: float,
    start_lon_deg: float,
    end_lat_deg: float,
    end_lon_deg: float,
) -> float:
    """
    Compute the central angle (angular separation) between two points on a sphere.

    cos(γ) = sin(φ₁)·sin(φ₂) + cos(φ₁)·cos(φ₂)·cos(Δλ)

    Parameters
    ----------
    start_lat_deg : float
        Latitude of start point in degrees
    start_lon_deg : float
        Longitude of start point in degrees
    end_lat_deg : float
        Latitude of end point in degrees
    end_lon_deg : float
        Longitude of end point in degrees

    Returns
    -------
    float
        Central angle in degrees
    """
    phi1 = math.radians(start_lat_deg)
    phi2 = math.radians(end_lat_deg)
    delta_lambda = math.radians(end_lon_deg - start_lon_deg)

    cos_gamma = (
        math.sin(phi1) * math.sin(phi2)
        + math.cos(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    )
    # Clamp to [-1, 1] to avoid numerical issues with acos
    cos_gamma = max(-1.0, min(1.0, cos_gamma))
    gamma_rad = math.acos(cos_gamma)

    return math.degrees(gamma_rad)


def compute_elevation_deg(
    ground_lat_deg: float,
    ground_lon_deg: float,
    subsatellite_lat_deg: float,
    subsatellite_lon_deg: float,
    satellite_altitude_km: float,
) -> float:
    """
    Compute the elevation angle from a ground station to a satellite.

    El = arctan[(cos(γ) - R_E/(R_E + h)) / sin(γ)]

    Where γ is the central angle between ground station and subsatellite point,
    R_E is Earth's radius, and h is the satellite altitude.

    Parameters
    ----------
    ground_lat_deg : float
        Latitude of ground station in degrees (-90 to 90)
    ground_lon_deg : float
        Longitude of ground station in degrees (-180 to 180)
    subsatellite_lat_deg : float
        Latitude of subsatellite point in degrees (-90 to 90)
    subsatellite_lon_deg : float
        Longitude of subsatellite point in degrees (-180 to 180)
    satellite_altitude_km : float
        Satellite altitude above Earth's surface in kilometers

    Returns
    -------
    float
        Elevation angle in degrees. Negative values indicate the satellite
        is below the horizon.
    """
    if satellite_altitude_km <= 0:
        raise ValueError("Satellite altitude must be positive")

    # Compute central angle
    gamma_deg = compute_central_angle_deg(
        ground_lat_deg, ground_lon_deg,
        subsatellite_lat_deg, subsatellite_lon_deg
    )
    gamma_rad = math.radians(gamma_deg)

    # Handle the case where ground station is directly below satellite
    if gamma_deg < 1e-9:
        return 90.0

    # Compute elevation angle
    r_ratio = EARTH_RADIUS_KM / (EARTH_RADIUS_KM + satellite_altitude_km)
    numerator = math.cos(gamma_rad) - r_ratio
    denominator = math.sin(gamma_rad)

    elevation_rad = math.atan2(numerator, denominator)
    elevation_deg = math.degrees(elevation_rad)

    return elevation_deg


def compute_nadir_angle_deg(
    central_angle_deg: float,
    satellite_altitude_km: float,
) -> float:
    """
    Compute the nadir angle (eta) at the satellite.

    η = arctan[sin(λ) · r / (1 - cos(λ) · r)]

    Where λ is the central angle and r = R_E / (R_E + h).

    Parameters
    ----------
    central_angle_deg : float
        Central angle (lambda) between ground station and subsatellite point in degrees
    satellite_altitude_km : float
        Satellite altitude above Earth's surface in kilometers

    Returns
    -------
    float
        Nadir angle (eta) in degrees
    """
    if satellite_altitude_km <= 0:
        raise ValueError("Satellite altitude must be positive")

    lambda_rad = math.radians(central_angle_deg)

    # Handle the case where ground station is directly below satellite
    if central_angle_deg < 1e-9:
        return 0.0

    r_ratio = EARTH_RADIUS_KM / (EARTH_RADIUS_KM + satellite_altitude_km)

    numerator = math.sin(lambda_rad) * r_ratio
    denominator = 1.0 - math.cos(lambda_rad) * r_ratio

    eta_rad = math.atan2(numerator, denominator)
    eta_deg = math.degrees(eta_rad)

    return eta_deg


def compute_terminal_phi_deg(
    ground_lat_deg: float,
    subsatellite_lat_deg: float,
    central_angle_deg: float,
) -> float:
    """
    Compute the terminal phi angle (bearing at subsatellite point toward ground station).

    φ_terminal = arccos[(sin(φ₁) - cos(λ)·sin(φ₂)) / (sin(λ)·cos(φ₂))]

    This is the angle in the spherical triangle at the subsatellite point,
    used for polarization alignment calculations.

    Parameters
    ----------
    ground_lat_deg : float
        Latitude of ground station in degrees (-90 to 90)
    subsatellite_lat_deg : float
        Latitude of subsatellite point in degrees (-90 to 90)
    central_angle_deg : float
        Central angle (lambda) between ground station and subsatellite point in degrees

    Returns
    -------
    float
        Terminal phi angle in degrees
    """
    phi1 = math.radians(ground_lat_deg)
    phi2 = math.radians(subsatellite_lat_deg)
    lambda_rad = math.radians(central_angle_deg)

    # Handle the case where ground station is directly below satellite
    if central_angle_deg < 1e-9:
        return 0.0

    # Handle the case where subsatellite point is at a pole
    if abs(math.cos(phi2)) < 1e-9:
        return 0.0

    numerator = math.sin(phi1) - math.cos(lambda_rad) * math.sin(phi2)
    denominator = math.sin(lambda_rad) * math.cos(phi2)

    # Clamp to [-1, 1] to avoid numerical issues with acos
    cos_phi_terminal = numerator / denominator
    cos_phi_terminal = max(-1.0, min(1.0, cos_phi_terminal))

    phi_terminal_rad = math.acos(cos_phi_terminal)
    phi_terminal_deg = math.degrees(phi_terminal_rad)

    return phi_terminal_deg


def compute_slant_range_km(
    central_angle_deg: float,
    satellite_altitude_km: float,
) -> float:
    """
    Compute the slant range (distance) from the ground station to the satellite.

    d = √[(R_E + h)² + R_E² - 2·R_E·(R_E + h)·cos(λ)]

    Using the law of cosines in the triangle formed by Earth's center,
    the ground station, and the satellite.

    Parameters
    ----------
    central_angle_deg : float
        Central angle (lambda) between ground station and subsatellite point in degrees
    satellite_altitude_km : float
        Satellite altitude above Earth's surface in kilometers

    Returns
    -------
    float
        Slant range (distance) from ground station to satellite in kilometers
    """
    if satellite_altitude_km <= 0:
        raise ValueError("Satellite altitude must be positive")

    lambda_rad = math.radians(central_angle_deg)

    r_e = EARTH_RADIUS_KM
    r_s = EARTH_RADIUS_KM + satellite_altitude_km

    # Law of cosines: d² = r_s² + r_e² - 2·r_e·r_s·cos(λ)
    d_squared = r_s**2 + r_e**2 - 2 * r_e * r_s * math.cos(lambda_rad)
    slant_range_km = math.sqrt(d_squared)

    return slant_range_km
