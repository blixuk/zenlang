import os
from typing import Optional, Any
from Parser.AST import *
from Transpiler.MIR import *
from Checker.Type import SymbolKind, TypeStructure, TypeClass, TypeTaskHandle

# Must match selfhost/compiler/Token.zl kind_id / enumerator order (0..114).
TOKEN_TYPE_IDS = {
    "KEYWORD": 0, "IDENTIFIER": 1, "LITERAL": 2, "OPERATOR": 3, "TYPE": 4,
    "UNKNOWN": 5, "COMMENT": 6, "DOC_COMMENT": 7, "ERROR": 8,
    "ERROR_UNTERMINATED_STRING": 9, "ERROR_UNTERMINATED_STRING_EOF": 10,
    "ERROR_UNTERMINATED_CHARACTER": 11, "ERROR_UNTERMINATED_CHARACTER_EOF": 12,
    "ERROR_INVALID_NUMBER": 13, "ERROR_INVALID_ASSIGNMENT": 14,
    "ERROR_INVALID_ASSIGNMENT_OPERATOR": 15, "ERROR_UNEXPECTED_CHARACTER": 16,
    "ERROR_UNEXPECTED_TOKEN": 17, "VOID": 18, "NOTHING": 19, "DEFAULT": 20,
    "VARIANT": 21, "INTEGER": 22, "DECIMAL": 23, "STRING": 24, "RUNE": 25,
    "BOOLEAN": 26, "FUNCTION": 27, "STRUCTURE": 28, "OBJECT": 29, "CLASS": 30,
    "ENUMERATOR": 31, "RAISE": 32, "CHECK": 33, "ASSERT": 34, "DEFER": 35,
    "CASE": 36, "WITH": 37, "TASK": 38, "AWAIT": 39, "LIST": 40, "TUPLE": 41,
    "VECTOR": 42, "MAP": 43, "SET": 44, "ITERATOR": 45, "ITERABLE": 46,
    "AUTO": 47, "LEFT_PAREN": 48, "RIGHT_PAREN": 49, "LEFT_BRACE": 50,
    "RIGHT_BRACE": 51, "LEFT_BRACKET": 52, "RIGHT_BRACKET": 53, "COMMA": 54,
    "DOT": 55, "SEMICOLON": 56, "TYPE_SET": 57, "TYPE_LET": 58,
    "ASSIGNMENT": 59, "RETURN": 60, "ADDITION": 61, "SUBTRACTION": 62,
    "MULTIPLICATION": 63, "DIVISION": 64, "MODULO": 65, "EXPONENTIATION": 66,
    "QUOTIENT": 67, "AND": 68, "OR": 69, "NOT": 70, "XOR": 71, "NOR": 72,
    "NAND": 73, "XNOR": 74, "BITWISE_AND": 75, "BITWISE_OR": 76,
    "BITWISE_NOT": 77, "BITWISE_XOR": 78, "BITWISE_NOR": 79, "BITWISE_NAND": 80,
    "BITWISE_XNOR": 81, "BITWISE_MOD": 82, "BITWISE_LEFT_SHIFT": 83,
    "BITWISE_RIGHT_SHIFT": 84, "AND_EQUAL": 85, "OR_EQUAL": 86, "XOR_EQUAL": 87,
    "MOD_EQUAL": 88, "LEFT_SHIFT_EQUAL": 89, "RIGHT_SHIFT_EQUAL": 90,
    "INCREMENT": 91, "DECREMENT": 92, "EQUAL": 93, "NOT_EQUAL": 94,
    "GREATER_THAN": 95, "LESS_THAN": 96, "GREATER_THAN_OR_EQUAL": 97,
    "LESS_THAN_OR_EQUAL": 98, "RANGE": 99, "RANGE_INCLUSIVE": 100,
    "ELLIPSIS": 101, "SCOPE": 102, "EXPORT": 103, "IS": 104, "EXTENDS": 105,
    "PARENT": 106, "SELF": 107, "IMPORT": 108, "FROM": 109, "AS": 110,
    "CHECK_SYMBOL": 111, "RAISE_SYMBOL": 112, "ASSERT_SYMBOL": 113,
    "TYPE_CAST": 114, "EOF": 115,
    "RANGE_INCL_END": 116, "RANGE_EXCL_END": 117, "RANGE_FULL_INCL": 118,
    "YIELD_ARROW": 119, "BYTE": 120, "BYTES": 121, "COALESCE": 122, "PIPELINE": 123,
}

