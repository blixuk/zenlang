from typing import Optional
from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    TypeLiteral,
    ParameterLiteral,
    MemberLiteral,
    ElementLiteral,
    EnumVariant,
    NothingLiteral,
    AutoLiteral,
    IntegerLiteral,
    Identifier
)
from Checker.Type import PRIMITIVE_TYPES, Type, TypeVariant, TypeMember, TypeElement, TypeParameter

class ParsingHelpersMixin:
    def parse_types(self) -> TypeLiteral:
        qualifier = None
        if self.token_handler.check_type_value(TokenType.KEYWORD, "borrowed") or \
           self.token_handler.check_type_value(TokenType.KEYWORD, "owned"):
            qual_tok = self.token_handler.advance()
            qualifier = qual_tok.value

        token = self.token_handler.expect_types([TokenType.TYPE, TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected type name")
        name = getattr(token, "value")
        
        while self.token_handler.match_type(TokenType.DOT):
            member = self.token_handler.expect_types([TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected member name after `.`")
            name += "." + getattr(member, "value")
            
        node = TypeLiteral(getattr(token, "line"), getattr(token, "column"), name=name)
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
            
        if qualifier:
            wrapper = TypeLiteral(getattr(token, "line"), getattr(token, "column"), name=qualifier)
            wrapper.subtypes = [node]
            return wrapper
            
        return node

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

                parameter_type = self.parse_types()

            parameter_value: ASTNode | None = NothingLiteral()
            if self.token_handler.match_type(TokenType.ASSIGNMENT):
                parameter_value = self.expression()

            parameters.append(
                ParameterLiteral(
                    line=getattr(parameter, "line"),
                    column=getattr(parameter, "column"),
                    name=parameter_name,
                    value=parameter_value,
                    declared_type=parameter_type,
                    type=TypeParameter(parameter_name, parameter_type, parameter_value),
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

    def parse_arguments(self) -> tuple[list, Optional[str]]:
        arguments: list = []
        arena_target: Optional[str] = None

        if self.token_handler.check_type(TokenType.RIGHT_PAREN):
            self.token_handler.advance()
            return arguments, None

        if self.token_handler.check_value("in"):
            self.token_handler.advance()  # consume `in`
            arena_token = self.token_handler.expect_types(
                [TokenType.IDENTIFIER, TokenType.KEYWORD], 
                "Expected arena name after `in`"
            )
            arena_target = getattr(arena_token, "value")
            
            if self.token_handler.match_type(TokenType.COMMA):
                pass 
            elif self.token_handler.check_type(TokenType.RIGHT_PAREN):
                self.token_handler.advance()
                return arguments, arena_target

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

        return arguments, arena_target

    def parse_members(
        self, token: Token | None = None, member_kind="structure", is_instantiation=False
    ) -> list:
        if not token:
            token = self.token_handler.previous()

        members: list = []
        value: ASTNode | None = None
        count: int = 0

        while not self.token_handler.check_type(TokenType.RIGHT_BRACE) and not self.token_handler.at_end():
            if self.token_handler.check_types([TokenType.COMMENT, TokenType.DOC_COMMENT]):
                self.token_handler.advance()
                continue
            
            if self.token_handler.check_type(TokenType.KEYWORD):
                 pk = self.token_handler.peek().value
                 if pk in ("let", "var"):
                      self.token_handler.advance()

            if self.token_handler.match_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE, TokenType.NOTHING]):
                member_name = self.token_handler.previous()
            else:
                break
                
            params = []
            if member_kind == "enumerator" and self.token_handler.match_type(TokenType.LEFT_PAREN):
                while not self.token_handler.check_type(TokenType.RIGHT_PAREN) and not self.token_handler.at_end():
                    param = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected parameter name")
                    params.append(param.value)
                    if not self.token_handler.match_type(TokenType.COMMA):
                        break
                self.token_handler.expect_type(TokenType.RIGHT_PAREN, "Expected `)` after enum variant parameters")

            if member_kind == "enumerator":
                if self.token_handler.match_type(TokenType.ASSIGNMENT):
                    value = self.expression()
                
                members.append(EnumVariant(member_name.line, member_name.column, member_name.value, params, value))
                value = None 
                
                if self.token_handler.match_type(TokenType.COMMA):
                    continue
                elif self.token_handler.check_type(TokenType.RIGHT_BRACE):
                    break
                else:
                    pass
                continue

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
            expression: ASTNode = self.logical()
            
            key = None
            value = expression
            
            if self.token_handler.match_type(TokenType.ASSIGNMENT):
                key = expression
                value = self.expression()

            element: ElementLiteral = ElementLiteral(
                getattr(value, "line") or getattr(token, "line"),
                getattr(value, "column") or getattr(token, "column"),
                key,
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
                if self.token_handler.check_type(delimiter):
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
