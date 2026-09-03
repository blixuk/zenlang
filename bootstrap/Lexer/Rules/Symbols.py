from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Symbols:
    def make_bracket(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number
        bracket: str | None = self.advance()
        bracket_type: TokenType = BRACKETS[bracket]

        self.add_token(
            bracket_type,
            bracket,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_assignment(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.advance()
        self.add_token(
            TokenType.ASSIGNMENT,
            "assign",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_type(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()

        if self.peek() == ">":
            self.advance()
            self.add_token(
                TokenType.TYPE_LET,
                ":>",
                self.line_number,
                self.column_number,
                start_line,
                start_column,
            )
        else:
            self.add_token(
                TokenType.TYPE_SET,
                ":",
                self.line_number,
                self.column_number,
                start_line,
                start_column,
            )

    def make_comma(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.add_token(
            TokenType.COMMA,
            ",",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_dot(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        if self.peek() == ".":
            self.advance()
            if self.peek() == ".":
                # `...` full inclusive range or ellipsis
                self.advance()
                self.add_token(
                    TokenType.RANGE_FULL_INCLUSIVE,
                    "...",
                    start_line,
                    start_column,
                    self.line_number,
                    self.column_number,
                )
            elif self.peek() == "+":
                # `..+` inclusive end range
                self.advance()
                self.add_token(
                    TokenType.RANGE_INCLUSIVE_END,
                    "..+",
                    start_line,
                    start_column,
                    self.line_number,
                    self.column_number,
                )
            elif self.peek() == "-":
                # `..-` exclusive end range
                self.advance()
                self.add_token(
                    TokenType.RANGE_EXCLUSIVE_END,
                    "..-",
                    start_line,
                    start_column,
                    self.line_number,
                    self.column_number,
                )
            else:
                self.add_token(
                    TokenType.RANGE,
                    "..",
                    start_line,
                    start_column,
                    self.line_number,
                    self.column_number,
                )
        else:
            self.add_token(
                TokenType.DOT,
                ".",
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )

    def make_return(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.advance()
        self.add_token(
            TokenType.RETURN,
            "<-",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_yield_arrow(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.advance()
        self.add_token(
            TokenType.YIELD_ARROW,
            "<~",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )


    def make_type_cast(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.advance()
        self.add_token(
            TokenType.TYPE_CAST,
            "<:",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_check_symbol(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        if self.peek() == "?":
            self.advance()
            self.add_token(
                TokenType.COALESCE,
                "??",
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            return

        self.add_token(
            TokenType.CHECK_SYMBOL,
            "?",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_raise_symbol(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.add_token(
            TokenType.RAISE_SYMBOL,
            "^",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_assert_symbol(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
        self.add_token(
            TokenType.ASSERT_SYMBOL,
            "!",
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )
