from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Strings:
    def make_string(self, prefix: str | None = None) -> None:
        string: str = ""
        start_line: int = self.line_number
        start_column: int = self.column_number
        quote: str | None = self.advance()

        if quote == "`" and self.peek() == "`" and self.peek(1) == "`":
            self.advance() # 2nd `
            self.advance() # 3rd `
            while (character := self.peek()) is not None:
                if character == "`" and self.peek(1) == "`" and self.peek(2) == "`":
                    break
                string += self.advance()

            if self.peek() is None:
                snippet = self.get_snippet(
                    start_line, start_column, int(self.column_number - start_column)
                )
                self.add_token(
                    TokenType.ERROR_UNTERMINATED_STRING_EOF,
                    snippet,
                    start_line,
                    start_column,
                    self.line_number,
                    self.column_number,
                )
                raise self.logger.error_token(
                    TokenType.ERROR_UNTERMINATED_STRING_EOF.name,
                    start_line,
                    start_column,
                    snippet,
                )

            self.advance()
            self.advance()
            self.advance()
            self.add_token(
                TokenType.STRING,
                string,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            if prefix:
                self.tokens[-1].prefix = prefix
            return

        while (character := self.peek()) and character != quote:
            if character == "\\":
                self.advance() # consume \
                next_char = self.peek()
                if next_char == "n":
                    string += "\n"
                    self.advance()
                elif next_char == "t":
                    string += "\t"
                    self.advance()
                elif next_char == "r":
                    string += "\r"
                    self.advance()
                elif next_char == "\\":
                    string += "\\"
                    self.advance()
                elif next_char == '"':
                    string += '"'
                    self.advance()
                elif next_char == "`":
                    string += "`"
                    self.advance()
                elif next_char == "e":
                    string += "\033"
                    self.advance()
                elif next_char == "x":
                    self.advance() # consume x
                    hex_digits = ""
                    if self.peek() and self.peek() in "0123456789abcdefABCDEF":
                        hex_digits += self.advance()
                        if self.peek() and self.peek() in "0123456789abcdefABCDEF":
                            hex_digits += self.advance()
                    if hex_digits:
                        string += chr(int(hex_digits, 16))
                    else:
                        string += "\\x"
                elif next_char == "0": # Support for \033
                    # Simplified octal/escape
                    esc_code = self.advance() # 0
                    if self.peek() == "3" and self.peek(1) == "3":
                        self.advance() # 3
                        self.advance() # 3
                        string += "\033"
                    else:
                        string += "\\" + esc_code
                else:
                    string += "\\"
            else:
                string += self.advance()

        if self.peek() is None:
            snippet = self.get_snippet(
                start_line, start_column, int(self.column_number - start_column)
            )
            self.add_token(
                TokenType.ERROR_UNTERMINATED_STRING_EOF,
                snippet,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            raise self.logger.error_token(
                TokenType.ERROR_UNTERMINATED_STRING_EOF.name,
                start_line,
                start_column,
                snippet,
            )

        self.advance()
        self.add_token(
            TokenType.STRING,
            string,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )
        if prefix:
            self.tokens[-1].prefix = prefix

    def make_rune(self) -> None:
        rune: str | None = ""
        start_line: int = self.line_number
        start_column: int = self.column_number
        quote: str | None = self.advance()
        snippet: str = ""

        rune = self.advance()

        if self.peek() == quote:
            self.advance()
            self.add_token(
                TokenType.RUNE,
                rune,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )

        elif self.peek() is None:
            snippet = self.get_snippet(
                start_line, start_column, int(self.column_number - start_column)
            )
            self.add_token(
                TokenType.ERROR_UNTERMINATED_CHARACTER_EOF,
                snippet,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            raise self.logger.error_token(
                TokenType.ERROR_UNTERMINATED_CHARACTER_EOF.name,
                start_line,
                start_column,
                snippet,
            )
        else:
            snippet = self.get_snippet(
                start_line, start_column, int(self.column_number - start_column)
            )
            self.add_token(
                TokenType.ERROR_UNTERMINATED_CHARACTER,
                snippet,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            raise self.logger.error_token(
                TokenType.ERROR_UNTERMINATED_CHARACTER.name,
                start_line,
                start_column,
                snippet,
            )
