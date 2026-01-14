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
