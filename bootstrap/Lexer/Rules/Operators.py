from tokenize import TokenError
from typing import Any
from Lexer.Token import *

class Operators:
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

        elif operator == "|" and self.peek() == ">":
            operator += self.advance()
            operator_type = TokenType.PIPELINE

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
