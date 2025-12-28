# ternaryops.py

from __future__ import annotations
from enum import IntEnum
from typing import Tuple


class Trit(IntEnum):
    """Balanced ternary digit: -1, 0, +1."""
    MINUS = -1
    ZERO = 0
    PLUS = 1

    @classmethod
    def from_int(cls, value: int) -> "Trit":
        """Safely construct from -1, 0, +1 (raises for other values)."""
        if value not in (-1, 0, 1):
            raise ValueError(f"Invalid trit value: {value}")
        return cls(value)

    def __str__(self) -> str:
        """Human-friendly symbol."""
        if self is Trit.MINUS:
            return "-1"
        if self is Trit.ZERO:
            return "0"
        return "+1"


# ---------- Unary operations ----------

def cyclic(trit: Trit) -> Trit:
    """
    Cyclic inverter C:
        -1 -> 0
         0 -> +1
        +1 -> -1
    """
    if trit is Trit.MINUS:
        return Trit.ZERO
    if trit is Trit.ZERO:
        return Trit.PLUS
    return Trit.MINUS


def negator(trit: Trit) -> Trit:
    """
    Negator N: drive everything to -1.
        -1 -> -1
         0 -> -1
        +1 -> -1
    You can later relax this if you want a subtler behavior.
    """
    return Trit.MINUS


def antinegator(trit: Trit) -> Trit:
    """
    Antinegator A: drive everything to +1.
        -1 -> +1
         0 -> +1
        +1 -> +1
    """
    return Trit.PLUS


def tnot(trit: Trit) -> Trit:
    """
    Ternary NOT (sign inversion):
        -1 -> +1
         0 ->  0
        +1 -> -1
    This is the standard balanced-ternary negation.[web:47][web:94]
    """
    if trit is Trit.ZERO:
        return Trit.ZERO
    # flip sign for +/- 1
    return Trit.MINUS if trit is Trit.PLUS else Trit.PLUS


# ---------- Binary operations ----------

def tand(a: Trit, b: Trit) -> Trit:
    """
    Ternary AND (TAND) defined as the minimum in the order -1 < 0 < +1:
        tand(a, b) = min(a, b)
    This generalizes Boolean AND to balanced ternary.[web:41][web:47]
    """
    # IntEnum compares by numeric value so min() works directly.
    return Trit(min(int(a), int(b)))


def tnand(a: Trit, b: Trit) -> Trit:
    """
    Ternary NAND (TNAND) defined as the NOT of TAND:
        tnand(a, b) = tnot(tand(a, b))
    This mirrors Boolean NAND = NOT(AND).[web:41][web:53]
    """
    return tnot(tand(a, b))


# ---------- Convenience helpers ----------

def truth_table_unary(op, name: str) -> Tuple[Tuple[Trit, Trit], ...]:
    """
    Build a small truth table for a unary operation 'op(Trit) -> Trit'.
    Returns tuples of (input, output) in order (-1, 0, +1).
    """
    inputs = (Trit.MINUS, Trit.ZERO, Trit.PLUS)
    return tuple((x, op(x)) for x in inputs)


def truth_table_binary(op, name: str) -> Tuple[Tuple[Trit, Trit, Trit], ...]:
    """
    Build a small truth table for a binary operation 'op(Trit, Trit) -> Trit'.
    Returns tuples of (a, b, output) for all 3x3 combinations.
    """
    values = (Trit.MINUS, Trit.ZERO, Trit.PLUS)
    table = []
    for a in values:
        for b in values:
            table.append((a, b, op(a, b)))
    return tuple(table)


if __name__ == "__main__":
    # Quick self-check when running this file directly.
    print("Unary TNOT truth table:")
    for x, y in truth_table_unary(tnot, "TNOT"):
        print(f"TNOT({x}) = {y}")

    print("\nBinary TNAND truth table:")
    for a, b, y in truth_table_binary(tnand, "TNAND"):
        print(f"TNAND({a}, {b}) = {y}")
