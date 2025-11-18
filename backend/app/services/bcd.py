def int_to_bcd_bits(value: int, digits: int) -> str:
    """
    Encode a non-negative integer to BCD as a human-readable bit string.
    Example: value=13, digits=3 -> '0000 0001 0011'
    """
    if value < 0:
        raise ValueError("Value must be non-negative for BCD encoding.")
    if digits <= 0:
        raise ValueError("Digits must be positive for BCD encoding.")

    str_val = str(value)
    if len(str_val) > digits:
        raise ValueError("Value has more decimal digits than requested BCD digits.")

    str_val = str_val.zfill(digits)
    nibbles = []
    for ch in str_val:
        d = int(ch)
        nibbles.append(f"{d:04b}")
    return " ".join(nibbles)


def bcd_bits_to_int(bcd_bits: str) -> int:
    """
    Decode a BCD bit string back to integer.
    Accepts spaces between 4-bit nibbles.
    """
    cleaned = bcd_bits.replace(" ", "")
    if len(cleaned) == 0 or len(cleaned) % 4 != 0:
        raise ValueError("BCD bit string length must be a non-zero multiple of 4.")

    value_digits = []
    for i in range(0, len(cleaned), 4):
        nibble = cleaned[i : i + 4]
        d = int(nibble, 2)
        if d > 9:
            raise ValueError("Invalid BCD digit (>9) encountered.")
        value_digits.append(str(d))
    return int("".join(value_digits))


