import math
import pytest

from app.services.weather_loss import (
    compute_weather_loss_db,
    compute_specific_attenuation_db_per_km,
    compute_rain_height_km,
    get_rain_rate_mm_hr,
    _interpolate_p838_coefficients,
    GEO_ALTITUDE_KM,
)


class TestInterpolateP838Coefficients:
    """Tests for ITU-R P.838 coefficient interpolation."""

    def test_frequency_at_table_point(self):
        """Coefficients at exact table frequencies should match."""
        # 12 GHz is in the table: k_h=0.0188, alpha_h=1.217
        k, alpha = _interpolate_p838_coefficients(12.0)
        assert k == pytest.approx(0.0188, rel=1e-3)
        assert alpha == pytest.approx(1.217, rel=1e-3)

    def test_frequency_interpolation(self):
        """Interpolation between table points."""
        # 14 GHz is between 12 and 15
        k, alpha = _interpolate_p838_coefficients(14.0)
        # k should be between 0.0188 (12 GHz) and 0.0367 (15 GHz)
        assert 0.0188 < k < 0.0367
        # alpha should be between 1.217 (12 GHz) and 1.154 (15 GHz)
        assert 1.154 < alpha < 1.217

    def test_frequency_below_minimum_raises(self):
        """Frequency below 1 GHz should raise ValueError."""
        with pytest.raises(ValueError, match="at least 1 GHz"):
            _interpolate_p838_coefficients(0.5)

    def test_frequency_above_maximum_raises(self):
        """Frequency above 100 GHz should raise ValueError."""
        with pytest.raises(ValueError, match="not exceed 100 GHz"):
            _interpolate_p838_coefficients(150.0)

    def test_ka_band_coefficients(self):
        """Check Ka-band (20-30 GHz) gives reasonable values."""
        k, alpha = _interpolate_p838_coefficients(30.0)
        assert k > 0
        assert 0.5 < alpha < 1.5


class TestGetRainRateMmHr:
    """Tests for rain rate lookup."""

    def test_exact_availability_level(self):
        """Exact availability levels should return table values."""
        rain_rate = get_rain_rate_mm_hr(99.9)
        assert rain_rate == pytest.approx(50.0, rel=1e-3)

    def test_interpolated_availability(self):
        """Interpolated availability should be between table values."""
        rain_rate = get_rain_rate_mm_hr(99.7)
        # Should be between 99.5 (32 mm/hr) and 99.9 (50 mm/hr)
        assert 32.0 < rain_rate < 50.0

    def test_availability_below_minimum_raises(self):
        """Availability below 97% should raise ValueError."""
        with pytest.raises(ValueError, match="at least 97%"):
            get_rain_rate_mm_hr(96.0)

    def test_availability_above_maximum_raises(self):
        """Availability above 99.999% should raise ValueError."""
        with pytest.raises(ValueError, match="not exceed 99.999%"):
            get_rain_rate_mm_hr(99.9999)

    def test_higher_availability_higher_rain_rate(self):
        """Higher availability should require higher rain rate threshold."""
        r_low = get_rain_rate_mm_hr(99.0)
        r_high = get_rain_rate_mm_hr(99.99)
        assert r_high > r_low


class TestComputeRainHeightKm:
    """Tests for rain height calculation."""

    def test_tropical_latitude(self):
        """Tropical latitudes should have ~5 km rain height."""
        height = compute_rain_height_km(10.0)
        assert height == pytest.approx(5.0, abs=0.1)

    def test_temperate_latitude(self):
        """Temperate latitudes should have lower rain height."""
        height = compute_rain_height_km(45.0)
        assert height < 5.0
        assert height > 2.0

    def test_symmetric_hemispheres(self):
        """Rain height should be symmetric for north/south."""
        height_n = compute_rain_height_km(40.0)
        height_s = compute_rain_height_km(-40.0)
        assert height_n == pytest.approx(height_s, rel=1e-6)


class TestComputeSpecificAttenuation:
    """Tests for specific attenuation calculation."""

    def test_zero_rain_rate_zero_attenuation(self):
        """Zero rain rate should give zero attenuation."""
        gamma = compute_specific_attenuation_db_per_km(20.0, 0.0)
        assert gamma == 0.0

    def test_higher_frequency_higher_attenuation(self):
        """Higher frequency should generally give higher attenuation."""
        gamma_20 = compute_specific_attenuation_db_per_km(20.0, 50.0)
        gamma_40 = compute_specific_attenuation_db_per_km(40.0, 50.0)
        assert gamma_40 > gamma_20

    def test_higher_rain_rate_higher_attenuation(self):
        """Higher rain rate should give higher attenuation."""
        gamma_low = compute_specific_attenuation_db_per_km(30.0, 20.0)
        gamma_high = compute_specific_attenuation_db_per_km(30.0, 80.0)
        assert gamma_high > gamma_low

    def test_ka_band_reasonable_value(self):
        """Ka-band at moderate rain rate should give typical values."""
        # At 30 GHz with 25 mm/hr rain, expect ~2-5 dB/km
        gamma = compute_specific_attenuation_db_per_km(30.0, 25.0)
        assert 1.0 < gamma < 10.0


