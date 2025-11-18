import math


LIGHT_SPEED = 299_792_458.0  # m/s


def free_space_path_loss_db(frequency_hz: float, distance_m: float) -> float:
    """
    Compute free-space path loss in dB using:
        FSPL = 20*log10(4 * pi * d * f / c)
    """
    if frequency_hz <= 0 or distance_m <= 0:
        raise ValueError("Frequency and distance must be positive.")
    return 20.0 * math.log10(4.0 * math.pi * distance_m * frequency_hz / LIGHT_SPEED)


def link_budget_received_power_db(
    frequency_hz: float,
    distance_m: float,
    tx_power_dbw: float,
    tx_antenna_gain_db: float,
    rx_antenna_gain_db: float,
    tx_losses_db: float = 0.0,
    rx_losses_db: float = 0.0,
    other_losses_db: float = 0.0,
) -> tuple[float, float]:
    """
    Classic link budget:
        Pr(dBW) = Pt + Gt + Gr - Lfs - Ltx - Lrx - Lother
    Returns (fspl_db, received_power_dbw).
    """
    fspl_db = free_space_path_loss_db(frequency_hz, distance_m)
    total_losses_db = tx_losses_db + rx_losses_db + other_losses_db + fspl_db
    pr_dbw = tx_power_dbw + tx_antenna_gain_db + rx_antenna_gain_db - total_losses_db
    return fspl_db, pr_dbw



