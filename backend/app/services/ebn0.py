import math


def compute_ebn0_db(cn0_db_hz: float, data_rate_bps: float) -> float:
    """
    Eb/N0 = C/N0 - 10*log10(Rb)
    where:
      C/N0 in dB-Hz
      Rb in bps
    """
    if data_rate_bps <= 0:
        raise ValueError("Data rate must be positive.")
    return cn0_db_hz - 10.0 * math.log10(data_rate_bps)


