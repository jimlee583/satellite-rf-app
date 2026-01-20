import math
from typing import Dict, Tuple

from app.services.azimuth import (
    compute_central_angle_deg,
    compute_elevation_deg,
    compute_nadir_angle_deg,
    compute_slant_range_km,
    compute_terminal_phi_deg,
)

# WGS84 ellipsoid parameters
EARTH_SEMI_MAJOR_AXIS_KM = 6378.137  # Equatorial radius in km
EARTH_FLATTENING = 1 / 298.257223563
EARTH_SEMI_MINOR_AXIS_KM = EARTH_SEMI_MAJOR_AXIS_KM * (1 - EARTH_FLATTENING)
EARTH_ECCENTRICITY_SQ = 1 - (EARTH_SEMI_MINOR_AXIS_KM / EARTH_SEMI_MAJOR_AXIS_KM) ** 2


def geodetic_to_ecef(
    lat_deg: float,
    lon_deg: float,
    alt_km: float,
) -> Tuple[float, float, float]:
    """
    Convert geodetic coordinates (latitude, longitude, altitude) to
    Earth-Centered Earth-Fixed (ECEF) Cartesian coordinates.

    Uses WGS84 ellipsoid model.

    Parameters
    ----------
    lat_deg : float
        Geodetic latitude in degrees (-90 to 90)
    lon_deg : float
        Longitude in degrees (-180 to 180)
    alt_km : float
        Altitude above the ellipsoid in kilometers

    Returns
    -------
    Tuple[float, float, float]
        (x, y, z) ECEF coordinates in kilometers
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)

    # Radius of curvature in the prime vertical
    N = EARTH_SEMI_MAJOR_AXIS_KM / math.sqrt(1 - EARTH_ECCENTRICITY_SQ * sin_lat ** 2)

    x = (N + alt_km) * cos_lat * cos_lon
    y = (N + alt_km) * cos_lat * sin_lon
    z = (N * (1 - EARTH_ECCENTRICITY_SQ) + alt_km) * sin_lat

    return (x, y, z)


def vector_subtract(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Compute a - b for 3D vectors."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vector_dot(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
) -> float:
    """Compute dot product of two 3D vectors."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vector_magnitude(v: Tuple[float, float, float]) -> float:
    """Compute magnitude of a 3D vector."""
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def compute_beam_off_axis_angle_deg(
    sat_lat_deg: float,
    sat_lon_deg: float,
    sat_alt_km: float,
    user_lat_deg: float,
    user_lon_deg: float,
    user_alt_km: float,
    beam_center_lat_deg: float,
    beam_center_lon_deg: float,
    beam_center_alt_km: float,
) -> float:
    """
    Compute the beam off-axis angle using the vector method.

    This is the angle at the satellite between:
    - The vector from satellite to beam center
    - The vector from satellite to user terminal

    θ = arccos[(V_beam · V_user) / (|V_beam| · |V_user|)]

    Parameters
    ----------
    sat_lat_deg : float
        Satellite subsatellite point latitude in degrees
    sat_lon_deg : float
        Satellite subsatellite point longitude in degrees
    sat_alt_km : float
        Satellite altitude above Earth's surface in km
    user_lat_deg : float
        User terminal latitude in degrees
    user_lon_deg : float
        User terminal longitude in degrees
    user_alt_km : float
        User terminal altitude above Earth's surface in km
    beam_center_lat_deg : float
        Beam center latitude in degrees
    beam_center_lon_deg : float
        Beam center longitude in degrees
    beam_center_alt_km : float
        Beam center altitude above Earth's surface in km (typically 0)

    Returns
    -------
    float
        Off-axis angle in degrees (0 means user is at beam center)
    """
    # Convert all positions to ECEF
    sat_ecef = geodetic_to_ecef(sat_lat_deg, sat_lon_deg, sat_alt_km)
    user_ecef = geodetic_to_ecef(user_lat_deg, user_lon_deg, user_alt_km)
    beam_ecef = geodetic_to_ecef(beam_center_lat_deg, beam_center_lon_deg, beam_center_alt_km)

    # Compute vectors from satellite to user and from satellite to beam center
    vec_to_user = vector_subtract(user_ecef, sat_ecef)
    vec_to_beam = vector_subtract(beam_ecef, sat_ecef)

    # Compute magnitudes
    mag_to_user = vector_magnitude(vec_to_user)
    mag_to_beam = vector_magnitude(vec_to_beam)

    if mag_to_user < 1e-9 or mag_to_beam < 1e-9:
        # Degenerate case: satellite is at one of the points
        return 0.0

    # Compute angle using dot product
    cos_theta = vector_dot(vec_to_user, vec_to_beam) / (mag_to_user * mag_to_beam)

    # Clamp to [-1, 1] to handle numerical precision issues
    cos_theta = max(-1.0, min(1.0, cos_theta))

    theta_rad = math.acos(cos_theta)
    return math.degrees(theta_rad)


