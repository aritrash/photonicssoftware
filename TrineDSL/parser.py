# TrineDSL/parser.py

from __future__ import annotations

from typing import List, Optional

from . import ast
from .lexer import Token, tokenize, _pos_to_line_col
from .errors import TrineDSLParseError


class Parser:
    def __init__(self, tokens: List[Token], src: str):
        self.tokens = tokens
        self.src = src
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _line_info(self, pos: int):
        return _pos_to_line_col(self.src, pos)

    def _expect(self, kind: str) -> Token:
        tok = self.current
        if tok.kind != kind:
            line_no, col_no, line_text = self._line_info(tok.pos)
            # Use a generic "Unexpected Token" here; more specific cases
            # are handled in parse_statement / parse_expr.
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Unexpected Token",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description=(
                    f"Expected {kind}, got {tok.kind} ('{tok.value}')."
                ),
            )
        self.pos += 1
        return tok

    def _match(self, kind: str) -> Optional[Token]:
        if self.current.kind == kind:
            return self._advance()
        return None

    # Program ::= { Statement }
    def parse_program(self) -> ast.Program:
        statements: List[ast.Statement] = []
        while self.current.kind != "EOF":
            statements.append(self.parse_statement())
        return ast.Program(statements=statements)

    # Statement ::= DeclStmt ";" | AssignStmt ";"
    def parse_statement(self) -> ast.Statement:
        if self.current.kind == "KW_TRIT":
            stmt = self.parse_decl_stmt()
        elif self.current.kind == "IDENT":
            stmt = self.parse_assign_stmt()
        else:
            tok = self.current
            line_no, col_no, line_text = self._line_info(tok.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Unexpected Token at Statement Start",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description=(
                    f"Unexpected token '{tok.value}' ({tok.kind}) "
                    "at the beginning of a statement."
                ),
            )

        semi = self.current
        if semi.kind != "SEMI":
            line_no, col_no, line_text = self._line_info(semi.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Missing Semicolon",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description="Expected ';' at the end of the statement.",
            )
        self._advance()
        return stmt

    # DeclStmt ::= "trit" IdentList
    def parse_decl_stmt(self) -> ast.Decl:
        kw_tok = self.current
        if kw_tok.kind != "KW_TRIT":
            line_no, col_no, line_text = self._line_info(kw_tok.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Expected 'trit' Keyword",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description="Declaration must start with the 'trit' keyword.",
            )
        self._advance()

        names: List[str] = []

        first = self.current
        if first.kind != "IDENT":
            line_no, col_no, line_text = self._line_info(first.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Expected Identifier in Declaration",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description="Expected an identifier after 'trit'.",
            )
        self._advance()
        names.append(first.value)

        while self._match("COMMA"):
            ident = self.current
            if ident.kind != "IDENT":
                line_no, col_no, line_text = self._line_info(ident.pos)
                raise TrineDSLParseError(
                    error_type="Parsing Error",
                    error_statement="Expected Identifier in Declaration",
                    line=line_no,
                    column=col_no,
                    line_text=line_text,
                    description="Expected an identifier after ','.",
                )
            self._advance()
            names.append(ident.value)

        return ast.Decl(type_name="trit", names=names)

    # AssignStmt ::= IDENT "=" Expr
    def parse_assign_stmt(self) -> ast.Assign:
        name_tok = self.current
        if name_tok.kind != "IDENT":
            line_no, col_no, line_text = self._line_info(name_tok.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Expected Identifier in Assignment",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description="Assignment must start with an identifier.",
            )
        self._advance()

        eq_tok = self.current
        if eq_tok.kind != "EQUAL":
            line_no, col_no, line_text = self._line_info(eq_tok.pos)
            raise TrineDSLParseError(
                error_type="Parsing Error",
                error_statement="Expected '=' After Identifier",
                line=line_no,
                column=col_no,
                line_text=line_text,
                description="Expected '=' after identifier in assignment.",
            )
        self._advance()

        expr = self.parse_expr()
        return ast.Assign(name=name_tok.value, expr=expr)

    # Expr ::= FuncCall | IDENT | TRIT_LITERAL
    def parse_expr(self) -> ast.Expr:
        tok = self.current

        if tok.kind == "TRIT":
            self._advance()
            value = int(tok.value)
            return ast.TritLiteral(value=value)

        if tok.kind == "IDENT":
            ident_tok = self._advance()
            if self._match("LPAREN"):
                args: List[ast.Expr] = []
                if self.current.kind != "RPAREN":
                    args.append(self.parse_expr())
                    while self._match("COMMA"):
                        args.append(self.parse_expr())
                rparen = self.current
                if rparen.kind != "RPAREN":
                    line_no, col_no, line_text = self._line_info(rparen.pos)
                    raise TrineDSLParseError(
                        error_type="Parsing Error",
                        error_statement="Missing Closing Parenthesis",
                        line=line_no,
                        column=col_no,
                        line_text=line_text,
                        description=(
                            "Expected ')' to close function call arguments."
                        ),
                    )
                self._advance()
                return ast.FuncCall(func=ident_tok.value, args=args)
            else:
                return ast.Name(name=ident_tok.value)

        line_no, col_no, line_text = self._line_info(tok.pos)
        raise TrineDSLParseError(
            error_type="Parsing Error",
            error_statement="Unexpected Token in Expression",
            line=line_no,
            column=col_no,
            line_text=line_text,
            description=(
                f"Unexpected token '{tok.value}' ({tok.kind}) in expression."
            ),
        )


def parse_program(src: str) -> ast.Program:
    tokens = tokenize(src)
    parser = Parser(tokens, src)
    return parser.parse_program()
