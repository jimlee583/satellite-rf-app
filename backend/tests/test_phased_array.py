import math
import pytest

from app.services.phased_array import compute_phased_array_gain_db


def test_compute_phased_array_gain_basic():
  """
  Example:
    element_gain = 5 dB, N = 16, eta = 0.8
    N * eta = 12.8
    10*log10(12.8) ≈ 11.07 dB
    G_array ≈ 5 + 11.07 ≈ 16.07 dB
  """
  gain = compute_phased_array_gain_db(element_gain_db=5.0, num_elements=16, array_efficiency=0.8)
  assert math.isclose(gain, 16.07, rel_tol=0.01, abs_tol=0.2)


def test_compute_phased_array_gain_invalid_inputs():
  with pytest.raises(ValueError):
    compute_phased_array_gain_db(element_gain_db=5.0, num_elements=0, array_efficiency=0.8)

  with pytest.raises(ValueError):
    compute_phased_array_gain_db(element_gain_db=5.0, num_elements=4, array_efficiency=1.2)

  with pytest.raises(ValueError):
    compute_phased_array_gain_db(element_gain_db=5.0, num_elements=4, array_efficiency=-0.1)



