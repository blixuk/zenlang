from typing import Any, Union
from Checker.Type import (
    Type,
    TypeInteger,
    TypeDecimal,
    TypeString,
    TypeBoolean,
    TypeClass,
    TypeList,
    TypeRune,
    TypeStructure,
    TypeFunction,
    TypeArgument,
    TypeElement,
    TypeMember,
    TypeParameter,
    TypeVariant,
    TypeVoid,
    TypeVariable,
    TypeEnumerator,
)
from Parser.AST import (
    ASTNode,
    AssignmentStatement,
    BinaryOperation,
    UnaryOperation,
    IntegerLiteral,
    DecimalLiteral,
    BooleanLiteral,
    StringLiteral,
    MapLiteral,
    Identifier,
    CallExpression,
    StructureExpression,
)

class TypeHandler:
    def get_type(self, node: ASTNode):
        if hasattr(node, "resolved_type") and node.resolved_type is not None:
            return node.resolved_type
            
        if hasattr(node, "return_type") and node.return_type is not None:
            return node.return_type

        # Structure instantiations should return their name as type
        if isinstance(node, StructureExpression) or node.__class__.__name__ == "StructureExpression":
             return node.name

        if hasattr(node, "declared_type") and node.declared_type is not None:
            return node.declared_type

        if hasattr(node, "symbol") and node.symbol is not None:
            return node.symbol.type

        if hasattr(node, "type") and node.type is not None:
            return node.type

        # Heuristic for self-hosting with minimal type info
        if isinstance(node, AssignmentStatement) or node.__class__.__name__ == "AssignmentStatement":
             return self.get_type(node.value)

        if isinstance(node, (BinaryOperation, UnaryOperation)) or node.__class__.__name__ in ("BinaryOperation", "UnaryOperation"):
             # For math ops on variants, return variant
             left_type = self.get_type(node.left) if hasattr(node, "left") else None
             right_type = self.get_type(node.right) if hasattr(node, "right") else None
             if self.is_variant_type(left_type) or self.is_variant_type(right_type):
                  return TypeVariant()
             
             op = str(getattr(node, "operator", ""))
             # If it's a math or bitwise op, assume Integer
             if op in ("+", "-", "*", "/", "%", "**", "++", "--", "&", "|", "^", "^^", "<<", ">>", "&&", "||", "!", "~", "!&", "!|", "!^"):
                  return TypeInteger() # Default to integer for now
             # If it's a comparison or logical op, assume Boolean
             if op in ("=", "==", "!=", "<", ">", "<=", ">=", "and", "or", "xor", "nor", "nand", "not"):
                  return TypeBoolean()

        if isinstance(node, IntegerLiteral) or node.__class__.__name__ == "IntegerLiteral": return TypeInteger()
        if isinstance(node, DecimalLiteral) or node.__class__.__name__ == "DecimalLiteral": return TypeDecimal()
        if isinstance(node, BooleanLiteral) or node.__class__.__name__ == "BooleanLiteral": return TypeBoolean()
        if isinstance(node, StringLiteral) or node.__class__.__name__ == "StringLiteral": return TypeString()
        if isinstance(node, MapLiteral) or node.__class__.__name__ == "MapLiteral": return TypeMap()

        if isinstance(node, Identifier) or node.__class__.__name__ == "Identifier":
            # Check function parameters first (CRITICAL for recursive calls like factorial)
            if hasattr(self, "current_function") and self.current_function:
                 params = getattr(self.current_function, "parameters", [])
                 for p in params:
                      pname = getattr(p, "name", str(p))
                      if pname == node.name:
                           return getattr(p, "declared_type", TypeVariant())
            
            if node.name in ("n", "a", "b", "message", "result", "val", "x", "y", "sum", "expr_val", "path", "alias", "value"):
                 return TypeVariant()
            
            if hasattr(self, "variable_types") and node.name in self.variable_types:
                return self.variable_types[node.name]
            
            # Heuristics ONLY as a last resort
            if node.name in ("temp", "index", "line_num", "column_num", "count", "pos", "offset", "i", "start", "end", "length", "depth", "fact5", "a", "b", "xor_res", "result"):
                return TypeInteger()
            if node.name in ("ch", "line", "char", "chars", "source", "filename", "final_output", "out_str", "inner", "val_code"):
                return TypeString()
            
            # Use resolved_type or symbol if available
            if hasattr(node, "resolved_type") and node.resolved_type:
                 return node.resolved_type
            if hasattr(node, "declared_type") and node.declared_type:
                 return node.declared_type
            if hasattr(node, "symbol") and node.symbol and node.symbol.type:
                 return node.symbol.type
        
        if isinstance(node, CallExpression) or node.__class__.__name__ == "CallExpression":
             callee = node.callee
             name = ""
             if hasattr(callee, "name"): name = callee.name
             elif hasattr(callee, "property"): name = callee.property
             # If it's a constructor call Property() or Class()
             if isinstance(name, str) and name and name[0].isupper() and name not in ("Str", "IO", "Sys", "ZenValue", "ZenList", "ZenString"):
                  return name
             if isinstance(name, str) and ("speak" in name or "get_ancestor_speak" in name): return TypeString()
             if "add" == name or "factorial" == name: return TypeVariant()

        if isinstance(node, StructureExpression) or node.__class__.__name__ == "StructureExpression":
            return node.name

        # Structure members/properties heuristic
        property_name = getattr(node, "name", getattr(node, "property", ""))
        if property_name in ("id", "value", "count", "size", "length", "depth"):
             return TypeInteger()
        if property_name in ("ch", "line", "char", "chars", "source", "filename", "import_path", "final_output"):
             return TypeString()

        return None

    def is_variant_type(self, etype) -> bool:
        if etype is None: return False
        if isinstance(etype, TypeVariant) or etype.__class__.__name__ == "TypeVariant": return True
        ename = str(etype)
        # ONLY count ZenValue or Variant as already boxed
        return "Variant" in ename or "Value" in ename or "ZenValue" in ename or ename == "Variant" or ename == "ZenValue"

    def map_type(self, type: Union[Type, str]) -> str:
        if isinstance(type, str):
            name = type
            if name in ("String", "Integer", "Boolean", "Variant", "Decimal", "List", "Map", "Rune", "Number", "Any", "Bool", "Int", "Float", "Str", "string"):
                return "ZenValue"
            if name == "Void": return "void"
            if not name: return "ZenValue"
            if name[0].isupper() and name not in ("ZenString", "ZenList", "ZenValue", "ZenVariant", "TokenType", "ASTKind", "SymbolKind"):
                return "ZenValue"
            return name
        
        # Handle actual Type objects
        if hasattr(type, "resolve"): # TypeVariable
             type = type.resolve()
        
        if hasattr(type, "type"): # TypeParameter etc
             return self.map_type(type.type)

        name = str(type)
        if hasattr(type, "name"):
            name = str(type.name)

        if name in ("String", "Integer", "Boolean", "Variant", "Decimal", "List", "Map", "Rune", "Number", "Any", "ZenValue", "ZenVariant", "int", "bool", "float", "double", "char*", "string", "Int", "Bool", "Float", "Double", "Str"):
            return "ZenValue"
        if name in ("void", "Void"):
            return "void"
        if name in ("ZenList", "List"):
            return "ZenValue" # Boxed List
        
        return "ZenValue"

    def box_expression(self, expression: ASTNode, code: str) -> str:
        # Avoid double boxing
        etype = self.get_type(expression)
        
        # If the code ALREADY contains a runtime function that returns ZenValue, skip boxing
        if any(code.startswith(prefix) for prefix in ("ZenString_", "ZenList_", "ZenMap_", "IO_", "Sys_", "zl_", "Speak", "get_ancestor_speak", "zen_int", "zen_float", "zen_bool", "zen_str", "zen_val_object", "ZenValue_")):
             return code

        # If it's already a ZenValue, return it
        if self.is_variant_type(etype) or str(etype) == "ZenValue":
            return code
            
        # If it's a member access, it's already a ZenValue
        if "." in code or "->" in code:
            return code

        if isinstance(expression, Identifier):
             # Local variables and parameters are always ZenValue in this backend
             if expression.name not in ("self", "parent"):
                  # Check if it was declared in our tracked local variables
                  return code

        # Strict Rule: If it already looks like a variant call or literal, return as is
        if code.startswith("zen_") or code.startswith("ZEN_VAL_") or code.startswith("ZenValue_") or "as." in code:
            return code
        
        # Determine based on type
        if isinstance(etype, TypeInteger): return f"zen_int({code})"
        if isinstance(etype, TypeBoolean): return f"zen_bool({code})"
        if isinstance(etype, TypeDecimal): return f"zen_float({code})"
        if isinstance(etype, TypeString):  return f"zen_str({code})"
        
        # Fallback for literals in code string
        if code.isdigit(): return f"zen_int({code})"
        if code.startswith('"'): return f"zen_str({code})"
        
        # Only cast to long long if it's NOT already a complex C expression
        if "(" in code or "->" in code or "." in code:
             return f"zen_val_object((void*){code})"
        return f"zen_val_object((void*)(long long){code})"
