import math
import pytest

from app.services.scan_loss import (
    compute_nadir_angle_deg,
    compute_scan_loss_db,
    EARTH_RADIUS_KM,
    GEO_ORBITAL_RADIUS_KM,
)


class TestComputeNadirAngle:
    """Tests for compute_nadir_angle_deg function."""

    def test_user_at_subsatellite_point(self):
        """User directly below satellite should have 0° nadir angle."""
        angle = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=0.0,
        )
        assert angle == pytest.approx(0.0, abs=1e-6)

    def test_user_at_equator_offset_longitude(self):
        """User at equator with longitude offset from satellite."""
        # User at 10° longitude offset on equator
        angle = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=10.0,
        )
        # Expected: arcsin((R_E/r_sat) * sin(10°))
        expected = math.degrees(
            math.asin((EARTH_RADIUS_KM / GEO_ORBITAL_RADIUS_KM) * math.sin(math.radians(10.0)))
        )
        assert angle == pytest.approx(expected, rel=1e-6)

    def test_user_at_latitude_offset(self):
        """User at latitude offset from sub-satellite point."""
        # User at 30° latitude, same longitude as satellite
        angle = compute_nadir_angle_deg(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=30.0,
            user_longitude_deg=-100.0,
        )
        # cos(gamma) = cos(30°) * cos(0°) = cos(30°)
        gamma = math.radians(30.0)
        expected = math.degrees(
            math.asin((EARTH_RADIUS_KM / GEO_ORBITAL_RADIUS_KM) * math.sin(gamma))
        )
        assert angle == pytest.approx(expected, rel=1e-6)

    def test_user_not_visible_raises_error(self):
        """User beyond Earth's limb should raise ValueError."""
        # User at extreme position - opposite side of Earth
        with pytest.raises(ValueError, match="not visible"):
            compute_nadir_angle_deg(
                satellite_longitude_deg=0.0,
                user_latitude_deg=0.0,
                user_longitude_deg=180.0,
            )

    def test_symmetric_east_west(self):
        """Nadir angle should be symmetric for east/west offsets."""
        angle_east = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=15.0,
        )
        angle_west = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=-15.0,
        )
        assert angle_east == pytest.approx(angle_west, rel=1e-6)

    def test_symmetric_north_south(self):
        """Nadir angle should be symmetric for north/south latitudes."""
        angle_north = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=20.0,
            user_longitude_deg=0.0,
        )
        angle_south = compute_nadir_angle_deg(
            satellite_longitude_deg=0.0,
            user_latitude_deg=-20.0,
            user_longitude_deg=0.0,
        )
        assert angle_north == pytest.approx(angle_south, rel=1e-6)


class TestComputeScanLoss:
    """Tests for compute_scan_loss_db function."""

    def test_zero_scan_angle_zero_loss(self):
        """Zero scan angle should result in zero loss."""
        loss = compute_scan_loss_db(scan_angle_deg=0.0, scan_exponent=1.3)
        assert loss == pytest.approx(0.0, abs=1e-10)

    def test_positive_scan_angle_positive_loss(self):
        """Positive scan angle should result in positive loss."""
        loss = compute_scan_loss_db(scan_angle_deg=30.0, scan_exponent=1.3)
        assert loss > 0

    def test_scan_loss_formula(self):
        """Verify scan loss matches expected formula."""
        scan_angle = 45.0
        exponent = 1.5
        loss = compute_scan_loss_db(scan_angle_deg=scan_angle, scan_exponent=exponent)
        expected = -10.0 * exponent * math.log10(math.cos(math.radians(scan_angle)))
        assert loss == pytest.approx(expected, rel=1e-6)

    def test_larger_angle_more_loss(self):
        """Larger scan angle should result in more loss."""
        loss_small = compute_scan_loss_db(scan_angle_deg=10.0, scan_exponent=1.3)
        loss_large = compute_scan_loss_db(scan_angle_deg=60.0, scan_exponent=1.3)
        assert loss_large > loss_small

    def test_larger_exponent_more_loss(self):
        """Larger exponent should result in more loss for same angle."""
        loss_small_n = compute_scan_loss_db(scan_angle_deg=30.0, scan_exponent=1.0)
        loss_large_n = compute_scan_loss_db(scan_angle_deg=30.0, scan_exponent=1.5)
        assert loss_large_n > loss_small_n

    def test_invalid_exponent_raises_error(self):
        """Non-positive exponent should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            compute_scan_loss_db(scan_angle_deg=30.0, scan_exponent=0.0)
        with pytest.raises(ValueError, match="positive"):
            compute_scan_loss_db(scan_angle_deg=30.0, scan_exponent=-1.0)

    def test_invalid_scan_angle_raises_error(self):
        """Scan angle >= 90° should raise ValueError."""
        with pytest.raises(ValueError, match="less than 90"):
            compute_scan_loss_db(scan_angle_deg=90.0, scan_exponent=1.3)
        with pytest.raises(ValueError, match="less than 90"):
            compute_scan_loss_db(scan_angle_deg=95.0, scan_exponent=1.3)
