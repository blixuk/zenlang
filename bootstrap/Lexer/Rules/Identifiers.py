from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Identifiers:
    def make_identifier(self) -> None:
        identifier: str = ""
        identifier_type: TokenType
        start_line: int = self.line_number
        start_column: int = self.column_number

        while (character := self.peek()) and (character.isalnum() or character == "_"):
            identifier += self.advance()

        if self.peek() == "`":
            self.make_string(prefix=identifier)
            return

        identifier_type = IDENTIFIER_MAP.get(identifier, TokenType.IDENTIFIER)

        self.add_token(
            identifier_type,
            identifier,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )
