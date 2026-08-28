from Lexer.Token import Token
from Parser.Scope import ScopeManager
from Parser.TokenHandler import TokenHandler
from Logging.ParserLogger import ParserLogger

class ParseContext:
    def __init__(self, token_handler: TokenHandler, logger: ParserLogger, filename: str = None) -> None:
        self.token_handler: TokenHandler = token_handler
        self.logger: ParserLogger = logger
        self.filename: str | None = filename
        self.scope_manager: ScopeManager = ScopeManager()

    def enter_scope(self, scope_type: str) -> None:
        self.scope_manager.enter(scope_type)

    def exit_scope(self, scope_type: str) -> None:
        self.scope_manager.exit(scope_type)
