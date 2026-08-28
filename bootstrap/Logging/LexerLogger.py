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
        self,
        name: str,
        source_path: str | None,
        message: str,
        attachment: Any | None = None,
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.attachment: Any = attachment

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
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="LexerError", span=span)
        return diag.render()


class TokenError(Exception):
    def __init__(
        self,
        name: str,
        source_path: str | None,
        message: str,
        line: int | None = None,
        column: int | None = None,
        snippet: Any = None,
    ):
        self.name: str = name
        self.source_path: str | None = source_path
        self.message: str = message
        self.line: int | None = line
        self.column: int | None = column
        self.snippet: Any = snippet

        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.line is not None and self.column is not None:
            snippet_len = len(str(self.snippet)) if self.snippet else 1
            span = Span(self.source_path, self.line, self.column, snippet_len, label="syntax error here")
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="LexerTokenError", span=span)
        return diag.render()


class LexerLogger:
    def __init__(self, source_path: str | None = None):
        self.name: str = "Lexer"
        self.source_path: str | None = source_path
        self.debugs: list[Debug] = []
        self.errors: list[Error | TokenError] = []

    def debug(self, message: str, attachment: Any = None):
        self.debugs.append(Debug(self.name, self.source_path, message, attachment))

    def print_debugs(self):
        for debug in self.debugs:
            print(debug)

    def error(self, message: str, attachment: Any = None):
        error: Error = Error(self.name, self.source_path, message, attachment)
        self.errors.append(error)
        return error

    def error_token(
        self, message: str, line: int, column: int, snippet: Any | None = None
    ):
        error: TokenError = TokenError(
            self.name, self.source_path, message, line, column, snippet
        )
        self.errors.append(error)
        return error

    def print_errors(self):
        for error in self.errors:
            print(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

