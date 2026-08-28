import os
from typing import Any, Union
from Parser.AST import Identifier, MemberExpression, ASTNode, ParentExpression
from Checker.Type import SymbolKind

class MangleHandler:
    def sanitize_name(self, name: str) -> str:
        if name in (
            "char", "int", "float", "double", "void", "struct", "return", 
            "if", "else", "while", "for", "do", "break", "continue", "switch", 
            "case", "default", "typedef", "static", "extern", "long", "short",
            "signed", "unsigned", "inline", "volatile", "const", "enum", "union",
            "register", "auto", "restrict", "complex", "imaginary"
        ):
            return f"zen_{name}"
        return name

    def map_builtin_name(self, name: str) -> str:
        if not name: return name

        # Imported modules win over builtin short-names (e.g. `import zen.math as math`).
        if hasattr(self, "module_aliases") and name in self.module_aliases:
            return self.module_aliases[name]
        
        # Check for direct matches or prefixed matches (e.g. collections_Map)
        check_name = name
        if "_" in name:
             parts = name.split("_")
             if parts[-1] and parts[-1][0].isupper():
                  check_name = parts[-1]
             
        if check_name in ("Str", "string") and name == check_name: return "__builtin_string"
        if check_name in ("IO", "io") and name == check_name: return "__builtin_io"
        if check_name in ("Sys", "sys") and name == check_name: return "__builtin_sys"
        if check_name in ("Signal", "signal") and name == check_name: return "__builtin_signal"
        # Bare Math/math only map to the C math runtime when not a module alias.
        if name in ("Math",) or (name == "math" and not (hasattr(self, "module_aliases") and "math" in self.module_aliases)):
            if check_name in ("Math", "math"):
                return "__builtin_math"
        # Only capital Range maps to the builtin module object — bare `range`
        # is a common function name (zen.math.range.range).
        if name == "Range": return "__builtin_range"
        if check_name == "List": return "__builtin_list"
        if check_name == "Map": return "__builtin_map"
        if check_name == "file" and name == check_name and not (hasattr(self, "module_aliases") and "file" in self.module_aliases): return "__builtin_file"
        if check_name == "out" and name == check_name: return "__builtin_output"
        if check_name == "in" and name == check_name: return "__builtin_input"
        # Bare `time` / `term` only map when not an import alias.
        if name == "time" and not (hasattr(self, "module_aliases") and "time" in self.module_aliases):
            return "__builtin_time"
        if name == "term" and not (hasattr(self, "module_aliases") and "term" in self.module_aliases):
            return "__builtin_term"
             
        return name

    def get_mangled_type_name(self, type_obj: Any) -> str:
        if not type_obj:
            return "ZenValue"
            
        if type_obj.__class__.__name__ in ("TypeReference", "TypePointer") or (hasattr(type_obj, "inner_type") and type_obj.inner_type):
            return self.get_mangled_type_name(type_obj.inner_type)
        
        # If it's a string name, try to resolve it or just return it
        if isinstance(type_obj, str):
            if type_obj in (
                "String", "Bool", "Boolean", "Integer", "Float", "Decimal",
                "Variant", "List", "Map", "Any", "string", "char*", "int",
                "bool", "double", "float", "rune", "Rune", "Void", "void"
            ):
                return "ZenValue"
            return self.sanitize_name(type_obj)

        if not hasattr(type_obj, "name") or type_obj.name is None:
            return "ZenObject"
            
        name = type_obj.name
        filename = getattr(type_obj, "filename", None)
        if not filename and hasattr(type_obj, "symbol") and type_obj.symbol:
            filename = getattr(type_obj.symbol, "filename", None)
        if name in ("String", "Bool", "Boolean", "Integer", "Float", "Decimal", "Variant", "List", "Map", "Any", "string", "char*", "int", "bool", "double", "float", "rune", "Rune", "Void", "void"):
            return "ZenValue"
        
        if not filename or not self.main_file:
            return self.sanitize_name(name)
            
        stmt_path = os.path.abspath(filename)
        main_path = os.path.abspath(self.main_file)
        
        if stmt_path != main_path:
            module_name = os.path.basename(stmt_path).replace(".zl", "")
            if module_name and module_name not in ("bootstrap_runtime",):
                 return f"{module_name}_{self.sanitize_name(name)}"
        return self.sanitize_name(name)

    def get_mangled_name(self, node: Union[Identifier, MemberExpression, ASTNode], should_prefix: bool = True) -> str:
        if isinstance(node, ParentExpression):
            return "self"
        if isinstance(node, MemberExpression):
            if hasattr(node, "symbol") and node.symbol:
                if node.symbol.kind in (SymbolKind.CLASS, SymbolKind.STRUCTURE, SymbolKind.NAMESPACE, SymbolKind.MODULE):
                    return self.get_mangled_name(node.symbol)
            # ADT Variant case: Enum.Variant
            name = self.sanitize_name(node.property)
            if hasattr(node, "symbol") and node.symbol and node.symbol.kind == SymbolKind.VARIANT:
                enum_mangled = self.get_mangled_name(node.object)
                return f"ZenVariant_{enum_mangled}_{node.symbol.name}"
            
            raw_prop = node.property
            if hasattr(raw_prop, "name"): raw_prop = raw_prop.name
            if hasattr(raw_prop, "value"): raw_prop = raw_prop.value
            raw_prop = self.sanitize_name(raw_prop)

            # Special mapping for built-in objects
            obj_name = self.get_mangled_name(node.object, should_prefix=should_prefix)
            if hasattr(node.object, "resolved_type") and node.object.resolved_type:
                t = node.object.resolved_type
                if hasattr(t, "name"):
                    t_name = t.name
                    if t_name == "List": obj_name = "__builtin_list"
                    elif t_name == "Map": obj_name = "__builtin_map"
                    elif t_name == "String": obj_name = "__builtin_string"
                    elif t_name == "IO": obj_name = "__builtin_output"
                    elif t_name == "Set": obj_name = "__builtin_set"
                
                if hasattr(t, "symbol") and t.symbol:
                     if t.symbol.kind == SymbolKind.CLASS:
                         class_mangled = self.get_mangled_name(t.symbol)
                         # Prefer TypeClass/symbol filename so methods match
                         # definitions (time_Timer_start vs Timer_start).
                         t_file = getattr(t, "filename", None) or getattr(t.symbol, "filename", None)
                         if t_file and self.main_file:
                             stmt_path = os.path.abspath(t_file)
                             main_path = os.path.abspath(self.main_file)
                             if stmt_path != main_path:
                                 mod = os.path.basename(stmt_path).replace(".zl", "")
                                 if mod and mod not in ("bootstrap_runtime",) and not class_mangled.startswith(mod + "_"):
                                     class_mangled = f"{mod}_{self.sanitize_name(t.name if hasattr(t, 'name') else class_mangled)}"
                         return f"{class_mangled}_{raw_prop}"
            
            obj_name = self.map_builtin_name(obj_name)
            
            # Generic builtins on __builtin (bytes, serialize, errors, …)
            if obj_name == "__builtin":
                if raw_prop in ("error", "raise"):
                    return "ZenValue_make_error_message"
                if raw_prop == "error_literal":
                    return "ZenValue_make_error_literal"
                builtin_map = {
                    "create_bytes_size": "ZenBytes_create_size",
                    "create_bytes_list": "ZenBytes_create_list",
                    "string_to_bytes": "ZenBytes_string_to_bytes",
                    "bytes_to_string": "ZenBytes_bytes_to_string",
                    "bytes_from_string": "ZenBytes_from_string",
                    "pack_binary": "ZenBytes_pack_binary",
                    "unpack_binary": "ZenBytes_unpack_binary",
                    "instantiate": "ZenValue_instantiate",
                    "create_object": "ZenValue_create_object",
                }
                if raw_prop in builtin_map:
                    return builtin_map[raw_prop]
                return f"ZenValue_{raw_prop}"

            # Standard mapping for built-ins
            if obj_name == "__builtin_output":
                if raw_prop == "write": return "ZenIO_write_value"
                if raw_prop in ("write_line", "writeln"): return "ZenIO_write_line"
                if raw_prop == "write_raw": return "ZenIO_write_raw"
                if raw_prop == "info": return "ZenIO_write_info"
                if raw_prop == "warn": return "ZenIO_write_warning"
                if raw_prop == "error": return "ZenIO_write_error"
                if raw_prop == "debug": return "ZenIO_write_debug"
                if raw_prop == "flush": return "ZenIO_flush"
                return "ZenIO_write_value"
            if obj_name == "__builtin_input":
                if raw_prop == "read": return "ZenIO_read_value"
                if raw_prop == "read_line": return "ZenIO_read_line"
                if raw_prop == "read_exact": return "ZenIO_read_exact"
                return "ZenIO_read_value"
            if obj_name == "__builtin_file":
                if raw_prop == "read": return "ZenIO_read_file"
                if raw_prop == "write": return "ZenIO_write_file"
                if raw_prop == "exists": return "ZenIO_file_exists"
                if raw_prop == "write_bytes": return "ZenIO_write_bytes"
                if raw_prop == "append": return "ZenIO_append"
                if raw_prop == "remove": return "ZenIO_remove"
                if raw_prop == "is_file": return "ZenIO_is_file"
                if raw_prop == "is_dir": return "ZenIO_is_dir"
                if raw_prop == "open": return "ZenIO_open"
                if raw_prop == "list_dir": return "ZenIO_list_dir"
                if raw_prop == "mkdir": return "ZenIO_mkdir"
                if raw_prop == "mkdir_p": return "ZenIO_mkdir_p"
                return f"ZenIO_{raw_prop}"
            if obj_name == "__builtin_io":
                if raw_prop == "write": return "ZenIO_write_value"
                if raw_prop == "info": return "ZenIO_write_info"
                if raw_prop == "warn": return "ZenIO_write_warning"
                if raw_prop == "error": return "ZenIO_write_error"
                if raw_prop == "debug": return "ZenIO_write_debug"
                if raw_prop == "flush": return "ZenIO_flush"
                if raw_prop == "read_file": return "ZenIO_read_file"
                if raw_prop == "write_file": return "ZenIO_write_file"
                if raw_prop == "append": return "ZenIO_append"
                if raw_prop == "exists": return "ZenIO_file_exists"
                if raw_prop == "list_dir": return "ZenIO_list_dir"
                return f"ZenIO_{raw_prop}"
            if obj_name == "__builtin_sys":
                 if raw_prop == "get_args": return "ZenSystem_get_args"
                 if raw_prop == "exit": return "ZenSystem_exit"
                 if raw_prop.startswith("inotify_"): return f"ZenSys_{raw_prop}"
                 return f"ZenSystem_{raw_prop}"

            if obj_name == "__builtin_time":
                return f"ZenTime_{raw_prop}"

            if obj_name == "__builtin_term":
                return f"ZenTerm_{raw_prop}"

            if obj_name == "__builtin_process":
                return f"ZenProcess_{raw_prop}"

            if obj_name == "__builtin_signal":
                return f"ZenSignal_{raw_prop}"

            if obj_name == "__builtin_net":
                if raw_prop == "http_request":
                    return "ZenNet_http_request"
                return f"ZenNet_{raw_prop}"

            if obj_name == "__builtin_math":
                # Avoid colliding with libm symbols (sin/cos/floor/...).
                if raw_prop == "pow":
                    return "ZenMath_power"
                if raw_prop in ("pi", "e"):
                    return f"ZenMath_{raw_prop}"  # handled as GetAttr constants when needed
                return f"ZenMath_{raw_prop}"

            if obj_name == "__builtin_memory":
                return f"ZenMemory_{raw_prop}"

            if obj_name == "__builtin_regex":
                return f"ZenRegex_{raw_prop}"
            
            if obj_name == "__builtin_string":
                if raw_prop == "length": return "ZenString_get_length"
                if raw_prop == "at": return "ZenString_get_character_at_index"
                if raw_prop == "substring": return "ZenString_get_substring"
                if raw_prop == "to_lower": return "ZenString_to_lowercase"
                if raw_prop == "to_upper": return "ZenString_to_uppercase"
                if raw_prop == "index_of": return "ZenString_find_index"
                if raw_prop == "to_string": return "ZenValue_to_string"
                return f"ZenString_{raw_prop}"
            
            if obj_name == "__builtin_list":
                if raw_prop == "length" or raw_prop == "count": return "ZenList_get_length"
                if raw_prop == "at": return "ZenList_get_value_at_index"
                if raw_prop == "append": return "ZenList_append_value"
                return f"ZenList_{raw_prop}"
            
            if obj_name == "__builtin_map":
                if raw_prop == "keys": return "ZenMap_get_keys"
                if raw_prop == "values": return "ZenMap_get_values"
                if raw_prop == "items": return "ZenMap_get_items"
                if raw_prop == "has": return "ZenMap_has_key"
                if raw_prop == "get": return "ZenMap_get_value_at_key"
                return f"ZenMap_{raw_prop}"

            if obj_name == "__builtin_reflect":
                mapping = {
                    "fields": "ZenReflect_fields",
                    "methods": "ZenReflect_methods",
                    "has_field": "ZenReflect_has_field",
                    "has_method": "ZenReflect_has_method",
                    "field": "ZenReflect_field",
                    "set_field": "ZenReflect_set_field",
                    "type_name": "ZenReflect_type_name",
                    "is_reflectable": "ZenReflect_is_reflectable",
                    "register_type": "ZenReflect_register_type",
                    "call": "ZenReflect_call",
                    "apply": "ZenReflect_apply",
                }
                if raw_prop in mapping:
                    return mapping[raw_prop]
                return f"ZenReflect_{raw_prop}"
            
            if obj_name == "__builtin_set":
                if raw_prop == "has": return "ZenSet_contains_value"
                if raw_prop == "add": return "ZenSet_add_value"
                return f"ZenSet_{raw_prop}"
            
            # If it was a built-in, we already returned.
            # Otherwise, check for module prefixing
            target_filename = None
            if hasattr(node.object, "symbol") and node.object.symbol:
                if node.object.symbol.kind == SymbolKind.MODULE:
                    target_filename = node.object.symbol.filename
            if not target_filename:
                # Only use filename if it's a module identifier
                if isinstance(node.object, Identifier) and hasattr(node.object, "symbol") and node.object.symbol and node.object.symbol.kind == SymbolKind.MODULE:
                    target_filename = getattr(node.object, "filename", None)
            
            if target_filename and self.main_file:
                stmt_path = os.path.abspath(target_filename)
                main_path = os.path.abspath(self.main_file)
                if stmt_path != main_path:
                    module_name = os.path.basename(stmt_path).replace(".zl", "")
                    if module_name not in ("bootstrap_runtime"):
                        name = f"{module_name}_{name}"
                        return name # If we prefixed it, it's a module call

            # Scope / structure / class static helpers: Paragraph.wrap → text_Paragraph_wrap
            # (definitions live in `scope Paragraph { function wrap … }` with module prefix).
            # Do not use get_mangled_name(object) here: while generating another scope
            # (e.g. Chapter), current_scope would wrongly prefix the type name.
            obj_sym = getattr(node.object, "symbol", None) if hasattr(node.object, "symbol") else None
            if obj_sym and obj_sym.kind in (
                SymbolKind.STRUCTURE, SymbolKind.CLASS, SymbolKind.NAMESPACE, SymbolKind.ENUMERATOR
            ):
                type_mangled = self.sanitize_name(obj_sym.name)
                t_file = getattr(obj_sym, "filename", None) or getattr(
                    getattr(obj_sym, "type", None), "filename", None
                )
                if t_file and self.main_file:
                    stmt_path = os.path.abspath(t_file)
                    main_path = os.path.abspath(self.main_file)
                    if stmt_path != main_path:
                        mod = os.path.basename(stmt_path).replace(".zl", "")
                        if mod and mod not in ("bootstrap_runtime",):
                            type_mangled = f"{mod}_{type_mangled}"
                if type_mangled and type_mangled not in ("unknown", "ZenObject", "ZenValue"):
                    return f"{type_mangled}_{raw_prop}"
 
            # Fallback for common methods on unknown types
            dispatch_mapping = {
                "length": "get_length", "count": "get_length",
                "at": "get_at",
                "append": "append",
                "substring": "get_substring",
                "starts_with": "starts_with",
                "ends_with": "ends_with",
                "contains": "contains",
                "keys": "get_keys",
                "values": "get_values",
                "pop": "pop_dispatch",
                "push": "append",
                "enqueue": "append",
                "dequeue": "pop",
                "write": "write",
                "writeln": "writeln",
                "read": "read",
                "remove": "remove",
                "remove_at": "remove_at",
                "join": "join",
                "has": "contains",
                "info": "info",
                "warn": "warn",
                "error": "error"
            }
            if raw_prop in dispatch_mapping:
                # Special case: length/count on objects with .as.object access?
                # For now, keep it as ZenValue_ method
                return f"ZenValue_{dispatch_mapping[raw_prop]}"
            
            return name

        # Explicit C symbol override (e.g. scope constants → ZenVariant_Scope_Name)
        force = getattr(node, "_force_c_name", None)
        if force:
            return force

        name = ""
        if isinstance(node, Identifier):
            name = node.name
        else:
            name = getattr(node, "name", "unknown")
        
        name = self.sanitize_name(name)

        if name == "self":
             return "self"

        # If it's a special identifier like __builtin, don't mangle
        if name.startswith("__"):
            return name

        level = getattr(node, "scope_level", 0)
        if hasattr(node, "symbol") and node.symbol:
            level = node.symbol.scope_level

        # Local variables named `out`/`in`/`file`/… must not become builtins
        # (e.g. `let out -> []` was incorrectly rewritten to `__builtin_output`).
        is_local_var = (
            hasattr(node, "symbol")
            and node.symbol
            and node.symbol.kind == SymbolKind.VARIABLE
            and level > 0
        )
        if not is_local_var:
            mapped_name = self.map_builtin_name(name)
            if mapped_name != name:
                return mapped_name
            
        is_func = hasattr(node, "symbol") and node.symbol and node.symbol.kind == SymbolKind.FUNCTION
        # Only functions in named scopes get the current_scope prefix (Sentence_to_words).
        # Structure/class/type identifiers must stay bare so module prefixing is correct
        # (Paragraph not Chapter_Paragraph while generating Chapter methods).
        is_type_name = hasattr(node, "symbol") and node.symbol and node.symbol.kind in (
            SymbolKind.STRUCTURE, SymbolKind.CLASS, SymbolKind.NAMESPACE, SymbolKind.ENUMERATOR, SymbolKind.MODULE
        )
        if self.current_scope and is_func:
            name = f"{self.current_scope}_{name}"
        elif self.current_scope and level == 0 and not is_type_name and not is_func:
            # Module-level non-function globals inside a scope body (rare)
            pass
            
        # Global symbols (level 0) or specific AST nodes (Class, Function)
        # We also prefix level 1 symbols if they are inside a named scope
        should_prefix = (level == 0 or (level == 1 and self.current_scope) or is_func)
        
        # Prefer the AST node's own filename for declarations. Symbol.filename
        # can be wrong after import-alias collisions (e.g. io.error vs module error).
        target_filename = getattr(node, "filename", None)
        node_cls = node.__class__.__name__
        if node_cls in (
            "FunctionStatement", "ClassStatement", "StructureStatement",
            "TaskStatement", "ObjectStatement", "EnumeratorStatement",
        ):
            if not target_filename and hasattr(node, "symbol") and node.symbol:
                target_filename = node.symbol.filename
        else:
            if hasattr(node, "symbol") and node.symbol:
                target_filename = node.symbol.filename or target_filename

        if should_prefix and target_filename and self.main_file:
            stmt_path = os.path.abspath(target_filename)
            main_path = os.path.abspath(self.main_file)
            
            if stmt_path != main_path:
                module_name = os.path.basename(stmt_path).replace(".zl", "")
                # basename can include nested dirs only via last component; good.
                # Always prefix non-main module declarations so call sites
                # (which use symbol.filename) agree with definitions.
                if module_name and module_name not in ("bootstrap_runtime",):
                    if name not in ("Option", "Result", "Option.Something", "Option.Nothing", "Result.Ok", "Result.Error"):
                        name = f"{module_name}_{name}"

        # ADT Variant case
        if hasattr(node, "symbol") and node.symbol and node.symbol.kind == SymbolKind.VARIANT:
            return f"ZenVariant_{name}"

        if level > 0:
            if hasattr(node, "symbol") and node.symbol and node.symbol.kind in (SymbolKind.FUNCTION, SymbolKind.CLASS, SymbolKind.STRUCTURE):
                return name
            return f"{name}_L{level}"
        return name

    def _resolve_member_path(self, obj_type: Any, member_name: str) -> str:
        current = obj_type
        prefix = ""
        while current:
            members = getattr(current, "members", {})
            if isinstance(members, list):
                 if any(m.name == member_name for m in members if hasattr(m, "name")):
                      return prefix + "." + member_name
            elif member_name in members:
                 return prefix + "." + member_name
            
            parent = getattr(current, "parent", None)
            if parent:
                 prefix += ".base"
                 if isinstance(parent, str): break
                 current = parent
            else:
                 break
        return "." + member_name
