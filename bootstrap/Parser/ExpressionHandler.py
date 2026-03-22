# -----------------------------
# Expression parsing
# -----------------------------
# Precedence:
# expression → equality
# equality   → comparison ( ( "==" | "!=" ) comparison )*
# comparison → term ( ( ">" | ">=" | "<" | "<=" ) term )*
# term       → factor ( ( "+" | "-" ) factor )*
# factor     → unary ( ( "*" | "/" | "%" ) unary )*
# unary      → ( "-" | "!" ) unary | primary
# primary    → NUMBER | STRING | IDENTIFIER | function_expression | block_expression | "(" expression ")"
# -----------------------------

from multiprocessing import Value

from Checker.Type import (
    PRIMITIVE_TYPES,
    Type,
    TypeBoolean,
    TypeDecimal,
    TypeElement,
    TypeInteger,
    TypeMember,
    TypeNothing,
    TypeParameter,
    TypeSet,
    TypeString,
    TypeTuple,
    TypeVariant,
    TypeVector,
    TypeVoid,
    TypeMap,
)
from Lexer.Token import TYPE_TOKENS, Token, TokenType
from Logging.ParserLogger import ParserLogger
from Parser.AST import (
    ASTNode,
    AutoLiteral,
    BinaryOperation,
    BlockExpression,
    BooleanLiteral,
    CallExpression,
    DecimalLiteral,
    ElementLiteral,
    FunctionExpression,
    Identifier,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MemberExpression,
    MemberLiteral,
    MemberReassignmentStatement,
    NothingLiteral,
    ParameterLiteral,
    ParentExpression,
    ReturnStatement,
    RuneLiteral,
    StringLiteral,
    StructureExpression,
    UnaryOperation,
    WhenExpression,
    WhenInlineExpression,
    CheckExpression,
    TypeLiteral,
    DictionaryLiteral,
    SetLiteral,
    VectorLiteral,
    TupleLiteral,
)
from Parser.Scope import ScopeManager
from Parser.TokenHandler import TokenHandler


