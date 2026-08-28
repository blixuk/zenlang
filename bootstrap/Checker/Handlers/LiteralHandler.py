from typing import Any
from Checker.Type import (
    TypeInteger,
    TypeDecimal,
    TypeString,
    TypeRune,
    TypeNothing,
    TypeVoid,
    TypeBoolean,
    TypeVariant,
    TypeList,
    TypeVector,
    TypeMap,
    TypeSet,
    TypeTuple,
    TypeElement,
    TypeDefault,
    Type,
)
from Parser.AST import (
    IntegerLiteral,
    DefaultLiteral,
    DecimalLiteral,
    StringLiteral,
    RuneLiteral,
    NothingLiteral,
    VoidLiteral,
    BooleanLiteral,
    VariantLiteral,
    ListLiteral,
    VectorLiteral,
    DictionaryLiteral,
    SetLiteral,
    TupleLiteral,
)

class LiteralHandler:
    def _check_integer_literal(self, expression: IntegerLiteral) -> Type:
        expression.resolved_type = TypeInteger()
        return expression.resolved_type

    def _check_decimal_literal(self, expression: DecimalLiteral) -> Type:
        expression.resolved_type = TypeDecimal()
        return expression.resolved_type

    def _check_string_literal(self, expression: StringLiteral) -> Type:
        expression.resolved_type = TypeString()
        return expression.resolved_type

    def _check_rune_literal(self, expression: RuneLiteral) -> Type:
        expression.resolved_type = TypeRune()
        return expression.resolved_type

    def _check_nothing_literal(self, expression: NothingLiteral) -> Type:
        expression.resolved_type = TypeNothing()
        return expression.resolved_type

    def _check_void_literal(self, expression: VoidLiteral) -> Type:
        expression.resolved_type = TypeVoid()
        return expression.resolved_type

    def _check_default_literal(self, expression: DefaultLiteral) -> Type:
        expression.resolved_type = TypeDefault()
        return expression.resolved_type

    def _check_boolean_literal(self, expression: BooleanLiteral) -> Type:
        expression.resolved_type = TypeBoolean()
        return expression.resolved_type

    def _check_variant_literal(self, expression: VariantLiteral) -> Type:
        expression.resolved_type = TypeVariant()
        return expression.resolved_type

    def check_list_literal(self, expression: ListLiteral) -> Type:
        self.logger.debug("check_list_literal", expression)
        
        element_types = []
        for element in expression.elements:
             # Unwrap ElementLiteral
             item_node = element.value
             t = self.check_expression(item_node)
             # Store type on both element and value for safety
             element.resolved_type = t
             item_node.resolved_type = t
             element_types.append(t)
             
        # For now, return a generic list or infer type
        # TODO: Homogenous check
        expression.resolved_type = TypeList(None, [])
        return expression.resolved_type

    def check_vector_literal(self, expression: VectorLiteral) -> Type:
        self.logger.debug("check_vector_literal", expression)
        # Infer element type from first element or Variant
        element_types = [self.check_expression(el.value) for el in expression.elements]
        if not element_types:
            expression.resolved_type = TypeVector(None, TypeVariant(), 0)
            return expression.resolved_type
            
        common_type = element_types[0]
        for t in element_types[1:]:
            common_type = self.unify(common_type, t, expression)
            
        expression.resolved_type = TypeVector(None, common_type, len(expression.elements))
        return expression.resolved_type

    def check_dictionary_literal(self, expression: DictionaryLiteral) -> Type:
        self.logger.debug("check_dictionary_literal", expression)
        # Infer key and value types
        if not expression.elements:
            expression.resolved_type = TypeMap(None, TypeVariant(), TypeVariant())
            return expression.resolved_type
            
        key_types = [self.check_expression(el.name) for el in expression.elements]
        value_types = [self.check_expression(el.value) for el in expression.elements]
        
        common_key_type = key_types[0]
        for t in key_types[1:]:
            common_key_type = self.unify(common_key_type, t, expression)
            
        common_value_type = value_types[0]
        for t in value_types[1:]:
            common_value_type = self.unify(common_value_type, t, expression)
            
        expression.resolved_type = TypeMap(None, common_key_type, common_value_type)
        return expression.resolved_type

    def check_map_literal(self, expression: Any) -> Type:
        return self.check_dictionary_literal(expression)

    def check_set_literal(self, expression: SetLiteral) -> Type:
        self.logger.debug("check_set_literal", expression)
        element_types = [self.check_expression(el.value) for el in expression.elements]
        if not element_types:
            expression.resolved_type = TypeSet(None, TypeVariant())
            return expression.resolved_type
            
        common_type = element_types[0]
        for t in element_types[1:]:
            common_type = self.unify(common_type, t, expression)
            
        expression.resolved_type = TypeSet(None, common_type)
        return expression.resolved_type

    def check_tuple_literal(self, expression: TupleLiteral) -> Type:
        self.logger.debug("check_tuple_literal", expression)
        element_types = [TypeElement(getattr(el, "name") if hasattr(el, "name") else None, self.check_expression(el.value)) for el in expression.elements]
        expression.resolved_type = TypeTuple(None, element_types)
        return expression.resolved_type
