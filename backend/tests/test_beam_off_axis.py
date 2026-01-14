import pytest
import math
from app.services.beam_off_axis import (
    geodetic_to_ecef,
    vector_subtract,
    vector_dot,
    vector_magnitude,
    compute_beam_off_axis_angle_deg,
    EARTH_SEMI_MAJOR_AXIS_KM,
)


class TestGeodeticToEcef:
    """Tests for geodetic to ECEF coordinate conversion."""

    def test_equator_prime_meridian_sea_level(self):
        """Point at equator, prime meridian, sea level should be on +X axis."""
        x, y, z = geodetic_to_ecef(0.0, 0.0, 0.0)
        assert abs(x - EARTH_SEMI_MAJOR_AXIS_KM) < 0.01
        assert abs(y) < 1e-6
        assert abs(z) < 1e-6

    def test_equator_90_east_sea_level(self):
        """Point at equator, 90°E should be on +Y axis."""
        x, y, z = geodetic_to_ecef(0.0, 90.0, 0.0)
        assert abs(x) < 1e-6
        assert abs(y - EARTH_SEMI_MAJOR_AXIS_KM) < 0.01
        assert abs(z) < 1e-6

    def test_north_pole_sea_level(self):
        """Point at north pole should be on +Z axis."""
        x, y, z = geodetic_to_ecef(90.0, 0.0, 0.0)
        assert abs(x) < 1e-6
        assert abs(y) < 1e-6
        # Z should be approximately semi-minor axis (polar radius)
        assert z > 6350  # Greater than polar radius

    def test_altitude_increases_distance(self):
        """Adding altitude should increase distance from Earth center."""
        x1, y1, z1 = geodetic_to_ecef(0.0, 0.0, 0.0)
        x2, y2, z2 = geodetic_to_ecef(0.0, 0.0, 1000.0)  # 1000 km altitude
        
        dist1 = math.sqrt(x1**2 + y1**2 + z1**2)
        dist2 = math.sqrt(x2**2 + y2**2 + z2**2)
        
        assert dist2 - dist1 > 999  # Should be ~1000 km more


class TestVectorOperations:
    """Tests for vector helper functions."""

    def test_vector_subtract(self):
        """Test vector subtraction."""
        result = vector_subtract((5.0, 3.0, 1.0), (2.0, 1.0, 1.0))
        assert result == (3.0, 2.0, 0.0)

    def test_vector_dot(self):
        """Test dot product."""
        result = vector_dot((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
        assert abs(result - 32.0) < 1e-6  # 1*4 + 2*5 + 3*6 = 32

    def test_vector_magnitude(self):
        """Test vector magnitude."""
        result = vector_magnitude((3.0, 4.0, 0.0))
        assert abs(result - 5.0) < 1e-6

    def test_vector_dot_orthogonal(self):
        """Dot product of orthogonal vectors should be 0."""
        result = vector_dot((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        assert abs(result) < 1e-6


class TestBeamOffAxisAngle:
    """Tests for beam off-axis angle calculation."""

    def test_user_at_beam_center(self):
        """
        When user is at the beam center, off-axis angle should be 0.
        """
        angle = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=45.0,
            user_lon_deg=0.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        assert abs(angle) < 1e-6

    def test_symmetric_offset(self):
        """
        User offset east and west from beam center by same amount
        should give same off-axis angle.
        """
        angle_east = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=45.0,
            user_lon_deg=10.0,  # 10° east of beam center
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        angle_west = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=45.0,
            user_lon_deg=-10.0,  # 10° west of beam center
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        assert abs(angle_east - angle_west) < 0.01

    def test_larger_offset_larger_angle(self):
        """
        User further from beam center should have larger off-axis angle.
        """
        angle_small = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=46.0,  # 1° offset
            user_lon_deg=0.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        angle_large = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=50.0,  # 5° offset
            user_lon_deg=0.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        assert angle_large > angle_small

    def test_geo_typical_beam(self):
        """
        Test a typical GEO beam scenario.
        GEO at 0° lon, beam center at 45°N/0°E, user at 40°N/5°W.
        The off-axis angle should be a few degrees.
        """
        angle = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=40.0,
            user_lon_deg=-5.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        # Should be a small angle, few degrees
        assert 0.5 < angle < 3.0

    def test_leo_satellite(self):
        """
        Test with LEO satellite at lower altitude.
        Off-axis angles should be larger for LEO due to proximity.
        """
        angle_leo = compute_beam_off_axis_angle_deg(
            sat_lat_deg=45.0,
            sat_lon_deg=0.0,
            sat_alt_km=550.0,  # Starlink-like altitude
            user_lat_deg=46.0,
            user_lon_deg=0.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        angle_geo = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=46.0,
            user_lon_deg=0.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        # LEO should have larger off-axis angle for same ground separation
        assert angle_leo > angle_geo

    def test_user_altitude_effect(self):
        """
        User at higher altitude (e.g., on mountain or aircraft)
        should have slightly different off-axis angle.
        """
        angle_sea_level = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=40.0,
            user_lon_deg=5.0,
            user_alt_km=0.0,
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        angle_aircraft = compute_beam_off_axis_angle_deg(
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
            user_lat_deg=40.0,
            user_lon_deg=5.0,
            user_alt_km=10.0,  # 10 km altitude (aircraft)
            beam_center_lat_deg=45.0,
            beam_center_lon_deg=0.0,
            beam_center_alt_km=0.0,
        )
        
        # Angles should be close but not identical
        assert abs(angle_sea_level - angle_aircraft) < 0.5
        assert angle_sea_level != angle_aircraft

    def test_off_axis_angle_always_positive(self):
        """
        Off-axis angle should always be non-negative.
        """
        # Various test cases
        test_cases = [
            (0, 0, 35786, 45, 10, 0, 45, 0, 0),
            (0, 0, 35786, 30, -20, 0, 45, 10, 0),
            (45, 90, 550, 40, 85, 0, 50, 95, 0),
        ]
        
        for sat_lat, sat_lon, sat_alt, user_lat, user_lon, user_alt, beam_lat, beam_lon, beam_alt in test_cases:
            angle = compute_beam_off_axis_angle_deg(
                sat_lat_deg=sat_lat,
                sat_lon_deg=sat_lon,
                sat_alt_km=sat_alt,
                user_lat_deg=user_lat,
                user_lon_deg=user_lon,
                user_alt_km=user_alt,
                beam_center_lat_deg=beam_lat,
                beam_center_lon_deg=beam_lon,
                beam_center_alt_km=beam_alt,
            )
            assert angle >= 0
