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
        if self.attachment:
            return f"""[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}
    {WHITE}'{self.attachment.type}': {self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"


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
        if self.attachment:
            return f"""[{self.name}] [{RED}ExpectTokenError{RESET}] {YELLOW}{self.message}{RESET}
    {WHITE}Token: {self.attachment}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}ExpectTokenError{RESET}] {YELLOW}{self.message}{RESET}"


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
        if self.attachment:
            return f"""[{self.name}] [{RED}ExpectTokenValueError{RESET}] {YELLOW}{self.message}{RESET}
    {WHITE}Token: {self.attachment}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}ExpectTokenValueError{RESET}] {YELLOW}{self.message}{RESET}"


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
        if self.attachment:
            return f"""[{self.name}] [{RED}TokenError{RESET}] {YELLOW}{self.message}{RESET}
    {WHITE}'{self.attachment.value}' at {self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return (
                f"[{self.name}] [{RED}TokenError{RESET}] {YELLOW}{self.message}{RESET}"
            )


class ParserLogger:
    def __init__(self, source_path: str | None = None):
        self.name: str = "Parser"
        self.source_path: str | None = source_path
        self.debugs: list[Debug] = []
        self.errors: list[
            Error | TokenError | ExpectTokenError | ExpectTokenValueError
        ] = []

    def debug(self, message: str, attachment: Any = None):
        self.debugs.append(Debug(self.name, message, attachment))

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

