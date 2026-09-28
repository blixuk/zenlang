from Lexer.Token import Token, TokenType
from Parser.AST import (
    ASTNode,
    Pattern,
    WildcardPattern,
    RestPattern,
    DestructurePattern,
    IsMatchPattern,
    ListPattern,
    MapPattern,
    IdentifierPattern,
    VariantPattern,
    LiteralPattern,
    InPattern
)

class PatternParserMixin:
    def parse_pattern(self) -> Pattern:
        token = self.token_handler.peek()
        
        # Wildcard
        if self.token_handler.match_type_value(TokenType.IDENTIFIER, "_"):
             return WildcardPattern(getattr(token, "line"), getattr(token, "column"))

        # In Match Pattern (in <collection>)
        if self.token_handler.match_type_value(TokenType.KEYWORD, "in"):
            coll = self.expression_handler.expression()
            return InPattern(getattr(token, "line"), getattr(token, "column"), coll)

        # Rest Pattern (...name)
        if self.token_handler.match_type(TokenType.ELLIPSIS) or self.token_handler.match_type(TokenType.RANGE_FULL_INCLUSIVE):
             name = "_"
             if self.token_handler.check_type(TokenType.IDENTIFIER):
                 name = self.token_handler.advance().value
             return RestPattern(getattr(token, "line"), getattr(token, "column"), name)

        # Is match (type or pattern)
        if self.token_handler.check_type_value(TokenType.KEYWORD, "is"):
             if self.token_handler.check_types([TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.TYPE], 1) and \
                not self.token_handler.check_type(TokenType.DOT, 2) and \
                not self.token_handler.check_type(TokenType.LEFT_PAREN, 2) and \
                not self.token_handler.check_type(TokenType.LEFT_BRACE, 2):
                  self.token_handler.advance() # consume 'is'
                  type_name = self.token_handler.advance().value
                  if self.token_handler.match_type(TokenType.LEFT_BRACKET):
                      inner = self.token_handler.expect_type(TokenType.INTEGER, "Expected size").value
                      self.token_handler.expect_type(TokenType.RIGHT_BRACKET, "Expected `]`")
                      type_name = f"{type_name}[{inner}]"
                  if self.token_handler.match_type(TokenType.LESS_THAN):
                      subtypes = []
                      while True:
                          sub = self.token_handler.expect_types([TokenType.TYPE, TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected type name").value
                          subtypes.append(sub)
                          if not self.token_handler.match_type(TokenType.COMMA):
                              break
                      self.token_handler.expect_type(TokenType.GREATER_THAN, "Expected `>`")
                      type_name = f"{type_name}<{', '.join(subtypes)}>"
                  return IsMatchPattern(getattr(token, "line"), getattr(token, "column"), type_name)
             else:
                  self.token_handler.advance() # consume 'is'
                  return self.parse_pattern() # Recurse

        # Type Match Pattern
        if self.token_handler.check_type(TokenType.TYPE):
             type_token = self.token_handler.advance()
             type_name = type_token.value
             
             # Support namespaced variants/destructuring: Type.Member or Type.Enum.Variant
             if self.token_handler.check_type(TokenType.DOT):
                  # Fall through to identifier logic which handles namespaces
                  # We'll prepend the type_name
                  return self._parse_namespaced_pattern(type_token, type_name)

             if self.token_handler.match_type(TokenType.LEFT_BRACKET):
                 inner = self.token_handler.expect_type(TokenType.INTEGER, "Expected size").value
                 self.token_handler.expect_type(TokenType.RIGHT_BRACKET, "Expected `]`")
                 type_name = f"{type_name}[{inner}]"
             if self.token_handler.match_type(TokenType.LESS_THAN):
                 subtypes = []
                 while True:
                     sub = self.token_handler.expect_types([TokenType.TYPE, TokenType.IDENTIFIER, TokenType.KEYWORD], "Expected type name").value
                     subtypes.append(sub)
                     if not self.token_handler.match_type(TokenType.COMMA):
                         break
                 self.token_handler.expect_type(TokenType.GREATER_THAN, "Expected `>`")
                 type_name = f"{type_name}<{', '.join(subtypes)}>"

             is_destructure = False
             if self.token_handler.check_type(TokenType.LEFT_BRACE):
                 next_t = self.token_handler.peek(1)
                 next_next_t = self.token_handler.peek(2)
                 if next_t and next_t.type == TokenType.IDENTIFIER:
                     if next_next_t and next_next_t.type in (TokenType.ASSIGNMENT, TokenType.COMMA, TokenType.RIGHT_BRACE):
                         is_destructure = True
             if is_destructure and self.token_handler.match_type(TokenType.LEFT_BRACE):
                 # Destructure Pattern: Point { x -> x_val, y -> y_val }
                 members = []
                 while not self.token_handler.check_type(TokenType.RIGHT_BRACE):
                     member_name = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected member name in destructure pattern").value
                     pattern = WildcardPattern(getattr(token, "line"), getattr(token, "column")) # Default
                     if self.token_handler.match_type(TokenType.ASSIGNMENT):
                         pattern = self.parse_pattern()
                     else:
                         # Shorthand: Point { x } is Point { x -> x }
                         pattern = IdentifierPattern(getattr(token, "line"), getattr(token, "column"), member_name)
                     
                     members.append((member_name, pattern))
                     if not self.token_handler.match_type(TokenType.COMMA):
                         break
                 self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after destructure pattern")
                 return DestructurePattern(getattr(token, "line"), getattr(token, "column"), type_name, members)
             
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
            # Could be IdentifierPattern, VariantPattern, or DestructurePattern (if it starts with Identifier)
            identifier = self.token_handler.advance()
            name = identifier.value
            
            if self.token_handler.check_type(TokenType.DOT):
                 return self._parse_namespaced_pattern(identifier, name)
            
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
            
            is_destructure = False
            if self.token_handler.check_type(TokenType.LEFT_BRACE):
                next_t = self.token_handler.peek(1)
                next_next_t = self.token_handler.peek(2)
                if next_t and next_t.type == TokenType.IDENTIFIER:
                     if next_next_t and next_next_t.type in (TokenType.ASSIGNMENT, TokenType.COMMA, TokenType.RIGHT_BRACE):
                         is_destructure = True
            if is_destructure and self.token_handler.match_type(TokenType.LEFT_BRACE):
                # Destructure Pattern for structures (if not already handled by Type check)
                 members = []
                 while not self.token_handler.check_type(TokenType.RIGHT_BRACE):
                     member_name = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected member name in destructure pattern").value
                     pattern = WildcardPattern(getattr(token, "line"), getattr(token, "column")) # Default
                     if self.token_handler.match_type(TokenType.ASSIGNMENT):
                         pattern = self.parse_pattern()
                     else:
                         pattern = IdentifierPattern(getattr(token, "line"), getattr(token, "column"), member_name)
                     
                     members.append((member_name, pattern))
                     if not self.token_handler.match_type(TokenType.COMMA):
                         break
                 self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after destructure pattern")
                 return DestructurePattern(getattr(token, "line"), getattr(token, "column"), name, members)

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

    def _parse_namespaced_pattern(self, start_token: Token, name: str) -> Pattern:
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
            
            parts = name.split(".")
            enum_name = ".".join(parts[:-1])
            variant_name = parts[-1]
            return VariantPattern(start_token.line, start_token.column, variant_name, enum_name, params)
        
        is_destructure = False
        if self.token_handler.check_type(TokenType.LEFT_BRACE):
            next_t = self.token_handler.peek(1)
            next_next_t = self.token_handler.peek(2)
            if next_t and next_t.type == TokenType.IDENTIFIER:
                if next_next_t and next_next_t.type in (TokenType.ASSIGNMENT, TokenType.COMMA, TokenType.RIGHT_BRACE):
                    is_destructure = True
        if is_destructure and self.token_handler.match_type(TokenType.LEFT_BRACE):
             members = []
             while not self.token_handler.check_type(TokenType.RIGHT_BRACE):
                 member_name = self.token_handler.expect_type(TokenType.IDENTIFIER, "Expected member name in destructure pattern").value
                 pattern = WildcardPattern(start_token.line, start_token.column) # Default
                 if self.token_handler.match_type(TokenType.ASSIGNMENT):
                     pattern = self.parse_pattern()
                 else:
                     pattern = IdentifierPattern(start_token.line, start_token.column, member_name)
                 
                 members.append((member_name, pattern))
                 if not self.token_handler.match_type(TokenType.COMMA):
                     break
             self.token_handler.expect_type(TokenType.RIGHT_BRACE, "Expected `}` after destructure pattern")
             return DestructurePattern(start_token.line, start_token.column, name, members)

        # Constant Variant Pattern (no params)
        parts = name.split(".")
        enum_name = ".".join(parts[:-1])
        variant_name = parts[-1]
        return VariantPattern(start_token.line, start_token.column, variant_name, enum_name, [])
