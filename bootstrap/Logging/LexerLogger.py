from typing import Any

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
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
        if self.attachment:
            return f"""[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}
    {YELLOW}'{self.attachment.type}': {self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"


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
        if self.snippet:
            return f"""[{self.name}] [{RED}TokenError{RESET}] {YELLOW}{self.message}{RESET}
    {YELLOW}'{self.snippet}' at Line: {self.line}, Column: {self.column}{RESET}
{WHITE}{self.source_path}:{self.line}:{self.column}{RESET}"""
        else:
            return (
                f"[{self.name}] [{RED}TokenError{RESET}] {YELLOW}{self.message}{RESET}"
            )


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