class ExpressionHandler:
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
        return self.conditional(allow_instantiation=allow_instantiation)

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

        if self.token_handler.match_type(TokenType.CHECK_SYMBOL):
            # Ternary operator: condition ? true_expr : false_expr
            true_expr = self.expression(allow_instantiation=allow_instantiation)
            self.token_handler.expect_type(TokenType.TYPE_SET, "Expected `:` after true expression in ternary operator")
            false_expr = self.expression(allow_instantiation=allow_instantiation)
            node = WhenInlineExpression(
                getattr(node, "line", 0),
                getattr(node, "column", 0),
                self.scope_manager.get_scope_level("global"),
                node,  # condition
                true_expr,
                false_expr,
            )
            self.logger.debug("when_inline_expression", node)

        return node

    def parse_types(self) -> TypeLiteral:
        if self.token_handler.match_types([TokenType.TYPE, TokenType.IDENTIFIER]):
            token = self.token_handler.previous()
        else:
            raise self.logger.error_expect_token(
                "Expected type name", self.token_handler.peek()
            )
        node = TypeLiteral(name=getattr(token, "value"))
        if self.token_handler.match_type(TokenType.LEFT_BRACKET):
            bits = self.token_handler.expect_type(
                TokenType.INTEGER, "Expected bit width"
            )
            self.token_handler.expect_type(
                TokenType.RIGHT_BRACKET, "Expected `]` after bit width"
            )
            node.bits = getattr(bits, "value")
        if self.token_handler.match_type(TokenType.LESS_THAN):
            subtypes = []
            while True:
                subtypes.append(self.parse_types())
                if not self.token_handler.match_type(TokenType.COMMA):
                    break
            self.token_handler.expect_type(
                TokenType.GREATER_THAN, "Expected '>' after type arguments"
            )
            node.subtypes = subtypes
        return node

    def logical(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.logical_xor(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.OR, TokenType.NOR]):
            operator = self.token_handler.previous()
            right = self.logical_xor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("logical_or/nor", node)

        return node

    def logical_xor(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.logical_and(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.XOR, TokenType.XNOR]):
            operator = self.token_handler.previous()
            right = self.logical_and(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("logical_xor/xnor", node)

        return node

    def logical_and(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_or(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.AND, TokenType.NAND]):
            operator = self.token_handler.previous()
            right = self.bitwise_or(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("logical_and/nand", node)

        return node

    def bitwise_or(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_xor(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_OR, TokenType.BITWISE_NOR]):
            operator = self.token_handler.previous()
            right = self.bitwise_xor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_or/nor", node)

        return node

    def bitwise_xor(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitwise_and(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_XOR, TokenType.BITWISE_XNOR]):
            operator = self.token_handler.previous()
            right = self.bitwise_and(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_xor/xnor", node)

        return node

    def bitwise_and(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.bitshift(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_AND, TokenType.BITWISE_NAND]):
            operator = self.token_handler.previous()
            right = self.bitshift(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
            self.logger.debug("bitwise_and/nand", node)

        return node

    def bitshift(self, allow_instantiation: bool = True) -> ASTNode:
        node: ASTNode = self.equality(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types([TokenType.BITWISE_LEFT_SHIFT, TokenType.BITWISE_RIGHT_SHIFT]):
            operator = self.token_handler.previous()
            right = self.equality(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)
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
            node = BinaryOperation(getattr(operator, "value"), node, right)

        self.logger.debug("equality", node)

        return node

    def comparison(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.term(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types(
            [
                TokenType.GREATER_THAN,
                TokenType.LESS_THAN,
                TokenType.GREATER_THAN_OR_EQUAL,
                TokenType.LESS_THAN_OR_EQUAL,
            ]
        ):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.term(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)

        self.logger.debug("comparison", node)

        return node

    def term(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.factor(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types(
            [TokenType.ADDITION, TokenType.SUBTRACTION]
        ):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.factor(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)

        self.logger.debug("term", node)

        return node

    def factor(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.exponent(allow_instantiation=allow_instantiation)

        while self.token_handler.match_types(
            [TokenType.MULTIPLICATION, TokenType.DIVISION, TokenType.MODULO]
        ):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.exponent(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)

        self.logger.debug("factor", node)

        return node

    def exponent(self, allow_instantiation: bool = True) -> ASTNode | BinaryOperation:
        node: ASTNode = self.unary(allow_instantiation=allow_instantiation)

        if self.token_handler.match_type(TokenType.EXPONENTIATION):
            operator: Token | None = self.token_handler.previous()
            right: ASTNode | None = self.exponent(allow_instantiation=allow_instantiation)
            node = BinaryOperation(getattr(operator, "value"), node, right)

        self.logger.debug("exponent", node)

        return node

    def unary(self, allow_instantiation: bool = True) -> ASTNode | UnaryOperation:
        operator: Token | None = None
        right: ASTNode | None = None
        node: ASTNode | None = None

        if self.token_handler.match_type(TokenType.SUBTRACTION):
            operator = self.token_handler.previous()
            right = self.unary(allow_instantiation=allow_instantiation)
            node = UnaryOperation(getattr(operator, "value"), right)

            self.logger.debug("unary", node)

            return node

        if self.token_handler.match_types([TokenType.NOT, TokenType.BITWISE_NOT]):
            operator = self.token_handler.previous()
            right = self.unary(allow_instantiation=allow_instantiation)
            node = UnaryOperation(getattr(operator, "value"), right)

            self.logger.debug("unary", node)

            return node

        return self.call(allow_instantiation=allow_instantiation)

    def call(
        self, allow_instantiation: bool = True
    ) -> ASTNode | CallExpression | MemberExpression | IndexExpression | None:
        """
        Entry for 'call' expressions. Start from a primary expression and repeatedly accept
        Supports:
            call: ( arguments )
            member: .identifier
            index: [ expression ]
        Produces nested CallExpression / MemberExpression / IndexExpression nodes.
        """

        node: ASTNode | None = self.primary()

        while True:
            # function call
            if self.token_handler.match_type(TokenType.LEFT_PAREN):
                arguments: list = self.parse_arguments()
                node = CallExpression(
                    getattr(node, "line"),
                    getattr(node, "column"),
                    self.scope_manager.get_scope_level("global"),
                    node,
                    arguments,
                )

                continue

            # member access
            if self.token_handler.match_type(TokenType.DOT):
                member: Token | None = self.token_handler.expect_types(
                    [TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected member name after `.`"
                )
                node = MemberExpression(
                    getattr(node, "line"),
                    getattr(node, "column"),
                    self.scope_manager.get_scope_level("global"),
                    node,
                    getattr(member, "value"),
                )

                continue

            # indexing
            if self.token_handler.match_type(TokenType.LEFT_BRACKET):
                index: ASTNode = self.expression()
                self.token_handler.expect_type(
                    TokenType.RIGHT_BRACKET, "Expected `]` after index expression"
                )
                node = IndexExpression(getattr(node, "line"), getattr(node, "column"), node, index)

                continue

            # structure instantiation
            if allow_instantiation and self.token_handler.check_type(TokenType.LEFT_BRACE):
                # Only allow structure instantiation after Identifier or MemberExpression
                # to avoid ambiguity with block statements after function calls (e.g. `when cond { ... }`)
                if isinstance(node, (Identifier, MemberExpression)):
                    # Peek ahead to see if it looks like a structure literal members
                    # must be ident/keyword followed by : or -> or :> OR just be an empty brace {}
                    if self.token_handler.check_type(TokenType.RIGHT_BRACE, 1) or \
                       ((self.token_handler.check_type(TokenType.IDENTIFIER, 1) or self.token_handler.check_type(TokenType.KEYWORD, 1)) and \
                        (self.token_handler.check_type(TokenType.TYPE_SET, 2) or self.token_handler.check_type(TokenType.ASSIGNMENT, 2) or self.token_handler.check_type(TokenType.TYPE_LET, 2))):
                        
                        self.token_handler.match_type(TokenType.LEFT_BRACE)
                        members = self.parse_members(is_instantiation=True)
                        node = StructureExpression(
                            getattr(node, "line"),
                            getattr(node, "column"),
                            self.scope_manager.get_scope_level("structure"),
                            getattr(node, "name", str(node)),
                            members
                        )
                        continue

            break

        self.logger.debug("call", node)
        return node

    def primary(self) -> ASTNode | None:
        token: Token | None = self.token_handler.peek()

        if token.type in TYPE_TOKENS:
            return self.resolve_type_literals()

        if self.token_handler.match_type_value(TokenType.KEYWORD, "function"):
            primary_function: ASTNode = self.function_expression()

            self.logger.debug("primary function", primary_function)
            return primary_function

        if self.token_handler.match_type_value(TokenType.KEYWORD, "when"):
            primary_when: ASTNode = self.when_expression()

            self.logger.debug("primary when", primary_when)
            return primary_when

        if self.token_handler.check_type(TokenType.CHECK_SYMBOL) or self.token_handler.match_type_value(TokenType.KEYWORD, "check"):
            if self.token_handler.match_type(TokenType.CHECK_SYMBOL):
                 pass # consumed by match_type
            # If it was a keyword, match_type_value consumed it
            primary_check: ASTNode = self.check_expression()

            self.logger.debug("primary check", primary_check)
            return primary_check

        if self.token_handler.match_type_value(TokenType.KEYWORD, "structure") or \
           self.token_handler.match_type_value(TokenType.KEYWORD, "object"):
            primary_structure: ASTNode = self.structure_expression()

            self.logger.debug("primary structure/object", primary_structure)
            return primary_structure

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            primary_block: ASTNode = self.block_expression()

            self.logger.debug("primary block", primary_block)
            return primary_block

        if self.token_handler.match_type_value(TokenType.KEYWORD, "parent"):
            node = ParentExpression(
                getattr(token, "line"),
                getattr(token, "column"),
                self.scope_manager.get_scope_level("global"),
            )
            self.logger.debug("parent expression", node)
            return node

        if self.token_handler.match_type_value(TokenType.KEYWORD, "self"):
            node = Identifier(
                getattr(token, "line"),
                getattr(token, "column"),
                self.scope_manager.get_scope_level("global"),
                "self",
                "Identifier",
            )
            self.logger.debug("self identifier", node)
            return node

        if self.token_handler.match_type_value(TokenType.KEYWORD, "nothing"):
            token = self.token_handler.previous()
            primary_nothing: NothingLiteral = NothingLiteral(
                getattr(token, "line"), getattr(token, "column"), getattr(token, "value")
            )
            self.logger.debug("primary nothing", primary_nothing)
            return primary_nothing

        if self.token_handler.match_type_value(TokenType.KEYWORD, "true") or \
           self.token_handler.match_type_value(TokenType.KEYWORD, "false"):
            token = self.token_handler.previous()
            primary_boolean: BooleanLiteral = BooleanLiteral(
                getattr(token, "line"), getattr(token, "column"), getattr(token, "value")
            )
            self.logger.debug("primary boolean", primary_boolean)
            return primary_boolean

        if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            id_token = self.token_handler.peek()
            val = getattr(id_token, "value")
            if val in ["l", "v", "t", "d", "s"] and self.token_handler.check_type(TokenType.LEFT_BRACE, 1):
                self.token_handler.advance() # consume prefix
                self.token_handler.advance() # consume `{`
                elements = self.parse_elements(TokenType.RIGHT_BRACE)
                self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after collection literal")
                
                if val == "l":
                    node = ListLiteral(getattr(id_token, "line"), getattr(id_token, "column"), elements)
                elif val == "v":
                    node = VectorLiteral(getattr(id_token, "line"), getattr(id_token, "column"), elements)
                elif val == "t":
                    node = TupleLiteral(getattr(id_token, "line"), getattr(id_token, "column"), elements)
                elif val == "d":
                    node = DictionaryLiteral(getattr(id_token, "line"), getattr(id_token, "column"), elements)
                elif val == "s":
                    node = SetLiteral(getattr(id_token, "line"), getattr(id_token, "column"), elements)
                
                self.logger.debug(f"primary generic literal {val}", node)
                return node

        if (self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD])) and self.token_handler.check_type(TokenType.DOT, 1):
            primary_member: MemberExpression | None = self.member_expression()

            self.logger.debug("primary member", primary_member)
            return primary_member

        if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            primary_identifier: ASTNode = self.resolve_identifier()

            self.logger.debug("primary identifier", primary_identifier)
            return primary_identifier

        if self.token_handler.match_type(TokenType.LEFT_PAREN):
            # Check if it's an empty tuple
            if self.token_handler.match_type(TokenType.RIGHT_PAREN):
                node = TupleLiteral(getattr(token, "line"), getattr(token, "column"), [])
                self.logger.debug("primary empty tuple", node)
                return node
            
            primary_expression: ASTNode = self.expression()
            
            # Check if it's a tuple (has comma)
            if self.token_handler.match_type(TokenType.COMMA):
                elements = [ElementLiteral(getattr(token, "line"), getattr(token, "column"), None, primary_expression, True, TypeVariant(), TypeElement(None, TypeVariant()))]
                elements.extend(self.parse_elements(TokenType.RIGHT_PAREN)) # parse_elements needs to handle the rest
                self.token_handler.expect_type(TokenType.RIGHT_PAREN, "Expected `)` after tuple")
                node = TupleLiteral(getattr(token, "line"), getattr(token, "column"), elements)
                self.logger.debug("primary tuple", node)
                return node

            self.token_handler.expect_type(
                TokenType.RIGHT_PAREN, "Expected ')' after expression..."
            )

            self.logger.debug("primary expression", primary_expression)
            return primary_expression

        if self.token_handler.match_type(TokenType.LEFT_BRACKET):
            elements = self.parse_elements(TokenType.RIGHT_BRACKET)
            self.token_handler.expect_type(TokenType.RIGHT_BRACKET, "Expected `]` after list")

            primary_list: ListLiteral = ListLiteral(
                getattr(token, "line"), getattr(token, "column"), elements
            )

            self.logger.debug("primary list", primary_list)
            return primary_list

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            # Check if it's a dictionary or a block
            # If it's an empty brace, it could be either. Standard says empty dictionary.
            if self.token_handler.match_type(TokenType.RIGHT_BRACE):
                node = DictionaryLiteral(getattr(token, "line"), getattr(token, "column"), [])
                self.logger.debug("primary empty dictionary", node)
                return node
            
            # Peek to see if it's a dictionary (key -> value)
            # This is tricky because we might need to backtrack or look ahead.
            # For now, let's assume if the first 'statement' or 'expression' is followed by ->, it's a dictionary.
            
            # Actually, let's try parsing a dictionary first if possible.
            # But dict keys can be expressions.
            
            # Alternative: block_expression already handles statements. 
            # If we want literal { a -> 1 }, we need a check.
            
            # For now, let's handle the prefixed ones which are unambiguous.
            primary_block: ASTNode = self.block_expression()
            self.logger.debug("primary block", primary_block)
            return primary_block

        # Fallback
        raise self.logger.error_expect_token("Expected expression", self.token_handler.peek())


    ## Literal Types

    def resolve_type_literals(self) -> ASTNode | None:
        token: Token | None = self.token_handler.peek()

        if self.token_handler.match_type(TokenType.INTEGER):
            primary_integer: IntegerLiteral = IntegerLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )

            self.logger.debug("primary integer", primary_integer)
            return primary_integer

        if self.token_handler.match_type(TokenType.DECIMAL):
            primary_decimal: DecimalLiteral = DecimalLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )

            self.logger.debug("primary decimal", primary_decimal)
            return primary_decimal

        if self.token_handler.match_type(TokenType.STRING):
            primary_string: StringLiteral = StringLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
                prefix=getattr(token, "prefix", None),
            )

            self.logger.debug("primary string", primary_string)
            return primary_string

        if self.token_handler.match_type(TokenType.RUNE):
            primary_character: RuneLiteral = RuneLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )

            self.logger.debug("primary character", primary_character)
            return primary_character

        if self.token_handler.match_type(TokenType.BOOLEAN):
            primary_boolean: BooleanLiteral = BooleanLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )

            self.logger.debug("primary boolean", primary_boolean)
            return primary_boolean

        if self.token_handler.match_type(TokenType.LIST):
            elements: list[ASTNode] = self.parse_elements()

            primary_list: ListLiteral = ListLiteral(
                getattr(token, "line"), getattr(token, "column"), elements
            )

            self.logger.debug("primary list", primary_list)
            return primary_list

        if self.token_handler.match_type(TokenType.NOTHING):
            primary_nothing: NothingLiteral = NothingLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )

            self.logger.debug("primary nothing", primary_nothing)
            return primary_nothing

        return None

    def resolve_identifier(self) -> ASTNode:
        identifier: ASTNode | None = None
        token: Token | None = self.token_handler.previous()

        identifier = Identifier(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            getattr(token, "value"),
            "Identifier",
        )

        self.logger.debug("resolve_identifier", identifier)

        return identifier

    ## Expressions

    def call_expression(self) -> CallExpression | None:
        token: Token | None = None
        expression: CallExpression | None = None
        callee: Identifier | None = None

        token = self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD])

        callee = Identifier(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            getattr(token, "value"),
            getattr(token, "type"),
        )

        expression = callee
        while True:
            if self.token_handler.match_type(TokenType.LEFT_PAREN):
                arguments: list = self.parse_arguments()

                expression = CallExpression(
                    getattr(token, "line"),
                    getattr(token, "column"),
                    self.scope_manager.get_scope_level("global"),
                    expression,
                    arguments,
                )
            elif self.token_handler.match_type(TokenType.LEFT_BRACE):
                members = self.parse_members()
                name = getattr(expression, "name", getattr(token, "value"))
                if isinstance(expression, MemberExpression):
                     name = expression.property
                
                expression = StructureExpression(
                    getattr(token, "line"),
                    getattr(token, "column"),
                    self.scope_manager.get_scope_level("global"),
                    name,
                    members,
                )
            else:
                break

        self.logger.debug("call_expression", expression)
        return expression

    def member_expression(
        self,
    ) -> MemberExpression | MemberReassignmentStatement | None:
        expression: ASTNode | None = None
        token: Token | None = None
        callee: Identifier | None = None

        token = self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD])

        callee = Identifier(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            getattr(token, "value"),
            None,
        )

        expression = callee
        while True:
            if self.token_handler.match_type(TokenType.DOT):
                property: Token | None = self.token_handler.expect_types(
                    [TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected property name after `.`"
                )

                expression = MemberExpression(
                    getattr(token, "line"),
                    getattr(token, "column"),
                    self.scope_manager.get_scope_level("global"),
                    expression,
                    getattr(property, "value"),
                )
            else:
                break

        if self.token_handler.check_type(TokenType.ASSIGNMENT):
            self.token_handler.expect_type(
                TokenType.ASSIGNMENT, "Expected `->` after member name"
            )

            value: ASTNode = self.expression()

            expression = MemberReassignmentStatement(
                getattr(token, "line"),
                getattr(token, "column"),
                self.scope_manager.get_scope_level("global"),
                callee,
                expression,
                value,
                declared_type=getattr(value, "type")
                if hasattr(value, "type")
                else TypeVariant.name,
            )

        self.logger.debug("member_expression", expression)

        return expression

    def function_expression(self) -> FunctionExpression:
        token: Token | None = None
        expression: ASTNode | None = None
        parameters: list | None = []
        inferred_return_type: Type | None = None
        return_type: Type | str | None = "infer_type"
        block: BlockExpression | None = None

        # Identifier
        if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            raise self.logger.error(
                "Unexpected identifier in `function` expression",
                self.token_handler.previous(),
            )

        # Keyword
        token = self.token_handler.previous()

        # Parameters
        if self.token_handler.check_type(TokenType.LEFT_PAREN):
            parameters = self.parse_parameters()

        # Return Type
        if self.token_handler.check_type(TokenType.TYPE_SET):
            self.token_handler.expect_type(
                TokenType.TYPE_SET, "Expected type setter `:` after `function` keyword"
            )
            type: Token | None = self.token_handler.expect_type(
                TokenType.TYPE, "Expected type after type setter `:`"
            )
            return_type = getattr(type, "value", "infer_type")

        # Block Scope
        self.token_handler.expect_type(
            TokenType.LEFT_BRACE, "Expected `{` after `function` keyword"
        )
        block = self.block_expression("function")

        # try infer functions return type from it's blocks return type
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
        expression: ASTNode | None = None
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

        # check if block has any return statements
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
        expression: ASTNode | None = None
        members: MemberExpression | None = None

        # Identifier
        if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            raise self.logger.error(
                "Unexpected identifier in `structure` expression",
                self.token_handler.previous(),
            )

        # Keyword
        token = self.token_handler.previous()

        # Members
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

    def when_expression(self) -> ASTNode:
        token: Token | None = None
        expression: ASTNode | None = None
        condition: ASTNode | None = None
        when_block: BlockExpression | None = None
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
                conditional_block: BlockExpression = self.block_expression(
                    "conditional"
                )

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

    ## Helpers

    def parse_parameters(self) -> list:
        self.token_handler.expect_type(
            TokenType.LEFT_PAREN, "Expected `(` after function name"
        )

        parameters: list = []

        if self.token_handler.check_type(TokenType.RIGHT_PAREN):
            self.token_handler.advance()
            return parameters

        while True:
            parameter: Token | None = self.token_handler.expect_types(
                [TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected parameter name"
            )
            parameter_name: str = getattr(parameter, "value")
            parameter_type: Type = TypeVariant

            if self.token_handler.check_type(TokenType.TYPE_SET):
                self.token_handler.expect_type(
                    TokenType.TYPE_SET, "Expected type setter `:` after parameter name"
                )

                if self.token_handler.match_types([TokenType.TYPE, TokenType.IDENTIFIER]):
                    type_token: Token | None = self.token_handler.previous()
                else:
                    raise self.logger.error_expect_token("Expected parameter type", self.token_handler.peek())
                
                type_name = getattr(type_token, "value")
                type: Type = PRIMITIVE_TYPES.get(type_name, TypeVariant)
                parameter_type = type

            parameters.append(
                ParameterLiteral(
                    getattr(parameter, "line"),
                    getattr(parameter, "column"),
                    parameter_name,
                    None,
                    parameter_type,
                    TypeParameter(parameter_name, parameter_type),
                )
            )

            if self.token_handler.match_type(TokenType.COMMA):
                continue
            elif self.token_handler.match_type(TokenType.RIGHT_PAREN):
                break
            else:
                raise self.logger.error_expect_token(
                    "Expected `,` or `)` in parameters", self.token_handler.peek()
                )

        self.logger.debug("parse_parameters", parameters)

        return parameters

    def parse_arguments(self) -> list:
        arguments: list = []

        if self.token_handler.check_type(TokenType.RIGHT_PAREN):
            self.token_handler.advance()
            return arguments

        while True:
            arguments.append(self.expression())

            if self.token_handler.match_type(TokenType.COMMA):
                continue
            elif self.token_handler.match_type(TokenType.RIGHT_PAREN):
                break
            else:
                token: Token | None = self.token_handler.expect_type(
                    TokenType.RIGHT_PAREN, "Expected `)` after arguments"
                )
                raise token

        self.logger.debug("parse_arguments", arguments)

        return arguments

    def parse_members(
        self, token: Token | None = None, member_kind="structure", is_instantiation=False
    ) -> list:
        if not token:
            token = self.token_handler.previous()

        members: list = []
        value: ASTNode | None = None
        count: int = 0

        while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
            # Skip let/var keyword if present (it's optional in members for bootstrap but used in smoke test)
            if self.token_handler.check_type(TokenType.KEYWORD):
                 pk = self.token_handler.peek().value
                 if pk in ("let", "var"):
                      self.token_handler.advance()

            if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
                member_name = self.token_handler.previous()
            else:
                break
                
            member_type: Type = TypeVariant
            member_value: any = NothingLiteral()

            if self.token_handler.check_type(TokenType.TYPE_LET):
                self.token_handler.expect_type(
                    TokenType.TYPE_LET, "Expected `:>` after member name"
                )
                value = self.expression()
                member_type = getattr(value, "type", TypeVariant)
                member_value = (
                    getattr(value, "value") if value else NothingLiteral()
                )

            if self.token_handler.check_type(TokenType.TYPE_SET):
                self.token_handler.expect_type(
                    TokenType.TYPE_SET,
                    "Expected typer setter `:` after member name",
                )
                
                if is_instantiation:
                    value = self.expression()
                    member_value = value
                    member_type = getattr(value, "type", TypeVariant)
                else:
                    member_type = self.parse_types()

            if self.token_handler.check_type(TokenType.ASSIGNMENT):
                self.token_handler.expect_type(
                    TokenType.ASSIGNMENT,
                    "Expected assignment operator `->` after member name",
                )

                if self.token_handler.check_type_value(
                    TokenType.KEYWORD, "function"
                ):
                    self.token_handler.expect_type(
                        TokenType.KEYWORD, "Expected `function` after member name"
                    )
                    value = self.function_expression()
                elif (
                    self.token_handler.check_type_value(TokenType.KEYWORD, "auto")
                    and member_kind == "enumerator"
                ):
                    assigned_value = self.expression()
                    value = AutoLiteral(
                        getattr(member_name, "line"),
                        getattr(member_name, "column"),
                        assigned_value if isinstance(assigned_value, int) else 0,
                    )
                else:
                    value = self.expression()

                member_value = value if value else NothingLiteral()

            if member_kind == "enumerator" and value == None:
                value = IntegerLiteral(
                    getattr(member_name, "line"),
                    getattr(member_name, "column"),
                    count,
                )

                member_value = value
                count += 1
                value = None

            members.append(
                MemberLiteral(
                    getattr(member_name, "line"),
                    getattr(member_name, "column"),
                    getattr(member_name, "value"),
                    member_value,
                    member_type,
                    True,
                    TypeMember(getattr(member_name, "value"), member_type, True),
                )
            )

            if not self.token_handler.match_type(TokenType.COMMA):
                if self.token_handler.check_type(TokenType.RIGHT_BRACE):
                    break

        self.token_handler.expect_type(
            TokenType.RIGHT_BRACE, "Expected `}` after members"
        )

        self.logger.debug("parse_members", members)
        return members

    def parse_elements(self, delimiter: TokenType = TokenType.RIGHT_BRACKET) -> list:
        token: Token | None = self.token_handler.previous()

        elements: list[ElementLiteral] = []

        if self.token_handler.check_type(delimiter):
            return elements

        while True:
            expression: ASTNode = self.expression()
            
            key = None
            value = expression
            
            # Check for key -> value (dictionary or named tuple)
            if self.token_handler.match_type(TokenType.ASSIGNMENT):
                key = expression
                value = self.expression()

            element: ElementLiteral = ElementLiteral(
                getattr(value, "line") or getattr(token, "line"),
                getattr(value, "column") or getattr(token, "column"),
                key, # Now supports ASTNode as key
                value,
                True,
                getattr(value, "type", TypeVariant),
                TypeElement(
                    getattr(key, "value", None) if isinstance(key, Identifier) else str(key) if key else None,
                    getattr(value, "type", TypeVariant),
                    True,
                ),
            )

            elements.append(element)

            if self.token_handler.match_type(TokenType.COMMA):
                if self.token_handler.check_type(delimiter): # Allow trailing comma
                    break
                continue

            elif self.token_handler.check_type(delimiter):
                break

            else:
                raise self.logger.error_expect_token(
                    f"Expected `,` or `{delimiter.name}` in elements", self.token_handler.peek()
                )

        return elements

    def parse_iterators(self) -> list:
        iterators: list = []

        if self.token_handler.check_type(TokenType.RIGHT_PAREN):
            self.token_handler.advance()
            return iterators

        while True:
            iterator: Token | None = self.token_handler.expect_type(
                TokenType.IDENTIFIER, "Expected iterator name"
            )
            iterator_name: str = getattr(iterator, "value")

            iterator_type: str = "Variant"
            if self.token_handler.check_type(TokenType.TYPE_SET):
                self.token_handler.expect_type(
                    TokenType.TYPE_SET, "Expected type setter `:` after iterator name"
                )
                type: Token | None = self.token_handler.expect_type(
                    TokenType.TYPE, "Expected iterator type"
                )
                iterator_type = type.value if type else "Variant"

            # iterators.append({"name": iterator_name, "type": iterator_type})
            iterators.append(
                Identifier(
                    getattr(iterator, "line"),
                    getattr(iterator, "column"),
                    self.scope_manager.get_scope_level("global"),
                    iterator_name,
                    iterator_type,
                )
            )

            if self.token_handler.match_type(TokenType.COMMA):
                continue
            elif self.token_handler.match_type(TokenType.RIGHT_PAREN):
                break
            else:
                raise self.logger.error_expect_token(
                    "Expected `,` or `)` in iterators", self.token_handler.peek()
                )

        self.logger.debug("parse_iterators", iterators)

        return iterators
    def check_expression(self) -> CheckExpression:
        token = self.token_handler.previous()
        expression = self.expression()
        or_value: ASTNode | None = None

        if self.token_handler.match_type(TokenType.OR) or self.token_handler.match_type(TokenType.OR):
            if self.token_handler.check_type(TokenType.LEFT_BRACE):
                or_value = self.statement_handler.block_statement("or")
            else:
                or_value = self.expression()
        elif isinstance(expression, BinaryOperation) and expression.operator == "or":
            or_value = expression.right
            expression = expression.left

        return CheckExpression(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_scope_level("global"),
            expression,
            or_value
        )
