from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    FunctionExpression,
    BlockExpression,
    StructureExpression,
    ReturnStatement
)
from Checker.Type import Type, TypeVoid, TypeVariant

class ComplexExpressionsMixin:
    def function_expression(self) -> FunctionExpression:
        token: Token | None = None
        parameters: list | None = []
        inferred_return_type: Type | None = None
        return_type: Type | str | None = "infer_type"
        block: BlockExpression | None = None

        if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            raise self.logger.error(
                "Unexpected identifier in `function` expression",
                self.token_handler.previous(),
            )

        token = self.token_handler.previous()

        if self.token_handler.check_type(TokenType.LEFT_PAREN):
            parameters = self.parse_parameters()

        if self.token_handler.check_type(TokenType.TYPE_SET):
            self.token_handler.expect_type(
                TokenType.TYPE_SET, "Expected type setter `:` after `function` keyword"
            )
            type: Token | None = self.token_handler.expect_type(
                TokenType.TYPE, "Expected type after type setter `:`"
            )
            return_type = getattr(type, "value", "infer_type")

        self.token_handler.expect_type(
            TokenType.LEFT_BRACE, "Expected `{` after `function` keyword"
        )
        block = self.block_expression("function")

        if (
            return_type == "infer_type"
            and block
            and hasattr(block, "inferred_return_type")
        ):
            inferred_return_type = getattr(block, "inferred_return_type")
        elif return_type is None and block and hasattr(block, "inferred_return_type"):
            if getattr(block, "inferred_return_type") == TypeVoid:
                inferred_return_type = TypeVoid
            else:
                inferred_return_type = TypeVariant
        else:
            inferred_return_type = TypeVoid

        expression = FunctionExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("function"),
            getattr(token, "value"),
            parameters,
            block,
            inferred_return_type,
        )

        self.logger.debug("function_expression", expression)

        return expression

    def block_expression(self, scope_type: str = "block") -> BlockExpression:
        token: Token | None = None
        statements: list | None = []
        return_type: Type | None = TypeVoid

        token = self.token_handler.previous()

        self.scope_manager.enter("block")

        while (
            not self.token_handler.check_type(TokenType.RIGHT_BRACE)
            and not self.token_handler.at_end()
        ):
            statements.append(self.statement_handler.statement())

        self.token_handler.expect_type(
            TokenType.RIGHT_BRACE, "Expected `}` to close block"
        )

        if statements:
            return_statements: list = []
            for statement in statements:
                if type(statement) is ReturnStatement:
                    return_statements.append(statement)

            if len(return_statements) == 1:
                if return_statements[0] and hasattr(
                    return_statements[0], "return_type"
                ):
                    return_type = return_statements[0].return_type
            elif len(return_statements) > 1:
                return_type = TypeVariant

        expression = BlockExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("block"),
            statements,
            scope_type,
            return_type,
        )

        self.scope_manager.exit("block")

        self.logger.debug("block_expression", expression)

        return expression

    def structure_expression(self) -> StructureExpression:
        token: Token | None = None
        members: list | None = None

        if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            raise self.logger.error(
                "Unexpected identifier in `structure` expression",
                self.token_handler.previous(),
            )

        token = self.token_handler.previous()

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            members = self.parse_members()

        expression = StructureExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("structure"),
            getattr(token, "value"),
            members,
        )

        self.logger.debug("structure_expression", expression)
        return expression
