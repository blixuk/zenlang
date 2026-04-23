from typing import List, Optional
from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    AssignmentStatement,
    ReassignmentStatement,
    MemberReassignmentStatement,
    IndexReassignmentStatement,
    FunctionStatement,
    StructureStatement,
    ObjectStatement,
    EnumeratorStatement,
    ClassStatement,
    Identifier,
    TypeLiteral
)
from Checker.Type import Type, TypeVoid

class DeclarationParserMixin:
    def assignment_statement(self) -> AssignmentStatement:
        from Zen import zen_trace
        zen_trace(f"ENTER assignment_statement at line {self.token_handler.peek().line}")
        statement: AssignmentStatement | None = None
        token: Token | None = None
        identifier: Token | None = None
        value: ASTNode | None = None
        declared_type: Type | None = None
        mutable: bool = False

        # Keyword
        token, mutable = self.handle_assignment_declaration()

        # Identifier
        identifier = self.handle_identifier()

        # Type
        declared_type, value = self.handle_typing()

        # Assignment
        value = self.handle_assignment(value, mutable)

        statement = AssignmentStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            getattr(identifier, "value"),
            value,
            declared_type,
            mutable,
            self.scope_manager.get_current_scope_level(),
        )

        self.logger.debug("assignment_statement", statement)

        return statement

    def reassignment_statement(self) -> ReassignmentStatement:
        from Zen import zen_trace
        zen_trace(f"ENTER reassignment_statement at line {self.token_handler.peek().line}")
        statement: ReassignmentStatement | None = None
        token: Token | None = None
        value: ASTNode | None = None
        inferred_type: Type | None = None
        mutable: bool = True

        # Identifier
        token = self.token_handler.expect_types(
            [TokenType.IDENTIFIER, TokenType.KEYWORD],
            "Expected `identifier` before assignment operator `->`",
        )

        # check for member reassignment
        if self.token_handler.check_type(TokenType.DOT):
             self.token_handler.advance() # consume '.'
             property_token = self.token_handler.expect_types(
                 [TokenType.IDENTIFIER, TokenType.KEYWORD], 
                 "Expected property name after `.`"
             )
             
             # Create callee node for MemberReassignment
             callee_node = Identifier(
                 getattr(token, "line"),
                 getattr(token, "column"),
                 self.scope_manager.get_current_scope_level(),
                 getattr(token, "value"),
                 "Identifier"
             )
             
             # Assignment
             value = self.handle_assignment(value, mutable)
             
             statement = MemberReassignmentStatement(
                 getattr(token, "line"),
                 getattr(token, "column"),
                 self.scope_manager.get_current_scope_level(),
                 callee_node,
                 getattr(property_token, "value"),
                 value,
                 "MemberReassignment"
             )
             self.logger.debug("member_reassignment_statement", statement)
             return statement

        # check for index reassignment
        if self.token_handler.check_type(TokenType.LEFT_BRACKET):
             self.token_handler.advance() # consume '['
             index_expr = self.expression_handler.expression()
             self.token_handler.expect_type(TokenType.RIGHT_BRACKET, "Expected `]` after index")
             
             # Create callee node
             callee_node = Identifier(
                 getattr(token, "line"),
                 getattr(token, "column"),
                 self.scope_manager.get_current_scope_level(),
                 getattr(token, "value"),
                 "Identifier"
             )
             
             # Assignment
             value = self.handle_assignment(value, mutable)
             
             statement = IndexReassignmentStatement(
                 getattr(token, "line"),
                 getattr(token, "column"),
                 self.scope_manager.get_current_scope_level(),
                 callee_node,
                 index_expr,
                 value
             )
             self.logger.debug("index_reassignment_statement", statement)
             return statement

        # Assignment
        value = self.handle_assignment(value, mutable)

        statement = ReassignmentStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            getattr(token, "value"),
            value,
            inferred_type,
            mutable,
            self.scope_manager.get_current_scope_level(),
        )

        self.logger.debug("reassignment_statement", statement)

        return statement

    def function_statement(self) -> FunctionStatement:
        """
        Entry for 'function' statement.
        Supports:
            function <identifier> { ... }
            function <identifier> : <type> { ... }
            function <identifier> ( <parameters> ) { ... }
            function <identifier> ( <parameters> ) : <type> { ... }
        """
        token: Token | None = None
        identifer: Token | None = None
        statement: ASTNode | None = None
        parameters: list = []
        inferred_return_type: Type = TypeVoid()
        block: ASTNode | None = None

        # Keyword
        token = self.handle_declaration("function")

        # Identifer
        identifer = self.handle_identifier()

        # Parameters
        if self.token_handler.check_type(TokenType.LEFT_PAREN):
            parameters = self.expression_handler.parse_parameters()

        # Return Type
        inferred_return_type, _ = self.handle_typing()

        # Block Scope
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            block = self.block_statement("function")
        else:
            raise self.logger.error_expect_token(
                "Expected block after function identifer", self.token_handler.peek()
            )

        statement = FunctionStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifer, "value"),
            parameters,
            block,
            inferred_return_type,
        )

        self.logger.debug("function_statement", statement)

        return statement

    def structure_statement(self) -> StructureStatement:
        """
        Entry for 'structure' statement.
        Supports:
            structure <identifier> { ... }
        """
        token: Token | None = None
        identifier: Token | None = None
        statement: ASTNode | None = None
        members: list | None = None

        # Keyword
        token = self.handle_declaration("structure")

        # Identifier
        identifier = self.handle_identifier()

        parent: Token | None = None
        if self.token_handler.match_type_value(TokenType.KEYWORD, "extends"):
            parent = self.handle_identifier()

        # Members
        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            members = self.expression_handler.parse_members()

        statement = StructureStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifier, "value"),
            members,
            parent=getattr(parent, "value") if parent else None,
        )

        self.logger.debug("structure_statement", statement)
        return statement

    def object_statement(self) -> ObjectStatement:
        """
        Entry for 'object' statement.
        Supports:
            object <identifier> { ... }
        """
        token: Token | None = None
        identifier: Token | None = None
        statement: ASTNode | None = None
        members: list | None = None

        # Keyword
        token = self.handle_declaration("object")

        # Identifier
        identifier = self.handle_identifier()

        parent: Token | None = None
        if self.token_handler.match_type_value(TokenType.KEYWORD, "extends"):
            parent = self.handle_identifier()

        # Members
        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            members = self.expression_handler.parse_members()

        statement = ObjectStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifier, "value"),
            members,
            parent=getattr(parent, "value") if parent else None,
        )

        self.logger.debug("object_statement", statement)
        return statement

    def enumerator_statement(self) -> EnumeratorStatement:
        """
        Entry for 'enumerator' statement.
        Supports:
            enumerator <identifier> { ... }
        """
        token: Token | None = None
        identifier: Token | None = None
        statement: ASTNode | None = None
        members: list | None = None

        # Keyword
        token = self.handle_declaration("enumerator")

        # Identifier
        identifier = self.handle_identifier()

        # Members
        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            members = self.expression_handler.parse_members(member_kind="enumerator")

        statement = EnumeratorStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifier, "value"),
            members,
        )

        self.logger.debug("enumerator_statement", statement)
        return statement

    def class_statement(self) -> ClassStatement:
        token = self.handle_declaration("class")
        identifier = self.handle_identifier()
        parent_identifier: Token | None = None

        if self.token_handler.match_type_value(TokenType.KEYWORD, "extends"):
            parent_identifier = self.handle_identifier()

        self.token_handler.expect_type(TokenType.LEFT_BRACE, "Expected `{` after class name/parent")
        self.scope_manager.enter("class")
        members: list = []
        methods: list = []

        while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
            t = self.token_handler.peek()
            from Logging.Trace import zen_trace
            zen_trace(f"CLASS_MEMBER_PEEK: {t}")
            if not t: break
            if self.token_handler.check_types([TokenType.COMMENT, TokenType.DOC_COMMENT]):
                token = self.token_handler.advance()
                continue
            if t.type == TokenType.KEYWORD:
                if t.value in ["let", "set"]:
                    members.append(self.assignment_statement())
                    continue
                if t.value == "function":
                    methods.append(self.function_statement())
                    continue
            if self.token_handler.check_type(TokenType.IDENTIFIER) and self.token_handler.check_type(TokenType.ASSIGNMENT, 1):
                 raise self.logger.error("Reassignment not allowed in class body. Use 'let' or 'set' for fields.", t)
            raise self.logger.error(f"Unexpected token '{t.value}' in class body", t)

        self.scope_manager.exit("class")
        self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after class body")
        statement = ClassStatement(getattr(token, "line"), getattr(token, "column"), 0, getattr(identifier, "value"), getattr(parent_identifier, "value") if parent_identifier else None, members, methods)
        return statement

    def handle_declaration(self, value: str) -> Token | None:
        return self.token_handler.expect_type_value(TokenType.KEYWORD, value, f"Expected `{value}` declaration")

    def handle_assignment_declaration(self) -> tuple[Token | None, bool]:
        token = self.token_handler.expect_type_values(TokenType.KEYWORD, ["let", "set"], "Expected assignment `let` or `set` declaration")
        return token, getattr(token, "value") == "let"

    def handle_identifier(self) -> Token | None:
        previous_token = self.token_handler.previous()
        return self.token_handler.expect_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE], f"Expected `identifier` after declaration `{getattr(previous_token, 'value')}`")

    def handle_typing(self, is_return: bool = False) -> tuple[Type | None, ASTNode | None]:
        declared_type: TypeLiteral | None = None
        value: ASTNode | None = None
        if self.token_handler.match_type(TokenType.TYPE_SET):
            declared_type = self.expression_handler.parse_types()
        elif self.token_handler.match_type(TokenType.TYPE_LET):
            value = self.expression_handler.expression()
            if hasattr(value, "type"):
                declared_type = getattr(value, "type")
        return declared_type, value

    def handle_assignment(self, value: ASTNode | None, mutable: bool) -> ASTNode | None:
        if not mutable and value is None:
            self.token_handler.expect_types([TokenType.ASSIGNMENT, TokenType.EQUAL], "Expected assignment operator '->' or '=' after identifier")
            return self.expression_handler.expression()
        elif mutable and value is None:
            if self.token_handler.match_types([TokenType.ASSIGNMENT, TokenType.EQUAL]): return self.expression_handler.expression()
        return None
