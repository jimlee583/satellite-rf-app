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
    return schema.AzimuthResponse(azimuth_deg=azimuth_deg)

