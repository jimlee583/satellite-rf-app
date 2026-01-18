from fastapi import APIRouter, HTTPException

from .. import schema
from ..services import (
    link_budget,
    eirp,
    gt,
    ebn0,
    phased_array,
    scan_loss,
    azimuth,
    beam_off_axis,
    weather_loss,
    duplex_satellite_link,
)


router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/link-budget", response_model=schema.LinkBudgetResponse)
def compute_link_budget(payload: schema.LinkBudgetRequest):
    try:
        fspl_db, pr_dbw = link_budget.link_budget_received_power_db(
            frequency_hz=payload.frequency_hz,
            distance_m=payload.distance_m,
            tx_power_dbw=payload.tx_power_dbw,
            tx_antenna_gain_db=payload.tx_antenna_gain_db,
            rx_antenna_gain_db=payload.rx_antenna_gain_db,
            tx_losses_db=payload.tx_losses_db,
            rx_losses_db=payload.rx_losses_db,
            other_losses_db=payload.other_losses_db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return schema.LinkBudgetResponse(
        fspl_db=fspl_db,
        received_power_dbw=pr_dbw,
        margin_db=None,
    )


@router.post("/eirp", response_model=schema.EIRPResponse)
def compute_eirp(payload: schema.EIRPRequest):
    eirp_dbw = eirp.compute_eirp_dbw(
        tx_power_dbw=payload.tx_power_dbw,
        tx_antenna_gain_db=payload.tx_antenna_gain_db,
        tx_losses_db=payload.tx_losses_db,
    )
    return schema.EIRPResponse(eirp_dbw=eirp_dbw)


@router.post("/gt", response_model=schema.GTResponse)
def compute_gt(payload: schema.GTRequest):
    try:
        gt_db_k = gt.compute_gt_db_per_k(
            antenna_gain_db=payload.antenna_gain_db,
            system_noise_temp_k=payload.system_noise_temp_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.GTResponse(gt_db_per_k=gt_db_k)


@router.post("/ebn0", response_model=schema.EbN0Response)
def compute_ebn0(payload: schema.EbN0Request):
    try:
        ebn0_db = ebn0.compute_ebn0_db(
            cn0_db_hz=payload.cn0_db_hz,
            data_rate_bps=payload.data_rate_bps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.EbN0Response(ebn0_db=ebn0_db)


@router.post("/phased-array-gain", response_model=schema.PhasedArrayGainResponse)
def compute_phased_array_gain(payload: schema.PhasedArrayGainRequest):
    try:
        gain_db = phased_array.compute_phased_array_gain_db(
            element_gain_db=payload.element_gain_db,
            num_elements=payload.num_elements,
            array_efficiency=payload.array_efficiency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.PhasedArrayGainResponse(array_gain_db=gain_db)


@router.post("/scan-loss", response_model=schema.ScanLossResponse)
def compute_scan_loss(payload: schema.ScanLossRequest):
    try:
        scan_angle_deg = scan_loss.compute_nadir_angle_deg(
            satellite_longitude_deg=payload.satellite_longitude_deg,
            user_latitude_deg=payload.user_latitude_deg,
            user_longitude_deg=payload.user_longitude_deg,
        )
        loss_db = scan_loss.compute_scan_loss_db(
            scan_angle_deg=scan_angle_deg,
            scan_exponent=payload.scan_exponent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.ScanLossResponse(scan_angle_deg=scan_angle_deg, scan_loss_db=loss_db)


@router.post("/azimuth", response_model=schema.AzimuthResponse)
def compute_azimuth(payload: schema.AzimuthRequest):
    azimuth_deg = azimuth.compute_azimuth_deg(
        start_lat_deg=payload.start_lat_deg,
        start_lon_deg=payload.start_lon_deg,
        end_lat_deg=payload.end_lat_deg,
        end_lon_deg=payload.end_lon_deg,
    )
    central_angle_deg = azimuth.compute_central_angle_deg(
        start_lat_deg=payload.start_lat_deg,
        start_lon_deg=payload.start_lon_deg,
        end_lat_deg=payload.end_lat_deg,
        end_lon_deg=payload.end_lon_deg,
    )
    try:
        elevation_deg = azimuth.compute_elevation_deg(
            ground_lat_deg=payload.start_lat_deg,
            ground_lon_deg=payload.start_lon_deg,
            subsatellite_lat_deg=payload.end_lat_deg,
            subsatellite_lon_deg=payload.end_lon_deg,
            satellite_altitude_km=payload.satellite_altitude_km,
        )
        nadir_angle_deg = azimuth.compute_nadir_angle_deg(
            central_angle_deg=central_angle_deg,
            satellite_altitude_km=payload.satellite_altitude_km,
        )
        terminal_phi_deg = azimuth.compute_terminal_phi_deg(
            ground_lat_deg=payload.start_lat_deg,
            subsatellite_lat_deg=payload.end_lat_deg,
            central_angle_deg=central_angle_deg,
        )
        slant_range_km = azimuth.compute_slant_range_km(
            central_angle_deg=central_angle_deg,
            satellite_altitude_km=payload.satellite_altitude_km,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.AzimuthResponse(
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg,
        central_angle_deg=central_angle_deg,
        nadir_angle_deg=nadir_angle_deg,
        terminal_phi_deg=terminal_phi_deg,
        slant_range_km=slant_range_km,
    )


@router.post("/beam-off-axis", response_model=schema.BeamOffAxisResponse)
def compute_beam_off_axis(payload: schema.BeamOffAxisRequest):
    result = beam_off_axis.compute_beam_off_axis_full(
        sat_lat_deg=payload.sat_lat_deg,
        sat_lon_deg=payload.sat_lon_deg,
        sat_alt_km=payload.sat_alt_km,
        user_lat_deg=payload.user_lat_deg,
        user_lon_deg=payload.user_lon_deg,
        user_alt_km=payload.user_alt_km,
        beam_center_lat_deg=payload.beam_center_lat_deg,
        beam_center_lon_deg=payload.beam_center_lon_deg,
        beam_center_alt_km=payload.beam_center_alt_km,
    )
    return schema.BeamOffAxisResponse(**result)


@router.post("/weather-loss", response_model=schema.WeatherLossResponse)
def compute_weather_loss(payload: schema.WeatherLossRequest):
    try:
        elevation_deg, rain_rate_mm_hr, loss_db = weather_loss.compute_weather_loss_db(
            satellite_longitude_deg=payload.satellite_longitude_deg,
            user_latitude_deg=payload.user_latitude_deg,
            user_longitude_deg=payload.user_longitude_deg,
            availability_percent=payload.availability_percent,
            frequency_ghz=payload.frequency_ghz,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.WeatherLossResponse(
        elevation_deg=elevation_deg,
        rain_rate_mm_hr=rain_rate_mm_hr,
        weather_loss_db=loss_db,
    )


@router.post("/duplex-satellite-link", response_model=schema.DuplexSatelliteLinkResponse)
def compute_duplex_satellite_link_budget(payload: schema.DuplexSatelliteLinkRequest):
    """
    Calculate duplex bent-pipe satellite link budget.

    Computes forward (A→Sat→B) and return (B→Sat→A) links
    with geometry, losses, and combined C/N0.
    """
    try:
        result = duplex_satellite_link.compute_duplex_satellite_link(
            terminal_a=payload.terminal_a.model_dump(),
            terminal_b=payload.terminal_b.model_dump(),
            satellite=payload.satellite.model_dump(),
            link_params=payload.link_params.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.DuplexSatelliteLinkResponse(**result)

