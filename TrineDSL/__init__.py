# photology_simulator/TrineDSL/__init__.py

from __future__ import annotations

from . import ast  # re-exported for advanced use if needed
from .lexer import tokenize
from .parser import Parser, parse_program
from .interp import Env, eval_program


__all__ = [
    "ast",
    "tokenize",
    "Parser",
    "parse_program",
    "Env",
    "eval_program",
    "run_source",
]


def run_source(src: str, env: Env | None = None) -> Env:
    """
    Parse and execute a TrineDSL source string.

    Parameters
    ----------
    src : str
        TrineDSL program text.
    env : Env | None
        Optional existing environment. If None, a new Env is created.

    Returns
    -------
    Env
        The environment after executing the program.
    """
    prog = parse_program(src)
    return eval_program(prog, env)
