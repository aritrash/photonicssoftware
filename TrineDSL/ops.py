# TrineDSL/ops.py

from __future__ import annotations

from .errors import TrineDSLRuntimeError

Trit = int  # values must be in {-1, 0, +1}


def _rt_error(error_statement: str, description: str) -> TrineDSLRuntimeError:
    # Runtime errors in ops.py do not currently have precise source locations.
    return TrineDSLRuntimeError(
        error_type="Runtime Error",
        error_statement=error_statement,
        line=1,
        column=1,
        line_text="",
        description=description,
    )


def _check_trit(x: Trit) -> Trit:
    if x not in (-1, 0, +1):
        raise _rt_error(
            "Invalid Trit Value",
            f"Invalid trit value {x}, expected -1, 0, or +1.",
        )
    return x


# --- Unary operators ------------------------------------------------------


def op_C(x: Trit) -> Trit:
    """Cyclic inverter C: -1 -> 0, 0 -> +1, +1 -> -1."""
    x = _check_trit(x)
    if x == -1:
        return 0
    elif x == 0:
        return +1
    else:  # x == +1
        return -1


def op_N(x: Trit) -> Trit:
    """Negator N: forces all inputs to -1."""
    _check_trit(x)
    return -1


def op_A(x: Trit) -> Trit:
    """Antinegator A: forces all inputs to +1."""
    _check_trit(x)
    return +1


def op_TNOT(x: Trit) -> Trit:
    """Ternary NOT: sign inversion, preserves 0."""
    x = _check_trit(x)
    return -x


# --- Binary base operators -------------------------------------------------


def op_TAND(a: Trit, b: Trit) -> Trit:
    """Ternary AND as min over {-1,0,+1}."""
    a = _check_trit(a)
    b = _check_trit(b)
    return min(a, b)


def op_TOR(a: Trit, b: Trit) -> Trit:
    """Ternary OR as max over {-1,0,+1}."""
    a = _check_trit(a)
    b = _check_trit(b)
    return max(a, b)


def op_TNAND(a: Trit, b: Trit) -> Trit:
    """TNAND = TNOT(TAND(a, b)) = -min(a, b)."""
    return op_TNOT(op_TAND(a, b))


def op_TNOR(a: Trit, b: Trit) -> Trit:
    """TNOR = TNOT(TOR(a, b)) = -max(a, b)."""
    return op_TNOT(op_TOR(a, b))


# --- TXOR from Chapter 4 table --------------------------------------------
# a\b   -1   0   +1
# -1    0  -1   +1
#  0   -1   0   -1
# +1   +1  -1    0
# [file:34]


_TXOR_TABLE: dict[tuple[Trit, Trit], Trit] = {
    (-1, -1): 0,
    (-1, 0): -1,
    (-1, +1): +1,
    (0, -1): -1,
    (0, 0): 0,
    (0, +1): -1,
    (+1, -1): +1,
    (+1, 0): -1,
    (+1, +1): 0,
}


def op_TXOR(a: Trit, b: Trit) -> Trit:
    """TXOR from Chapter 4: symmetric difference detector."""
    a = _check_trit(a)
    b = _check_trit(b)
    return _TXOR_TABLE[(a, b)]


# --- TSUM and TCARRY (half-adder helpers) ---------------------------------


_TSUM_TABLE: dict[tuple[Trit, Trit], Trit] = {
    (-1, -1): 0,
    (-1,  0): -1,
    (-1, +1): 0,
    ( 0, -1): -1,
    ( 0,  0): 0,
    ( 0, +1): +1,
    (+1, -1): 0,
    (+1,  0): +1,
    (+1, +1): 0,
}


_TCARRY_TABLE: dict[tuple[Trit, Trit], Trit] = {
    (-1, -1): -1,
    (-1,  0): 0,
    (-1, +1): 0,
    ( 0, -1): 0,
    ( 0,  0): 0,
    ( 0, +1): 0,
    (+1, -1): 0,
    (+1,  0): 0,
    (+1, +1): +1,
}


def op_TSUM(a: Trit, b: Trit) -> Trit:
    a = _check_trit(a)
    b = _check_trit(b)
    return _TSUM_TABLE[(a, b)]


def op_TCARRY(a: Trit, b: Trit) -> Trit:
    a = _check_trit(a)
    b = _check_trit(b)
    return _TCARRY_TABLE[(a, b)]


# --- Dispatcher used by the interpreter -----------------------------------


def apply_func(name: str, args: list[Trit]) -> Trit:
    """
    Dispatch a TrineDSL function name to the corresponding operator.

    Supported names (v0):
      C, N, A, TNOT,
      TAND, TOR, TNAND, TNOR,
      TXOR,
      TSUM, TCARRY
    """

    # All arity errors are reported with the same shape.
    def _arity(expected: int, got: int) -> TrineDSLRuntimeError:
        return _rt_error(
            "Wrong Number of Arguments",
            f"Function '{name}' expects {expected} argument(s), "
            f"but {got} was provided.",
        )

    if name == "C":
        if len(args) != 1:
            raise _arity(1, len(args))
        return op_C(args[0])

    if name == "N":
        if len(args) != 1:
            raise _arity(1, len(args))
        return op_N(args[0])

    if name == "A":
        if len(args) != 1:
            raise _arity(1, len(args))
        return op_A(args[0])

    if name == "TNOT":
        if len(args) != 1:
            raise _arity(1, len(args))
        return op_TNOT(args[0])

    if name == "TAND":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TAND(args[0], args[1])

    if name == "TOR":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TOR(args[0], args[1])

    if name == "TNAND":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TNAND(args[0], args[1])

    if name == "TNOR":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TNOR(args[0], args[1])

    if name == "TXOR":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TXOR(args[0], args[1])

    if name == "TSUM":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TSUM(args[0], args[1])

    if name == "TCARRY":
        if len(args) != 2:
            raise _arity(2, len(args))
        return op_TCARRY(args[0], args[1])

    raise _rt_error(
        "Unknown Function",
        f"Function '{name}' is not defined.",
    )
