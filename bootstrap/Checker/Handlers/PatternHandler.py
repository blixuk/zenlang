from Checker.Type import (
    Type,
    TypeVariant,
    TypeList,
    TypeMap,
    Symbol,
    SymbolKind,
)
from Parser.AST import (
    Pattern,
    WildcardPattern,
    IdentifierPattern,
    IsMatchPattern,
    ListPattern,
    MapPattern,
    LiteralPattern,
    VariantPattern,
    RestPattern,
    DestructurePattern
)

class PatternHandler:
    def check_pattern(self, pattern: Pattern, matched_type: Type):
        if isinstance(pattern, WildcardPattern):
            return

        if isinstance(pattern, IdentifierPattern):
            # Bind the variable to the matched type in the current scope.
            # We use the matched_type (which might be Variant if unknown).
            level = self.scope.level
            pattern.scope_level = level
            symbol = Symbol(
                pattern.name,
                matched_type,
                None,
                False, # Immutable binding by default in patterns
                SymbolKind.VARIABLE,
                level
            )
            self.scope.define(symbol)
            pattern.symbol = symbol
            return

        if isinstance(pattern, RestPattern):
            # Bind the rest of the elements to a list.
            level = self.scope.level
            pattern.scope_level = level
            
            rest_type = matched_type # If it's a list, it's still a list.
            
            symbol = Symbol(
                pattern.name,
                rest_type,
                None,
                False,
                SymbolKind.VARIABLE,
                level
            )
            self.scope.define(symbol)
            pattern.symbol = symbol
            return

        if isinstance(pattern, IsMatchPattern):
            # Validates that it's a type match (simplified)
            return

        if isinstance(pattern, ListPattern):
            inner_type = TypeVariant()
            if isinstance(matched_type, TypeList):
                # TypeList has an 'elements' list of TypeElement, which has a 'type' field
                inner_type = matched_type.elements[0].type if matched_type.elements else TypeVariant()
            
            for element_pattern in pattern.elements:
                self.check_pattern(element_pattern, inner_type)
            return

        if isinstance(pattern, MapPattern):
            value_type = TypeVariant()
            if isinstance(matched_type, TypeMap):
                value_type = matched_type.value_type
                
            for key, val_pattern in pattern.pairs:
                self.check_pattern(val_pattern, value_type)
            return

        if isinstance(pattern, DestructurePattern):
            # Check if the type exists and has these members
            # For now, we assume it's valid and just bind members
            for member_name, member_pattern in pattern.members:
                self.check_pattern(member_pattern, TypeVariant())
            return

        if isinstance(pattern, VariantPattern):
             for param in pattern.params:
                 self.check_pattern(param, TypeVariant())
             return

        if isinstance(pattern, LiteralPattern):
            self.check_expression(pattern.value)
            return
