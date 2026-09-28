from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Numbers:
    def make_number(self) -> None:
        number: str = ""
        dot_count: int = 0
        start_line: int = self.line_number
        start_column: int = self.column_number

        if self.peek() == "0" and self.peek(1) in ["x", "X"]:
            number += self.advance() # '0'
            number += self.advance() # 'x'
            while (character := self.peek()) is not None:
                if character.isdigit() or (character.lower() in "abcdef"):
                    number += self.advance()
                elif character == "_":
                    self.advance()
                else:
                    break
            self.add_token(
                TokenType.INTEGER,
                int(number, 16),
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            return

        if self.peek() == "0" and self.peek(1) in ["b", "B"]:
            number += self.advance() # '0'
            number += self.advance() # 'b'
            while (character := self.peek()) is not None:
                if character in ["0", "1"]:
                    number += self.advance()
                elif character == "_":
                    self.advance()
                else:
                    break
            self.add_token(
                TokenType.INTEGER,
                int(number, 2),
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            return

        if self.peek() == "0" and self.peek(1) in ["o", "O"]:
            number += self.advance() # '0'
            number += self.advance() # 'o'
            while (character := self.peek()) is not None:
                if character in "01234567":
                    number += self.advance()
                elif character == "_":
                    self.advance()
                else:
                    break
            self.add_token(
                TokenType.INTEGER,
                int(number, 8),
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            return

        if self.peek() == "0" and self.peek(1) is not None and self.peek(1).isdigit():
            while (character := self.peek()) is not None and (character.isdigit() or character == "_"):
                number += self.advance()
            snippet: str = self.get_snippet(start_line, start_column, int(self.column_number - start_column))
            self.add_token(
                TokenType.ERROR_INVALID_NUMBER,
                snippet,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            raise self.logger.error_token(
                TokenType.ERROR_INVALID_NUMBER.name,
                start_line,
                start_column,
                "Leading zeros are not permitted in decimal literals; use 0o prefix for octal",
            )

        while (character := self.peek()) is not None:

            if character.isdigit():
                number += self.advance()
            elif character == "_":
                self.advance()
                continue
            elif character == ".":
                # Check for range operator '..'
                if self.peek(1) == "." or not self.peek(1).isdigit():
                    break
                
                number += self.advance()
                dot_count += 1
                if dot_count > 1:
                    snippet: str = self.get_snippet(
                        start_line, start_column, int(self.column_number - start_column)
                    )
                    self.add_token(
                        TokenType.ERROR_INVALID_NUMBER,
                        snippet,
                        start_line,
                        start_column,
                        self.line_number,
                        self.column_number,
                    )
                    raise self.logger.error_token(
                        TokenType.ERROR_INVALID_NUMBER.name,
                        start_line,
                        start_column,
                        snippet,
                    )
            else:
                break

        if dot_count == 1:
            self.add_token(
                TokenType.DECIMAL,
                float(number),
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
        elif dot_count == 0:
            self.add_token(
                TokenType.INTEGER,
                int(number),
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
