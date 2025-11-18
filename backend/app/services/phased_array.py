import math


def compute_phased_array_gain_db(
    element_gain_db: float,
    num_elements: int,
    array_efficiency: float = 1.0,
) -> float:
    """
    Simplified phased array gain:
        G_array[dB] = G_element[dB] + 10*log10(N * eta)
    where eta is array efficiency (0..1).
    """
    if num_elements <= 0:
        raise ValueError("Number of elements must be positive.")
    if not (0.0 <= array_efficiency <= 1.0):
        raise ValueError("Array efficiency must be between 0 and 1.")
    if array_efficiency == 0:
        # effectively no gain
        return -math.inf
    return element_gain_db + 10.0 * math.log10(num_elements * array_efficiency)


