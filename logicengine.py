# logic_engine.py

from __future__ import annotations
from typing import Callable, Dict

from photology_simulator.ternaryops import (
    Trit,
    cyclic,
    negator,
    antinegator,
    tnot,
    tand,
    tnand,
)


# Type aliases for clarity
UnaryOp = Callable[[Trit], Trit]
BinaryOp = Callable[[Trit, Trit], Trit]


# Mapping from user-facing names (for dropdown) to core functions
UNARY_FUNCS: Dict[str, UnaryOp] = {
    "Cyclic": cyclic,
    "Negator": negator,
    "Antinegator": antinegator,
    "TNOT": tnot,
}

BINARY_FUNCS: Dict[str, BinaryOp] = {
    "TAND": tand,
    "TNAND": tnand,
}


def list_unary_functions() -> list[str]:
    """Return names of available unary operations (for populating dropdowns)."""
    return list(UNARY_FUNCS.keys())


def list_binary_functions() -> list[str]:
    """Return names of available binary operations (for populating dropdowns)."""
    return list(BINARY_FUNCS.keys())


def is_unary(name: str) -> bool:
    """Check if a function name corresponds to a unary operation."""
    return name in UNARY_FUNCS


def is_binary(name: str) -> bool:
    """Check if a function name corresponds to a binary operation."""
    return name in BINARY_FUNCS


def eval_unary(name: str, x: Trit) -> Trit:
    """
    Evaluate a unary operation by name on input x.

    Raises KeyError if the name is not a known unary function.
    """
    try:
        func = UNARY_FUNCS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown unary function: {name}") from exc
    return func(x)


def eval_binary(name: str, x: Trit, y: Trit) -> Trit:
    """
    Evaluate a binary operation by name on inputs x, y.

    Raises KeyError if the name is not a known binary function.
    """
    try:
        func = BINARY_FUNCS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown binary function: {name}") from exc
    return func(x, y)


if __name__ == "__main__":
    # Quick self-check
    print("Unary functions:", list_unary_functions())
    print("Binary functions:", list_binary_functions())
