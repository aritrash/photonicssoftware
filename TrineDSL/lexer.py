# TrineDSL/lexer.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .errors import TrineDSLLexError


@dataclass
class Token:
    kind: str
    value: str
    pos: int  # simple character offset in source


# Kinds:
#  IDENT, TRIT, KW_TRIT,
#  EQUAL, COMMA, SEMI, LPAREN, RPAREN,
#  EOF


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def _is_ident_part(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _pos_to_line_col(src: str, pos: int) -> tuple[int, int, str]:
    """
    Map a 0-based character offset `pos` into (line, column, line_text).

    line:   1-based line number
    column: 1-based column number in that line
    line_text: contents of the line without trailing newline
    """
    # Line start is the character after the last '\n' before pos.
    line_start = src.rfind("\n", 0, pos)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    # Line end is the next '\n' or end of string.
    line_end = src.find("\n", pos)
    if line_end == -1:
        line_end = len(src)

    line_text = src[line_start:line_end]
    line_no = src.count("\n", 0, pos) + 1
    col_no = pos - line_start + 1
    return line_no, col_no, line_text


def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(src)

    while i < n:
        ch = src[i]

        # Whitespace
        if ch.isspace():
            i += 1
            continue

        # Line comments: //...
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            i += 2
            while i < n and src[i] != "\n":
                i += 1
            continue

        # Symbols
        if ch == "=":
            tokens.append(Token("EQUAL", "=", i))
            i += 1
            continue
        if ch == ",":
            tokens.append(Token("COMMA", ",", i))
            i += 1
            continue
        if ch == ";":
            tokens.append(Token("SEMI", ";", i))
            i += 1
            continue
        if ch == "(":
            tokens.append(Token("LPAREN", "(", i))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token("RPAREN", ")", i))
            i += 1
            continue

        # Trit literals: -1, 0, +1
        if ch in "+-0123456789":
            start = i
            if ch in "+-":
                i += 1
                if i >= n or not src[i].isdigit():
                    line_no, col_no, line_text = _pos_to_line_col(src, start)
                    raise TrineDSLLexError(
                        error_type="Lexing Error",
                        error_statement="Invalid Trit Literal",
                        line=line_no,
                        column=col_no,
                        line_text=line_text,
                        description=(
                            "Invalid signed numeric literal; "
                            "trits must be -1, 0, or +1."
                        ),
                    )
            while i < n and src[i].isdigit():
                i += 1
            text = src[start:i]
            if text not in ("-1", "0", "+1"):
                line_no, col_no, line_text = _pos_to_line_col(src, start)
                raise TrineDSLLexError(
                    error_type="Lexing Error",
                    error_statement="Invalid Trit Literal",
                    line=line_no,
                    column=col_no,
                    line_text=line_text,
                    description=(
                        f"'{text}' is not a valid trit literal; "
                        "expected -1, 0, or +1."
                    ),
                )
            tokens.append(Token("TRIT", text, start))
            continue

        # Identifiers / keywords
        if _is_ident_start(ch):
            start = i
            i += 1
            while i < n and _is_ident_part(src[i]):
                i += 1
            text = src[start:i]
            if text == "trit":
                tokens.append(Token("KW_TRIT", text, start))
            else:
                tokens.append(Token("IDENT", text, start))
            continue

        # Unexpected character
        line_no, col_no, line_text = _pos_to_line_col(src, i)
        raise TrineDSLLexError(
            error_type="Lexing Error",
            error_statement="Unexpected Character",
            line=line_no,
            column=col_no,
            line_text=line_text,
            description=f"'{ch}' is an unexpected character.",
        )

    tokens.append(Token("EOF", "", n))
    return tokens
