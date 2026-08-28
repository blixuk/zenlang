from typing import Any
from Parser.AST import (
    IntegerLiteral,
    DecimalLiteral,
    StringLiteral,
    RuneLiteral,
    BooleanLiteral,
    ListLiteral,
    VectorLiteral,
    MapLiteral,
    SetLiteral,
    TupleLiteral,
    VoidLiteral,
    NothingLiteral,
    VariantLiteral,
    ElementLiteral,
)

class LiteralHandler:
    def _evaluate_integer_literal(self, node: IntegerLiteral, environment) -> int:
        return int(node.value)

    def _evaluate_decimal_literal(self, node: DecimalLiteral, environment) -> float:
        return float(node.value)

    def _evaluate_string_literal(self, node: StringLiteral, environment) -> str:
        return str(node.value)

    def _evaluate_rune_literal(self, node: RuneLiteral, environment) -> str:
        return str(node.value)

    def _evaluate_boolean_literal(self, node: BooleanLiteral, environment) -> bool:
        if isinstance(node.value, bool):
            return node.value
        return node.value == "true" or node.value == "True"

    def _evaluate_void_literal(self, node: VoidLiteral, environment) -> Any:
        return node.value

    def _evaluate_nothing_literal(self, node: Any, environment) -> Any:
        return None

    def _evaluate_default_literal(self, node: Any, environment) -> Any:
        from Checker.Type import (
            TypeInteger,
            TypeBoolean,
            TypeDecimal,
            TypeRune,
            TypeString,
            TypeList,
            TypeMap,
            TypeDefault,
        )
        rt = getattr(node, "resolved_type", None)
        target = getattr(rt, "zero_value_target", None) if rt is not None else None
        t = target if target is not None else rt
        if isinstance(t, TypeInteger):
            return 0
        if isinstance(t, TypeBoolean):
            return False
        if isinstance(t, TypeDecimal):
            return 0.0
        if isinstance(t, (TypeString, TypeRune)):
            return ""
        if isinstance(t, TypeList):
            return []
        if isinstance(t, TypeMap):
            return {}
        nt = getattr(node, "node_type", "")
        if nt == "IntegerLiteral":
            return 0
        if nt == "BooleanLiteral":
            return False
        if nt == "DecimalLiteral":
            return 0.0
        if nt in ("StringLiteral", "RuneLiteral"):
            return ""
        return None

    def _evaluate_variant_literal(self, node: VariantLiteral, environment) -> Any:
        return node.value

    def _evaluate_list_literal(self, node: ListLiteral, environment) -> list:
        return [self._evaluate(element, environment) for element in node.elements]

    def _evaluate_vector_literal(self, node: VectorLiteral, environment) -> list:
        return [self._evaluate(element, environment) for element in node.elements]

    def _evaluate_map_literal(self, node: MapLiteral, environment) -> dict:
        result = {}
        for element in node.elements:
            key = self._evaluate(element.name, environment)
            value = self._evaluate(element.value, environment)
            result[key] = value
        return result

    def _evaluate_set_literal(self, node: SetLiteral, environment) -> set:
        return {self._evaluate(element, environment) for element in node.elements}

    def _evaluate_tuple_literal(self, node: TupleLiteral, environment) -> tuple:
        return tuple(self._evaluate(element, environment) for element in node.elements)

    def _evaluate_element_literal(self, node: ElementLiteral, environment) -> Any:
        return self._evaluate(node.value, environment)
