from typing import Any
from Logging.Diagnostic import Diagnostic, Span, DiagnosticSeverity

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
BOLD = "\033[1m"
RESET = "\033[0m"


class Debug(Exception):
    def __init__(
        self, name: str, source_path: str | None, message: str, attachment: Any = None
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: str = attachment

        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"[{self.name}] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}\n    Attachment: {YELLOW}{self.attachment}{RESET}"
        else:
            return f"[{self.name}] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}"


class Error(Exception):
    def __init__(
        self, name: str, source_path: str | None, message: str, attachment: Any = None
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: Any = attachment

        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.attachment:
            span = Span.from_token(self.attachment, self.source_path)
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="SyntaxError", span=span)
        return diag.render()


class ExpectTokenError(Exception):
    def __init__(
        self, name: str, source_path: str | None, message: str, attachment: Any = None
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: Any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.attachment:
            span = Span.from_token(self.attachment, self.source_path, label="unexpected token here")
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="E0001: ExpectedToken", span=span)
        return diag.render()


class ExpectTokenValueError(Exception):
    def __init__(
        self, name: str, source_path: str | None, message: str, attachment: Any = None
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: Any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.attachment:
            span = Span.from_token(self.attachment, self.source_path, label="unexpected value")
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="E0002: ExpectedTokenValue", span=span)
        return diag.render()


class TokenError(Exception):
    def __init__(
        self, name: str, source_path: str | None, message: str, attachment: Any = None
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: Any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.attachment:
            span = Span.from_token(self.attachment, self.source_path)
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="SyntaxError", span=span)
        return diag.render()


class ParserLogger:
    def __init__(self, source_path: str | None = None, enabled: bool = False):
        self.name: str = "Parser"
        self.source_path: str | None = source_path
        self.enabled: bool = enabled
        self.debugs: list[Debug] = []
        self.errors: list[
            Error | TokenError | ExpectTokenError | ExpectTokenValueError
        ] = []

    def debug(self, message: str, attachment: Any = None):
        if self.enabled:
            self.debugs.append(Debug(self.name, self.source_path, message, attachment))

    def print_debugs(self):
        for debug in self.debugs:
            print(debug)

    def error(self, message: str, attachment: Any = None):
        error: Error = Error(self.name, self.source_path, message, attachment)
        self.errors.append(error)
        return error

    def error_expect_token(self, message: str, attachment: Any = None):
        error: ExpectTokenError = ExpectTokenError(
            self.name, self.source_path, message, attachment
        )
        self.errors.append(error)
        return error

    def error_expect_token_value(self, message: str, attachment: Any = None):
        error: ExpectTokenValueError = ExpectTokenValueError(
            self.name, self.source_path, message, attachment
        )
        self.errors.append(error)
        return error

    def error_token(self, message: str, attachment: Any = None):
        error: TokenError = TokenError(self.name, self.source_path, message, attachment)
        self.errors.append(error)
        return error

    def print_errors(self):
        for error in self.errors:
            print(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

