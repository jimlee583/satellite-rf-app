from app.services.eirp import compute_eirp_dbw


def test_compute_eirp_basic():
  """
  EIRP = Pt + Gt - Ltx
  Example: 20 dBW + 40 dB - 1 dB = 59 dBW
  """
  eirp_dbw = compute_eirp_dbw(tx_power_dbw=20.0, tx_antenna_gain_db=40.0, tx_losses_db=1.0)
  assert abs(eirp_dbw - 59.0) < 1e-6



