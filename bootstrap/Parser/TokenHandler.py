from typing import Any

from Lexer.Token import Token, TokenType
from Logging.ParserLogger import ParserLogger


class TokenHandler:
    def __init__(self, tokens: list, logger: ParserLogger) -> None:
        self.tokens: list = [t for t in tokens if t.type != TokenType.COMMENT]
        self.current_token: int = 0

        self.logger: ParserLogger = logger

    def peek(self, offset: int = 0) -> Token | None:
        position: int = self.current_token + offset

        if position >= len(self.tokens):
            return None

        return self.tokens[position]

    def previous(self, offset: int = 1) -> Token | None:
        position: int = self.current_token - offset

        if self.current_token == 0:
            return None

        return self.tokens[position]

    def advance(self) -> Token | None:
        token: Token | None = self.peek()

        if token is not None:
            self.current_token += 1

        return token

    def match_type(self, type: TokenType, offset: int = 0) -> Token | None:
        token: Token | None = self.peek(offset)

        self.logger.debug("match", token)

        if token and (token.type == type or token.type.value == type.value):
            return self.advance()

        return None

    def match_value(self, value: Any, offset: int = 0) -> Token | None:
        token: Token | None = self.peek(offset)

        self.logger.debug("match", token)

        if token and token.value == value:
            return self.advance()

        return None

    def match_type_value(
        self, type: TokenType, value: str, offset: int = 0
    ) -> Token | None:
        token: Token | None = self.peek(offset)

        self.logger.debug("match_type_value", token)

        if token and token.type == type and token.value == value:
            return self.advance()

        return None

    def match_types(self, types: list | dict, offset: int = 0) -> Token | None:
        token: Token | None = self.peek(offset)

        self.logger.debug("match_types", token)

        if token and token.type in types:
            return self.advance()

        return None

    def match_values(self, values: list | dict, offset: int = 0) -> Token | None:
        token: Token | None = self.peek(offset)

        self.logger.debug("match_values", token)

        if token and token.value in values:
            return self.advance()

        return None

    def check_type(self, type: TokenType, offset: int = 0) -> bool:
        token: Token | None = self.peek(offset)

        self.logger.debug("check", token)

        return token is not None and token.type == type

    def check_value(self, value: Any, offset: int = 0) -> bool:
        token: Token | None = self.peek(offset)

        self.logger.debug("check_value", token)

        return token is not None and token.value == value

    def check_type_value(self, type: TokenType, value: str, offset: int = 0) -> bool:
        token: Token | None = self.peek(offset)

        self.logger.debug("check_type_value", token)

        return token is not None and token.type == type and token.value == value

    def check_types(self, types: list | dict, offset: int = 0) -> bool:
        token: Token | None = self.peek(offset)

        self.logger.debug("check_types", token)

        return token is not None and token.type in types

    def check_values(self, values: list | dict, offset: int = 0) -> bool:
        token: Token | None = self.peek(offset)

        self.logger.debug("check_values", token)

        return token is not None and token.value in values

    def expect_type(self, type: TokenType, message: str) -> Token | None:
        previous_token: Token | None = self.previous()
        token: Token | None = self.peek()

        self.logger.debug("expect_type", token)

        if token and token.type == type:
            return self.advance()

        raise self.logger.error_expect_token(message, previous_token)

    def expect_types(self, types: list, message: str) -> Token | None:
        previous_token: Token | None = self.previous()
        token: Token | None = self.peek()

        self.logger.debug("expect_types", token)

        if token and token.type in types:
            return self.advance()

        raise self.logger.error_expect_token(message, previous_token)

    def expect_value(self, value: Any, message: str) -> Token | None:
        token: Token | None = self.peek()

        self.logger.debug("expect_value", token)

        if token and token.value == value:
            return self.advance()

        raise self.logger.error_expect_token(message, token)

    def expect_type_value(
        self, type: TokenType, value: str, message: str
    ) -> Token | None:
        token: Token | None = self.peek()

        self.logger.debug("expect_type_value", token)

        if token and token.type == type and token.value == value:
            return self.advance()

        raise self.logger.error_expect_token_value(message, token)

    def expect_type_values(
        self, type: TokenType, values: list | dict, message: str
    ) -> Token | None:
        token: Token | None = self.peek()

        self.logger.debug("expect_type_values", token)

        if token and token.type == type and token.value in values:
            return self.advance()

        raise self.logger.error_expect_token_value(message, token)

    def at_end(self) -> bool | None:
        token: Token | None = self.peek()
        res = token is None or token.type == TokenType.EOF
        from Logging.Trace import zen_trace
        zen_trace(f"AT_END: {res} (peek={token})")
        return res
