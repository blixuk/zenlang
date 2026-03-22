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


class Lexer:
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

        if character and character.isspace():
            self.advance()
            return

        if (
            character
            and character == "/"
            and (self.peek(1) == "/" or self.peek(1) == "*")
        ):
            self.make_comment()
            return

        if character:
            start_line: int = self.line_number
            start_column: int = self.column_number

            if character == "`":
                self.make_string()

            elif character.isalpha() or character == "_":
                self.make_identifier()

            elif character.isdigit():
                self.make_number()

            elif character in BRACKETS.keys():
                self.make_bracket()

            elif character == "-" and self.peek(1) == ">":
                self.make_assignment()

            elif character == "<" and self.peek(1) == "-":
                self.make_return()

            elif character == ":":
                self.make_type()

            elif character == ",":
                self.make_comma()

            elif character == ".":
                self.make_dot()

            elif character == "?":
                self.make_check_symbol()

            elif character == "^":
                if self.peek(1) in ["^", "="]:
                    self.make_operator()
                else:
                    self.make_raise_symbol()

            elif character == "&":
                self.make_operator()

            elif character == "|":
                self.make_operator()

            elif character == "!":
                if self.peek(1) == "=":
                    self.make_comparator()
                elif self.peek(1) in ["!", "|", "&", "^"]:
                    self.make_operator()
                else:
                    self.make_assert_symbol()

            elif character == "%":
                self.make_operator()

            elif character == "/":
                if self.peek(1) in ["/", "*"]:
                    self.make_comment()
                else:
                    self.make_operator()

            elif character == "<":
                if self.peek(1) == "-":
                    self.make_return()
                elif self.peek(1) == "<":
                    self.make_operator()
                else:
                    self.make_comparator()

            elif character == ">":
                if self.peek(1) == ">":
                    self.make_operator()
                else:
                    self.make_comparator()

            elif character in OPERATORS.keys() or character == "~" or (character == "*" and self.peek(1) == "*"):
                self.make_operator()

            elif character in COMPARATORS.keys():
                self.make_comparator()

            elif character == "'":
                self.make_rune()

            else:
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

        else:
            self.make_operator()
            return

        self.add_token(
            TokenType.COMMENT,
            comment,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_identifier(self) -> None:
        identifier: str = ""
        identifier_type: TokenType
        start_line: int = self.line_number
        start_column: int = self.column_number

        while (character := self.peek()) and (character.isalnum() or character == "_"):
            identifier += self.advance()

        if identifier in TYPES:
            identifier_type = TokenType.TYPE
        
        elif identifier in ASSIGNMENTS:
            identifier_type = ASSIGNMENTS[identifier]

        elif identifier in LITERALS.keys():
            identifier_type = LITERALS[identifier]

        elif identifier in LOGICALS:
            identifier_type = LOGICALS[identifier]

        elif self.peek() == "`":
            self.make_string(prefix=identifier)
            return

        elif identifier in TYPES:
            identifier_type = TokenType.TYPE

        elif identifier in KEYWORDS:
            identifier_type = TokenType.KEYWORD

        else:
            identifier_type = TokenType.IDENTIFIER

        self.add_token(
            identifier_type,
            identifier,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_number(self) -> None:
        number: str = ""
        dot_count: int = 0
        start_line: int = self.line_number
        start_column: int = self.column_number
        separators: list[str] = [".", "_"]

        while (character := self.peek()) and (
            character.isdigit() or character in separators
        ):
            number += self.advance()

            if character == ".":
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
            elif character == "_":
                continue

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

    def make_string(self, prefix: str | None = None) -> None:
        string: str = ""
        start_line: int = self.line_number
        start_column: int = self.column_number
        quote: str | None = self.advance()

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

        if len(string) == 1:
            self.add_token(
                TokenType.RUNE,
                string,
                start_line,
                start_column,
                self.line_number,
                self.column_number,
            )
            if prefix:
                self.tokens[-1].prefix = prefix
        else:
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

    def make_operator(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number
        operator: str | None = self.advance()
        operator_type: TokenType

        if operator == "*" and self.peek() == "*":
            operator += self.advance()
            operator_type = TokenType.EXPONENTIATION

        elif operator == "+" and self.peek() == "+":
            operator += self.advance()
            operator_type = TokenType.INCREMENT

        elif operator == "-" and self.peek() == "-":
            operator += self.advance()
            operator_type = TokenType.DECREMENT

        elif operator == "&" and self.peek() == "&":
            operator += self.advance()
            operator_type = TokenType.BITWISE_AND

        elif operator == "|" and self.peek() == "|":
            operator += self.advance()
            operator_type = TokenType.BITWISE_OR

        elif operator == "!" and self.peek() == "!":
            operator += self.advance()
            operator_type = TokenType.BITWISE_NOT

        elif operator == "^" and self.peek() == "^":
            operator += self.advance()
            operator_type = TokenType.BITWISE_XOR

        elif operator == "!" and self.peek() == "|":
            operator += self.advance()
            operator_type = TokenType.BITWISE_NOR

        elif operator == "!" and self.peek() == "&":
            operator += self.advance()
            operator_type = TokenType.BITWISE_NAND

        elif operator == "!" and self.peek() == "^":
            operator += self.advance()
            operator_type = TokenType.BITWISE_XNOR

        elif operator == "%" and self.peek() == "%":
            operator += self.advance()
            operator_type = TokenType.BITWISE_MOD

        elif operator == "<" and self.peek() == "<":
            operator += self.advance()
            if self.peek() == "=":
                operator += self.advance()
                operator_type = TokenType.LEFT_SHIFT_EQUAL
            else:
                operator_type = TokenType.BITWISE_LEFT_SHIFT

        elif operator == ">" and self.peek() == ">":
            operator += self.advance()
            if self.peek() == "=":
                operator += self.advance()
                operator_type = TokenType.RIGHT_SHIFT_EQUAL
            else:
                operator_type = TokenType.BITWISE_RIGHT_SHIFT


        elif operator == "&" and self.peek() == "=":
            operator += self.advance()
            operator_type = TokenType.AND_EQUAL

        elif operator == "|" and self.peek() == "=":
            operator += self.advance()
            operator_type = TokenType.OR_EQUAL

        elif operator == "^" and self.peek() == "=":
            operator += self.advance()
            operator_type = TokenType.XOR_EQUAL

        elif operator == "%" and self.peek() == "=":
            operator += self.advance()
            operator_type = TokenType.MOD_EQUAL
        else:
            operator_type = OPERATORS[operator]

        self.add_token(
            operator_type,
            operator,
            start_line,
            start_column,
            self.line_number,
            self.column_number,
        )

    def make_comparator(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number
        comparator: str | None = self.advance()
        comparator_type: TokenType

        if comparator == "=" and self.peek() == "=":
            comparator += self.advance()
            comparator_type = TokenType.EQUAL
        elif comparator == "!" and self.peek() == "=":
            comparator += self.advance()
            comparator_type = TokenType.NOT_EQUAL
        elif comparator == ">" and self.peek() == "=":
            comparator += self.advance()
            comparator_type = TokenType.GREATER_THAN_OR_EQUAL
        elif comparator == "<" and self.peek() == "=":
            comparator += self.advance()
            comparator_type = TokenType.LESS_THAN_OR_EQUAL
        else:
            comparator_type = COMPARATORS[comparator]

        self.add_token(
            comparator_type,
            comparator,
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

    def make_check_symbol(self) -> None:
        start_line: int = self.line_number
        start_column: int = self.column_number

        self.advance()
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
