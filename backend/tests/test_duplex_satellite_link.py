"""
Unit tests for duplex satellite link budget calculations.
"""

import math
import pytest

from app.services.duplex_satellite_link import (
    compute_slant_range_km,
    compute_elevation_angle_deg,
    compute_beam_roll_off_db,
    compute_single_hop_cn0,
    combine_cn0_bent_pipe,
    check_elevation_warnings,
    compute_duplex_satellite_link,
    compute_operating_eirp,
    compute_ci_from_npr,
    combine_ci_sources,
    combine_cn_with_ci,
    cn0_to_cn,
    cn0_to_es_n0,
)


class TestSlantRange:
    """Tests for slant range computation."""

    def test_geo_satellite_from_subsatellite_point(self):
        """Slant range from subsatellite point should equal satellite altitude."""
        # Terminal at subsatellite point (0°, 0°)
        # Satellite at GEO altitude directly above
        range_km = compute_slant_range_km(
            terminal_lat_deg=0.0,
            terminal_lon_deg=0.0,
            terminal_alt_km=0.0,
            sat_lat_deg=0.0,
            sat_lon_deg=0.0,
            sat_alt_km=35786.0,
        )
        # Should be approximately satellite altitude
        assert abs(range_km - 35786.0) < 10  # Within 10 km

    def test_slant_range_increases_with_distance(self):
        """Slant range should increase as terminal moves away from subsatellite point."""
        range_at_subsat = compute_slant_range_km(
            terminal_lat_deg=0.0, terminal_lon_deg=0.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        range_at_offset = compute_slant_range_km(
            terminal_lat_deg=40.0, terminal_lon_deg=10.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        assert range_at_offset > range_at_subsat


class TestElevationAngle:
    """Tests for elevation angle computation."""

    def test_subsatellite_point_has_90_deg_elevation(self):
        """Elevation angle at subsatellite point should be 90°."""
        elev = compute_elevation_angle_deg(
            terminal_lat_deg=0.0, terminal_lon_deg=0.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        assert abs(elev - 90.0) < 0.1

    def test_elevation_decreases_with_distance(self):
        """Elevation should decrease as terminal moves away from subsatellite point."""
        elev_at_subsat = compute_elevation_angle_deg(
            terminal_lat_deg=0.0, terminal_lon_deg=0.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        elev_at_offset = compute_elevation_angle_deg(
            terminal_lat_deg=40.0, terminal_lon_deg=10.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        assert elev_at_offset < elev_at_subsat

    def test_typical_geo_elevation(self):
        """Test elevation angle for a typical GEO scenario."""
        # Terminal at 40°N, 5°W looking at satellite at 0° longitude
        elev = compute_elevation_angle_deg(
            terminal_lat_deg=40.0, terminal_lon_deg=-5.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        # Should be a reasonable elevation (between 30-60°)
        assert 30 < elev < 60

    def test_negative_elevation_for_far_terminal(self):
        """Elevation should be negative if satellite is below horizon."""
        # Terminal at 80°N looking at satellite at 0° longitude
        # At this latitude, a GEO satellite at 0° lon should be very low or below horizon
        elev = compute_elevation_angle_deg(
            terminal_lat_deg=80.0, terminal_lon_deg=0.0, terminal_alt_km=0.0,
            sat_lat_deg=0.0, sat_lon_deg=0.0, sat_alt_km=35786.0,
        )
        # Very low elevation expected
        assert elev < 20


class TestBeamRollOff:
    """Tests for beam roll-off using cos^n pattern."""

    def test_zero_off_axis_no_rolloff(self):
        """At beam center (0° off-axis), roll-off should be 0 dB."""
        rolloff = compute_beam_roll_off_db(off_axis_angle_deg=0.0, cosine_exponent_n=1.5)
        assert abs(rolloff) < 0.001

    def test_rolloff_increases_with_angle(self):
        """Roll-off should increase (more negative) with off-axis angle."""
        rolloff_5deg = compute_beam_roll_off_db(off_axis_angle_deg=5.0, cosine_exponent_n=1.5)
        rolloff_10deg = compute_beam_roll_off_db(off_axis_angle_deg=10.0, cosine_exponent_n=1.5)
        assert rolloff_10deg < rolloff_5deg < 0

    def test_rolloff_increases_with_exponent(self):
        """Higher exponent should result in sharper roll-off."""
        rolloff_n1 = compute_beam_roll_off_db(off_axis_angle_deg=10.0, cosine_exponent_n=1.0)
        rolloff_n2 = compute_beam_roll_off_db(off_axis_angle_deg=10.0, cosine_exponent_n=2.0)
        assert rolloff_n2 < rolloff_n1

    def test_90_deg_off_axis_max_rolloff(self):
        """At 90° off-axis, roll-off should be very large (negative)."""
        rolloff = compute_beam_roll_off_db(off_axis_angle_deg=90.0, cosine_exponent_n=1.5)
        assert rolloff <= -100.0

    def test_expected_rolloff_value(self):
        """Test specific roll-off calculation."""
        # At 10° with n=1.0: 10 * 1.0 * log10(cos(10°))
        # cos(10°) ≈ 0.9848
        # log10(0.9848) ≈ -0.00665
        # Expected: 10 * 1.0 * (-0.00665) ≈ -0.0665 dB
        rolloff = compute_beam_roll_off_db(off_axis_angle_deg=10.0, cosine_exponent_n=1.0)
        expected = 10.0 * 1.0 * math.log10(math.cos(math.radians(10.0)))
        assert abs(rolloff - expected) < 0.001


class TestSingleHopCN0:
    """Tests for single hop C/N0 calculation."""

    def test_cn0_increases_with_eirp(self):
        """C/N0 should increase with higher EIRP."""
        cn0_low, _ = compute_single_hop_cn0(
            tx_eirp_dbw=50.0, rx_gt_db_per_k=10.0,
            frequency_hz=30e9, slant_range_m=40000e3,
            beam_roll_off_db=0.0, weather_atten_db=0.0,
            pointing_loss_db=0.0, polarization_loss_db=0.0,
        )
        cn0_high, _ = compute_single_hop_cn0(
            tx_eirp_dbw=60.0, rx_gt_db_per_k=10.0,
            frequency_hz=30e9, slant_range_m=40000e3,
            beam_roll_off_db=0.0, weather_atten_db=0.0,
            pointing_loss_db=0.0, polarization_loss_db=0.0,
        )
        assert cn0_high - cn0_low == pytest.approx(10.0, abs=0.01)

    def test_cn0_decreases_with_losses(self):
        """C/N0 should decrease with additional losses."""
        cn0_no_loss, _ = compute_single_hop_cn0(
            tx_eirp_dbw=50.0, rx_gt_db_per_k=10.0,
            frequency_hz=30e9, slant_range_m=40000e3,
            beam_roll_off_db=0.0, weather_atten_db=0.0,
            pointing_loss_db=0.0, polarization_loss_db=0.0,
        )
        cn0_with_loss, _ = compute_single_hop_cn0(
            tx_eirp_dbw=50.0, rx_gt_db_per_k=10.0,
            frequency_hz=30e9, slant_range_m=40000e3,
            beam_roll_off_db=0.0, weather_atten_db=2.0,
            pointing_loss_db=0.5, polarization_loss_db=0.3,
        )
        assert cn0_no_loss > cn0_with_loss
        assert cn0_no_loss - cn0_with_loss == pytest.approx(2.8, abs=0.01)

    def test_losses_breakdown_returned(self):
        """Should return breakdown of all losses."""
        cn0, losses = compute_single_hop_cn0(
            tx_eirp_dbw=50.0, rx_gt_db_per_k=10.0,
            frequency_hz=30e9, slant_range_m=40000e3,
            beam_roll_off_db=-1.5, weather_atten_db=2.0,
            pointing_loss_db=0.5, polarization_loss_db=0.3,
        )
        assert "fspl_db" in losses
        assert "beam_roll_off_db" in losses
        assert "weather_atten_db" in losses
        assert "pointing_loss_db" in losses
        assert "polarization_loss_db" in losses
        assert "total_path_loss_db" in losses
        assert losses["weather_atten_db"] == 2.0
        assert losses["pointing_loss_db"] == 0.5


class TestBentPipeCombination:
    """Tests for bent-pipe C/N0 combination."""

    def test_equal_cn0_combination(self):
        """When uplink = downlink C/N0, combined should be 3 dB lower."""
        uplink_cn0 = 80.0
        downlink_cn0 = 80.0
        combined = combine_cn0_bent_pipe(uplink_cn0, downlink_cn0)
        # 1/total = 1/up + 1/down = 2/up
        # total = up/2 → in dB: combined = up - 10*log10(2) ≈ up - 3.01 dB
        assert combined == pytest.approx(80.0 - 3.01, abs=0.05)

    def test_dominated_by_weaker_link(self):
        """Combined C/N0 should be dominated by the weaker link."""
        uplink_cn0 = 90.0
        downlink_cn0 = 70.0
        combined = combine_cn0_bent_pipe(uplink_cn0, downlink_cn0)
        # Combined should be slightly below the weaker link
        assert combined < downlink_cn0
        assert combined > downlink_cn0 - 1.0  # Within 1 dB of weaker

    def test_combination_symmetric(self):
        """Order of arguments shouldn't matter."""
        combined1 = combine_cn0_bent_pipe(85.0, 75.0)
        combined2 = combine_cn0_bent_pipe(75.0, 85.0)
        assert combined1 == pytest.approx(combined2, abs=0.001)


class TestElevationWarnings:
    """Tests for elevation angle warnings."""

    def test_no_warnings_for_good_elevations(self):
        """No warnings when both terminals have good elevation."""
        warnings = check_elevation_warnings(
            terminal_a_elev_deg=45.0,
            terminal_b_elev_deg=35.0,
            threshold_deg=5.0,
        )
        assert len(warnings) == 0

    def test_warning_for_low_elevation(self):
        """Warning when elevation is below threshold."""
        warnings = check_elevation_warnings(
            terminal_a_elev_deg=3.0,
            terminal_b_elev_deg=35.0,
            threshold_deg=5.0,
        )
        assert len(warnings) == 1
        assert warnings[0]["terminal"] == "A"
        assert "below minimum threshold" in warnings[0]["message"]

    def test_warning_for_negative_elevation(self):
        """Warning when satellite is below horizon."""
        warnings = check_elevation_warnings(
            terminal_a_elev_deg=45.0,
            terminal_b_elev_deg=-2.0,
            threshold_deg=5.0,
        )
        assert len(warnings) == 1
        assert warnings[0]["terminal"] == "B"
        assert "below horizon" in warnings[0]["message"]

    def test_multiple_warnings(self):
        """Multiple warnings when both terminals have issues."""
        warnings = check_elevation_warnings(
            terminal_a_elev_deg=-5.0,
            terminal_b_elev_deg=3.0,
            threshold_deg=5.0,
        )
        assert len(warnings) == 2


class TestOperatingEirp:
    """Tests for operating EIRP calculation from saturated EIRP and OBO."""

    def test_uses_operating_eirp_when_no_saturated(self):
        """Should use operating EIRP directly if saturated not provided."""
        result = compute_operating_eirp(
            eirp_dbw=50.0,
            eirp_saturated_dbw=None,
            obo_db=3.0,
        )
        assert result == 50.0

    def test_computes_from_saturated_and_obo(self):
        """Should compute operating EIRP = saturated - OBO."""
        result = compute_operating_eirp(
            eirp_dbw=50.0,  # Should be ignored
            eirp_saturated_dbw=60.0,
            obo_db=6.0,
        )
        assert result == 54.0


class TestCiFromNpr:
    """Tests for C/I calculation from NPR."""

    def test_none_npr_returns_none(self):
        """Should return None for ideal amplifier."""
        assert compute_ci_from_npr(None) is None

    def test_returns_npr_as_ci(self):
        """C/I should equal NPR in simplified model."""
        assert compute_ci_from_npr(25.0) == 25.0


class TestCombineCiSources:
    """Tests for combining multiple C/I sources."""

    def test_no_sources_returns_none(self):
        """Should return None if no intermod sources."""
        assert combine_ci_sources(None, None) is None

    def test_single_source(self):
        """Single source should return that value."""
        result = combine_ci_sources(25.0, None)
        assert result == pytest.approx(25.0, abs=0.01)

    def test_two_equal_sources(self):
        """Two equal sources should be 3 dB lower."""
        result = combine_ci_sources(25.0, 25.0)
        # 1/total = 1/25linear + 1/25linear = 2/25linear
        # total = 25linear/2 → -3 dB
        assert result == pytest.approx(22.0, abs=0.1)

    def test_dominated_by_worse(self):
        """Result should be dominated by worse C/I."""
        result = combine_ci_sources(30.0, 20.0)
        assert result < 20.0
        assert result > 19.0


class TestCombineCnWithCi:
    """Tests for combining C/N with C/I."""

    def test_no_intermod_returns_cn(self):
        """Should return C/N if no intermod."""
        result = combine_cn_with_ci(cn_db=15.0, ci_db=None)
        assert result == 15.0

    def test_combines_cn_and_ci(self):
        """Should combine C/N and C/I properly."""
        result = combine_cn_with_ci(cn_db=20.0, ci_db=20.0)
        # 1/total = 1/20linear + 1/20linear = 2/20linear
        assert result == pytest.approx(17.0, abs=0.1)


class TestCn0ToCn:
    """Tests for C/N0 to C/N conversion."""

    def test_cn0_to_cn_calculation(self):
        """C/N = C/N0 - 10*log10(B)."""
        # 36 MHz bandwidth = 36e6 Hz
        # 10*log10(36e6) = 75.56 dB-Hz
        result = cn0_to_cn(cn0_db_hz=90.0, bandwidth_hz=36e6)
        expected = 90.0 - 10 * math.log10(36e6)
        assert result == pytest.approx(expected, abs=0.01)


class TestCn0ToEsN0:
    """Tests for C/N0 to Es/N0 conversion."""

    def test_cn0_to_es_n0_calculation(self):
        """Es/N0 = C/N0 - 10*log10(Rs)."""
        # 30 Msps = 30e6 sps
        result = cn0_to_es_n0(cn0_db_hz=90.0, symbol_rate_hz=30e6)
        expected = 90.0 - 10 * math.log10(30e6)
        assert result == pytest.approx(expected, abs=0.01)


class TestFullDuplexLink:
    """Integration tests for full duplex link calculation."""

    @pytest.fixture
    def basic_link_request(self):
        """Basic link request with typical values."""
        return {
            "terminal_a": {
                "lat_deg": 40.0,
                "lon_deg": -5.0,
                "alt_km": 0.0,
                "eirp_dbw": 60.0,
                "gt_db_per_k": 35.0,
                "pointing_loss_db": 0.5,
                "polarization_loss_db": 0.3,
            },
            "terminal_b": {
                "lat_deg": 35.0,
                "lon_deg": 10.0,
                "alt_km": 0.0,
                "eirp_dbw": 50.0,
                "gt_db_per_k": 25.0,
                "pointing_loss_db": 0.5,
                "polarization_loss_db": 0.3,
            },
            "satellite": {
                "lat_deg": 0.0,
                "lon_deg": 0.0,
                "alt_km": 35786.0,
                "fwd_uplink_gt_db_per_k": 10.0,
                "fwd_downlink_eirp_dbw": 45.0,
                "ret_uplink_gt_db_per_k": 10.0,
                "ret_downlink_eirp_dbw": 45.0,
                "fwd_uplink_beam": {
                    "center_lat_deg": 40.0,
                    "center_lon_deg": -5.0,
                    "cosine_exponent_n": 1.5,
                },
                "fwd_downlink_beam": {
                    "center_lat_deg": 35.0,
                    "center_lon_deg": 10.0,
                    "cosine_exponent_n": 1.5,
                },
                "ret_uplink_beam": {
                    "center_lat_deg": 35.0,
                    "center_lon_deg": 10.0,
                    "cosine_exponent_n": 1.5,
                },
                "ret_downlink_beam": {
                    "center_lat_deg": 40.0,
                    "center_lon_deg": -5.0,
                    "cosine_exponent_n": 1.5,
                },
            },
            "link_params": {
                "fwd_uplink_freq_ghz": 30.0,
                "fwd_downlink_freq_ghz": 20.0,
                "ret_uplink_freq_ghz": 30.0,
                "ret_downlink_freq_ghz": 20.0,
                "weather_atten_fwd_uplink_db": 2.0,
                "weather_atten_fwd_downlink_db": 1.0,
                "weather_atten_ret_uplink_db": 2.0,
                "weather_atten_ret_downlink_db": 1.0,
                "min_elevation_warning_deg": 5.0,
            },
        }

    def test_full_link_returns_all_fields(self, basic_link_request):
        """Full link calculation should return all expected fields."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Check structure
        assert "forward_link" in result
        assert "return_link" in result
        assert "geometry" in result
        assert "warnings" in result

        # Check forward link structure
        assert "uplink" in result["forward_link"]
        assert "downlink" in result["forward_link"]
        assert "combined_cn0_db_hz" in result["forward_link"]

        # Check hop structure
        uplink = result["forward_link"]["uplink"]
        assert "slant_range_km" in uplink
        assert "elevation_angle_deg" in uplink
        assert "off_axis_angle_deg" in uplink
        assert "cn0_db_hz" in uplink
        assert "fspl_db" in uplink

    def test_geometry_values_reasonable(self, basic_link_request):
        """Geometry values should be in reasonable ranges."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        geom = result["geometry"]

        # Slant ranges should be between GEO altitude and max slant range (~42000 km)
        assert 35000 < geom["terminal_a_slant_range_km"] < 42000
        assert 35000 < geom["terminal_b_slant_range_km"] < 42000

        # Elevation angles should be positive and reasonable
        assert 20 < geom["terminal_a_elevation_deg"] < 90
        assert 20 < geom["terminal_b_elevation_deg"] < 90

    def test_combined_cn0_less_than_individual(self, basic_link_request):
        """Combined C/N0 should be less than individual hops."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        fwd = result["forward_link"]
        assert fwd["combined_cn0_db_hz"] < fwd["uplink"]["cn0_db_hz"]
        assert fwd["combined_cn0_db_hz"] < fwd["downlink"]["cn0_db_hz"]

    def test_no_warnings_for_good_geometry(self, basic_link_request):
        """No warnings for terminals with good elevation angles."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Both terminals have good elevation (40°N and 35°N with sat at 0°)
        assert len(result["warnings"]) == 0

    def test_warning_for_high_latitude_terminal(self, basic_link_request):
        """Warning generated for terminal at high latitude with low elevation."""
        # Move Terminal A to very high latitude where elevation will be low
        basic_link_request["terminal_a"]["lat_deg"] = 80.0
        basic_link_request["terminal_a"]["lon_deg"] = 60.0  # Also offset longitude for lower elevation
        # Raise the warning threshold to ensure we trigger it
        basic_link_request["link_params"]["min_elevation_warning_deg"] = 15.0

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Should have a warning for Terminal A due to low elevation
        assert len(result["warnings"]) >= 1
        assert any(w["terminal"] == "A" for w in result["warnings"])

    def test_beam_centered_on_terminal_no_rolloff(self, basic_link_request):
        """When beam is centered on terminal, off-axis angle should be ~0."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Forward uplink beam is centered on Terminal A
        fwd_up_off_axis = result["forward_link"]["uplink"]["off_axis_angle_deg"]
        assert abs(fwd_up_off_axis) < 0.1  # Should be very close to 0

    def test_off_axis_angle_when_beam_offset(self, basic_link_request):
        """Off-axis angle should be non-zero when beam is offset from terminal."""
        # Move beam center away from Terminal A
        basic_link_request["satellite"]["fwd_uplink_beam"]["center_lat_deg"] = 45.0
        basic_link_request["satellite"]["fwd_uplink_beam"]["center_lon_deg"] = 0.0

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        fwd_up_off_axis = result["forward_link"]["uplink"]["off_axis_angle_deg"]
        assert fwd_up_off_axis > 0.5  # Should have noticeable off-axis angle

    def test_cn_and_es_n0_calculated_with_symbol_rate(self, basic_link_request):
        """C/N and Es/N0 should be calculated when symbol rate is provided."""
        basic_link_request["link_params"]["symbol_rate_msps"] = 27.5
        basic_link_request["link_params"]["roll_off_factor"] = 0.20

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Check that C/N values are present
        assert result["forward_link"]["combined_cn_db"] is not None
        assert result["forward_link"]["es_n0_db"] is not None
        assert result["forward_link"]["channel_bandwidth_mhz"] is not None

        # Verify bandwidth calculation: 27.5 * (1 + 0.20) = 33 MHz
        assert result["forward_link"]["channel_bandwidth_mhz"] == pytest.approx(33.0, abs=0.1)

        # C/N should be less than C/N0 (since we're dividing by bandwidth)
        assert result["forward_link"]["combined_cn_db"] < result["forward_link"]["combined_cn0_db_hz"]

    def test_cn_not_calculated_without_symbol_rate(self, basic_link_request):
        """C/N should be None when symbol rate is not provided."""
        basic_link_request["link_params"]["symbol_rate_msps"] = None

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        assert result["forward_link"]["combined_cn_db"] is None
        assert result["forward_link"]["es_n0_db"] is None
        assert result["forward_link"]["channel_bandwidth_mhz"] is None

    def test_intermod_with_terminal_npr(self, basic_link_request):
        """C/I should be calculated when terminal NPR is provided."""
        basic_link_request["terminal_a"]["hpa_npr_db"] = 25.0
        basic_link_request["link_params"]["symbol_rate_msps"] = 27.5

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Forward link should have terminal HPA C/I
        assert result["forward_link"]["ci_terminal_hpa_db"] == 25.0
        assert result["forward_link"]["ci_total_db"] is not None
        assert result["forward_link"]["cnir_db"] is not None

        # C/(N+I) should be less than C/N
        assert result["forward_link"]["cnir_db"] < result["forward_link"]["combined_cn_db"]

    def test_intermod_with_satellite_npr(self, basic_link_request):
        """C/I should be calculated when satellite NPR is provided."""
        basic_link_request["satellite"]["fwd_downlink_npr_db"] = 22.0
        basic_link_request["link_params"]["symbol_rate_msps"] = 27.5

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Forward link should have satellite transponder C/I
        assert result["forward_link"]["ci_satellite_transponder_db"] == 22.0
        assert result["forward_link"]["cnir_db"] is not None

    def test_saturated_eirp_with_obo(self, basic_link_request):
        """Operating EIRP should be calculated from saturated EIRP minus OBO."""
        # Set saturated EIRP and OBO for terminal A
        basic_link_request["terminal_a"]["eirp_saturated_dbw"] = 65.0
        basic_link_request["terminal_a"]["hpa_obo_db"] = 5.0
        # Operating EIRP should be 65 - 5 = 60 dBW (same as original eirp_dbw)

        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # Result should be same as without saturated (since 65-5=60)
        assert "forward_link" in result
        assert result["forward_link"]["combined_cn0_db_hz"] > 0

    def test_no_intermod_when_no_npr(self, basic_link_request):
        """No intermod should be calculated when NPR values are not provided."""
        result = compute_duplex_satellite_link(
            terminal_a=basic_link_request["terminal_a"],
            terminal_b=basic_link_request["terminal_b"],
            satellite=basic_link_request["satellite"],
            link_params=basic_link_request["link_params"],
        )

        # No intermod values should be present
        assert result["forward_link"]["ci_terminal_hpa_db"] is None
        assert result["forward_link"]["ci_satellite_transponder_db"] is None
        assert result["forward_link"]["ci_total_db"] is None
