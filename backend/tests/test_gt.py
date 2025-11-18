import math

from app.services.gt import compute_gt_db_per_k


def test_compute_gt_basic():
  """
  For G = 40 dB, T = 500 K:
    10*log10(500) ≈ 26.99
    G/T ≈ 40 - 26.99 ≈ 13.01 dB/K
  """
  gt_db_k = compute_gt_db_per_k(antenna_gain_db=40.0, system_noise_temp_k=500.0)
  assert math.isclose(gt_db_k, 13.01, rel_tol=0.01, abs_tol=0.2)


def test_compute_gt_invalid_temp():
  try:
    compute_gt_db_per_k(antenna_gain_db=40.0, system_noise_temp_k=0.0)
    assert False, "Expected ValueError for non-positive temperature"
  except ValueError:
    pass



