# TrineDSL/ast.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


# --- Base types -----------------------------------------------------------

class Node:
    """Base class for all AST nodes."""
    pass


# --- Program and statements ----------------------------------------------


@dataclass
class Program(Node):
    statements: List["Statement"]


class Statement(Node):
    """Base class for all statements."""
    pass


@dataclass
class Decl(Statement):
    """
    Declaration of one or more trit variables.

    Example:  trit A, B, S;
    """
    type_name: str  # currently always "trit"
    names: List[str]


@dataclass
class Assign(Statement):
    """
    Assignment of an expression to a variable.

    Example:  S = TXOR(A, B);
    """
    name: str
    expr: "Expr"


# --- Expressions ----------------------------------------------------------


class Expr(Node):
    """Base class for all expressions."""
    pass


@dataclass
class Name(Expr):
    """
    Reference to a signal/variable.

    Example:  A
    """
    name: str


@dataclass
class TritLiteral(Expr):
    """
    Literal trit value: -1, 0, or +1.
    """
    value: int  # must be in {-1, 0, +1}


@dataclass
class FuncCall(Expr):
    """
    Function call expression.

    Example:  TXOR(A, B)
    """
    func: str
    args: List[Expr]


# A small helper union for type hints
AnyStmt = Union[Decl, Assign]
AnyExpr = Union[Name, TritLiteral, FuncCall]
