from typing import List, Optional
from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    DoStatement,
    BreakStatement,
    ContinueStatement,
    ReturnStatement,
    WhenStatement,
    CaseBranch,
    IteratorLiteral,
    VariantLiteral
)
from Checker.Type import Type, TypeVoid, TypeVariant

class ControlFlowParserMixin:
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
        
        branches: Optional[List[CaseBranch]] = None
        when_block: Optional[ASTNode] = None
        conditional_blocks: list = []
        or_block: ASTNode | None = None

        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            # Peak inside to see if it's a structural match (starts with 'is')
            next_t = self.token_handler.tokens[self.token_handler.current_token + 1]
            if next_t.type == TokenType.KEYWORD and next_t.value == "is":
                self.token_handler.advance() # consume '{'
                branches = []
                while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
                    if self.token_handler.match_type_value(TokenType.KEYWORD, "is"):
                        pattern = self.parse_pattern()
                        block = self.block_statement("case")
                        branches.append(CaseBranch(pattern.line, pattern.column, pattern, block))
                    elif self.token_handler.match_type(TokenType.OR):
                        or_block = self.block_statement("or")
                        break
                    else:
                        raise self.logger.error_expect_token("Expected `is` or `or`", self.token_handler.peek())
                self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after match branches")
            else:
                when_block = self.block_statement("when")
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
            line=getattr(token, "line"),
            column=getattr(token, "column"),
            scope_level=self.scope_manager.get_current_scope_level(),
            condition=condition,
            when_block=when_block,
            conditional_blocks=conditional_blocks,
            or_block=or_block,
            branches=branches,
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
