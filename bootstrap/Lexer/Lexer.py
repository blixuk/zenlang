from tokenize import TokenError
from typing import Any

from Lexer.Token import (
    ASSIGNMENTS,
    BRACKETS,
    COMPARATORS,
    KEYWORDS,
    LITERALS,
    LOGICALS,
    OPERATORS,
    TYPES,
    Token,
    TokenType,
)
from Logging import Printer
from Logging.LexerLogger import LexerLogger

from Lexer.Rules import Comments, Identifiers, Numbers, Strings, Operators, Symbols

class Lexer(Comments, Identifiers, Numbers, Strings, Operators, Symbols):
    def __init__(
        self,
        source: str,
        source_path: str | None = None,
        strict: bool = False,
        debug: bool = False,
    ):
        self.debugging: bool = debug
        self.strict: bool = strict

        self.source_path: str | None = source_path
        self.source: str = source
        self.current_position: int = 0
        self.line_number: int = 1
        self.column_number: int = 1

        self.tokens: list = []

        self.logger: LexerLogger = LexerLogger(self.source_path)

        self.char_dispatch: dict = {}
        self._build_dispatch_table()

    def _build_dispatch_table(self):
        import string

        self.char_dispatch = {
            "`": self.make_string,
            "\"": self.make_string,
            ":": self.make_type,
            ",": self.make_comma,
            ".": self.make_dot,
            "?": self.make_check_symbol,
            "^": self._dispatch_caret,
            "&": self.make_operator,
            "|": self.make_operator,
            "!": self._dispatch_bang,
            "%": self.make_operator,
            "/": self._dispatch_slash,
            "<": self._dispatch_less_than,
            ">": self._dispatch_greater_than,
            "-": self._dispatch_minus,
            "'": self.make_rune,
            "~": self.make_operator,
            "*": self.make_operator,
        }

        for c in string.ascii_letters + "_":
            self.char_dispatch[c] = self.make_identifier

        for c in string.digits:
            self.char_dispatch[c] = self.make_number

        for c in BRACKETS.keys():
            self.char_dispatch[c] = self.make_bracket

        for c in OPERATORS.keys():
            if c not in self.char_dispatch:
                self.char_dispatch[c] = self.make_operator

        for c in COMPARATORS.keys():
            if c not in self.char_dispatch:
                self.char_dispatch[c] = self.make_comparator

    def _dispatch_caret(self):
        if self.peek(1) in ["^", "="]:
            self.make_operator()
        else:
            self.make_raise_symbol()

    def _dispatch_bang(self):
        if self.peek(1) == "=":
            self.make_comparator()
        elif self.peek(1) in ["!", "|", "&", "^"]:
            self.make_operator()
        else:
            self.make_assert_symbol()

    def _dispatch_slash(self):
        if self.peek(1) in ["/", "*", "!"]:
            self.make_comment()
        else:
            self.make_operator()

    def _dispatch_less_than(self):
        if self.peek(1) == ":":
            self.make_type_cast()
        elif self.peek(1) == "-":
            self.make_return()
        elif self.peek(1) == "~":
            self.make_yield_arrow()
        elif self.peek(1) == "<":
            self.make_operator()
        else:
            self.make_comparator()

    def _dispatch_greater_than(self):
        if self.peek(1) == ">":
            self.make_operator()
        else:
            self.make_comparator()

    def _dispatch_minus(self):
        if self.peek(1) == ">":
            self.make_assignment()
        else:
            self.make_operator()


    def get_snippet(
        self, line: int | None = None, column: int | None = None, context: int = 0
    ) -> str:
        _line: int = line or self.line_number
        _column: int = column or self.column_number

        start: int = max(0, self.current_position - context)
        end: int = min(len(self.source), self.current_position)

        snippet: str = self.source[start:end].replace("\n", "").strip()

        return snippet

    def print_tokens(self, as_json: bool = False) -> None:
        Printer.print_data(self.tokens, as_json, "LEXER TOKENS")

    def peek(self, offset: int = 0) -> str | None:
        position: int = self.current_position + offset
        if position >= len(self.source):
            return None

        return self.source[position]

    def advance(self) -> str | None:
        character: str | None = self.peek()
        if character is None:
            return None

        self.current_position += 1

        if character == "\n":
            self.line_number += 1
            self.column_number = 1
        else:
            self.column_number += 1

        return character

    def tokenize(self, source: str | None = None) -> list:
        if source:
            self.source = source

        while (character := self.peek()) is not None:
            try:
                self.make_tokens()
            except Exception as error:
                self.logger.print_errors()

                if self.strict:
                    raise error
                else:
                    self.recover()

        self.add_token(
            TokenType.EOF,
            None,
            self.line_number,
            self.column_number,
            self.line_number,
            self.column_number,
        )
        return self.tokens

    def recover(self) -> None:
        self.advance()
        while (character := self.peek()) is not None:
            if character.isspace() or character in ["{", "}"]:
                self.advance()
            else:
                break

    def add_token(
        self,
        type: TokenType,
        value: Any,
        line: int | None = None,
        column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
        message: str | None = None,
    ) -> Token:
        token: Token = Token(type, value, line, column, end_line, end_column, message)
        self.tokens.append(token)

        self.logger.debug("Token", token)

        return token

    def make_tokens(self) -> None:
        character: str | None = self.peek()

        if character is None:
            return

        if character.isspace():
            self.advance()
            return

        handler = self.char_dispatch.get(character)

        if handler:
            handler()
        else:
            start_line: int = self.line_number
            start_column: int = self.column_number
            self.logger.error_token(
                TokenType.ERROR_UNEXPECTED_CHARACTER.name,
                start_line,
                start_column,
                character,
            )
            self.add_token(
                TokenType.ERROR_UNEXPECTED_CHARACTER,
                character,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            raise TokenError

