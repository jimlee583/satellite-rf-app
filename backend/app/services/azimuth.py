import math


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
