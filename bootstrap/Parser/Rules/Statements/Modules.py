from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    ImportStatement,
    FromImportStatement,
    ScopeStatement,
    ExportStatement,
    WithStatement
)

class ModuleParserMixin:
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
        
        name = alias if alias else path.split('.')[-1]
        statement = ImportStatement(getattr(token, "line"), getattr(token, "column"), name, path, alias)
        return statement

    def from_import_statement(self) -> FromImportStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "from", "Expected `from` keyword")
        
        path = self.parse_import_path()
        
        self.token_handler.expect_type_value(TokenType.KEYWORD, "import", "Expected `import` keyword after path")

        symbols = []
        while True:
            symbol_token = None
            if self.token_handler.check_type(TokenType.IDENTIFIER):
                symbol_token = self.token_handler.advance()
                symbol_name = getattr(symbol_token, "value")
            elif self.token_handler.check_type(TokenType.KEYWORD):
                symbol_token = self.token_handler.advance()
                symbol_name = getattr(symbol_token, "value")
            else:
                raise self.logger.error_expect_token("Expected symbol name in import list", self.token_handler.peek())

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

    def with_statement(self) -> WithStatement:
        token = self.token_handler.expect_type_value(TokenType.KEYWORD, "with", "Expected `with` keyword")
        expression = self.expression_handler.expression()
        
        alias = ""
        if self.token_handler.match_type_value(TokenType.KEYWORD, "as"):
            alias_token = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected alias after `as`")
            alias = getattr(alias_token, "value")
        
        block = self.block_statement("with")
        
        statement = WithStatement(
            line=getattr(token, "line"), 
            column=getattr(token, "column"), 
            scope_level=self.scope_manager.get_current_scope_level(),
            expression=expression, 
            alias=alias, 
            body=block
        )
        self.logger.debug("with_statement", statement)
        return statement
