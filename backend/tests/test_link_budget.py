import math

from app.services.link_budget import free_space_path_loss_db, link_budget_received_power_db


def test_free_space_path_loss_known_value():
  """
  At 1 GHz and 1 km, FSPL should be ~92.45 dB (canonical reference).
  """
  fspl = free_space_path_loss_db(frequency_hz=1e9, distance_m=1e3)
  assert math.isclose(fspl, 92.45, rel_tol=0.01, abs_tol=0.2)


def test_free_space_path_loss_invalid_inputs():
  for freq, dist in [(0, 1e3), (1e9, 0), (-1e9, 1e3), (1e9, -10)]:
    try:
      free_space_path_loss_db(frequency_hz=freq, distance_m=dist)
      assert False, "Expected ValueError for invalid inputs"
    except ValueError:
      pass


def test_link_budget_received_power_simple_case():
  """
  GEO-style example:
    f = 1 GHz, d = 40,000 km -> FSPL ~184.5 dB
    Pt = 20 dBW, Gt = 40 dB, Gr = 40 dB, losses = 0
    Pr ≈ 20 + 40 + 40 - 184.5 = -84.5 dBW
  """
  fspl_db, pr_dbw = link_budget_received_power_db(
    frequency_hz=1e9,
    distance_m=40_000_000.0,
    tx_power_dbw=20.0,
    tx_antenna_gain_db=40.0,
    rx_antenna_gain_db=40.0,
    tx_losses_db=0.0,
    rx_losses_db=0.0,
    other_losses_db=0.0,
  )

  assert math.isclose(fspl_db, 184.5, rel_tol=0.01, abs_tol=0.5)
  assert math.isclose(pr_dbw, -84.5, rel_tol=0.01, abs_tol=0.5)



