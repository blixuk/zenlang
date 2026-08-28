from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Comments:
    def make_comment(self) -> None:
        comment: str = ""
        start_line: int = self.line_number
        start_column: int = self.column_number

        if self.peek() == "/" and self.peek(1) == "/":
            self.advance()
            self.advance()

            while (character := self.peek()) and character != "\n":
                comment += character
                self.advance()
            
            token_type = TokenType.COMMENT

        elif self.peek() == "/" and self.peek(1) == "*":
            self.advance()
            self.advance()

            while (character := self.peek()) and not (
                character == "*" and self.peek(1) == "/"
            ):
                comment += character
                self.advance()

            self.advance()
            self.advance()
            
            token_type = TokenType.COMMENT

        elif self.peek() == "/" and self.peek(1) == "!":
            self.advance()
            self.advance()

            while (character := self.peek()) and not (
                character == "!" and self.peek(1) == "/"
            ):
                comment += character
                self.advance()

            self.advance()
            self.advance()
            
            token_type = TokenType.DOC_COMMENT

        else:
            self.make_operator()
            return

        self.add_token(
            token_type,
            comment,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )
