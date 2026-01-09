# TrineDSL/errors.py

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TrineDSLError(Exception):
    error_type: str          # e.g. "Lexing Error"
    error_statement: str     # e.g. "Unexpected Character"
    line: int
    column: int
    line_text: str
    description: str

    def __str__(self) -> str:
        # Core formatter used by the GUI
        return (
            f"{self.error_type}: {self.error_statement}\n"
            f"    in line {self.line}: {self.line_text}\n"
            f"    {self.description}"
        )


class TrineDSLLexError(TrineDSLError):
    pass


class TrineDSLParseError(TrineDSLError):
    pass


class TrineDSLRuntimeError(TrineDSLError):
    pass
