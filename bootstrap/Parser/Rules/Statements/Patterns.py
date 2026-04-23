from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    Pattern,
    WildcardPattern,
    IsMatchPattern,
    ListPattern,
    MapPattern,
    IdentifierPattern,
    VariantPattern,
    LiteralPattern
)

class PatternParserMixin:
    def parse_pattern(self) -> Pattern:
        token = self.token_handler.peek()
        
        # Wildcard
        if self.token_handler.match_type_value(TokenType.IDENTIFIER, "_"):
             return WildcardPattern(getattr(token, "line"), getattr(token, "column"))

        # Is match (type or pattern)
        if self.token_handler.check_type_value(TokenType.KEYWORD, "is"):
             if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE], 1) and \
                not self.token_handler.check_type(TokenType.DOT, 2) and \
                not self.token_handler.check_type(TokenType.LEFT_PAREN, 2):
                  self.token_handler.advance() # consume 'is'
                  type_name = self.token_handler.advance().value
                  return IsMatchPattern(getattr(token, "line"), getattr(token, "column"), type_name)
             else:
                  self.token_handler.advance() # consume 'is'
                  return self.parse_pattern() # Recurse

        # Type Match Pattern
        if self.token_handler.check_type(TokenType.TYPE):
             type_name = self.token_handler.advance().value
             return IsMatchPattern(getattr(token, "line"), getattr(token, "column"), type_name)

        # List Pattern
        if self.token_handler.match_type(TokenType.LEFT_BRACKET):
            elements = []
            while not self.token_handler.check_type(TokenType.RIGHT_BRACKET):
                elements.append(self.parse_pattern())
                if not self.token_handler.match_type(TokenType.COMMA):
                    break
            self.token_handler.expect_type(TokenType.RIGHT_BRACKET, "Expected `]` after list pattern")
            return ListPattern(getattr(token, "line"), getattr(token, "column"), elements)

        # Map Pattern
        if self.token_handler.match_type(TokenType.LEFT_BRACE):
            pairs = []
            while not self.token_handler.check_type(TokenType.RIGHT_BRACE):
                # In Map Pattern, we expect key -> pattern
                key = self.expression_handler.expression()
                self.token_handler.expect_type(TokenType.ASSIGNMENT, "Expected `->` in map pattern")
                value_pattern = self.parse_pattern()
                pairs.append((key, value_pattern))
                if not self.token_handler.match_type(TokenType.COMMA):
                    break
            self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after map pattern")
            return MapPattern(getattr(token, "line"), getattr(token, "column"), pairs)

        # Identifier Pattern (Variable binding)
        if self.token_handler.check_type(TokenType.IDENTIFIER):
            # Could be IdentifierPattern or VariantPattern
            identifier = self.token_handler.advance()
            name = identifier.value
            
            # Support namespaced variants: Enum.Variant or Mod.Enum.Variant
            while self.token_handler.match_type(TokenType.DOT):
                if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.TYPE, TokenType.NOTHING]):
                    member = self.token_handler.advance()
                else:
                    raise self.logger.error_expect_token("Expected identifier, type or Nothing after `.` in pattern", self.token_handler.peek())
                name = f"{name}.{member.value}"
            
            if self.token_handler.match_type(TokenType.LEFT_PAREN):
                # VariantPattern: Some(v)
                params = []
                while not self.token_handler.check_type(TokenType.RIGHT_PAREN) and not self.token_handler.at_end():
                    params.append(self.parse_pattern())
                    if not self.token_handler.match_type(TokenType.COMMA):
                        break
                self.token_handler.expect_type(TokenType.RIGHT_PAREN, "Expected `)` after variant patterns")
                
                if "." in name:
                    parts = name.split(".")
                    enum_name = ".".join(parts[:-1])
                    variant_name = parts[-1]
                else:
                    enum_name = ""
                    variant_name = name
                return VariantPattern(identifier.line, identifier.column, variant_name, enum_name, params)
            
            # Constant Variant Pattern (no params)
            if "." in name or name[0].isupper():
                if "." in name:
                    parts = name.split(".")
                    enum_name = ".".join(parts[:-1])
                    variant_name = parts[-1]
                else:
                    enum_name = ""
                    variant_name = name
                return VariantPattern(identifier.line, identifier.column, variant_name, enum_name, [])
                
            return IdentifierPattern(identifier.line, identifier.column, name)

        # Fallback to literals
        expr = self.expression_handler.expression()
        return LiteralPattern(getattr(token, "line"), getattr(token, "column"), expr)
