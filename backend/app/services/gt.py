import math


def compute_gt_db_per_k(antenna_gain_db: float, system_noise_temp_k: float) -> float:
    """
    G/T in dB/K:
        G/T = G[dB] - 10*log10(T[K])
    """
    if system_noise_temp_k <= 0:
        raise ValueError("System noise temperature must be positive.")
    return antenna_gain_db - 10.0 * math.log10(system_noise_temp_k)