def compute_spherical_angles(
    sat_lat_deg: float,
    sat_lon_deg: float,
    sat_alt_km: float,
    target_lat_deg: float,
    target_lon_deg: float,
    target_alt_km: float,
) -> Dict[str, float]:
    """
    Compute lambda (central angle), eta (nadir angle), phi (azimuthal angle),
    and the corresponding unit vector (x, y, z) from satellite to target.

    Parameters
    ----------
    sat_lat_deg : float
        Satellite subsatellite point latitude in degrees
    sat_lon_deg : float
        Satellite subsatellite point longitude in degrees
    sat_alt_km : float
        Satellite altitude above Earth's surface in km
    target_lat_deg : float
        Target latitude in degrees
    target_lon_deg : float
        Target longitude in degrees
    target_alt_km : float
        Target altitude above Earth's surface in km

    Returns
    -------
    Dict[str, float]
        Dictionary with keys: lambda_deg, eta_deg, phi_deg, x, y, z
    """
    # Central angle (lambda) between subsatellite point and target
    lambda_deg = compute_central_angle_deg(
        sat_lat_deg, sat_lon_deg,
        target_lat_deg, target_lon_deg
    )

    # Nadir angle (eta) at the satellite
    eta_deg = compute_nadir_angle_deg(lambda_deg, sat_alt_km)

    # Terminal phi angle
    phi_deg = compute_terminal_phi_deg(
        target_lat_deg,  # ground station lat
        sat_lat_deg,     # subsatellite lat
        lambda_deg
    )

    # Convert to unit vector
    eta_rad = math.radians(eta_deg)
    phi_rad = math.radians(phi_deg)

    x = math.sin(eta_rad) * math.sin(phi_rad)
    y = math.sin(eta_rad) * math.cos(phi_rad)
    z = math.cos(eta_rad)

    return {
        "lambda_deg": lambda_deg,
        "eta_deg": eta_deg,
        "phi_deg": phi_deg,
        "x": x,
        "y": y,
        "z": z,
    }


def compute_beam_off_axis_full(
    sat_lat_deg: float,
    sat_lon_deg: float,
    sat_alt_km: float,
    user_lat_deg: float,
    user_lon_deg: float,
    user_alt_km: float,
    beam_center_lat_deg: float,
    beam_center_lon_deg: float,
    beam_center_alt_km: float,
) -> Dict[str, float]:
    """
    Compute beam off-axis angle and all spherical angle components
    for both satellite-to-user and satellite-to-beam directions.

    Parameters
    ----------
    sat_lat_deg : float
        Satellite subsatellite point latitude in degrees
    sat_lon_deg : float
        Satellite subsatellite point longitude in degrees
    sat_alt_km : float
        Satellite altitude above Earth's surface in km
    user_lat_deg : float
        User terminal latitude in degrees
    user_lon_deg : float
        User terminal longitude in degrees
    user_alt_km : float
        User terminal altitude in km
    beam_center_lat_deg : float
        Beam center latitude in degrees
    beam_center_lon_deg : float
        Beam center longitude in degrees
    beam_center_alt_km : float
        Beam center altitude in km

    Returns
    -------
    Dict[str, float]
        Dictionary with all computed values
    """
    # Compute off-axis angle using existing ECEF method
    off_axis_angle_deg = compute_beam_off_axis_angle_deg(
        sat_lat_deg, sat_lon_deg, sat_alt_km,
        user_lat_deg, user_lon_deg, user_alt_km,
        beam_center_lat_deg, beam_center_lon_deg, beam_center_alt_km
    )

    # Compute spherical angles for satellite to user
    user_angles = compute_spherical_angles(
        sat_lat_deg, sat_lon_deg, sat_alt_km,
        user_lat_deg, user_lon_deg, user_alt_km
    )

    # Compute spherical angles for satellite to beam center
    beam_angles = compute_spherical_angles(
        sat_lat_deg, sat_lon_deg, sat_alt_km,
        beam_center_lat_deg, beam_center_lon_deg, beam_center_alt_km
    )

    # Compute elevation angle from user terminal to satellite
    user_elevation_deg = compute_elevation_deg(
        ground_lat_deg=user_lat_deg,
        ground_lon_deg=user_lon_deg,
        subsatellite_lat_deg=sat_lat_deg,
        subsatellite_lon_deg=sat_lon_deg,
        satellite_altitude_km=sat_alt_km,
    )

    # Compute slant range from user terminal to satellite
    user_slant_range_km = compute_slant_range_km(
        central_angle_deg=user_angles["lambda_deg"],
        satellite_altitude_km=sat_alt_km,
    )

    return {
        "off_axis_angle_deg": off_axis_angle_deg,
        "sat_to_user_lambda_deg": user_angles["lambda_deg"],
        "sat_to_user_eta_deg": user_angles["eta_deg"],
        "sat_to_user_phi_deg": user_angles["phi_deg"],
        "sat_to_user_x": user_angles["x"],
        "sat_to_user_y": user_angles["y"],
        "sat_to_user_z": user_angles["z"],
        "sat_to_beam_lambda_deg": beam_angles["lambda_deg"],
        "sat_to_beam_eta_deg": beam_angles["eta_deg"],
        "sat_to_beam_phi_deg": beam_angles["phi_deg"],
        "sat_to_beam_x": beam_angles["x"],
        "sat_to_beam_y": beam_angles["y"],
        "sat_to_beam_z": beam_angles["z"],
        "user_elevation_deg": user_elevation_deg,
        "user_slant_range_km": user_slant_range_km,
    }