class ExpressionHandler:
    def _visit_expression(self, node: ASTNode, target_region: Optional[str] = None) -> str:
        if isinstance(node, CheckExpression):
            return self._visit_check_expression(node, target_region)
        
        if isinstance(node, IsExpression):
            return self._visit_is_expression(node, target_region)
        
        if isinstance(node, WhenExpression):
            return self._visit_when_expression(node, target_region)
        
        if isinstance(node, WhenInlineExpression):
            return self._visit_when_inline_expression(node, target_region)

        if isinstance(node, AwaitExpression):
            return self._visit_await(node, target_region)

        current_reg = target_region if target_region else self.current_region
        
        if isinstance(node, InExpression):
            # The 'in' expression specifies a target region for its inner expression
            return self._visit_expression(node.expression, target_region=node.arena)

        if isinstance(node, IntegerLiteral):
            tmp = self._alloc_temp(self.new_label("tmp"), node, "int", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value), type="int"), node)
            return tmp
        elif isinstance(node, StringLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_str"), node, "string", region=current_reg)
            self._emit(Load(target=tmp, source=f"`{node.value}`", type="string"), node)
            return tmp
        elif isinstance(node, DecimalLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_dec"), node, "decimal", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value), type="decimal"), node)
            return tmp
        elif isinstance(node, RuneLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_rune"), node, "rune", region=current_reg)
            # Convert to integer code point for this runtime
            v = ord(node.value)
            self._emit(Load(target=tmp, source=str(v), type="rune"), node)
            return tmp
        elif isinstance(node, BooleanLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_bool"), node, "bool", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value).lower(), type="bool"), node)
            return tmp
        elif isinstance(node, Identifier):
            m_name = self.get_mangled_name(node)
            sym = getattr(node, "symbol", None)
            # Import aliases are module handles, not first-class functions.
            if isinstance(node, Identifier) and hasattr(self, "module_aliases") and node.name in self.module_aliases:
                return m_name
            if sym and sym.kind == SymbolKind.MODULE:
                return m_name
            if sym and sym.kind in (SymbolKind.FUNCTION, SymbolKind.CLASS) and m_name not in getattr(self, "global_variable_names", set()):
                 # Return a function object wrapper
                 return f"ZenValue_from_function((ZenValue (*)(void)){m_name})"
            return m_name
        elif isinstance(node, BinaryOperation):
            op = node.operator.value if hasattr(node.operator, "value") else str(node.operator)
            if op == "<:":
                left = self._visit_expression(node.left, target_region=target_region)
                target_type = getattr(node.right, "name", str(node.right))
                if hasattr(node.right, "bits") and node.right.bits:
                    target_type = f"{target_type}[{node.right.bits}]"
                if hasattr(node.right, "subtypes") and node.right.subtypes:
                    subs = [getattr(s, "name", str(s)) for s in node.right.subtypes]
                    target_type = f"{target_type}<{', '.join(subs)}>"
                tmp = self._alloc_temp(self.new_label("tmp_cast"), node, region=current_reg)
                self._emit(Call(target=tmp, callee="ZenValue_cast", args=[left, f'"{target_type}"'], region=current_reg), node)
                return tmp
            if op == "??":
                left = self._visit_expression(node.left, target_region=target_region)
                right = self._visit_expression(node.right, target_region=target_region)
                tmp = self._alloc_temp(self.new_label("tmp_coalesce"), node, region=current_reg)
                self._emit(Call(target=tmp, callee="ZenValue_coalesce", args=[left, right], region=current_reg), node)
                return tmp
            left = self._visit_expression(node.left, target_region=target_region)
            right = self._visit_expression(node.right, target_region=target_region)
            res_type = getattr(node, "resolved_type", None)
            tmp = self._alloc_temp(self.new_label("tmp_bin"), node, type=res_type, region=current_reg)
            self._emit(Compute(target=tmp, op=op, left=left, right=right), node)
            return tmp
        elif isinstance(node, UnaryOperation):
            right = self._visit_expression(node.right, target_region=target_region)
            tmp = self._alloc_temp(self.new_label("tmp_unary"), node, region=current_reg)
            op = node.operator.value if hasattr(node.operator, "value") else str(node.operator)
            if op == "&":
                self._emit(Borrow(dest=tmp, src=right), node)
            else:
                # Use empty string for left operand in unary operations
                self._emit(Compute(target=tmp, op=op, left="", right=right), node)
            return tmp
        elif isinstance(node, CallExpression):
            if isinstance(node.callee, IndexExpression) and isinstance(node.callee.object, Identifier) and node.callee.object.name in ("Integer", "Decimal", "String", "Vector"):
                idx_val = getattr(node.callee.index, "value", str(node.callee.index))
                target_type = f"{node.callee.object.name}[{idx_val}]"
                args = [self._visit_expression(arg, target_region=target_region) for arg in node.arguments]
                val = args[0] if args else "ZEN_NOTHING_VAL"
                tmp = self._alloc_temp(self.new_label("tmp_cast"), node, region=current_reg)
                self._emit(Call(target=tmp, callee="ZenValue_cast", args=[val, f'"{target_type}"'], region=current_reg), node)
                return tmp
            args = [self._visit_expression(arg, target_region=target_region) for arg in node.arguments]
            if isinstance(node.callee, Identifier) and (node.callee.name in ("Integer", "String", "Decimal", "Boolean", "Rune", "Bytes", "Set", "List", "Map", "Byte", "Vector", "Tuple", "Number", "Text", "Collection", "Container") or node.callee.name.startswith("Integer[") or node.callee.name.startswith("Decimal[") or node.callee.name.startswith("String[") or node.callee.name.startswith("Vector[") or node.callee.name.startswith("List<") or node.callee.name.startswith("Map<") or node.callee.name.startswith("Set<") or node.callee.name.startswith("Tuple<") or node.callee.name.startswith("Vector<")):
                target_type = node.callee.name
                val = args[0] if args else "ZEN_NOTHING_VAL"
                tmp = self._alloc_temp(self.new_label("tmp_cast"), node, region=current_reg)
                self._emit(Call(target=tmp, callee="ZenValue_cast", args=[val, f'"{target_type}"'], region=current_reg), node)
                return tmp
            if isinstance(node.callee, MemberExpression):
                obj_node = node.callee.object
                obj = self._visit_expression(obj_node, target_region=target_region)
                
                callee = self.get_mangled_name(node.callee)
                
                # Detect if it's a method call (needs 'self' or object as first arg)
                is_method = True
                
                # Built-ins are static
                obj_name = getattr(obj_node, "name", str(obj_node))
                if isinstance(obj_node, MemberExpression):
                    obj_name = self.get_mangled_name(obj_node)

                # Local variables named out/in/file must not look like builtins
                obj_is_local = (
                    isinstance(obj_node, Identifier)
                    and getattr(obj_node, "symbol", None) is not None
                    and obj_node.symbol.kind == SymbolKind.VARIABLE
                    and getattr(obj_node.symbol, "scope_level", 0) > 0
                )
                mapped_obj = obj_name if obj_is_local else self.map_builtin_name(obj_name)

                # Enum variant constructors: Result.Ok(x), Option.Something(v)
                obj_type = getattr(obj_node, "resolved_type", None)
                from Checker.Type import TypeEnum, TypeEnumerator
                prop = node.callee.property
                if hasattr(prop, "value"): prop = prop.value
                if hasattr(prop, "name"): prop = prop.name
                prop = str(prop)
                is_enum_ctor = (
                    isinstance(obj_type, (TypeEnum, TypeEnumerator))
                    or obj_name in ("Result", "Option")
                    or (isinstance(prop, str) and prop[:1].isupper() and obj_name[:1].isupper()
                        and obj_name not in ("Math", "Sys", "IO", "Str", "String", "List", "Map"))
                )
                if is_enum_ctor and prop[:1].isupper():
                    # Emit ZenValue_make_variant(enum, variant, n, args...)
                    enum_name = obj_name if isinstance(obj_name, str) else str(obj_name)
                    if hasattr(obj_type, "name") and obj_type.name and not isinstance(obj_type, TypeVariant):
                        enum_name = obj_type.name
                    res = self._alloc_temp(self.new_label("tmp_variant"), node, region=current_reg)
                    enum_s = self._alloc_temp(self.new_label("enum_s"), node, "string", region=current_reg)
                    var_s = self._alloc_temp(self.new_label("var_s"), node, "string", region=current_reg)
                    self._emit(Load(target=enum_s, source=f"`{enum_name}`", type="string"), node)
                    self._emit(Load(target=var_s, source=f"`{prop}`", type="string"), node)
                    # Call signature: (enum, variant, n_params, ...)
                    ctor_args = [enum_s, var_s, str(len(args))] + args
                    self._emit(Call(target=res, callee="ZenValue_make_variant", args=ctor_args, region=current_reg), node)
                    return res

                if mapped_obj in (
                    "__builtin",
                    "__builtin_ast",
                    "__builtin_list",
                    "__builtin_map",
                    "__builtin_set",
                    "__builtin_string",
                    "__builtin_output",
                    "__builtin_input",
                    "__builtin_file",
                    "__builtin_sys",
                    "__builtin_signal",
                    "__builtin_math",
                    "__builtin_range",
                    "__builtin_io",
                    "__builtin_memory",
                    "__builtin_process",
                    "__builtin_random",
                    "__builtin_error",
                    "__builtin_time",
                    "__builtin_term",
                    "__builtin_regex",
                    "stdout",
                    "stderr",
                    "stdin",
                    "z_stdout",
                    "z_stderr",
                    "z_stdin",
                ):
                    is_method = False
                
                # Modules, classes, structures, namespaces: static helpers (not instance methods)
                static_type_call = False
                if hasattr(obj_node, "symbol") and obj_node.symbol:
                    if obj_node.symbol.kind in (SymbolKind.MODULE, SymbolKind.NAMESPACE, SymbolKind.CLASS, SymbolKind.STRUCTURE, SymbolKind.ENUMERATOR):
                        is_method = False
                        if obj_node.symbol.kind in (
                            SymbolKind.STRUCTURE, SymbolKind.CLASS, SymbolKind.NAMESPACE, SymbolKind.ENUMERATOR
                        ):
                            static_type_call = True

                # Import aliases are modules even if a same-named function leaked
                # into the symbol table earlier during checking.
                module_call = False
                if isinstance(obj_node, Identifier) and hasattr(self, "module_aliases"):
                    if obj_node.name in self.module_aliases or obj_name in getattr(self, "imported_modules", set()):
                        is_method = False
                        module_call = True
                
                if isinstance(obj_node, ParentExpression):
                    # self.method(...) inside a class body — emit Class_method(self, ...)
                    is_method = False
                    prop_s = node.callee.property
                    if hasattr(prop_s, "value"): prop_s = prop_s.value
                    if hasattr(prop_s, "name"): prop_s = prop_s.name
                    prop_s = self.sanitize_name(str(prop_s))
                    class_m = None
                    if getattr(self, "current_class", None):
                        # Prefer mangled name of the class being generated
                        for s in self.program.statements:
                            actual = s.statement if s.__class__.__name__ == "ExportStatement" else s
                            if isinstance(actual, (ClassStatement, ObjectStatement)) and actual.name == self.current_class:
                                class_m = self.get_mangled_name(actual)
                                break
                        if not class_m:
                            class_m = self.sanitize_name(self.current_class)
                    if class_m:
                        callee = f"{class_m}_{prop_s}"
                    else:
                        callee = self.get_mangled_name(node.callee)
                    args = ["self"] + list(args)
                
                # Module-qualified calls: alias.fn → <module>_<fn> (matches definition mangling)
                if module_call and isinstance(obj_node, Identifier):
                    mod_key = obj_node.name
                    mod_prefix = self.module_aliases.get(mod_key, mod_key)
                    prop = node.callee.property
                    if hasattr(prop, "value"): prop = prop.value
                    if hasattr(prop, "name"): prop = prop.name
                    prop = self.sanitize_name(str(prop))
                    callee = f"{mod_prefix}_{prop}"
                    # Class constructors: time.Timer() → time_Timer_new
                    callee_symbol = getattr(node.callee, "symbol", None)
                    callee_type = getattr(node.callee, "resolved_type", None)
                    if (callee_symbol and callee_symbol.kind == SymbolKind.CLASS) or isinstance(callee_type, (TypeClass, TypeStructure)):
                         callee = f"{callee}_new"
                # Structure/class scope statics: always use full mangled name
                # (Paragraph.wrap → text_Paragraph_wrap), never instance dispatch.
                elif static_type_call:
                    callee = self.get_mangled_name(node.callee)
                # If it's a method call, prepend the object
                elif is_method:
                    user_args = list(args)
                    prop_s = self.sanitize_name(node.callee.property)
                    # Class receiver (Identifier or fluent Call) → Class_method((Class*)obj.as.object, ...)
                    obj_type = getattr(obj_node, "resolved_type", None)
                    class_mangled = None
                    if obj_type is not None and obj_type.__class__.__name__ in ("TypeClass", "TypeStructure"):
                        class_mangled = self.get_mangled_type_name(obj_type)
                        if class_mangled in ("ZenValue", "ZenObject", None, ""):
                            class_mangled = None
                    if class_mangled:
                        callee = f"{class_mangled}_{prop_s}"
                        if obj == "self":
                            args = ["self"] + user_args
                        else:
                            args = [f"(({class_mangled}*)({obj}).as.object)"] + user_args
                    else:
                        # Opaque ZenValue receiver (e.g. process handle) → MIR ZenObject_*
                        args = [obj] + user_args
                        callee = f"{obj}.{prop_s}"
                elif callee == "unknown" or "." in callee:
                     callee = f"{obj}.{self.sanitize_name(node.callee.property)}"
                
                # If it's NOT a method call, but the callee is a class/struct, it's a constructor
                callee_type = getattr(node.callee, "resolved_type", None)
                callee_symbol = getattr(node.callee, "symbol", None)
                if not is_method and not module_call and (isinstance(callee_type, (TypeClass, TypeStructure)) or (callee_symbol and callee_symbol.kind == SymbolKind.CLASS)):
                     callee = f"{callee}_new"
                elif not is_method and callee_symbol and callee_symbol.kind == SymbolKind.FUNCTION:
                     # Keep the mangled name as is for the call
                     pass

            else:
                callee_type = getattr(node.callee, "resolved_type", None)
                callee_symbol = getattr(node.callee, "symbol", None)
                if isinstance(callee_type, (TypeClass, TypeStructure)) or (callee_symbol and callee_symbol.kind == SymbolKind.CLASS):
                     # Call structure constructor: [Name]_new
                     mangled_name = self.get_mangled_name(node.callee)
                     callee = f"{mangled_name}_new"
                elif isinstance(node.callee, Identifier):
                     # Get raw mangled name for direct call
                     callee = self.get_mangled_name(node.callee)
                else:
                     callee = self._visit_expression(node.callee, target_region=target_region)
            
            res_type = getattr(node, "resolved_type", None)
            if isinstance(res_type, TypeTaskHandle):
                 tmp = self._alloc_temp(self.new_label("tmp_spawn"), node, type=res_type, region=current_reg)
                 self._emit(Spawn(target=tmp, callee=callee, args=args), node)
                 return tmp
            
            tmp = self._alloc_temp(self.new_label("tmp_call"), node, type=res_type, region=current_reg)
            self._emit(Call(target=tmp, callee=callee, args=args, region=current_reg), node)
            return tmp
        elif isinstance(node, MemberExpression):
            if hasattr(node, "symbol") and node.symbol:
                if node.symbol.kind in (SymbolKind.VARIANT, SymbolKind.MODULE, SymbolKind.NAMESPACE, SymbolKind.FUNCTION, SymbolKind.CLASS, SymbolKind.STRUCTURE):
                    return self.get_mangled_name(node)
                
            obj = self._visit_expression(node.object, target_region=target_region)
            prop = node.property
            if hasattr(prop, "value"): prop = prop.value
            
            # Inheritance resolution
            obj_type = getattr(node.object, "resolved_type", None)
            path = str(prop)
            if obj_type:
                 path = self._resolve_member_path(obj_type, str(prop))
                 if path.startswith("."): path = path[1:]

            # Get the type of the property itself if possible
            prop_type = getattr(node, "resolved_type", None)
            
            from Checker.Type import TypeEnumerator, TypeEnum
            if isinstance(obj_type, (TypeEnumerator, TypeEnum)) or (hasattr(obj_type, "name") and obj_type.name == "TokenType"):
                return f"ZenVariant_{obj_type.name}_{prop}"
            
            tmp = self._alloc_temp(self.new_label("tmp_attr"), node, type=prop_type, region=current_reg)
            tname = self.get_mangled_type_name(obj_type) if obj_type else None

            self._emit(GetAttr(target=tmp, obj=obj, prop=path, type=tname), node)
            return tmp
        elif isinstance(node, NothingLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_none"), node, region=current_reg)
            self._emit(Nullify(target=tmp), node)
            return tmp
        elif isinstance(node, DefaultLiteral):
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
            tmp = self._alloc_temp(self.new_label("tmp_default"), node, region=current_reg)
            if isinstance(t, TypeInteger):
                self._emit(Load(target=tmp, source="0", type="int"), node)
            elif isinstance(t, TypeBoolean):
                self._emit(Load(target=tmp, source="false", type="bool"), node)
            elif isinstance(t, TypeDecimal):
                self._emit(Load(target=tmp, source="0.0", type="decimal"), node)
            elif isinstance(t, (TypeString, TypeRune)):
                self._emit(Load(target=tmp, source="``", type="string"), node)
            elif isinstance(t, TypeList):
                self._emit(Call(target=tmp, callee="List_from_args", args=["0"], region=current_reg), node)
            elif isinstance(t, TypeMap):
                self._emit(Call(target=tmp, callee="Map_from_args", args=["0"], region=current_reg), node)
            else:
                self._emit(Load(target=tmp, source="ZEN_DEFAULT_VAL", type="default"), node)
            return tmp
        elif isinstance(node, StructureExpression):
            return self._visit_structure_expression(node, target_region=target_region)
        elif isinstance(node, (ListLiteral, VectorLiteral, SetLiteral, TupleLiteral)):
            elements = [
                self._visit_expression(el.value if isinstance(el, ElementLiteral) else el, target_region=target_region)
                for el in node.elements
            ]
            
            prefix = "list"
            if isinstance(node, VectorLiteral):
                prefix = "vector"
            elif isinstance(node, SetLiteral):
                prefix = "set"
            elif isinstance(node, TupleLiteral):
                prefix = "tuple"

            tmp = self._alloc_temp(
                self.new_label(f"tmp_{prefix}"), node, region=current_reg
            )
            # Reconstruct as a call to ZenList_from_args
            args = [str(len(elements))] + elements
            # We use a special callee name that CodeGenerator will map to ZenList_from_args
            self._emit(
                Call(
                    target=tmp,
                    callee="List_from_args",
                    args=args,
                    region=current_reg,
                ),
                node,
            )
            if isinstance(node, SetLiteral):
                set_tmp = self._alloc_temp(
                    self.new_label("tmp_set_val"), node, region=current_reg
                )
                self._emit(
                    Call(
                        target=set_tmp,
                        callee="Set_from_list",
                        args=[tmp],
                        region=current_reg,
                    ),
                    node,
                )
                return set_tmp
            return tmp
        elif isinstance(node, MapLiteral):
             elements = []
             for entry in node.elements:
                 elements.append(self._visit_expression(entry.name, target_region=target_region))
                 elements.append(self._visit_expression(entry.value, target_region=target_region))
             
             tmp = self._alloc_temp(self.new_label("tmp_map"), node, region=current_reg)
             args = [str(len(node.elements))] + elements
             self._emit(Call(target=tmp, callee="Map_from_args", args=args, region=current_reg), node)
             return tmp
        elif isinstance(node, ElementLiteral):
            return self._visit_expression(node.value, target_region=target_region)
        elif isinstance(node, ArgumentLiteral):
            return self._visit_expression(node.value, target_region=target_region)
        elif isinstance(node, IndexExpression):
            obj = self._visit_expression(node.object, target_region=target_region)
            index = self._visit_expression(node.index, target_region=target_region)
            tmp = self._alloc_temp(self.new_label("tmp_idx"), node, region=current_reg)
            self._emit(Call(target=tmp, callee="Value_get_index", args=[obj, index], region=current_reg), node)
            return tmp
        elif isinstance(node, SliceExpression):
            obj = self._visit_expression(node.object, target_region=target_region)
            line = getattr(node, "line", 1)
            col = getattr(node, "column", 1)
            start = self._visit_expression(node.start, target_region=target_region) if node.start is not None else self._visit_expression(NothingLiteral(line, col), target_region=target_region)
            end = self._visit_expression(node.end, target_region=target_region) if node.end is not None else self._visit_expression(NothingLiteral(line, col), target_region=target_region)
            step = self._visit_expression(node.step, target_region=target_region) if node.step is not None else self._visit_expression(NothingLiteral(line, col), target_region=target_region)
            tmp = self._alloc_temp(self.new_label("tmp_slice"), node, region=current_reg)
            self._emit(Call(target=tmp, callee="ZenValue_slice", args=[obj, start, end, step], region=current_reg), node)
            return tmp
        elif isinstance(node, (BlockExpression, BlockStatement)):
            sym = None
            for stmt in node.statements:
                if isinstance(stmt, ExpressionStatement):
                    sym = self._visit_expression(stmt.expression, target_region=target_region)
                else:
                    self._visit(stmt)
                    sym = None
            
            if sym is None:
                tmp = self._alloc_temp(self.new_label("tmp_none"), node, region=current_reg)
                self._emit(Nullify(target=tmp), node)
                return tmp
            return sym

        elif isinstance(node, FunctionExpression):
             return self._visit_function_expression(node, target_region=target_region)
        elif isinstance(node, ParentExpression):
             return "self"
        
        raise Exception(f"SMIRGenerator: unhandled expression node type: {type(node)}")

    def _visit_structure_expression(self, node: StructureExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        args = []
        for member in node.members:
             val = self._visit_expression(member.value, target_region=current_reg)
             args.append(val)
        
        # Resolve constructor C name: Word / text.Word → text_Word_new
        mangled_name = None
        rt = getattr(node, "resolved_type", None)
        if rt is not None and getattr(rt, "name", None) and rt.__class__.__name__ in (
            "TypeStructure", "TypeClass"
        ):
            mangled_name = self.get_mangled_type_name(rt)
        if not mangled_name or mangled_name in ("ZenValue", "ZenObject", "Variant"):
            raw = node.name
            if isinstance(raw, str) and "<" in raw and raw.endswith(">"):
                raw = raw[:raw.index("<")]
            # Qualified "mod.Type" or bare "Type"
            if isinstance(raw, str) and "." in raw and not raw.startswith("MemberExpression"):
                parts = raw.split(".")
                mod_key = parts[0]
                type_name = parts[-1]
                mod_prefix = (getattr(self, "module_aliases", {}) or {}).get(mod_key, mod_key)
                # Prefer basename of module path when alias maps to nested package
                if "/" in str(mod_prefix) or "\\" in str(mod_prefix):
                    mod_prefix = os.path.basename(str(mod_prefix)).replace(".zl", "")
                mangled_name = f"{self.sanitize_name(mod_prefix)}_{self.sanitize_name(type_name)}"
            elif isinstance(raw, str) and not raw.startswith("MemberExpression"):
                mangled_name = self.sanitize_name(raw)
                filename = None
                if hasattr(node, "symbol") and node.symbol and node.symbol.filename:
                    filename = node.symbol.filename
                elif rt is not None and getattr(rt, "filename", None):
                    filename = rt.filename
                if filename and self.main_file:
                    stmt_path = os.path.abspath(filename)
                    main_path = os.path.abspath(self.main_file)
                    if stmt_path != main_path:
                        module_name = os.path.basename(stmt_path).replace(".zl", "")
                        if module_name and module_name not in ("bootstrap_runtime",):
                            mangled_name = f"{module_name}_{mangled_name}"
            else:
                # Parser stored str(MemberExpression); recover Type from trailing property=
                # or fall back to last Identifier-like token — prefer symbol if present.
                if hasattr(node, "symbol") and node.symbol:
                    mangled_name = self.get_mangled_name(node.symbol)
                else:
                    # Last resort: extract property='Word' from dumped MemberExpression
                    import re
                    m = re.search(r"property='([^']+)'", str(raw))
                    m_obj = re.search(r"name='([^']+)'", str(raw))
                    if m and m_obj:
                        mod_key = m_obj.group(1)
                        type_name = m.group(1)
                        mod_prefix = (getattr(self, "module_aliases", {}) or {}).get(mod_key, mod_key)
                        mangled_name = f"{self.sanitize_name(mod_prefix)}_{self.sanitize_name(type_name)}"
                    elif m:
                        mangled_name = self.sanitize_name(m.group(1))
                    else:
                        mangled_name = "ZenObject"

        res = self._alloc_temp(
            self.new_label("struct_inst"), node, type=rt, region=current_reg
        )
        self._emit(Call(target=res, callee=f"{mangled_name}_new", args=args), node)
        return res

    def _visit_is_expression(self, node: IsExpression, target_region: Optional[str] = None) -> str:
        subject = self._visit_expression(node.left, target_region=target_region)
        return self._visit_pattern_match(subject, node.right, node)

    def _visit_check_expression(self, node: CheckExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        exit_label = self.new_label("check_expr_exit")
        catch_label = self.new_label("check_expr_catch")
        
        res_tmp = self._alloc_temp(self.new_label("check_res"), node, region=current_reg)

        # Catch both raised exceptions (setjmp) and Error/Nothing return values,
        # matching the interpreter's check-expression semantics.
        self._emit(Try(catch_label=catch_label), node)
        
        val_tmp = self._visit_expression(node.expression)
        
        # Determine if we are checking an Option or Result
        expr_type = getattr(node.expression, "resolved_type", None)
        from Checker.Type import TypeOption, TypeResult, TypeEnumVariant
        
        is_fail = self._alloc_temp(self.new_label("is_fail"), node, "bool", region=current_reg)
        
        if isinstance(expr_type, TypeOption):
            # Check if Nothing
            self._emit(Call(target=is_fail, callee="ZenValue_is_nothing", args=[val_tmp], region=current_reg), node)
        elif isinstance(expr_type, TypeResult):
            # Check if Error
            self._emit(Call(target=is_fail, callee="ZenValue_is_error", args=[val_tmp], region=current_reg), node)
        else:
            # Fallback to general error/nothing check
            nothing_check = self._alloc_temp(self.new_label("is_none"), node, "bool", region=current_reg)
            self._emit(Call(target=nothing_check, callee="ZenValue_is_nothing", args=[val_tmp], region=current_reg), node)
            error_check = self._alloc_temp(self.new_label("is_err"), node, "bool", region=current_reg)
            self._emit(Call(target=error_check, callee="ZenValue_is_type_name", args=[val_tmp, '"Error"'], region=current_reg), node)
            self._emit(Compute(target=is_fail, op="or", left=nothing_check, right=error_check), node)

        self._emit(Branch(condition=is_fail, true_label=catch_label, false_label=None), node)
        
        # Success: Unwrap and move to res_tmp
        if isinstance(expr_type, (TypeOption, TypeResult, TypeEnumVariant)):
            # Enums store data in variants. For Option.Something and Result.Ok, data is at index 0
            self._emit(Call(target=res_tmp, callee="ZenValue_get_variant_data", args=[val_tmp, "0"], region=current_reg), node)
        else:
            self._emit(Move(dest=res_tmp, src=val_tmp), node)
            
        self._emit(Jump(target=exit_label), node)
        
        # 2. Catch block (raised exception or Error/Nothing value)
        self._emit(Catch(), node)
        self._emit(Label(name=catch_label), node)
        
        if node.or_value:
            fb = self._visit_expression(node.or_value)
            self._emit(Move(dest=res_tmp, src=fb), node)
        elif node.raise_expression:
            msg = self._visit_expression(node.raise_expression)
            self._emit(Raise(value=msg), node)
        else:
             # Default fallback if nothing provided?
             self._emit(Nullify(target=res_tmp), node)
        
        self._emit(EndTry(), node)
        self._emit(Label(name=exit_label), node)
        return res_tmp

    def _visit_when_expression(self, node: WhenExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        exit_label = self.new_label("when_expr_exit")
        res_tmp = self._alloc_temp(self.new_label("when_res"), node, region=current_reg)
        
        next_branch_label = self.new_label("when_expr_next")
        cond = self._visit_expression(node.condition)
        self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
        val = self._visit_expression(node.when_block)
        self._emit(Move(dest=res_tmp, src=val), node)
        self._emit(Jump(target=exit_label), node)
        self._emit(Label(name=next_branch_label), node)
        
        for branch in node.conditional_blocks:
            next_branch_label = self.new_label("when_expr_next")
            cond = self._visit_expression(branch["condition"])
            self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
            val = self._visit_expression(branch["block"])
            self._emit(Move(dest=res_tmp, src=val), node)
            self._emit(Jump(target=exit_label), node)
            self._emit(Label(name=next_branch_label), node)
            
        if node.or_block:
            val = self._visit_expression(node.or_block)
            self._emit(Move(dest=res_tmp, src=val), node)
        else:
            self._emit(Nullify(target=res_tmp), node)
            
        self._emit(Label(name=exit_label), node)
        return res_tmp

    def _visit_when_inline_expression(self, node: WhenInlineExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        exit_label = self.new_label("when_inline_exit")
        false_label = self.new_label("when_inline_false")
        res_tmp = self._alloc_temp(self.new_label("when_inline_res"), node, region=current_reg)
        
        cond = self._visit_expression(node.condition)
        self._emit(Branch(condition=cond, true_label=None, false_label=false_label), node)
        true_val = self._visit_expression(node.when_value)
        self._emit(Move(dest=res_tmp, src=true_val), node)
        self._emit(Jump(target=exit_label), node)
        self._emit(Label(name=false_label), node)
        false_val = self._visit_expression(node.or_value)
        self._emit(Move(dest=res_tmp, src=false_val), node)
        self._emit(Label(name=exit_label), node)
        return res_tmp

    def _lambda_collect_captures(self, node: FunctionExpression) -> list:
        """Return free outer locals referenced by the lambda body (by-value captures).

        Each entry is a dict: {name, outer_c} where outer_c is the mangled C
        name of the value in the enclosing function at creation time.
        """
        from Parser.AST import Identifier, AssignmentStatement, ReassignmentStatement

        param_names = set()
        for p in (node.parameters or []):
            pname = getattr(p, "name", None)
            if pname:
                param_names.add(pname)

        # Locals declared inside the lambda body are not free.
        local_names = set()

        def collect_locals(n):
            if n is None:
                return
            if isinstance(n, list):
                for item in n:
                    collect_locals(item)
                return
            cls = n.__class__.__name__
            if cls in ("AssignmentStatement", "ReassignmentStatement") or isinstance(
                n, (AssignmentStatement, ReassignmentStatement)
            ):
                nm = getattr(n, "name", None)
                if isinstance(nm, str):
                    local_names.add(nm)
                elif hasattr(nm, "name"):
                    local_names.add(nm.name)
            if hasattr(n, "__dict__"):
                for key, val in n.__dict__.items():
                    if key.startswith("_"):
                        continue
                    collect_locals(val)

        collect_locals(node.body)

        # Builtins / globals that must not be captured as locals.
        skip = set(param_names) | set(local_names) | {
            "self", "True", "False", "true", "false", "nothing", "Nothing",
            "Result", "Option", "Error", "Str", "IO", "Sys", "Math", "List", "Map",
        }
        if hasattr(self, "global_variable_names"):
            skip |= set(self.global_variable_names)
        if hasattr(self, "module_aliases"):
            skip |= set(self.module_aliases.keys())
        if hasattr(self, "imported_modules"):
            skip |= set(self.imported_modules)

        free_ordered = []
        seen = set()

        def walk_ids(n):
            if n is None:
                return
            if isinstance(n, list):
                for item in n:
                    walk_ids(item)
                return
            if isinstance(n, Identifier):
                name = n.name
                if not name or name in skip or name.startswith("__"):
                    return
                # Nested function expressions: their bodies are separate.
                # (We still walk them; free vars relative to *this* lambda
                # that are only used inside nested lambdas should still be
                # captured by the outer lambda if referenced — skip nested
                # FunctionExpression bodies to avoid double-counting confusion.)
                if name in seen:
                    return
                # Prefer variables with a symbol from an outer scope, or any
                # non-param identifier (conservative capture).
                sym = getattr(n, "symbol", None)
                if sym is not None:
                    kind = getattr(sym, "kind", None)
                    from Checker.Type import SymbolKind
                    if kind in (
                        SymbolKind.FUNCTION, SymbolKind.CLASS, SymbolKind.STRUCTURE,
                        SymbolKind.MODULE, SymbolKind.NAMESPACE, SymbolKind.ENUMERATOR,
                        SymbolKind.VARIANT,
                    ):
                        return
                seen.add(name)
                outer_c = self.get_mangled_name(n)
                free_ordered.append({"name": name, "outer_c": outer_c})
                return
            if n.__class__.__name__ == "FunctionExpression" or isinstance(n, FunctionExpression):
                # Do not walk into nested lambda bodies for free-var discovery
                # of *this* lambda (nested lambdas capture independently).
                return
            if hasattr(n, "__dict__"):
                for key, val in n.__dict__.items():
                    if key.startswith("_"):
                        continue
                    walk_ids(val)

        walk_ids(node.body)
        return free_ordered

    def _visit_function_expression(self, node: FunctionExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        # Generate a named C function; free outer locals are by-value captures.
        lambda_name = self.new_label("lambda")

        captures = self._lambda_collect_captures(node)
        node._closure_captures = captures  # consumed by FunctionalHandler
        user_arity = len(node.parameters or [])

        # Forward-declare early so the enclosing function can take the address.
        if not hasattr(self, "lambda_forward_decls"):
            self.lambda_forward_decls = []
        if not hasattr(self, "_lambda_fwd_names"):
            self._lambda_fwd_names = set()
        if lambda_name not in self._lambda_fwd_names:
            self._lambda_fwd_names.add(lambda_name)
            param_parts = []
            for cap in captures:
                param_parts.append(f"ZenValue {self.sanitize_name(cap['name'])}")
            for p in (node.parameters or []):
                param_parts.append(
                    f"ZenValue {self.sanitize_name(getattr(p, 'name', p))}"
                )
            params = ", ".join(param_parts) if param_parts else "void"
            self.lambda_forward_decls.append(f"ZenValue {lambda_name}({params});")

        # Record this lambda for the FunctionalHandler to emit later
        if hasattr(self, "pending_lambdas"):
             self.pending_lambdas.append((lambda_name, node))

        res = self._alloc_temp(self.new_label("lambda_val"), node, region=current_reg)
        if captures:
            # ZenValue_from_closure(fn, user_arity, n_caps, cap0, cap1, ...)
            cap_args = [cap["outer_c"] for cap in captures]
            self._emit(
                Call(
                    target=res,
                    callee="ZenValue_from_closure",
                    args=[
                        f"(void*){lambda_name}",
                        str(user_arity),
                        str(len(captures)),
                    ] + cap_args,
                    region=current_reg,
                ),
                node,
            )
        else:
            self._emit(
                Call(
                    target=res,
                    callee="ZenValue_from_function",
                    args=[f"(ZenValue (*)(void)){lambda_name}"],
                    region=current_reg,
                ),
                node,
            )

        return res
    def _visit_await(self, node: AwaitExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        handle = self._visit_expression(node.expression, target_region=target_region)
        
        res_type = getattr(node, "resolved_type", None)
        tmp = self._alloc_temp(self.new_label("tmp_await"), node, type=res_type, region=current_reg)
        self._emit(Await(target=tmp, handle=handle), node)
        return tmp
