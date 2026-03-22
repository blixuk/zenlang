import sys
#sys.tracebacklimit = 0

from Lexer.Token import Token
from Parser.AST import ASTNode

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

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int, context: str = None):
        self.message: str = message
        self.line: int = line
        self.column: int = column
        self.context: str = context
        super().__init__(self.__str__())

    def __str__(self) -> str:
        location: str = f"Line: {YELLOW}{self.line}{RESET}, Column: {YELLOW}{self.column}{RESET}"

        if self.context:
            return f"[Lexer] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET} ({location})\n    {YELLOW}Context: {self.context}{RESET}"
        else:
            return f"[Lexer] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET} ({location})"

class LexerDebug(Exception):
    def __init__(self, message: str, line: int = None, column: int = None, context: str = None):
        self.message: str = message
        self.line: int = line
        self.column: int = column
        self.context: str = context
        super().__init__(self.__str__())

    def __str__(self) -> str:
        location: str = ""
        if self.line and self.column:
            location: str = f"(Line: {YELLOW}{self.line}{RESET}, Column: {YELLOW}{self.column}{RESET})"
            
        if self.context:
            return f"[Lexer] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET} {location}\n    {GREEN}Context: {self.context}{RESET}"
        else:
            return f"[Lexer] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET} {location}"

class ParserError(Exception):
    def __init__(self, message: str, token: Token = None):
        self.message: str = message
        self.token: Token = token
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        if self.token:
            return f"[Parser] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}\n    {WHITE}Token: {self.token}{RESET}"
        else:
            return f"[Parser] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"

class ParserDebug(Exception):
    def __init__(self, message: str, token: str = None):
        self.message: str = message
        self.token: str = token
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        if self.token:
            return f"[Parser] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}\n    Token: {YELLOW}{self.token}{RESET}"
        else:
            return f"[Parser] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}"

class TypeCheckerError(Exception):
    def __init__(self, message: str, node: ASTNode = None):
        self.message: str = message
        self.node: str = node
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        if self.node:
            return f"[TypeChecker] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}\n    {WHITE}AST Node: {self.node}{RESET}"
        else:
            return f"[TypeChecker] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"

class TypeCheckerDebug(Exception):
    def __init__(self, message: str, node: ASTNode = None):
        self.message: str = message
        self.node: str = node
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        if self.node:
            return f"[TypeChecker] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}\n    AST Node: {YELLOW}{self.node}{RESET}"
        else:
            return f"[TypeChecker] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}"

class InterpreterError(Exception):
    def __init__(self, message: str):
        self.message: str = message
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"[Interpreter] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"

# RuntimeError

