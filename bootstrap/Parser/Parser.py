from Lexer.Token import (
    BRACKETS,
    KEYWORDS,
    Token,
    TokenType,
)
from Logging import Printer
from Logging.ParserLogger import ParserLogger
from Parser.AST import ASTNode, Statements
from Parser.StatementHandler import StatementHandler
from Parser.TokenHandler import TokenHandler


class Parser:
    def __init__(
        self, tokens: list, source_path: str, strict: bool = False, debug: bool = False
    ) -> None:
        self.debugging: bool = debug
        self.strict: bool = strict
        self.tokens: list = tokens
        self.source_path: str = source_path

        self.logger: ParserLogger = ParserLogger(self.source_path)

        self.token_handler: TokenHandler = TokenHandler(self.tokens, self.logger)

        self.statement_handler: StatementHandler = StatementHandler(
            self.token_handler, self.logger
        )

        self.statements: list[ASTNode] = []
        self.AST: ASTNode = Statements(self.statements)

    def print_ast(self, as_json: bool = False) -> None:
        Printer.print_data(self.AST, as_json, "PARSER AST")

    def parse(self, tokens: list[Token] | None = None) -> ASTNode:
        if tokens:
            self.tokens = tokens
            self.token_handler.tokens = self.tokens

        while not self.token_handler.at_end():
            try:
                statement: ASTNode | None = self.statement_handler.statement()

                if statement:
                    # print(f"DEBUG: Parsed {statement.__class__.__name__} at line {getattr(statement, 'line', '?')}")
                    self.statements.append(statement)

            except Exception as error:
                self.logger.print_errors()

                if self.strict:
                    raise error
                else:
                    self.recover()

        return self.AST

    def recover(self) -> None:
        self.token_handler.advance()

        while not self.token_handler.at_end():
            if self.token_handler.check_types(
                BRACKETS
            ) or self.token_handler.check_types(KEYWORDS):
                break
            else:
                self.token_handler.advance()
                continue
            break
