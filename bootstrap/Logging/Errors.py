import sys
from typing import Optional
from Lexer.Token import Token
from Parser.AST import ASTNode
from Logging.Diagnostic import Diagnostic, Span, DiagnosticSeverity

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
BOLD = "\033[1m"
RESET = "\033[0m"

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int, context: str = None, file_path: str = None):
        self.message: str = message
        self.line: int = line
        self.column: int = column
        self.context: str = context
        self.file_path: str = file_path or "unknown"
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = Span(self.file_path, self.line, self.column, len(self.context) if self.context else 1, label=self.context)
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="LexerError", span=span)
        return diag.render()

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
            location = f"(Line: {YELLOW}{self.line}{RESET}, Column: {YELLOW}{self.column}{RESET})"
        if self.context:
            return f"[Lexer] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET} {location}\n    {GREEN}Context: {self.context}{RESET}"
        else:
            return f"[Lexer] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET} {location}"

class ParserError(Exception):
    def __init__(self, message: str, token: Token = None, file_path: str = None):
        self.message: str = message
        self.token: Token = token
        self.file_path: str = file_path
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        span = Span.from_token(self.token, self.file_path) if self.token else None
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="SyntaxError", span=span)
        return diag.render()

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
    def __init__(self, message: str, node: ASTNode = None, file_path: str = None):
        self.message: str = message
        self.node: ASTNode = node
        self.file_path: str = file_path
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        span = Span.from_node(self.node, self.file_path) if self.node else None
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="TypeCheck", span=span)
        return diag.render()

class TypeCheckerDebug(Exception):
    def __init__(self, message: str, node: ASTNode = None):
        self.message: str = message
        self.node: ASTNode = node
        super().__init__(self.__str__())

    def __str__(self) -> str:            
        if self.node:
            return f"[TypeChecker] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}\n    AST Node: {YELLOW}{self.node}{RESET}"
        else:
            return f"[TypeChecker] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}"

class InterpreterError(Exception):
    def __init__(self, message: str, node: ASTNode = None, file_path: str = None):
        self.message: str = message
        self.node: ASTNode = node
        self.file_path: str = file_path
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = Span.from_node(self.node, self.file_path) if self.node else None
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="RuntimeError", span=span)
        return diag.render()

# RuntimeError

