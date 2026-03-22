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
    AssignmentStatement,
    ASTNode,
    BlockStatement,
    BreakStatement,
    ContinueStatement,
    DoStatement,
    EnumeratorStatement,
    ExpressionStatement,
    ObjectStatement,
    TypeLiteral,
    VariantLiteral,
    IteratorLiteral,
    WhenStatement,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    BinaryOperation,
    BlockExpression,
    Identifier,
    MemberReassignmentStatement,
    ImportStatement,
    FromImportStatement,
    ClassStatement,
    FunctionStatement,
    ReassignmentStatement,
    ReturnStatement,
    ScopeStatement,
    StructureStatement,
    ExportStatement,
)
from Parser.ExpressionHandler import ExpressionHandler
from Parser.Scope import ScopeManager


class StatementHandler:
    def __init__(self, token_handler, logger: ParserLogger) -> None:
        self.token_handler = token_handler
        self.logger: ParserLogger = logger
        self.scope_manager: ScopeManager = ScopeManager()
        self.expression_handler: ExpressionHandler = ExpressionHandler(
            self.token_handler, self.scope_manager, self.logger, self
        )

    def statement(self) -> ASTNode | None:
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

        # Keyword Statements
        if self.token_handler.check_type(TokenType.KEYWORD):
            if self.token_handler.check_value("let"):
                return self.assignment_statement()

            if self.token_handler.check_value("set"):
                return self.assignment_statement()

            if self.token_handler.check_value("function"):
                return self.function_statement()

            if self.token_handler.check_value("structure"):
                return self.structure_statement()

            if self.token_handler.check_value("enumerator"):
                return self.enumerator_statement()

            if self.token_handler.check_value("return"):
                return self.return_statement()

            if self.token_handler.check_value("when"):
                return self.when_statement()

            if self.token_handler.check_value("class"):
                return self.class_statement()

            if self.token_handler.check_value("do"):
                return self.do_statement()

            if self.token_handler.check_value("break"):
                return self.break_statement()

            if self.token_handler.check_value("continue"):
                return self.continue_statement()

            if self.token_handler.check_value("while"):
                token = self.token_handler.advance()
                self.scope_manager.enter("loop")
                return self._do_while(token)

            if self.token_handler.check_value("for"):
                token = self.token_handler.advance()
                self.scope_manager.enter("loop")
                return self._do_for(token)

            if self.token_handler.check_value("until"):
                token = self.token_handler.advance()
                self.scope_manager.enter("loop")
                return self._do_until(token)

            if self.token_handler.check_value("import"):
                return self.import_statement()

            if self.token_handler.check_value("from"):
                return self.from_import_statement()

            if self.token_handler.check_value("scope"):
                return self.scope_statement()

            if self.token_handler.check_value("defer"):
                return self.defer_statement()

            if self.token_handler.check_value("raise"):
                return self.raise_statement()

            if self.token_handler.check_value("assert"):
                return self.assert_statement()

            if self.token_handler.check_value("check"):
                return self.check_statement()

            if self.token_handler.check_value("object"):
                return self.object_statement()

            if self.token_handler.check_value("export"):
                return self.export_statement()

        # Variable or Member Reassignment
        if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
            if self.token_handler.check_type(TokenType.ASSIGNMENT, 1):
                return self.reassignment_statement()
            if self.token_handler.check_type(TokenType.DOT, 1) and self.token_handler.check_type(TokenType.ASSIGNMENT, 3):
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

    def assignment_statement(self) -> AssignmentStatement:
        """
        Entry for 'assignment' statement.
        Supports:
        mutable:
            let <identifier>
            let <identifier> : <type>
            let <identifier> -> <expression>
            let <identifier> : <type> -> <expression>
        immutable:
            set <identifier> -> <expression>
            set <identifier> : <type> -> <expression>
        """
        statement: AssignmentStatement | None = None
        token: Token | None = None
        identifier: Token | None = None
        value: ASTNode | None = None
        declared_type: Type = TypeVariant()
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
        """
        Entry for 'reassignment' statement.
        Supports:
        mutable:
            <identifier> -> <expression>
        """
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

    def expression_statement(self) -> ExpressionStatement:
        expression: ASTNode = self.expression_handler.expression()
        statement: ExpressionStatement = ExpressionStatement(expression)

        self.logger.debug("expression_statement", statement)
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

    def return_statement(self) -> ReturnStatement:
        """
        Entry for 'return' statement.
        Supports:
            return <expression>
            <- <expression>
        """
        token: Token | None = None
        if self.token_handler.check_value("return"):
            token = self.token_handler.advance()
        else:
            token = self.token_handler.expect_type(
                TokenType.RETURN, "Expected return keyword or operator `<-`"
            )
        statement: ASTNode | None = None
        value: ASTNode | None = None
        inferred_type: Type = TypeVoid()

        if not self.token_handler.check_type(TokenType.RIGHT_BRACE):
            value = self.expression_handler.expression()

        if value and hasattr(value, "type"):
            inferred_type = getattr(value, "type")
        elif value and hasattr(value, "inferred_type"):
            inferred_type = getattr(value, "inferred_type")
        elif value and hasattr(value, "inferred_return_type"):
            inferred_type = getattr(value, "inferred_return_type")
        elif value and not hasattr(value, "type"):
            inferred_type = TypeVariant()

        statement = ReturnStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            value,
            inferred_type,
        )

        self.logger.debug("return_statement", statement)
        return statement

    def when_statement(self) -> WhenStatement:
        token = self.token_handler.expect_type(TokenType.KEYWORD, "when")
        self.scope_manager.enter("when")
        condition = self.expression_handler.expression(allow_instantiation=False)
        when_block = self.block_statement("when")
        conditional_blocks: list = []
        or_block: ASTNode | None = None

        while self.token_handler.match_type(TokenType.OR):
            if not self.token_handler.check_type(TokenType.LEFT_BRACE):
                self.token_handler.match_type_value(TokenType.KEYWORD, "when")
                conditional_condition: ASTNode = self.expression_handler.expression(allow_instantiation=False)
                conditional_block: ASTNode = self.block_statement("conditional")
                conditional_blocks.append(
                    {"condition": conditional_condition, "block": conditional_block}
                )
            else:
                or_block = self.block_statement("or")
                break

        statement = WhenStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            condition,
            when_block,
            conditional_blocks,
            or_block,
        )
        self.scope_manager.exit("when")
        self.logger.debug("when_statement", statement)
        return statement

    def do_statement(self) -> DoStatement:
        token = self.token_handler.expect_type(TokenType.KEYWORD, "Expected `do` keyword")
        self.scope_manager.enter("loop")

        if self.token_handler.match_type_value(TokenType.KEYWORD, "for"):
            return self._do_for(token)
        if self.token_handler.match_type_value(TokenType.KEYWORD, "while"):
            return self._do_while(token)
        if self.token_handler.match_type_value(TokenType.KEYWORD, "until"):
            return self._do_until(token)
        if self.token_handler.match_type_value(TokenType.KEYWORD, "when"):
            return self._do_when(token)

        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            block = self.block_statement()
            if self.token_handler.match_type_value(TokenType.KEYWORD, "while"):
                condition = self.expression_handler.expression(allow_instantiation=False)
                or_block = self.block_statement() if (self.token_handler.match_type(TokenType.OR)) else None
                statement = DoStatement(
                    getattr(token, "line"), getattr(token, "column"), "while_post",
                    self.scope_manager.get_current_scope_level(), block, condition, or_block=or_block,
                )
                self.scope_manager.exit("loop")
                return statement
            if self.token_handler.match_type_value(TokenType.KEYWORD, "until"):
                condition = self.expression_handler.expression(allow_instantiation=False)
                statement = DoStatement(
                    getattr(token, "line"), getattr(token, "column"), "until_post",
                    self.scope_manager.get_current_scope_level(), block, condition,
                )
                self.scope_manager.exit("loop")
                return statement
            statement = DoStatement(
                getattr(token, "line"), getattr(token, "column"), "block",
                self.scope_manager.get_current_scope_level(), block,
            )
            self.scope_manager.exit("loop")
            return statement

        raise self.logger.error_expect_token("Expected loop modifier or block after `do`", self.token_handler.peek())

    def _do_for(self, token: Token | None) -> DoStatement:
        iterator: ASTNode | str | None = None
        if self.token_handler.check_type(TokenType.LEFT_PAREN):
            self.token_handler.advance()
            iterators = self.expression_handler.parse_iterators()
            iterator = IteratorLiteral(getattr(token, "line"), getattr(token, "column"), iterators if iterators else [VariantLiteral(getattr(token, "line"), getattr(token, "column"), "key"), VariantLiteral(getattr(token, "line"), getattr(token, "column"), "value")])
        else:
            iterator = getattr(self.token_handler.advance(), "value") if self.token_handler.check_type(TokenType.IDENTIFIER) else "iterator"

        if not self.token_handler.match_type_value(TokenType.KEYWORD, "in"):
            raise self.logger.error_expect_token("Expected `in` after iterator in `for` loop", self.token_handler.peek())
        iterable = self.expression_handler.expression(allow_instantiation=False)
        block = self.block_statement()
        or_block = self.block_statement() if (self.token_handler.match_type(TokenType.OR)) else None
        statement = DoStatement(
            getattr(token, "line"), getattr(token, "column"), "for", self.scope_manager.get_current_scope_level(),
            block, iterator=iterator, iterable=iterable, or_block=or_block,
        )
        self.scope_manager.exit("loop")
        return statement

    def _do_while(self, token: Token | None) -> DoStatement:
        condition = self.expression_handler.expression(allow_instantiation=False)
        block = self.block_statement()
        else_block = self.block_statement() if (self.token_handler.match_type(TokenType.OR)) else None
        statement = DoStatement(
            getattr(token, "line"), getattr(token, "column"), "while",
            self.scope_manager.get_current_scope_level(), block, condition, or_block=else_block,
        )
        self.scope_manager.exit("loop")
        return statement

    def _do_until(self, token: Token | None) -> DoStatement:
        condition = self.expression_handler.expression(allow_instantiation=False)
        block = self.block_statement()
        statement = DoStatement(
            getattr(token, "line"), getattr(token, "column"), "until",
            self.scope_manager.get_current_scope_level(), block, condition,
        )
        self.scope_manager.exit("loop")
        return statement

    def _do_when(self, token: Token | None) -> DoStatement:
        condition = self.expression_handler.expression(allow_instantiation=False)
        self.scope_manager.enter("when")
        block = self.block_statement("when")
        self.scope_manager.exit("when")
        statement = DoStatement(
            getattr(token, "line"), getattr(token, "column"), "when",
            self.scope_manager.get_current_scope_level(), block, condition,
        )
        self.scope_manager.exit("loop")
        return statement

    def break_statement(self) -> BreakStatement:
        token = self.token_handler.expect_type(TokenType.KEYWORD, "Expected `break` keyword")
        statement = BreakStatement(getattr(token, "line"), getattr(token, "column"), self.scope_manager.get_current_scope_level())
        return statement

    def continue_statement(self) -> ContinueStatement:
        token = self.token_handler.expect_type(TokenType.KEYWORD, "Expected `continue` keyword")
        statement = ContinueStatement(getattr(token, "line"), getattr(token, "column"), self.scope_manager.get_current_scope_level())
        return statement

    def parse_import_path(self) -> str:
        path = ""
        
        # Check for string literal path
        if self.token_handler.check_type(TokenType.STRING):
            token = self.token_handler.advance()
            return getattr(token, "value")

        # Expect first identifier
        if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
             token = self.token_handler.advance()
             path += getattr(token, "value")
        else:
             raise self.logger.error_expect_token("Expected path identifier after import/from", self.token_handler.peek())
             
        while True:
            if self.token_handler.match_type(TokenType.DOT):
                path += "."
                if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD]):
                     token = self.token_handler.advance()
                     path += getattr(token, "value")
                else:
                     raise self.logger.error_expect_token("Expected identifier after dot in import path", self.token_handler.peek())
            else:
                break
                
        return path

    def import_statement(self) -> ImportStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "import", "Expected `import` keyword")
        
        path = self.parse_import_path()
        
        alias: str | None = None
        if self.token_handler.check_value("as"):
            self.token_handler.advance()
            alias_token = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected alias identifier after `as`")
            alias = getattr(alias_token, "value")
        
        # If path is dotted (e.g. tests.modules.MyLib) and no alias, alias is the last part? 
        # Or alias is the full path?
        # In python: import a.b.c -> name is a.b.c, but it binds 'a' in scope.
        # ZenLang spec isn't ultra clear but let's assume 'alias' is the name to bind.
        # If no alias, we bind the first part or the whole thing?
        # The interpreter uses 'alias' to define in env.
        if not alias:
            # Default alias behavior: 
            # For 'import a.b.c', do we bind 'a'? or 'c'?
            # The interpreter currently defines 'node.name' (which is passed alias or path).
            # And it uses `self._load_module(node.path, node.name, ...)`
            # If I pass path as name, it defines 'tests.modules.MyLib' as a symbol.
            pass

        name = alias if alias else path.split('.')[-1]
        statement = ImportStatement(getattr(token, "line"), getattr(token, "column"), name, path, alias)
        return statement

    def from_import_statement(self) -> FromImportStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "from", "Expected `from` keyword")
        
        path = self.parse_import_path()
        
        self.token_handler.expect_type_value(TokenType.KEYWORD, "import", "Expected `import` keyword after path")

        symbols = []
        while True:
            # We allow identifiers or even keywords (like 'in') if they are being imported
            symbol_token = None
            if self.token_handler.check_type(TokenType.IDENTIFIER):
                symbol_token = self.token_handler.advance()
            elif self.token_handler.check_type(TokenType.KEYWORD):
                symbol_token = self.token_handler.advance()
            else:
                raise self.logger.error_expect_token("Expected symbol name in import list", self.token_handler.peek())

            symbol_name = getattr(symbol_token, "value")
            symbol_alias = None

            if self.token_handler.check_value("as"):
                self.token_handler.advance()
                alias_token = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected alias after `as`")
                symbol_alias = getattr(alias_token, "value")

            symbols.append({"name": symbol_name, "alias": symbol_alias})

            if self.token_handler.match_type(TokenType.COMMA):
                continue
            break

        return FromImportStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            path,
            symbols
        )

    def scope_statement(self) -> ScopeStatement:
        token = self.handle_declaration("scope")
        identifier = self.handle_identifier()

        block = self.block_statement("scope")

        statement = ScopeStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            getattr(identifier, "value"),
            block
        )
        self.logger.debug("scope_statement", statement)
        return statement

    def export_statement(self) -> ExportStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "export", "Expected `export` keyword")
        
        # export { ... } or export statement
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            statement = self.block_statement("export")
        else:
            statement = self.statement()

        return ExportStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            statement
        )

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
            if not t: break
            if self.token_handler.check_type(TokenType.COMMENT):
                self.token_handler.advance()
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
        return self.token_handler.expect_types([TokenType.IDENTIFIER, TokenType.KEYWORD], f"Expected `identifier` after declaration `{getattr(previous_token, 'value')}`")

    def handle_typing(self, is_return: bool = False) -> tuple[Type, ASTNode | None]:
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
            self.token_handler.expect_type(TokenType.ASSIGNMENT, "Expected assignment operator '->' after identifier")
            return self.expression_handler.expression()
        elif mutable and value is None:
            if self.token_handler.match_type(TokenType.ASSIGNMENT): return self.expression_handler.expression()
        return None

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

        # Parse expression. We use equality() here to avoid consuming 'or' if it's a block.
        # But ZenLang allows 'check a or b'. 
        # So we use expression() but we might need to adjust.
        # For now, let's use a trick: parse the expression, 
        # but if it ends up being a BinaryOperation with 'or', we might need to split it.
        # Actually, the simplest way is to manually parse logical WITHOUT the final 'or' loop if followed by '{'
        expression = self.expression_handler.expression()
        
        cases: list = []
        or_block: ASTNode | None = None

        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
                if self.token_handler.match_type_value(TokenType.KEYWORD, "case"):
                    case_condition = self.expression_handler.expression()
                    case_block = self.block_statement("case")
                    cases.append({"condition": case_condition, "block": case_block})
                    if self.token_handler.match_type(TokenType.COMMA):
                        continue
                else:
                    break
            self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after check cases")
        
        # Check for 'or' block
        if self.token_handler.match_type(TokenType.OR):
            if self.token_handler.check_type(TokenType.LEFT_BRACE):
                or_block = self.block_statement("or")
            else:
                or_block = self.expression_statement()
        elif isinstance(expression, BinaryOperation) and expression.operator == "or":
            # If the expression we parsed ended with 'or', split it.
            or_block = ExpressionStatement(expression.right)
            expression = expression.left

        return CheckStatement(
            getattr(token, "line"),
            getattr(token, "column"),
            self.scope_manager.get_current_scope_level(),
            expression,
            cases,
            or_block
        )
