from __future__ import annotations


def to_int_color(hex_color: str):
    """
    Convert string hex color to int.
    """
    return int(hex_color.replace("#", "0x"), 16)


