def compute_eirp_dbw(
    tx_power_dbw: float,
    tx_antenna_gain_db: float,
    tx_losses_db: float = 0.0,
) -> float:
    """
    EIRP(dBW) = Pt(dBW) + Gt(dB) - Ltx(dB)
    """
    return tx_power_dbw + tx_antenna_gain_db - tx_losses_db


