import pytest
from app.services.azimuth import compute_azimuth_deg


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
