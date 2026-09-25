from Checker.Type import (
    PRIMITIVE_TYPES,
    Type,
    TypeVariant,
    TypeVoid,
)
from Lexer.Token import (
    ERRORS,
    Token,
    TokenType,
)
from Logging.ParserLogger import ParserLogger
from Parser.AST import (
    ASTNode,
    BlockStatement,
    ExpressionStatement,
)
from Parser.ExpressionHandler import ExpressionHandler
from Parser.Scope import ScopeManager

# Import Mixins
from Parser.Rules.Statements.ControlFlow import ControlFlowParserMixin
from Parser.Rules.Statements.Declarations import DeclarationParserMixin
from Parser.Rules.Statements.Modules import ModuleParserMixin
from Parser.Rules.Statements.Errors import ErrorParserMixin
from Parser.Rules.Statements.Patterns import PatternParserMixin

class StatementHandler(
    ControlFlowParserMixin,
    DeclarationParserMixin,
    ModuleParserMixin,
    ErrorParserMixin,
    PatternParserMixin
):
    def __init__(self, token_handler, logger: ParserLogger, filename: str = None) -> None:
        self.token_handler = token_handler
        self.logger: ParserLogger = logger
        self.filename = filename
        self.scope_manager: ScopeManager = ScopeManager()
        self.expression_handler: ExpressionHandler = ExpressionHandler(
            self.token_handler, self.scope_manager, self.logger, self
        )
        self.keyword_parsers = {
            "let": self.assignment_statement,
            "set": self.assignment_statement,
            "function": self.function_statement,
            "structure": self.structure_statement,
            "enumerator": self.enumerator_statement,
            "return": self.return_statement,
            "when": self.when_statement,
            "class": self.class_statement,
            "do": self.do_statement,
            "break": self.break_statement,
            "continue": self.continue_statement,
            "while": self._dispatch_while,
            "for": self._dispatch_for,
            "until": self._dispatch_until,
            "import": self.import_statement,
            "use": self.import_statement,  # alias for import
            "from": self.from_import_statement,
            "extern": self.extern_statement,
            "scope": self.scope_statement,
            "defer": self.defer_statement,
            "raise": self.raise_statement,
            "assert": self.assert_statement,
            "check": self.check_statement,
            "object": self.object_statement,
            "export": self.export_statement,
            "with": self.with_statement,
            "task": self.task_statement,
        }

    def _dispatch_while(self) -> ASTNode:
        token = self.token_handler.advance()
        self.scope_manager.enter("loop")
        return self._do_while(token)

    def _dispatch_for(self) -> ASTNode:
        token = self.token_handler.advance()
        self.scope_manager.enter("loop")
        return self._do_for(token)

    def _dispatch_until(self) -> ASTNode:
        token = self.token_handler.advance()
        self.scope_manager.enter("loop")
        return self._do_until(token)

    def statement(self) -> ASTNode | None:
        try:
            from Logging.Trace import zen_trace
            zen_trace(f"STATEMENT_ENTRY: peek={self.token_handler.peek()}")
        except ImportError:
            pass
            
        # Capture documentation comment
        doc_comment = None
        if self.token_handler.check_type(TokenType.DOC_COMMENT):
            doc_token = self.token_handler.advance()
            doc_comment = doc_token.value
            while self.token_handler.check_type(TokenType.DOC_COMMENT):
                next_doc = self.token_handler.advance()
                doc_comment += "\n" + next_doc.value

        stmt = self._statement_internal()
        
        if stmt:
            if self.filename:
                stmt.filename = self.filename
            if doc_comment:
                stmt.doc_comment = doc_comment
        
        return stmt

    def _statement_internal(self) -> ASTNode | None:
        token: Token | None = self.token_handler.peek()
        self.logger.debug("statement")

        # errors
        if self.token_handler.match_types(ERRORS):
            token_type: TokenType = getattr(token, "type")
            raise self.logger.error_token(getattr(token_type, "name"), token)

        # comments
        if self.token_handler.check_type(TokenType.COMMENT):
            self.token_handler.advance()
            return None

        # Symbol Statements
        if self.token_handler.check_type(TokenType.CHECK_SYMBOL):
            return self.check_statement()
        if self.token_handler.check_type(TokenType.ASSERT_SYMBOL):
            return self.assert_statement()
        if self.token_handler.check_type(TokenType.EXTERN):
            return self.extern_statement()

        # Keyword Statements
        if self.token_handler.check_type(TokenType.KEYWORD):
            try:
                from Logging.Trace import zen_trace
                if self.token_handler.check_value("let"):
                     zen_trace(f"MATCHED 'let' at line {self.token_handler.peek().line}")
            except ImportError:
                pass
            
            value = getattr(token, "value", "")
            handler = self.keyword_parsers.get(value)
            if handler:
                return handler()

        # Variable, Member, or Index Reassignment
        if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.MULTIPLICATION]):
            is_reassign = False
            # Look ahead for '->' at current level
            depth = 0
            for i in range(self.token_handler.current_token + 1, len(self.token_handler.tokens)):
                t = self.token_handler.tokens[i]
                if t.type == TokenType.LEFT_PAREN and depth == 0:
                    break # Call expression, not reassignment
                
                if t.type in [TokenType.LEFT_BRACKET, TokenType.LEFT_PAREN, TokenType.LEFT_BRACE]:
                    depth += 1
                elif t.type in [TokenType.RIGHT_BRACKET, TokenType.RIGHT_PAREN, TokenType.RIGHT_BRACE]:
                    depth -= 1
                    if depth < 0: break
                elif t.type in [TokenType.ASSIGNMENT, TokenType.EQUAL] and depth == 0:
                    is_reassign = True
                    break
                elif t.type in [TokenType.SEMICOLON, TokenType.RETURN] and depth == 0:
                    break
                elif t.type == TokenType.KEYWORD and depth == 0 and t.value in ["let", "set", "function", "class", "structure", "enumerator", "do", "for", "while", "until", "if", "when", "return", "break", "continue", "import", "use", "export"]:
                    break # New statement starting
            
            if is_reassign:
                return self.reassignment_statement()

        # Scope Block
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            return self.block_statement()

        # Symbols '^' (Raise), '!' (Assert), '?' (Check)
        if self.token_handler.check_type(TokenType.RAISE_SYMBOL):
            return self.raise_statement()

        if self.token_handler.check_type(TokenType.ASSERT_SYMBOL):
            return self.assert_statement()

        if self.token_handler.check_type(TokenType.CHECK_SYMBOL):
            return self.check_statement()

        # Return Statement '->'
        if self.token_handler.check_type(TokenType.RETURN):
            return self.return_statement()

        # fallback: expression statement
        return self.expression_statement()

    def expression_statement(self) -> ASTNode:
        expression: ASTNode = self.expression_handler.expression()
        
        # Lower standalone '++' and '--' operations to ReassignmentStatement
        from Parser.AST import BinaryOperation, Identifier, MemberExpression, IndexExpression, ReassignmentStatement, MemberReassignmentStatement, IndexReassignmentStatement
        if isinstance(expression, BinaryOperation) and getattr(expression, "operator", None) in ("++", "--"):
            left = expression.left
            right = expression.right
            scope_level = self.scope_manager.get_current_scope_level()
            line = getattr(expression, "line", 0)
            col = getattr(expression, "column", 0)
            
            target = None
            if isinstance(left, (Identifier, MemberExpression, IndexExpression)):
                target = left
            elif isinstance(right, (Identifier, MemberExpression, IndexExpression)):
                target = right
                
            if target is not None:
                if isinstance(target, Identifier):
                    return ReassignmentStatement(line, col, target.name, expression, None, True, scope_level)
                elif isinstance(target, MemberExpression):
                    return MemberReassignmentStatement(line, col, scope_level, target.object, target.property, expression, "MemberReassignment")
                elif isinstance(target, IndexExpression):
                    return IndexReassignmentStatement(line, col, scope_level, target.object, target.index, expression, "IndexReassignment")

        statement: ExpressionStatement = ExpressionStatement(
            getattr(expression, "line", 0),
            getattr(expression, "column", 0),
            expression
        )

        return statement

    def block_statement(self, scope_type: str = "block") -> BlockStatement:
        """
        Entry for 'block' statement.
        Supports:
            { ... }
        """
        token: Token | None = None
        statement: ASTNode | None = None
        statements: list[ASTNode | None] = []
        inferred_return_type: Type = TypeVoid()

        token = self.token_handler.expect_type(
            TokenType.LEFT_BRACE, "Expected `{` to open block"
        )

        self.scope_manager.enter("block")

        while not self.token_handler.check_type(TokenType.RIGHT_BRACE):
            statements.append(self.statement())

        self.token_handler.expect_type(
            TokenType.RIGHT_BRACE, "Expected `}` to close block"
        )

        statement = BlockStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            scope_type,
            statements,
            inferred_return_type,
        )

        self.scope_manager.exit("block")

        self.logger.debug("block_statement", statement)
        return statement