class TestComputeWeatherLossDb:
    """Tests for the main weather loss calculation."""

    def test_user_directly_below_satellite(self):
        """User at subsatellite point should have high elevation, lower loss."""
        elev, rain_rate, loss = compute_weather_loss_db(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=0.0,
            availability_percent=99.9,
            frequency_ghz=20.0,
        )
        assert elev == pytest.approx(90.0, abs=0.1)
        assert loss > 0

    def test_user_at_edge_of_coverage(self):
        """User at edge of coverage should have lower elevation angle."""
        # User at 60°N, satellite at 0° longitude
        elev_edge, _, loss_edge = compute_weather_loss_db(
            satellite_longitude_deg=0.0,
            user_latitude_deg=60.0,
            user_longitude_deg=0.0,
            availability_percent=99.9,
            frequency_ghz=20.0,
        )
        
        elev_center, _, loss_center = compute_weather_loss_db(
            satellite_longitude_deg=0.0,
            user_latitude_deg=0.0,
            user_longitude_deg=0.0,
            availability_percent=99.9,
            frequency_ghz=20.0,
        )
        
        # Edge should have lower elevation
        assert elev_edge < elev_center
        # Both should have positive loss
        assert loss_edge > 0
        assert loss_center > 0

    def test_higher_availability_higher_loss(self):
        """Higher availability requirement should result in higher loss."""
        _, _, loss_low = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=40.0,
            user_longitude_deg=-100.0,
            availability_percent=99.0,
            frequency_ghz=30.0,
        )
        
        _, _, loss_high = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=40.0,
            user_longitude_deg=-100.0,
            availability_percent=99.99,
            frequency_ghz=30.0,
        )
        
        assert loss_high > loss_low

    def test_higher_frequency_higher_loss(self):
        """Higher frequency should result in higher loss."""
        _, _, loss_ku = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=40.0,
            user_longitude_deg=-100.0,
            availability_percent=99.9,
            frequency_ghz=12.0,
        )
        
        _, _, loss_ka = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=40.0,
            user_longitude_deg=-100.0,
            availability_percent=99.9,
            frequency_ghz=30.0,
        )
        
        assert loss_ka > loss_ku

    def test_satellite_not_visible_raises(self):
        """User location where satellite is not visible should raise."""
        with pytest.raises(ValueError, match="not visible"):
            compute_weather_loss_db(
                satellite_longitude_deg=0.0,
                user_latitude_deg=0.0,
                user_longitude_deg=180.0,  # Opposite side of Earth
                availability_percent=99.9,
                frequency_ghz=20.0,
            )

    def test_invalid_latitude_raises(self):
        """Invalid latitude should raise ValueError."""
        with pytest.raises(ValueError, match="latitude"):
            compute_weather_loss_db(
                satellite_longitude_deg=0.0,
                user_latitude_deg=95.0,
                user_longitude_deg=0.0,
                availability_percent=99.9,
                frequency_ghz=20.0,
            )

    def test_invalid_longitude_raises(self):
        """Invalid longitude should raise ValueError."""
        with pytest.raises(ValueError, match="longitude"):
            compute_weather_loss_db(
                satellite_longitude_deg=0.0,
                user_latitude_deg=0.0,
                user_longitude_deg=200.0,
                availability_percent=99.9,
                frequency_ghz=20.0,
            )

    def test_returns_correct_types(self):
        """Return values should be correct types."""
        elev, rain_rate, loss = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=40.0,
            user_longitude_deg=-100.0,
            availability_percent=99.9,
            frequency_ghz=20.0,
        )
        assert isinstance(elev, float)
        assert isinstance(rain_rate, float)
        assert isinstance(loss, float)
        assert elev > 0
        assert rain_rate > 0
        assert loss > 0

    def test_typical_ka_band_scenario(self):
        """Typical Ka-band scenario should give reasonable loss values."""
        # Denver, CO looking at a satellite at -100° W
        elev, rain_rate, loss = compute_weather_loss_db(
            satellite_longitude_deg=-100.0,
            user_latitude_deg=39.7,
            user_longitude_deg=-104.9,
            availability_percent=99.5,
            frequency_ghz=30.0,
        )
        
        # Elevation should be reasonable (30-50 degrees for mid-lat)
        assert 20 < elev < 60
        
        # Rain rate at 99.5% should be around 32 mm/hr
        assert rain_rate == pytest.approx(32.0, rel=0.1)
        
        # Total loss should be in a reasonable range (few dB to ~20 dB)
        assert 1.0 < loss < 30.0
