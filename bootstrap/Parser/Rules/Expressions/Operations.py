from Lexer.Token import Token, TokenType
from Parser.AST import ASTNode, BinaryOperation, IsExpression, UnaryOperation, AwaitExpression

class OperationsParserMixin:
    def logical(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.logical_xor(allow_instantiation=allow_instantiation)

        while self.token_handler.check_types([TokenType.OR, TokenType.NOR]):
            next_t = self.token_handler.peek(1)
            if next_t:
                if next_t.type == TokenType.LEFT_BRACE:
                    break
                if next_t.type == TokenType.RETURN:
                    break
                if next_t.type == TokenType.KEYWORD and next_t.value in ("when", "return"):
                    break

            self.token_handler.advance()
            operator = self.token_handler.previous()
            right = self.logical_xor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("logical_or/nor", node)

        return node

    def logical_xor(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.logical_and(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.XOR, TokenType.XNOR]):
            operator = self.token_handler.previous()
            right = self.logical_and(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("logical_xor/xnor", node)

        return node

    def logical_and(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_or(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.AND, TokenType.NAND]):
            operator = self.token_handler.previous()
            right = self.bitwise_or(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("logical_and/nand", node)

        return node

    def bitwise_or(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_xor(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_OR, TokenType.BITWISE_NOR]):
            operator = self.token_handler.previous()
            right = self.bitwise_xor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_or/nor", node)

        return node

    def bitwise_xor(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_and(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_XOR, TokenType.BITWISE_XNOR]):
            operator = self.token_handler.previous()
            right = self.bitwise_and(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_xor/xnor", node)

        return node

    def bitwise_and(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitshift(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_AND, TokenType.BITWISE_NAND]):
            operator = self.token_handler.previous()
            right = self.bitshift(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_and/nand", node)

        return node

    def bitshift(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.equality(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_LEFT_SHIFT, TokenType.BITWISE_RIGHT_SHIFT]):
            operator = self.token_handler.previous()
            right = self.equality(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            self.logger.debug("bitshift", node)

        return node

    def equality(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.comparison(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([
            TokenType.EQUAL, TokenType.NOT_EQUAL,
            TokenType.AND_EQUAL, TokenType.OR_EQUAL, TokenType.XOR_EQUAL,
            TokenType.MOD_EQUAL, TokenType.LEFT_SHIFT_EQUAL, TokenType.RIGHT_SHIFT_EQUAL
        ]):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode = self.comparison(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)

        self.logger.debug("equality", node)

        return node

    def comparison(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.range_op(allow_instantiation=allow_instantiation)

        while True:
            if self.token_handler.match_types(
                [
                    TokenType.GREATER_THAN,
                    TokenType.LESS_THAN,
                    TokenType.GREATER_THAN_OR_EQUAL,
                    TokenType.LESS_THAN_OR_EQUAL,
                ]
            ):
                operator: Token | None = self.token_handler.previous()
                right: ASTNode | None = self.range_op(allow_instantiation=allow_instantiation)
                node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)
            elif self.token_handler.check_type_value(TokenType.KEYWORD, "is"):
                self.token_handler.advance() # consume 'is'
                right = self.statement_handler.parse_pattern()
                node = IsExpression(
                    line=node.line,
                    column=node.column,
                    scope_level=getattr(node, "scope_level", 0),
                    left=node,
                    right=right
                )
            else:
                break

        self.logger.debug("comparison", node)
        return node

    def range_op(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.term(allow_instantiation=allow_instantiation)

        # `a..b`  exclusive end (half-open)
        # `a..=b` inclusive end
        # Note: `...` is ELLIPSIS (rest/spread), not a range.
        if self.token_handler.match_types([TokenType.RANGE, TokenType.RANGE_INCLUSIVE]):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.term(allow_instantiation=allow_instantiation)
            op_value = getattr(operator, "value", "..") or ".."
            node = BinaryOperation(
                getattr(operator, "line"),
                getattr(operator, "column"),
                op_value,
                node,
                right,
            )

        self.logger.debug("range", node)
        return node

    def term(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.factor(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types(
            [TokenType.ADDITION, TokenType.SUBTRACTION, TokenType.INCREMENT, TokenType.DECREMENT]
        ):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.factor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)

        self.logger.debug("term", node)

        return node

    def factor(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.exponent(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types(
            [TokenType.MULTIPLICATION, TokenType.DIVISION, TokenType.MODULO]
        ):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.exponent(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)

        self.logger.debug("factor", node)

        return node

    def exponent(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.unary(allow_instantiation=allow_instantiation)

        if self.token_handler.match_type(TokenType.EXPONENTIATION):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.exponent(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), node, right)

        self.logger.debug("exponent", node)

        return node

    def unary(self, allow_instantiation: bool = True) -> ASTNode | UnaryOperation:
        operator: Token | None = None
        right: ASTNode | None = None
        node: ASTNode | None = None

        if self.token_handler.match_type(TokenType.SUBTRACTION):
            operator = self.token_handler.previous()
            right = self.unary(allow_instantiation=allow_instantiation)
            node = UnaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), right)

            self.logger.debug("unary", node)

            return node

        if self.token_handler.match_types([TokenType.NOT, TokenType.BITWISE_NOT]):
            operator = self.token_handler.previous()
            right = self.unary(allow_instantiation=allow_instantiation)
            node = UnaryOperation(getattr(operator, "line"), getattr(operator, "column"), getattr(operator, "value"), right)

            self.logger.debug("unary", node)

            return node

        if self.token_handler.match_type_value(TokenType.KEYWORD, "await"):
            operator = self.token_handler.previous()
            right = self.unary(allow_instantiation=allow_instantiation)
            node = AwaitExpression(
                line=getattr(operator, "line"),
                column=getattr(operator, "column"),
                scope_level=self.scope_manager.get_scope_level("global"),
                expression=right
            )
            return node

        if self.token_handler.match_type(TokenType.CHECK_SYMBOL) or self.token_handler.match_type_value(TokenType.KEYWORD, "check"):
            return self.check_expression()

        if self.token_handler.check_types([TokenType.BITWISE_AND, TokenType.MULTIPLICATION]):
            operator = self.token_handler.advance()
            op_str = "source" if operator.type == TokenType.BITWISE_AND else "target"
            right = self.unary(allow_instantiation=allow_instantiation)
            node = UnaryOperation(getattr(operator, "line"), getattr(operator, "column"), op_str, right)
            return node

        if self.token_handler.check_type(TokenType.KEYWORD):
            pk = self.token_handler.peek().value
            if pk in ["source", "target"]:
                operator = self.token_handler.advance()
                right = self.unary(allow_instantiation=allow_instantiation)
                node = UnaryOperation(getattr(operator, "line"), getattr(operator, "column"), pk, right)
                return node

        return self.call(allow_instantiation=allow_instantiation)
