# TrineDSL/interp.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from . import ast
from .ops import apply_func, Trit
from .errors import TrineDSLRuntimeError


@dataclass
class Env:
    """
    Runtime environment for TrineDSL.

    Maps variable names to trit values in {-1, 0, +1}.
    """
    vars: Dict[str, Trit] = field(default_factory=dict)

    def declare(self, name: str, initial: Trit = 0) -> None:
        if name in self.vars:
            raise TrineDSLRuntimeError(
                error_type="Runtime Error",
                error_statement="Redeclaration of Variable",
                line=1,
                column=1,
                line_text="",
                description=f"Variable '{name}' is already declared.",
            )
        self.vars[name] = initial

    def set(self, name: str, value: Trit) -> None:
        if name not in self.vars:
            raise TrineDSLRuntimeError(
                error_type="Runtime Error",
                error_statement="Assignment to Undeclared Variable",
                line=1,
                column=1,
                line_text="",
                description=f"Variable '{name}' is not declared.",
            )
        if value not in (-1, 0, +1):
            raise TrineDSLRuntimeError(
                error_type="Runtime Error",
                error_statement="Invalid Trit Value",
                line=1,
                column=1,
                line_text="",
                description=(
                    f"Invalid trit value {value} assigned to '{name}'; "
                    "expected -1, 0, or +1."
                ),
            )
        self.vars[name] = value

    def get(self, name: str) -> Trit:
        if name not in self.vars:
            raise TrineDSLRuntimeError(
                error_type="Runtime Error",
                error_statement="Use of Undeclared Variable",
                line=1,
                column=1,
                line_text="",
                description=f"Variable '{name}' is not declared.",
            )
        return self.vars[name]


# --- Top-level evaluation -------------------------------------------------


def eval_program(program: ast.Program, env: Env | None = None) -> Env:
    """
    Execute a Program AST in the given environment.

    If env is None, a fresh environment is created.
    Returns the environment after execution.
    """
    if env is None:
        env = Env()

    for stmt in program.statements:
        eval_stmt(stmt, env)

    return env


def eval_stmt(stmt: ast.Statement, env: Env) -> None:
    if isinstance(stmt, ast.Decl):
        _eval_decl(stmt, env)
    elif isinstance(stmt, ast.Assign):
        _eval_assign(stmt, env)
    else:
        raise TrineDSLRuntimeError(
            error_type="Runtime Error",
            error_statement="Internal Error",
            line=1,
            column=1,
            line_text="",
            description=f"Unknown statement type: {type(stmt)!r}.",
        )


def _eval_decl(decl: ast.Decl, env: Env) -> None:
    # For now we only support "trit" type.
    if decl.type_name != "trit":
        raise TrineDSLRuntimeError(
            error_type="Runtime Error",
            error_statement="Unsupported Type",
            line=1,
            column=1,
            line_text="",
            description=f"Unsupported type '{decl.type_name}' in declaration.",
        )

    for name in decl.names:
        env.declare(name, initial=0)  # default init to 0


def _eval_assign(assign: ast.Assign, env: Env) -> None:
    value = eval_expr(assign.expr, env)
    env.set(assign.name, value)


# --- Expression evaluation -----------------------------------------------


def eval_expr(expr: ast.Expr, env: Env) -> Trit:
    if isinstance(expr, ast.Name):
        return env.get(expr.name)

    if isinstance(expr, ast.TritLiteral):
        val = expr.value
        if val not in (-1, 0, +1):
            raise TrineDSLRuntimeError(
                error_type="Runtime Error",
                error_statement="Invalid Trit Literal",
                line=1,
                column=1,
                line_text="",
                description=(
                    f"Invalid trit literal {val}; expected -1, 0, or +1."
                ),
            )
        return val

    if isinstance(expr, ast.FuncCall):
        arg_vals = [eval_expr(arg, env) for arg in expr.args]
        return apply_func(expr.func, arg_vals)

    raise TrineDSLRuntimeError(
        error_type="Runtime Error",
        error_statement="Internal Error",
        line=1,
        column=1,
        line_text="",
        description=f"Unknown expression type: {type(expr)!r}.",
    )
