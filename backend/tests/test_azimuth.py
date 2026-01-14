import pytest
from app.services.azimuth import compute_azimuth_deg, compute_elevation_deg, compute_central_angle_deg


def test_azimuth_due_north():
    """
    From equator going due north along the same longitude.
    Expected azimuth: 0 degrees (north).
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=0.0,
        start_lon_deg=0.0,
        end_lat_deg=45.0,
        end_lon_deg=0.0,
    )
    assert abs(azimuth - 0.0) < 1e-6


def test_azimuth_due_east():
    """
    From equator going due east along the equator.
    Expected azimuth: 90 degrees (east).
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=0.0,
        start_lon_deg=0.0,
        end_lat_deg=0.0,
        end_lon_deg=90.0,
    )
    assert abs(azimuth - 90.0) < 1e-6


def test_azimuth_due_south():
    """
    From a point going due south along the same longitude.
    Expected azimuth: 180 degrees (south).
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=45.0,
        start_lon_deg=0.0,
        end_lat_deg=0.0,
        end_lon_deg=0.0,
    )
    assert abs(azimuth - 180.0) < 1e-6


def test_azimuth_due_west():
    """
    From equator going due west along the equator.
    Expected azimuth: 270 degrees (west).
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=0.0,
        start_lon_deg=0.0,
        end_lat_deg=0.0,
        end_lon_deg=-90.0,
    )
    assert abs(azimuth - 270.0) < 1e-6


def test_azimuth_new_york_to_london():
    """
    Approximate azimuth from New York (40.7128, -74.006) to London (51.5074, -0.1278).
    Expected azimuth: approximately 51.2 degrees (northeast).
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=40.7128,
        start_lon_deg=-74.006,
        end_lat_deg=51.5074,
        end_lon_deg=-0.1278,
    )
    # Tolerance of 0.5 degree for this real-world approximation
    assert abs(azimuth - 51.2) < 0.5


def test_azimuth_same_point():
    """
    Azimuth from a point to itself is undefined, but atan2 returns 0.
    """
    azimuth = compute_azimuth_deg(
        start_lat_deg=45.0,
        start_lon_deg=90.0,
        end_lat_deg=45.0,
        end_lon_deg=90.0,
    )
    # Result is 0 when both points are the same
    assert abs(azimuth - 0.0) < 1e-6


# ============================================================
# Elevation angle tests
# ============================================================


def test_central_angle_same_point():
    """
    Central angle between a point and itself should be 0.
    """
    gamma = compute_central_angle_deg(0.0, 0.0, 0.0, 0.0)
    assert abs(gamma) < 1e-6


def test_central_angle_antipodal():
    """
    Central angle between antipodal points should be 180 degrees.
    """
    gamma = compute_central_angle_deg(0.0, 0.0, 0.0, 180.0)
    assert abs(gamma - 180.0) < 1e-6


def test_central_angle_quarter_sphere():
    """
    Central angle from equator/0 lon to north pole should be 90 degrees.
    """
    gamma = compute_central_angle_deg(0.0, 0.0, 90.0, 0.0)
    assert abs(gamma - 90.0) < 1e-6


def test_elevation_directly_overhead():
    """
    When the satellite is directly overhead (same lat/lon as ground station),
    elevation should be 90 degrees.
    """
    elevation = compute_elevation_deg(
        ground_lat_deg=0.0,
        ground_lon_deg=0.0,
        subsatellite_lat_deg=0.0,
        subsatellite_lon_deg=0.0,
        satellite_altitude_km=35786.0,
    )
    assert abs(elevation - 90.0) < 1e-6


def test_elevation_geo_at_equator():
    """
    GEO satellite at 0 lon, viewed from ground station at equator, 60 degrees west.
    Central angle = 60 degrees. Expected elevation ~25 degrees.
    """
    elevation = compute_elevation_deg(
        ground_lat_deg=0.0,
        ground_lon_deg=-60.0,
        subsatellite_lat_deg=0.0,
        subsatellite_lon_deg=0.0,
        satellite_altitude_km=35786.0,
    )
    # Approximate expected value for 60 degree separation at GEO
    assert 20.0 < elevation < 30.0


def test_elevation_geo_new_york():
    """
    GEO satellite at -74.006 lon (same longitude as NYC), viewed from NYC.
    Ground station at 40.7128 lat means satellite is south.
    """
    elevation = compute_elevation_deg(
        ground_lat_deg=40.7128,
        ground_lon_deg=-74.006,
        subsatellite_lat_deg=0.0,
        subsatellite_lon_deg=-74.006,
        satellite_altitude_km=35786.0,
    )
    # NYC at ~40.7 lat should see equatorial GEO at elevation ~45-50 degrees
    assert 40.0 < elevation < 55.0


def test_elevation_below_horizon():
    """
    A satellite on the opposite side of Earth should have negative elevation.
    """
    elevation = compute_elevation_deg(
        ground_lat_deg=45.0,
        ground_lon_deg=0.0,
        subsatellite_lat_deg=-45.0,
        subsatellite_lon_deg=180.0,
        satellite_altitude_km=35786.0,
    )
    # Far side of Earth - should be below horizon
    assert elevation < 0


def test_elevation_leo_satellite():
    """
    LEO satellite at 400 km altitude directly overhead.
    """
    elevation = compute_elevation_deg(
        ground_lat_deg=40.0,
        ground_lon_deg=-75.0,
        subsatellite_lat_deg=40.0,
        subsatellite_lon_deg=-75.0,
        satellite_altitude_km=400.0,
    )
    # Slightly relaxed tolerance due to floating-point precision
    assert abs(elevation - 90.0) < 1e-4


def test_elevation_invalid_altitude():
    """
    Negative or zero altitude should raise ValueError.
    """
    with pytest.raises(ValueError):
        compute_elevation_deg(
            ground_lat_deg=0.0,
            ground_lon_deg=0.0,
            subsatellite_lat_deg=0.0,
            subsatellite_lon_deg=0.0,
            satellite_altitude_km=0.0,
        )

    with pytest.raises(ValueError):
        compute_elevation_deg(
            ground_lat_deg=0.0,
            ground_lon_deg=0.0,
            subsatellite_lat_deg=0.0,
            subsatellite_lon_deg=0.0,
            satellite_altitude_km=-100.0,
        )
