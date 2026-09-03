from Parser.AST import ASTNode
from Parser.Scope import ScopeManager
from Parser.TokenHandler import TokenHandler
from Logging.ParserLogger import ParserLogger

from Parser.Rules.Expressions.Operations import OperationsParserMixin
from Parser.Rules.Expressions.ControlFlow import ControlFlowExpressionsMixin
from Parser.Rules.Expressions.Complex import ComplexExpressionsMixin
from Parser.Rules.Expressions.ParsingHelpers import ParsingHelpersMixin
from Parser.Rules.Expressions.Primary import PrimaryExpressionsMixin

class ExpressionHandler(
    OperationsParserMixin,
    ControlFlowExpressionsMixin,
    ComplexExpressionsMixin,
    ParsingHelpersMixin,
    PrimaryExpressionsMixin
):
    def __init__(
        self,
        token_handler: TokenHandler,
        scope_manager: ScopeManager,
        logger: ParserLogger,
        statement_handler,
    ) -> None:
        self.token_handler: TokenHandler = token_handler
        self.scope_manager: ScopeManager = scope_manager
        self.logger: ParserLogger = logger
        self.statement_handler = statement_handler

    def expression(self, allow_instantiation: bool = True) -> ASTNode:
        self.logger.debug("expression")
        return self.pipeline(allow_instantiation=allow_instantiation)

    def pipeline(self, allow_instantiation: bool = True) -> ASTNode:
        from Lexer.Token import TokenType
        from Parser.AST import CallExpression
        node: ASTNode = self.conditional(allow_instantiation=allow_instantiation)
        while self.token_handler.match_type(TokenType.PIPELINE):
            op_tok = self.token_handler.previous()
            right = self.call(allow_instantiation=allow_instantiation)
            if isinstance(right, CallExpression):
                right.arguments.insert(0, node)
                node = right
            else:
                line = getattr(right, "line", getattr(op_tok, "line", 0))
                col = getattr(right, "column", getattr(op_tok, "column", 0))
                node = CallExpression(line, col, self.scope_manager.get_scope_level("global"), right, [node])
        return node
