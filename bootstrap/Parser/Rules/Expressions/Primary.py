from Lexer.Token import TYPE_TOKENS, Token, TokenType
from Parser.AST import (
    ASTNode,
    Identifier,
    MemberExpression,
    MemberReassignmentStatement,
    CallExpression,
    InExpression,
    IndexExpression,
    ListLiteral,
    VectorLiteral,
    MapLiteral,
    SetLiteral,
    TupleLiteral,
    StructureExpression,
    ParentExpression,
    NothingLiteral,
    DefaultLiteral,
    BooleanLiteral,
    IntegerLiteral,
    DecimalLiteral,
    StringLiteral,
    RuneLiteral,
    ElementLiteral
)
from Checker.Type import TypeVariant, TypeElement

class PrimaryExpressionsMixin:
    def _structure_type_name(self, node: ASTNode) -> str:
        """Dotted type path for structure instantiation (Word / text.Word)."""
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, MemberExpression):
            obj = self._structure_type_name(node.object) if hasattr(node, "object") else ""
            prop = node.property
            if hasattr(prop, "value"):
                prop = prop.value
            if hasattr(prop, "name"):
                prop = prop.name
            prop = str(prop)
            return f"{obj}.{prop}" if obj else prop
        return getattr(node, "name", None) or str(node)

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

        if self.token_handler.match_type_value(TokenType.KEYWORD, "await"):
            token = self.token_handler.previous()
            expression = self.expression()
            node = AwaitExpression(
                getattr(token, "line"),
                getattr(token, "column"),
                self.scope_manager.get_current_scope_level(),
                expression
            )
            self.logger.debug("primary await", node)
            return node

        if self.token_handler.check_type(TokenType.CHECK_SYMBOL) or self.token_handler.match_type_value(TokenType.KEYWORD, "check"):
            if self.token_handler.match_type(TokenType.CHECK_SYMBOL):
                 pass 
            primary_check: ASTNode = self.check_expression()

            self.logger.debug("primary check", primary_check)
            return primary_check

        if self.token_handler.match_type_value(TokenType.KEYWORD, "structure") or \
           self.token_handler.match_type_value(TokenType.KEYWORD, "object"):
            primary_structure: ASTNode = self.structure_expression()

            self.logger.debug("primary structure/object", primary_structure)
            return primary_structure

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            token = self.token_handler.previous()
            if self.token_handler.match_type(TokenType.RIGHT_BRACE):
                node = MapLiteral(getattr(token, "line"), getattr(token, "column"), [])
                return node
            
            has_assignment = False
            has_block_indicator = False
            depth = 0
            for i in range(self.token_handler.current_token, len(self.token_handler.tokens)):
                curr_t = self.token_handler.tokens[i]
                if curr_t.type == TokenType.LEFT_BRACE:
                    depth += 1
                elif curr_t.type == TokenType.RIGHT_BRACE:
                    if depth == 0:
                        break
                    depth -= 1
                elif depth == 0:
                    if curr_t.type == TokenType.SEMICOLON:
                        has_block_indicator = True
                        break
                    elif curr_t.type == TokenType.ASSIGNMENT:
                        has_assignment = True
                    elif curr_t.type in [TokenType.RETURN, TokenType.TYPE_LET, TokenType.TYPE_SET]:
                        has_block_indicator = True
                    elif curr_t.type == TokenType.KEYWORD and curr_t.value in ['let', 'set', 'if', 'when', 'for', 'while', 'until', 'do', 'return', 'break', 'continue', 'check', 'raise', 'assert', 'class', 'structure', 'enumerator', 'object', 'defer', 'case', 'with', 'export']:
                        has_block_indicator = True
            
            is_dict = has_assignment and not has_block_indicator
            
            if is_dict:
                elements = self.parse_elements(TokenType.RIGHT_BRACE)
                self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after dictionary literal")
                node = MapLiteral(getattr(token, "line"), getattr(token, "column"), elements)
                return node
            
            primary_block: ASTNode = self.block_expression()
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

        if self.token_handler.check_types(
            [TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE]
        ):
            id_token = self.token_handler.peek()
            val = getattr(id_token, "value")
            if (
                val in ["l", "v", "t", "d", "s", "m"]
                and self.token_handler.check_type(TokenType.LEFT_BRACE, 1)
            ):
                self.token_handler.advance()  
                self.token_handler.advance()  
                elements = self.parse_elements(TokenType.RIGHT_BRACE)
                self.token_handler.expect_type(
                    TokenType.RIGHT_BRACE, "Expected `}` after collection literal"
                )

                if val == "l":
                    node = ListLiteral(
                        getattr(id_token, "line"), getattr(id_token, "column"), elements
                    )
                elif val == "v":
                    node = VectorLiteral(
                        getattr(id_token, "line"), getattr(id_token, "column"), elements
                    )
                elif val == "t":
                    node = TupleLiteral(
                        getattr(id_token, "line"), getattr(id_token, "column"), elements
                    )
                elif val == "d" or val == "m":
                    node = MapLiteral(
                        getattr(id_token, "line"), getattr(id_token, "column"), elements
                    )
                elif val == "s":
                    node = SetLiteral(
                        getattr(id_token, "line"), getattr(id_token, "column"), elements
                    )

                self.logger.debug(f"primary generic literal {val}", node)
                return node

        if (
            self.token_handler.check_types(
                [TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE]
            )
        ) and self.token_handler.check_type(TokenType.DOT, 1):
            primary_member: MemberExpression | None = self.member_expression()

            self.logger.debug("primary member", primary_member)
            return primary_member

        if self.token_handler.match_types(
            [TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE]
        ):
            primary_identifier: ASTNode = self.resolve_identifier()

            self.logger.debug("primary identifier", primary_identifier)
            return primary_identifier

        if self.token_handler.match_type(TokenType.LEFT_PAREN):
            if self.token_handler.match_type(TokenType.RIGHT_PAREN):
                node = TupleLiteral(getattr(token, "line"), getattr(token, "column"), [])
                self.logger.debug("primary empty tuple", node)
                return node
            
            primary_expression: ASTNode = self.expression()
            
            if self.token_handler.match_type(TokenType.COMMA):
                elements = [ElementLiteral(getattr(token, "line"), getattr(token, "column"), None, primary_expression, True, TypeVariant(), TypeElement(None, TypeVariant()))]
                elements.extend(self.parse_elements(TokenType.RIGHT_PAREN)) 
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

        raise self.logger.error_expect_token("Expected expression", self.token_handler.peek())

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

        if self.token_handler.match_type(TokenType.DEFAULT):
            primary_default: DefaultLiteral = DefaultLiteral(
                getattr(token, "line"),
                getattr(token, "column"),
                getattr(token, "value"),
            )
            self.logger.debug("primary default", primary_default)
            return primary_default

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

    def member_expression(
        self,
    ) -> MemberExpression | MemberReassignmentStatement | None:
        expression: ASTNode | None = None
        token: Token | None = None
        callee: Identifier | None = None

        token = self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE])

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
                    [
                        TokenType.IDENTIFIER,
                        TokenType.KEYWORD,
                        TokenType.TYPE,
                        TokenType.NOTHING,
                        TokenType.VOID,
                        TokenType.VARIANT,
                        TokenType.BOOLEAN,
                    ],
                    "Expected property name after `.`",
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


        self.logger.debug("member_expression", expression)

        return expression

    def call(
        self, allow_instantiation: bool = True
    ) -> ASTNode | CallExpression | MemberExpression | IndexExpression | None:
        node: ASTNode | None = self.primary()

        while True:
            if self.token_handler.match_type(TokenType.LEFT_PAREN):
                arguments, arena_target = self.parse_arguments()
                node = CallExpression(
                    getattr(node, "line"),
                    getattr(node, "column"),
                    self.scope_manager.get_scope_level("global"),
                    node,
                    arguments,
                )
                
                if arena_target:
                    node = InExpression(
                        getattr(node, "line"),
                        getattr(node, "column"),
                        self.scope_manager.get_scope_level("global"),
                        arena_target,
                        node
                    )

                continue

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

            if self.token_handler.match_type(TokenType.LEFT_BRACKET):
                index: ASTNode = self.expression()
                self.token_handler.expect_type(
                    TokenType.RIGHT_BRACKET, "Expected `]` after index expression"
                )
                node = IndexExpression(getattr(node, "line"), getattr(node, "column"), node, index)

                continue

            if allow_instantiation and self.token_handler.check_type(
                TokenType.LEFT_BRACE
            ):
                if isinstance(node, (Identifier, MemberExpression)):
                    name = getattr(node, "name", None)
                    if isinstance(node, MemberExpression):
                        name = node.property

                    if name in [
                        "List", "L", "Vector", "V", "Map", "M", "Set", "S", "Tuple", "T",
                    ]:
                        self.token_handler.match_type(TokenType.LEFT_BRACE)
                        elements = self.parse_elements(TokenType.RIGHT_BRACE)
                        self.token_handler.expect_type(
                            TokenType.RIGHT_BRACE, "Expected `}` after elements"
                        )

                        if name in ["List", "L"]:
                            node = ListLiteral(
                                getattr(node, "line"), getattr(node, "column"), elements
                            )
                        elif name in ["Vector", "V"]:
                            node = VectorLiteral(
                                getattr(node, "line"), getattr(node, "column"), elements
                            )
                        elif name in ["Map", "M"]:
                            node = MapLiteral(
                                getattr(node, "line"), getattr(node, "column"), elements
                            )
                        elif name in ["Set", "S"]:
                            node = SetLiteral(
                                getattr(node, "line"), getattr(node, "column"), elements
                            )
                        elif name in ["Tuple", "T"]:
                            node = TupleLiteral(
                                getattr(node, "line"), getattr(node, "column"), elements
                            )
                        continue

                    if self.token_handler.check_type(TokenType.RIGHT_BRACE, 1) or (
                        (
                            self.token_handler.check_type(TokenType.IDENTIFIER, 1)
                            or self.token_handler.check_type(TokenType.KEYWORD, 1)
                        )
                        and (
                            self.token_handler.check_type(TokenType.TYPE_SET, 2)
                            or self.token_handler.check_type(TokenType.ASSIGNMENT, 2)
                            or self.token_handler.check_type(TokenType.TYPE_LET, 2)
                        )
                    ):

                        self.token_handler.match_type(TokenType.LEFT_BRACE)
                        members = self.parse_members(is_instantiation=True)
                        # Preserve qualified type names: text.Word → "text.Word"
                        # (never str(MemberExpression) which breaks native mangling).
                        struct_name = self._structure_type_name(node)
                        node = StructureExpression(
                            getattr(node, "line"),
                            getattr(node, "column"),
                            self.scope_manager.get_scope_level("structure"),
                            struct_name,
                            members,
                        )
                        continue

            break

        self.logger.debug("call", node)
        return node
