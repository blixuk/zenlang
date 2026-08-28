from typing import Any
from Parser.AST import (
    WildcardPattern,
    IdentifierPattern,
    IsMatchPattern,
    ListPattern,
    VariantPattern,
    MapPattern,
    LiteralPattern,
    RestPattern,
    DestructurePattern
)
from Interpreter.Runtime import Environment, VariantObject
from Interpreter.Exceptions import RaiseException

class PatternHandler:
    def _evaluate_pattern_match(self, value: Any, pattern: Any, environment: Environment) -> bool:
        if isinstance(pattern, WildcardPattern):
            return True
            
        if isinstance(pattern, IdentifierPattern):
            environment.define(pattern.name, value, mutable=False, type="Variant")
            return True

        if isinstance(pattern, RestPattern):
            environment.define(pattern.name, value, mutable=False, type="Variant")
            return True

        if isinstance(pattern, IsMatchPattern):
            val_type = type(value).__name__
            type_map = {
                "int": "Integer",
                "float": "Decimal",
                "str": "String",
                "bool": "Boolean",
                "list": "List",
                "dict": "Map",
                "NoneType": "Nothing"
            }
            if pattern.type_name == "Error":
                 if isinstance(value, (RaiseException, Exception)):
                     return True
                 if isinstance(value, dict) and value.get("__type__") == "Error":
                     return True
            
            return type_map.get(val_type) == pattern.type_name

        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return False
            
            # Check for RestPattern
            has_rest = any(isinstance(p, RestPattern) for p in pattern.elements)
            
            if not has_rest:
                if len(pattern.elements) != len(value):
                    return False
                for i, elem_pattern in enumerate(pattern.elements):
                    if not self._evaluate_pattern_match(value[i], elem_pattern, environment):
                        return False
            else:
                rest_idx = next(i for i, p in enumerate(pattern.elements) if isinstance(p, RestPattern))
                # Match elements before rest
                for i in range(rest_idx):
                    if i >= len(value): return False
                    if not self._evaluate_pattern_match(value[i], pattern.elements[i], environment):
                        return False
                
                # Match elements after rest (from the end)
                after_rest_count = len(pattern.elements) - 1 - rest_idx
                for i in range(after_rest_count):
                    v_idx = len(value) - 1 - i
                    p_idx = len(pattern.elements) - 1 - i
                    if v_idx < rest_idx: return False
                    if not self._evaluate_pattern_match(value[v_idx], pattern.elements[p_idx], environment):
                        return False
                
                # Bind rest
                rest_val = value[rest_idx : len(value) - after_rest_count]
                if not self._evaluate_pattern_match(rest_val, pattern.elements[rest_idx], environment):
                    return False

            return True

        if isinstance(pattern, DestructurePattern):
            # value should be an object (StructureObject or similar)
            if not hasattr(value, "get_member"):
                return False
            
            for member_name, member_pattern in pattern.members:
                try:
                    member_val = value.get_member(member_name)
                    if not self._evaluate_pattern_match(member_val, member_pattern, environment):
                        return False
                except:
                    return False
            return True

        if isinstance(pattern, VariantPattern):
            if not isinstance(value, VariantObject):
                return False
            
            if "." in pattern.name:
                 enum_part, variant_part = pattern.name.split(".", 1)
                 if value.enum_name != enum_part or value.variant_name != variant_part:
                      return False
            else:
                 if value.variant_name != pattern.name:
                      return False
            
            if len(pattern.params) != len(value.data):
                return False
                
            for p, v in zip(pattern.params, value.data):
                if not self._evaluate_pattern_match(v, p, environment):
                    return False
            return True

        if isinstance(pattern, MapPattern):
            if not isinstance(value, dict):
                return False
            
            for key_node, val_pattern in pattern.pairs:
                key = self._evaluate(key_node, environment)
                if key not in value:
                    return False
                if not self._evaluate_pattern_match(value[key], val_pattern, environment):
                    return False
            return True
            
        elif isinstance(pattern, LiteralPattern):
            match_val = self._evaluate(pattern.value, environment)
            return value == match_val
        
        return False

    def _bind_pattern(self, pattern: Any, value: Any, environment: Environment) -> bool:
        return self._evaluate_pattern_match(value, pattern, environment)
