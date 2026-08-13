from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    WhenExpression,
    WhenInlineExpression,
    CheckExpression,
    BinaryOperation
)

class ControlFlowExpressionsMixin:
    def conditional(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.logical(allow_instantiation=allow_instantiation)

        if self.token_handler.check_type_value(TokenType.KEYWORD, "when"):
            current_when = self.token_handler.peek()
            previous_token = self.token_handler.previous()

            if previous_token and current_when.line != previous_token.line:
                return node

            if self.token_handler.check_type(TokenType.LEFT_BRACE, 1):
                return node

            self.token_handler.advance() # consume `when`
            token: Token | None = self.token_handler.previous()

            condition = self.equality(allow_instantiation=allow_instantiation)

            if self.token_handler.check_type(TokenType.KEYWORD):
                self.token_handler.expect_type_value(
                    TokenType.KEYWORD, "or", "Expected `or` in inline when expression"
                )
            else:
                self.token_handler.expect_type(
                    TokenType.OR, "Expected `or` in inline when expression"
                )

            or_value = self.expression(allow_instantiation=allow_instantiation)

            node = WhenInlineExpression(
                getattr(token, "line"),
                getattr(token, "column"),
                self.scope_manager.get_scope_level("global"),
                condition,
                node,
                or_value,
            )

            self.logger.debug("when_inline_expression", node)


        return node

    def when_expression(self) -> ASTNode:
        token: Token | None = None
        expression: ASTNode | None = None
        condition: ASTNode | None = None
        when_block: ASTNode | None = None
        conditional_blocks: list | None = []
        or_block: ASTNode | None = None

        token = self.token_handler.previous()

        self.scope_manager.enter("when")

        condition = self.expression()
        self.token_handler.expect_type(TokenType.LEFT_BRACE, "Expected `{` after `when` condition")
        when_block = self.block_expression("when")

        # Handle any number of conditionals
        while self.token_handler.match_type(TokenType.OR):
            if not self.token_handler.check_type(TokenType.LEFT_BRACE):
                self.token_handler.match_type_value(TokenType.KEYWORD, "when")
                conditional_condition: ASTNode = self.expression()
                self.token_handler.expect_type(TokenType.LEFT_BRACE, "Expected `{` after `when` condition")
                conditional_block: ASTNode = self.block_expression("conditional")

                conditional_blocks.append(
                    {"condition": conditional_condition, "block": conditional_block}
                )

                continue

            else:
                self.token_handler.expect_type(TokenType.LEFT_BRACE, "Expected `{` after `or` keyword")
                or_block = self.block_expression("or")
                break

        expression = WhenExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("when"),
            condition,
            when_block,
            conditional_blocks,
            or_block,
        )

        self.scope_manager.exit("when")

        self.logger.debug("when_expression", expression)

        return expression

    def when_inline_expression(self, value: ASTNode | None = None) -> ASTNode:
        token: Token | None = None
        expression: ASTNode | None = None
        condition: ASTNode | None = None
        when_value: ASTNode | None = None
        or_value: ASTNode | None = None

        token = self.token_handler.previous()

        when_value = value if value else getattr(token, "value")

        self.token_handler.expect_type_value(
            TokenType.KEYWORD, "when", "Expected `when` keyword"
        )

        condition = self.expression()

        self.token_handler.expect_type_value(
            TokenType.KEYWORD, "or", "Expected `or` keyword"
        )

        or_value = self.expression()

        expression = WhenInlineExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            condition,
            when_value,
            or_value,
        )

        self.logger.debug("when_inline_expression", expression)

        return expression

    def check_expression(self) -> CheckExpression:
        token = self.token_handler.previous()
        expression = self.expression()
        or_value: ASTNode | None = None
        raise_expression: ASTNode | None = None

        if self.token_handler.match_type(TokenType.OR):
            if self.token_handler.check_type(TokenType.LEFT_BRACE):
                or_value = self.statement_handler.block_statement("or")
            else:
                or_value = self.expression()
        elif self.token_handler.match_type_value(TokenType.KEYWORD, "raise") or self.token_handler.match_type(TokenType.RAISE_SYMBOL):
            raise_expression = self.expression()
        elif isinstance(expression, BinaryOperation) and expression.operator == "or":
            or_value = expression.right
            expression = expression.left

        return CheckExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            expression,
            or_value,
            raise_expression
        )
