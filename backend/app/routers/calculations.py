from fastapi import APIRouter, HTTPException

from .. import schema
from ..services import (
    link_budget,
    eirp,
    gt,
    ebn0,
    bcd,
    phased_array,
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


@router.post("/bcd/encode", response_model=schema.BCDEncodeResponse)
def encode_bcd(payload: schema.BCDEncodeRequest):
    try:
        bits = bcd.int_to_bcd_bits(value=payload.value, digits=payload.digits)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.BCDEncodeResponse(bcd_bits=bits)


@router.post("/bcd/decode", response_model=schema.BCDDecodeResponse)
def decode_bcd(payload: schema.BCDDecodeRequest):
    try:
        value = bcd.bcd_bits_to_int(bcd_bits=payload.bcd_bits)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schema.BCDDecodeResponse(value=value)


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


