import pytest

from app.services.bcd import int_to_bcd_bits, bcd_bits_to_int


def test_int_to_bcd_bits_round_trip():
  bits = int_to_bcd_bits(value=123, digits=3)
  assert bits == "0001 0010 0011"

  decoded = bcd_bits_to_int(bits)
  assert decoded == 123


def test_int_to_bcd_bits_padding_and_digits():
  bits = int_to_bcd_bits(value=5, digits=3)
  # 005 -> 0000 0000 0101
  assert bits == "0000 0000 0101"


def test_int_to_bcd_bits_invalid_value_digits():
  with pytest.raises(ValueError):
    int_to_bcd_bits(value=-1, digits=2)

  # value has too many decimal digits for requested digits
  with pytest.raises(ValueError):
    int_to_bcd_bits(value=1234, digits=3)


def test_bcd_bits_to_int_invalid_nibbles():
  # Non-multiple of 4
  with pytest.raises(ValueError):
    bcd_bits_to_int("010")

  # Digit > 9 (e.g. 1010 -> 10)
  with pytest.raises(ValueError):
    bcd_bits_to_int("1010")



