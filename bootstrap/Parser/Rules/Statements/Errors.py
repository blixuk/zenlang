from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    ExpressionStatement,
    CaseBranch,
    BinaryOperation
)

class ErrorParserMixin:
    def defer_statement(self) -> DeferStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "defer", "Expected `defer` keyword")
        block: ASTNode | None = None
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            block = self.block_statement()
        else:
            block = self.expression_statement()

        return DeferStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            block
        )

    def raise_statement(self) -> RaiseStatement:
        token: Token | None = None
        if self.token_handler.match_type(TokenType.RAISE_SYMBOL):
            token = self.token_handler.previous()
        else:
            token = self.token_handler.expect_type_value(TokenType.KEYWORD, "raise", "Expected `raise` keyword or symbol `^`")

        value = self.expression_handler.expression()
        with_value: ASTNode | None = None

        if self.token_handler.match_type_value(TokenType.KEYWORD, "with"):
            with_value = self.expression_handler.expression()

        return RaiseStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            value,
            with_value
        )

    def assert_statement(self) -> AssertStatement:
        token: Token | None = None
        if self.token_handler.match_type(TokenType.ASSERT_SYMBOL):
            token = self.token_handler.previous()
        else:
            token = self.token_handler.expect_type_value(TokenType.KEYWORD, "assert", "Expected `assert` keyword or symbol `!`")

        condition = self.expression_handler.expression()
        raise_expression: ASTNode | None = None

        if self.token_handler.match_type_value(TokenType.KEYWORD, "raise") or self.token_handler.match_type(TokenType.RAISE_SYMBOL):
            raise_expression = self.expression_handler.expression()

        return AssertStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            condition,
            raise_expression
        )

    def check_statement(self) -> CheckStatement:
        token: Token | None = None
        if self.token_handler.match_type(TokenType.CHECK_SYMBOL):
            token = self.token_handler.previous()
        else:
            token = self.token_handler.expect_type_value(TokenType.KEYWORD, "check", "Expected `check` keyword or symbol `?`")

        expression = self.expression_handler.expression()
        
        cases: list = []
        or_block: ASTNode | None = None

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
                if self.token_handler.match_type_value(TokenType.KEYWORD, "case"):
                    case_token = self.token_handler.previous()
                    case_pattern = self.parse_pattern()
                    case_block = self.block_statement("case")
                    cases.append(CaseBranch(
                        getattr(case_token, "line"),
                        getattr(case_token, "column"),
                        case_pattern,
                        case_block
                    ))
                    if self.token_handler.match_type(TokenType.COMMA):
                        continue
                else:
                    break
            self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after check cases")
        
        raise_expr: ASTNode | None = None
        if self.token_handler.match_type(TokenType.OR):
            if self.token_handler.check_type(TokenType.LEFT_BRACE):
                or_block = self.block_statement("or")
            else:
                or_block = self.expression_statement()
        elif self.token_handler.match_type_value(TokenType.KEYWORD, "raise") or self.token_handler.match_type(TokenType.RAISE_SYMBOL):
            raise_expr = self.expression_handler.expression()
        elif isinstance(expression, BinaryOperation) and expression.operator == "or":
            or_block = ExpressionStatement(expression.right)
            expression = expression.left

        return CheckStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            expression,
            cases,
            or_block,
            raise_expr
        )
