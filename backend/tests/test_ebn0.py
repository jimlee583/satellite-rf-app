from app.services.ebn0 import compute_ebn0_db


def test_compute_ebn0_basic():
  """
  For C/N0 = 80 dB-Hz and Rb = 1e6 bps:
    10*log10(1e6) = 60 dB
    Eb/N0 = 80 - 60 = 20 dB
  """
  ebn0 = compute_ebn0_db(cn0_db_hz=80.0, data_rate_bps=1e6)
  assert abs(ebn0 - 20.0) < 1e-6


def test_compute_ebn0_invalid_rate():
  try:
    compute_ebn0_db(cn0_db_hz=80.0, data_rate_bps=0.0)
    assert False, "Expected ValueError for non-positive data rate"
  except ValueError:
    pass



