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
    TaskStatement,
    ObjectStatement,
    EnumeratorStatement,
    ClassStatement,
    Identifier,
    MemberExpression,
    IndexExpression,
    TypeLiteral,
    ReturnStatement,
    BlockStatement
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
        statement.is_set = (getattr(token, "value") == "set")

        self.logger.debug("assignment_statement", statement)

        return statement

    def reassignment_statement(self) -> ReassignmentStatement:
        from Zen import zen_trace
        zen_trace(f"ENTER reassignment_statement at line {self.token_handler.peek().line}")
        
        # Parse the left-hand side as an expression (MemberExpression, Identifier, or IndexExpression)
        target = self.expression_handler.expression()
        
        # Expect assignment operator
        self.token_handler.expect_types(
            [TokenType.ASSIGNMENT, TokenType.EQUAL],
            "Expected `->` or `=` after reassignment target"
        )
        
        # Parse the value
        value = self.expression_handler.expression()
        
        from Parser.AST import UnaryOperation, DereferenceReassignmentStatement
        if isinstance(target, UnaryOperation) and target.operator == "target":
            return DereferenceReassignmentStatement(
                target.line, target.column, target.right, value, self.scope_manager.get_current_scope_level()
            )
        elif isinstance(target, MemberExpression):
            return MemberReassignmentStatement(
                target.line, target.column, self.scope_manager.get_current_scope_level(),
                target.object, target.property, value, "MemberReassignment"
            )
        elif isinstance(target, IndexExpression):
            return IndexReassignmentStatement(
                target.line, target.column, self.scope_manager.get_current_scope_level(),
                target.object, target.index, value, "IndexReassignment"
            )
        else:
            # Fallback to simple variable reassignment
            name = getattr(target, "name", str(target))
            return ReassignmentStatement(
                target.line, target.column, name, value, None, True, self.scope_manager.get_current_scope_level()
            )

    def function_statement(self) -> FunctionStatement:
        """
        Entry for 'function' statement.
        Supports:
            function <identifier> { ... }
            function <identifier> : <type> { ... }
            function <identifier> ( <parameters> ) { ... }
            function <identifier> ( <parameters> ) : <type> { ... }
            function <identifier> ( <parameters> ) <- <expression>
            function <identifier> ( <parameters> ) : <type> <- <expression>
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

        # Parameters and Return Type (flexible order: `(params) : Type` or `: Type (params)`)
        if self.token_handler.check_type(TokenType.TYPE_SET):
            inferred_return_type, _ = self.handle_typing()
            if self.token_handler.check_type(TokenType.LEFT_PAREN):
                parameters = self.expression_handler.parse_parameters()
        elif self.token_handler.check_type(TokenType.LEFT_PAREN):
            parameters = self.expression_handler.parse_parameters()
            if self.token_handler.check_type(TokenType.TYPE_SET):
                inferred_return_type, _ = self.handle_typing()

        # Block Scope or Concise Expression Return (<- expr or -> expr)
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            block = self.block_statement("function")
        elif (
            self.token_handler.match_type(TokenType.RETURN)
            or self.token_handler.match_type(TokenType.ASSIGNMENT)
            or self.token_handler.match_type_value(TokenType.KEYWORD, "return")
        ):
            expr = self.expression_handler.expression()
            ret_stmt = ReturnStatement(
                line=expr.line,
                column=expr.column,
                scope_level=self.scope_manager.get_current_scope_level(),
                value=expr,
                inferred_type=None,
            )
            block = BlockStatement(
                line=expr.line,
                column=expr.column,
                scope_level=self.scope_manager.get_current_scope_level(),
                scope_type="function",
                statements=[ret_stmt],
            )
        else:
            raise self.logger.error_expect_token(
                "Expected `{`, `<-`, or `->` after function declaration", self.token_handler.peek()
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
        if self.filename: statement.filename = self.filename

        self.logger.debug("function_statement", statement)

        return statement

    def task_statement(self) -> TaskStatement:
        token: Token | None = None
        token = self.handle_declaration("task")
        parameters = []
        inferred_return_type = None

        # Identifier
        identifier = self.handle_identifier()

        # Parameters
        if self.token_handler.check_type(TokenType.LEFT_PAREN):
            parameters = self.expression_handler.parse_parameters()

        # Return Type
        inferred_return_type, _ = self.handle_typing()
        if not inferred_return_type: inferred_return_type = TypeVoid()

        # Block Scope or Concise Expression Return (<- expr)
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            block = self.block_statement("task")
        elif self.token_handler.match_type(TokenType.RETURN) or self.token_handler.match_type_value(TokenType.KEYWORD, "return"):
            expr = self.expression_handler.expression()
            ret_stmt = ReturnStatement(
                line=expr.line,
                column=expr.column,
                scope_level=self.scope_manager.get_current_scope_level(),
                value=expr,
                inferred_type=None,
            )
            block = BlockStatement(
                line=expr.line,
                column=expr.column,
                scope_level=self.scope_manager.get_current_scope_level(),
                scope_type="task",
                statements=[ret_stmt],
            )
        else:
            raise self.logger.error_expect_token(
                "Expected `{` or `<-` after task identifier", self.token_handler.peek()
            )

        statement = TaskStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifier, "value"),
            parameters,
            block,
            inferred_return_type,
        )
        if self.filename: statement.filename = self.filename

        self.logger.debug("task_statement", statement)
        return statement

    def _parse_is_traits(self) -> list:
        """Parse zero or more `is Trait` (optionally `is A, B`) after a type name."""
        traits: list = []
        while True:
            tok = self.token_handler.peek()
            is_kw = (
                tok
                and getattr(tok, "value", None) == "is"
                and tok.type in (TokenType.KEYWORD, TokenType.IS, TokenType.IDENTIFIER)
            )
            if not is_kw:
                break
            self.token_handler.advance()
            # trait name: identifier (reflectable) or keyword
            if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
                traits.append(getattr(self.token_handler.advance(), "value"))
            else:
                raise self.logger.error_expect_token(
                    "Expected trait name after `is`", self.token_handler.peek()
                )
            while self.token_handler.match_type(TokenType.COMMA):
                if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
                    traits.append(getattr(self.token_handler.advance(), "value"))
                else:
                    raise self.logger.error_expect_token(
                        "Expected trait name after `,`", self.token_handler.peek()
                    )
        return traits

    def structure_statement(self) -> StructureStatement:
        """
        Entry for 'structure' statement.
        Supports:
            structure <identifier> [is reflectable] [extends Parent] { ... }
        """
        token: Token | None = None
        identifier: Token | None = None
        statement: ASTNode | None = None
        members: list | None = None

        # Keyword
        token = self.handle_declaration("structure")

        # Identifier
        identifier = self.handle_identifier()

        traits = self._parse_is_traits()
        reflectable = "reflectable" in traits

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
            reflectable=reflectable,
        )

        self.logger.debug("structure_statement", statement)
        return statement

    def object_statement(self) -> ObjectStatement:
        """
        Entry for 'object' statement.
        Supports:
            object <identifier> [is reflectable] [extends Parent] { ... }
        """
        token: Token | None = None
        identifier: Token | None = None
        statement: ASTNode | None = None
        members: list | None = None

        # Keyword
        token = self.handle_declaration("object")

        # Identifier
        identifier = self.handle_identifier()

        traits = self._parse_is_traits()
        reflectable = "reflectable" in traits

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
            reflectable=reflectable,
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
        traits = self._parse_is_traits()
        reflectable = "reflectable" in traits
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
        statement = ClassStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            0,
            getattr(identifier, "value"),
            getattr(parent_identifier, "value") if parent_identifier else None,
            members,
            methods,
            reflectable=reflectable,
        )
        if self.filename: statement.filename = self.filename
        return statement

    def handle_declaration(self, value: str) -> Token | None:
        return self.token_handler.expect_type_value(TokenType.KEYWORD, value, f"Expected `{value}` declaration")

    def handle_assignment_declaration(self) -> tuple[Token | None, bool]:
        token = self.token_handler.expect_type_values(TokenType.KEYWORD, ["let", "set"], "Expected assignment `let` or `set` declaration")
        return token, True

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
        return value
