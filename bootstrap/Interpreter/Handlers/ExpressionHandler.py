from typing import Any, List, Optional
from Parser.AST import (
    BlockExpression,
    FunctionExpression,
    WhenExpression,
    WhenInlineExpression,
    StructureExpression,
    MemberExpression,
    IndexExpression,
    SliceExpression,
    ParentExpression,
    InExpression,
    IsExpression,
    BinaryOperation,
    UnaryOperation,
    Identifier,
    CallExpression,
    CheckExpression,
    NothingLiteral,
    IteratorLiteral,
    AwaitExpression,
)
from Interpreter.Runtime import (
    BaseObject,
    FunctionObject,
    StructureObject,
    ClassObject,
    InstanceObject,
    ParentProxy,
    Environment,
    VariantObject,
    TaskObject,
    TaskHandleObject,
    BuiltinCapability,
)
from Interpreter.Exceptions import ReturnException, RaiseException, RuntimeBreak, RuntimeContinue

class ExpressionHandler:
    def _evaluate_block_expression(
        self, node: BlockExpression, environment: Environment
    ) -> any:
        # create new nested environment
        new_environment = Environment(parent=environment)
        new_environment.defers = []

        result: any = None

        try:
            for statement in node.statements:
                try:
                    result = self._evaluate(statement, new_environment)

                except ReturnException:
                    # bubble up return to caller
                    raise

                except RuntimeBreak:
                    raise

                except RuntimeContinue:
                    raise

                except RaiseException:
                    raise
            
            return result
        finally:
            if hasattr(new_environment, "defers"):
                for defer_node in reversed(new_environment.defers):
                    self._evaluate(defer_node.body, environment)

    def _lambda_free_names(self, node: FunctionExpression) -> list:
        """Names referenced in the lambda body that are not params or inner locals."""
        from Parser.AST import Identifier, AssignmentStatement, ReassignmentStatement

        param_names = set()
        for p in (node.parameters or []):
            pname = p.get("name") if isinstance(p, dict) else getattr(p, "name", None)
            if pname:
                param_names.add(pname)

        local_names = set()
        visited_locals = set()

        def collect_locals(n):
            if n is None:
                return
            if id(n) in visited_locals:
                return
            visited_locals.add(id(n))
            if isinstance(n, list):
                for item in n:
                    collect_locals(item)
                return
            if isinstance(n, (AssignmentStatement, ReassignmentStatement)) or n.__class__.__name__ in (
                "AssignmentStatement",
                "ReassignmentStatement",
            ):
                nm = getattr(n, "name", None)
                if isinstance(nm, str):
                    local_names.add(nm)
                elif hasattr(nm, "name"):
                    local_names.add(nm.name)
            if n.__class__.__name__ == "FunctionExpression" or isinstance(n, FunctionExpression):
                return
            if hasattr(n, "__dict__"):
                for key, val in n.__dict__.items():
                    if not key.startswith("_"):
                        collect_locals(val)

        collect_locals(node.body)

        skip = param_names | local_names | {
            "self", "True", "False", "true", "false", "nothing", "Nothing",
            "Result", "Option", "Error",
        }
        free = []
        seen = set()
        visited_walk = set()

        def walk(n):
            if n is None:
                return
            if id(n) in visited_walk:
                return
            visited_walk.add(id(n))
            if isinstance(n, list):
                for item in n:
                    walk(item)
                return
            if isinstance(n, Identifier):
                name = n.name
                if name and name not in skip and name not in seen and not name.startswith("__"):
                    seen.add(name)
                    free.append(name)
                return
            if n.__class__.__name__ == "FunctionExpression" or isinstance(n, FunctionExpression):
                return
            if hasattr(n, "__dict__"):
                for key, val in n.__dict__.items():
                    if not key.startswith("_"):
                        walk(val)

        walk(node.body)
        return free

    def _evaluate_function_expression(
        self, node: FunctionExpression, environment: Environment
    ) -> FunctionObject:
        # Portable by-value capture: snapshot free outer locals at creation.
        # Matches the native backend (ZenClosureData caps).
        free = self._lambda_free_names(node)
        snap = Environment(parent=environment)
        for name in free:
            if environment.has(name):
                try:
                    snap.define(name, environment.get(name), True, None)
                except Exception:
                    pass

        function_object: FunctionObject = FunctionObject(
            name=node.name,
            parameters=node.parameters,
            body=node.body,
            closure=snap,
            return_type=getattr(node, "return_type", None),
        )

        return function_object

    def _evaluate_when_expression(
        self, node: WhenExpression, environment: Environment
    ) -> any:
        if self._evaluate(node.condition, environment):
            return self._evaluate(node.when_block, environment)

        for conditional in node.conditional_blocks or []:
            if self._evaluate(conditional["condition"], environment):
                return self._evaluate(conditional["block"], environment)

        if node.or_block:
            return self._evaluate(node.or_block, environment)

        return None

    def _evaluate_when_inline_expression(
        self, node: WhenInlineExpression, environment: Environment
    ) -> any:
        condition: any = self._evaluate(node.condition, environment)
        when_value: any = self._evaluate(node.when_value, environment)
        or_value: any = self._evaluate(node.or_value, environment)

        if condition:
            return when_value

        return or_value

    def _evaluate_structure_expression(
        self, node: StructureExpression, environment: Environment
    ) -> any:
        members: dict = {}

        for member in node.members:
            value: any = (
                self._evaluate(member.value, environment)
                if member.value
                else NothingLiteral()
            )
            members[member.name] = {
                "type": member.declared_type,
                "value": value,
                "mutable": member.mutable,
            }

        # Lookup the definition for parent + reflectable
        parent_obj = None
        reflectable = False
        try:
            definition = environment.get(node.name)
        except RuntimeError:
            definition = None
            if "<" in node.name and node.name.endswith(">"):
                base_name = node.name[:node.name.index("<")]
                try:
                    definition = environment.get(base_name)
                except RuntimeError:
                    definition = None
        if isinstance(definition, StructureObject):
            parent_obj = definition.parent
            reflectable = bool(getattr(definition, "reflectable", False))
            # Fill defaults from type template if missing
            for k, meta in (definition.members or {}).items():
                if k not in members:
                    members[k] = {
                        "type": meta.get("type"),
                        "value": meta.get("value"),
                        "mutable": meta.get("mutable", True),
                    }

        structure_object: StructureObject = StructureObject(
            name=node.name,
            members=members,
            closure=environment,
            parent=parent_obj,
            reflectable=reflectable,
        )

        return structure_object

    def _evaluate_member_expression(
        self, node: MemberExpression, environment: Environment
    ) -> any:
        # Evaluate the object (left side of the dot)
        object: any = self._evaluate(node.object, environment)
        member_name: str = getattr(node.property, "name", node.property)

        # --- 0. Universal Properties ---
        # `.kind` is type introspection unless the value itself stores a `kind` field
        # (maps/records used by term keys, ADTs, etc.).
        if member_name == "kind":
            if isinstance(object, BaseObject):
                if hasattr(object, "members") and isinstance(object.members, dict) and "kind" in object.members:
                     # Allow fallback to standard member access if 'kind' is a user-defined field
                     pass
                else:
                     return object.name
            elif isinstance(object, dict) and "kind" in object:
                # Prefer map key over type name so key events work in the interpreter
                pass
            elif isinstance(object, bool):
                return "Boolean"
            elif isinstance(object, int):
                return "Integer"
            elif isinstance(object, float):
                return "Decimal"
            elif isinstance(object, str):
                return "String"
            elif isinstance(object, list):
                return "List"
            elif isinstance(object, dict):
                return "Map"
            elif isinstance(object, set):
                return "Set"
            elif isinstance(object, tuple):
                return "Tuple"
            elif object is None:
                return "Nothing"
            elif isinstance(object, FunctionObject):
                return "Function"
            elif isinstance(object, TaskObject):
                return "Task"
            elif callable(object) and not isinstance(object, BaseObject):
                return "Function"
            else:
                return type(object).__name__

        if member_name == "members":
            if isinstance(object, BaseObject):
                if hasattr(object, "members") and isinstance(object.members, dict) and "members" in object.members:
                     # Allow fallback to standard member access if 'members' is a user-defined field
                     pass
                else:
                     # For InstanceObject, we might want to include methods from class too?
                     # For now, let's just return the data members.
                     return list(object.members.keys())
            elif isinstance(object, dict):
                return list(object.keys())
            else:
                return []

        if hasattr(object, "get_member") and not isinstance(object, BaseObject):
            return object.get_member(member_name)

        # --- 1. If it's a BaseObject (Structure, Class Instance, Module) ---
        if isinstance(object, BaseObject):
            # Use get_member to allow for inheritance / custom logic
            try:
                member_value = object.get_member(member_name)
            except RuntimeError:
                raise RuntimeError(
                    f"Object '{getattr(object, 'name', 'object')}' has no member '{member_name}'"
                )

            # If the member is a function/method, return a callable bound to this object
            if isinstance(member_value, tuple):
                 # It's (value, defining_class) from InstanceObject.get_member
                 value, defining_class = member_value
                 # Only bind if it's a FunctionObject
                 if isinstance(value, FunctionObject):
                      from Interpreter.Runtime import ParentProxy
                      instance_to_bind = object
                      if isinstance(object, ParentProxy):
                          instance_to_bind = object.instance
                      return self._bind_method(instance_to_bind, value, defining_class)
                 return value

            if isinstance(member_value, FunctionObject):
                from Interpreter.Runtime import ParentProxy
                instance_to_bind = object
                if isinstance(object, ParentProxy):
                    instance_to_bind = object.instance
                return self._bind_method(instance_to_bind, member_value, object)

            return member_value


        # --- 2. If it's a dictionary (Map) ---
        elif isinstance(object, dict):
            if member_name == "has":
                return lambda k: k in object
            elif member_name == "keys":
                return lambda: list(object.keys())
            elif member_name == "values":
                return lambda: list(object.values())
            elif member_name == "items":
                return lambda: [
                    {"key": k, "value": v} for k, v in object.items()
                ]
            elif member_name == "get":
                return lambda k, default=None: object.get(k, default)
            elif member_name == "merge":
                return lambda other: {**object, **(other if isinstance(other, dict) else {})}
            elif member_name == "invert":
                return lambda: {v: k for k, v in object.items()}
            elif member_name == "remove":
                def _remove(k):
                    if k in object:
                        del object[k]
                return _remove
            
            elif member_name in ["size", "length", "count", "len"] and member_name not in object:
                val = len(object)
                class CallableValue(type(val)):
                    def __call__(self, *args, **kwargs):
                        return self
                return CallableValue(val)
            
            if member_name not in object:
                raise RuntimeError(f"Object has no key '{member_name}'")

            return object[member_name]

        # --- 2.1 If it's a set ---
        elif isinstance(object, set):
            if member_name == "has":
                return lambda v: v in object
            elif member_name == "add":
                return object.add
            elif member_name == "remove":
                return object.remove
            elif member_name == "to_list":
                return lambda: list(object)
            elif member_name == "union":
                return lambda other: object.union(other if isinstance(other, set) else set(other))
            elif member_name == "intersection":
                return lambda other: object.intersection(other if isinstance(other, set) else set(other))
            elif member_name == "difference":
                return lambda other: object.difference(other if isinstance(other, set) else set(other))

        # --- 3. Collection Length Properties ---
        if isinstance(object, (list, set, dict, str, tuple, bytearray)) and member_name in ["size", "length", "count", "len"]:
            val = len(object)
            class CallableValue(type(val)):
                def __call__(self, *args, **kwargs):
                    return self
            return CallableValue(val)


        # --- 4. Special methods for other built-ins ---
        if isinstance(object, (list, tuple, bytearray)):
            if member_name == "append" and isinstance(object, list):
                return object.append
            elif member_name == "pop" and isinstance(object, list):
                return object.pop
            elif member_name == "at":
                return lambda idx: object[idx]
            elif member_name == "remove_at" and isinstance(object, list):
                return lambda idx: object.pop(idx)
            elif member_name == "slice":
                return lambda start, end=None: object[start:end] if end is not None else object[start:]
            elif member_name == "count":
                return lambda: len(object)
            elif member_name == "reverse" and isinstance(object, list):
                return lambda: list(reversed(object))
            elif member_name == "unique" and isinstance(object, list):
                return lambda: list(dict.fromkeys(object))
            elif member_name == "flatten" and isinstance(object, list):
                return lambda: [item for sub in object for item in (sub if isinstance(sub, list) else [sub])]
            elif member_name == "chunk" and isinstance(object, list):
                return lambda size: [object[i:i + (size if size > 0 else 1)] for i in range(0, len(object), (size if size > 0 else 1))]
            elif member_name == "take" and isinstance(object, list):
                return lambda n: object[:max(0, n)]
            elif member_name == "drop" and isinstance(object, list):
                return lambda n: object[max(0, n):]
            elif member_name == "contains" and isinstance(object, list):
                return lambda val: val in object
            elif member_name == "join" and isinstance(object, list):
                return lambda sep="": str(sep).join(str(x) for x in object)
            elif member_name == "map" and isinstance(object, list):
                def _map(fn):
                    return [self._call_function(fn, [x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(x) for x in object]
                return _map
            elif member_name == "filter" and isinstance(object, list):
                def _filter(fn):
                    return [x for x in object if (self._call_function(fn, [x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(x))]
                return _filter
            elif member_name == "reduce" and isinstance(object, list):
                def _reduce(initial, fn):
                    acc = initial
                    for x in object:
                        acc = self._call_function(fn, [acc, x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(acc, x)
                    return acc
                return _reduce
            elif member_name == "each" and isinstance(object, list):
                def _each(fn):
                    for x in object:
                        if isinstance(fn, (FunctionObject, BuiltinCapability)):
                            self._call_function(fn, [x])
                        else:
                            fn(x)
                    return None
                return _each
            elif member_name == "find" and isinstance(object, list):
                def _find(fn):
                    for x in object:
                        if (self._call_function(fn, [x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(x)):
                            return x
                    return None
                return _find
            elif member_name == "any" and isinstance(object, list):
                def _any(fn):
                    for x in object:
                        if (self._call_function(fn, [x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(x)):
                            return True
                    return False
                return _any
            elif member_name == "all" and isinstance(object, list):
                def _all(fn):
                    for x in object:
                        if not (self._call_function(fn, [x]) if isinstance(fn, (FunctionObject, BuiltinCapability)) else fn(x)):
                            return False
                    return True
                return _all

        if isinstance(object, str):
            if member_name == "substring":
                return lambda start, end=None: object[start:end] if end is not None else object[start:]
            elif member_name == "at":
                return lambda idx: object[idx]
            elif member_name == "split":
                return lambda sep: object.split(sep)
            elif member_name == "to_upper":
                return lambda: object.upper()
            elif member_name == "to_lower":
                return lambda: object.lower()
            elif member_name == "trim":
                return lambda: object.strip()
            elif member_name == "starts_with":
                return object.startswith
            elif member_name == "ends_with":
                return object.endswith
            elif member_name == "contains":
                return lambda s: s in object
            elif member_name == "to_number":
                return lambda: float(object) if "." in object else int(object)
            elif member_name == "to_integer":
                return lambda: int(object)
            elif member_name == "to_decimal":
                return lambda: float(object)
            elif member_name == "slice":
                return lambda start, end=None: object[start:end] if end is not None else object[start:]
            elif member_name == "replace":
                return lambda old, new: object.replace(old, new)
            elif member_name == "find":
                return lambda sub, start=0: object.find(sub, start)

        # --- 5. If it's a built-in Python object ---
        elif hasattr(object, member_name):
            val = getattr(object, member_name)
            from enum import Enum
            if isinstance(val, Enum):
                return val.name
            return val

        elif isinstance(object, (int, float)):
            if member_name in ["ms", "miliseconds"]:
                return object / 1000.0
            elif member_name in ["s", "seconds"]:
                return object
            elif member_name in ["m", "minutes"]:
                return object * 60.0
            elif member_name in ["h", "hours"]:
                return object * 3600.0
            elif member_name in ["d", "days"]:
                return object * 86400.0
            elif member_name == "times":
                 return object
            elif member_name == "to_decimal":
                return lambda: float(object)
            elif member_name == "to_integer":
                return lambda: int(object)
            elif member_name == "to_string":
                return lambda: str(object)
            raise RuntimeError(f"Number has no member '{member_name}'")

        if member_name == "has":
            return lambda k: False

        raise RuntimeError(
            f"Cannot access member '{member_name}' on type '{type(object).__name__}'"
        )
    
    def _bind_method(self, instance, method, defining_class):
        bound_function: FunctionObject = FunctionObject(
            name=method.name,
            parameters=method.parameters,
            body=method.body,
            closure=method.closure,
            return_type=method.return_type,
        )
        
        bound_env = Environment(parent=method.closure)
        bound_env.define("self", instance, mutable=False, type="instance")
        # Define the class where the method is defined to support 'parent'
        bound_env.define("__class__", defining_class, mutable=False, type="class")
        bound_function.closure = bound_env
        
        return bound_function

    def _evaluate_parent_expression(self, node, environment):
        if not environment.has("self"):
            raise RuntimeError("'parent' can only be used inside a class method")
        
        instance = environment.get("self")
        if not isinstance(instance, InstanceObject):
             raise RuntimeError("'parent' used in non-class context")
        
        if not environment.has("__class__"):
             raise RuntimeError("'parent' used in unknown class context")
        
        defining_class = environment.get("__class__")
        return ParentProxy(instance, defining_class)

    def _evaluate_identifier(self, node: Identifier, environment: Environment) -> any:
        name: str = node.name
        try:
            return environment.get(name)
        except RuntimeError:
            pass

        if "<" in name and name.endswith(">"):
            base_name = name[:name.index("<")]
            try:
                return environment.get(base_name)
            except RuntimeError:
                pass

        if environment.has("self"):
            self_object = environment.get("self")
            if hasattr(self_object, "members") and name in self_object.members:
                res = self_object.get_member(name)
                if isinstance(res, tuple):
                     return res[0]
                return res

        if getattr(self, "has_extern", False):
            import ctypes
            try:
                fn = getattr(ctypes.CDLL(None), name)
                def _c_wrap(*args):
                    c_args = []
                    for a in args:
                        if isinstance(a, str):
                            c_args.append(a.encode("utf-8"))
                        elif isinstance(a, bool):
                            c_args.append(int(a))
                        elif isinstance(a, float):
                            c_args.append(ctypes.c_double(a))
                        else:
                            c_args.append(a)
                    if name in ("sqrt", "pow", "sin", "cos", "tan", "exp", "log"):
                        fn.restype = ctypes.c_double
                    elif name in ("getenv", "strerror"):
                        fn.restype = ctypes.c_char_p
                    res = fn(*c_args)
                    if isinstance(res, bytes):
                        return res.decode("utf-8")
                    return res
                return _c_wrap
            except Exception:
                pass

        raise RuntimeError(f"Undefined variable '{name}'")

    def _evaluate_index_expression(
        self, node: IndexExpression, environment: Environment
    ) -> any:
        object_val: BaseObject | list | dict = self._evaluate(node.object, environment)
        index_val: any = self._evaluate(node.index, environment)

        # Check for valid index types based on object type
        if isinstance(object_val, (list, tuple, bytearray)) and not isinstance(index_val, int):
            raise RuntimeError(f"Index must be an integer for {type(object_val).__name__}, got {type(index_val).__name__}")
        if isinstance(object_val, BaseObject) and not isinstance(index_val, str):
             # Some BaseObjects might support integer indexing later, but for now they use string indexing
             pass

        if isinstance(object_val, (list, tuple, bytearray, str)):
            actual_idx = index_val
            if actual_idx < 0:
                actual_idx += len(object_val)
            if actual_idx < 0 or actual_idx >= len(object_val):
                 if getattr(self, "debugging", False):
                     print(f"DEBUG INTERPRETER INDEX OUT OF BOUNDS: object_val type={type(object_val)}, len={len(object_val)}, index_val={index_val}")
                 if isinstance(object_val, str):
                     print(f"  String value preview: {object_val[:200]!r}")
                 raise RuntimeError(f"Index out of bounds: {index_val}")
            return object_val[actual_idx]
        
        if isinstance(object_val, dict):
             if index_val not in object_val:
                  raise RuntimeError(f"Key error: {index_val}")
             return object_val[index_val]

    def _evaluate_slice_expression(
        self, node: SliceExpression, environment: Environment
    ) -> any:
        object_val = self._evaluate(node.object, environment)
        start_val = self._evaluate(node.start, environment) if node.start is not None else None
        end_val = self._evaluate(node.end, environment) if node.end is not None else None
        step_val = self._evaluate(node.step, environment) if node.step is not None else None

        if isinstance(object_val, (list, tuple, str, bytearray)):
            return object_val[slice(start_val, end_val, step_val)]
        raise RuntimeError(f"Cannot slice object of type {type(object_val)}")

        if isinstance(object_val, BaseObject) and isinstance(index_val, str):
            try:
                res = object_val.get_member(index_val)
                if isinstance(object_val, InstanceObject):
                    res, defining_class = res
                    if isinstance(res, FunctionObject):
                        from Interpreter.Runtime import ParentProxy
                        instance_to_bind = object_val
                        return lambda *args: self._call_function(res, args, instance_to_bind)
                return res
            except RuntimeError:
                raise RuntimeError(f"Object '{object_val.name}' has no member '{index_val}'")

        raise RuntimeError(f"Cannot index object of type {type(object_val)}")

    def _eval_cast(self, val: Any, target_type: str) -> Any:
        FORBIDDEN_TYPES = {
            "Int", "Int64", "Int32", "Int16", "Int8", "UInt8", "UInt16", "UInt32", "UInt64",
            "Float", "Float64", "Float32", "Double",
            "Str", "Bool", "Char", "Character", "Glyph", "Buffer",
            "V", "L", "S", "T", "M"
        }
        if target_type in FORBIDDEN_TYPES:
            raise RuntimeError(
                f"Type '{target_type}' is not supported in Zenlang. Use canonical types ('Integer', 'Decimal', 'String', 'Boolean', 'Byte', 'Rune')."
            )
        if target_type in ("Integer", "Integer[64]", "Integer[32]", "Integer[16]", "Integer[8]", "Byte") or (target_type.startswith("Integer[") and target_type.endswith("]")):
            n = 0
            if isinstance(val, int): n = val
            elif isinstance(val, float): n = int(val)
            elif isinstance(val, bool): n = 1 if val else 0
            elif val is None: n = 0
            elif isinstance(val, str):
                s = val.strip()
                if not s: n = 0
                elif len(s) == 1 and not s.isdigit(): n = ord(s[0])
                else:
                    try: n = int(s, 0)
                    except ValueError:
                        try: n = int(float(s))
                        except ValueError: n = 0
            elif isinstance(val, (list, dict, set)): n = len(val)
            else: n = 0

            if target_type in ("Byte", "Integer[8]"):
                u = n % 256
                if target_type == "Integer[8]":
                    return u - 256 if u >= 128 else u
                return u
            if target_type == "Integer[16]":
                u = n % 65536
                return u - 65536 if u >= 32768 else u
            if target_type == "Integer[32]":
                u = n % 4294967296
                return u - 4294967296 if u >= 2147483648 else u
            return n
        if target_type in ("Decimal", "Decimal[64]", "Decimal[32]") or (target_type.startswith("Decimal[") and target_type.endswith("]")):
            if isinstance(val, float): return val
            if isinstance(val, (int, bool)): return float(val)
            if val is None: return 0.0
            if isinstance(val, str):
                try: return float(val.strip())
                except ValueError: return 0.0
            return 0.0
        if target_type == "String" or (target_type.startswith("String[") and target_type.endswith("]")):
            if isinstance(val, str): s = val
            elif isinstance(val, bool): s = "True" if val else "False"
            elif val is None: s = ""
            elif isinstance(val, list):
                if val and all(isinstance(x, int) for x in val):
                    try: s = bytes(val).decode("utf-8", errors="replace")
                    except Exception: s = str(val)
                else: s = str(val)
            else: s = str(val)
            if target_type.startswith("String[") and target_type.endswith("]"):
                try:
                    max_len = int(target_type[7:-1])
                    if max_len >= 0 and len(s) > max_len:
                        s = s[:max_len]
                except ValueError:
                    pass
            return s
        if target_type == "Boolean":
            if isinstance(val, bool): return val
            if isinstance(val, (int, float)): return bool(val)
            if isinstance(val, str): return val in ("True", "true", "1")
            if isinstance(val, (list, dict, set)): return len(val) > 0
            if val is None: return False
            return True
        if target_type == "Rune":
            if isinstance(val, str): return val[0] if val else ""
            if isinstance(val, int):
                try: return chr(val)
                except Exception: return ""
            return ""
        if target_type == "Bytes":
            if isinstance(val, str): return list(val.encode("utf-8"))
            if isinstance(val, list): return val
            if isinstance(val, int): return [val]
            return []
        if target_type.startswith("List<") or target_type.startswith("List[") or target_type.startswith("Vector<") or target_type.startswith("Vector[") or target_type.startswith("Tuple<") or target_type.startswith("Tuple[") or target_type in ("List", "Vector", "Tuple"):
            if isinstance(val, list): return val
            if isinstance(val, (set, dict)): return list(val)
            if isinstance(val, str): return list(val)
            return [val]
        if target_type.startswith("Set<") or target_type.startswith("Set[") or target_type == "Set":
            if isinstance(val, list):
                return set(val)
            if isinstance(val, str): return set(val)
            return set([val])
        if target_type.startswith("Map<") or target_type.startswith("Map[") or target_type == "Map":
            if isinstance(val, dict): return val
            return {}
        if target_type == "Number":
            if isinstance(val, (int, float)) and not isinstance(val, bool): return val
            if isinstance(val, bool): return 1 if val else 0
            if isinstance(val, str):
                s = val.strip()
                if "." in s or "e" in s or "E" in s:
                    return self._eval_cast(val, "Decimal")
                return self._eval_cast(val, "Integer")
            return self._eval_cast(val, "Integer")
        if target_type == "Text":
            return self._eval_cast(val, "String")
        if target_type == "Collection":
            if isinstance(val, (list, tuple, set, dict)): return val
            return self._eval_cast(val, "List")
        if target_type == "Container":
            return val
        return val

    def _evaluate_call_expression(
        self, node: CallExpression, environment: Environment
    ) -> any:
        if isinstance(node.callee, IndexExpression) and isinstance(node.callee.object, Identifier) and node.callee.object.name in ("Integer", "Decimal", "String", "Vector"):
            idx_val = getattr(node.callee.index, "value", str(node.callee.index))
            type_name = f"{node.callee.object.name}[{idx_val}]"
            arguments = [self._evaluate(arg, environment) for arg in node.arguments]
            return self._eval_cast(arguments[0] if arguments else None, type_name)

        if isinstance(node.callee, Identifier):
            c_name = node.callee.name
            is_canonical_cast = (
                c_name in ("Integer", "String", "Decimal", "Boolean", "Rune", "Bytes", "Set", "List", "Map", "Byte", "Vector", "Tuple", "Number", "Text", "Collection", "Container")
                or c_name.startswith("Integer[") or c_name.startswith("Decimal[") or c_name.startswith("String[") or c_name.startswith("Vector[")
                or (("<" in c_name and c_name.endswith(">")) and c_name[:c_name.index("<")] in ("List", "Set", "Map", "Vector", "Tuple", "Option", "Result", "Task"))
            )
            if is_canonical_cast:
                arguments = [self._evaluate(arg, environment) for arg in node.arguments]
                return self._eval_cast(arguments[0] if arguments else None, c_name)

        callee: Any = self._evaluate(node.callee, environment)

        arguments: List[Any] = [
            self._evaluate(arg, environment) for arg in node.arguments
        ]

        if callable(callee) and not isinstance(callee, FunctionObject):
            try:
                return callee(*arguments)
            except IndexError:
                return None

        # Handle task calls
        if isinstance(callee, TaskObject):
            def run_task():
                return self._call_function(callee, arguments)
            return TaskHandleObject(run_task)

        if isinstance(callee, (FunctionObject, BuiltinCapability)):
            return self._call_function(callee, arguments)

        if isinstance(callee, ClassObject):
            # Instantiate Class
            instance_members = {}
            
            hierarchy = []
            curr = callee
            while curr:
                hierarchy.append(curr)
                curr = curr.parent
            hierarchy.reverse()

            for cls in hierarchy:
                for member_node in cls.members_ast:
                     value = self._evaluate(member_node.value, cls.closure)
                     instance_members[member_node.name] = {
                         "value": value,
                         "type": getattr(member_node, "declared_type", "Variant"),
                         "mutable": member_node.mutable
                     }
            
            instance = InstanceObject(callee, instance_members)
            
            init_result = instance._find_method_in_class("init", callee)
            if init_result[0]:
                 method, defining_class = init_result
                 bound_init = self._bind_method(instance, method, defining_class)
                 self._call_function(bound_init, arguments)
            elif len(arguments) > 0:
                 raise RuntimeError(f"Class '{callee.name}' has no 'init' method but received {len(arguments)} arguments")

            return instance

        # Structure type call: Point(…) or after StructureExpression path
        if isinstance(callee, StructureObject):
            # Instantiate Structure (Positional)
            new_members = {}
            member_names = list(callee.members.keys())
            
            if len(arguments) != len(member_names):
                raise RuntimeError(f"Structure '{callee.name}' expects {len(member_names)} arguments, got {len(arguments)}")
            
            for i, arg_val in enumerate(arguments):
                name = member_names[i]
                orig_member = callee.members[name]
                new_members[name] = {
                    "type": orig_member["type"],
                    "value": arg_val,
                    "mutable": orig_member["mutable"]
                }
            
            return StructureObject(
                callee.name,
                new_members,
                callee.closure,
                callee.parent,
                reflectable=bool(getattr(callee, "reflectable", False)),
            )

        raise RuntimeError(f"Attempted to call a non-function value: {callee}")

    def _call_function(self, function: FunctionObject, arguments: List[Any]) -> any:
        function_environment: Environment = Environment(parent=function.closure)

        if not function_environment.has("self"):
            function_environment.define("self", None, False, "structure_instance")

        for i, parameter in enumerate(function.parameters):
            name: str | None = (
                parameter.get("name")
                if isinstance(parameter, dict)
                else getattr(parameter, "name", None)
            )
            value: Any = arguments[i] if i < len(arguments) else None
            type: Any = parameter.get("type") if isinstance(parameter, dict) else None

            function_environment.define(name, value, True, type)

        try:
            return self._evaluate(function.body, function_environment)
        except ReturnException as return_exception:
            return return_exception.value

    def _evaluate_in_expression(self, node: InExpression, environment: Environment) -> any:
        # Placeholder
        return self._evaluate(node.expression, environment)

    def _evaluate_await_expression(self, node: AwaitExpression, environment: Environment) -> Any:
        handle = self._evaluate(node.expression, environment)
        if isinstance(handle, TaskHandleObject):
            return handle.await_result()
        return handle

    def _evaluate_is_expression(self, node: IsExpression, environment: Environment) -> bool:
        left_val = self._evaluate(node.left, environment)
        # Patterns can bind variables
        return self._bind_pattern(node.right, left_val, environment)

    def _evaluate_binary_operation_node(self, node: BinaryOperation, environment: Environment) -> any:
        left: any = self._evaluate(node.left, environment)
        op = getattr(node.operator, "value", node.operator)
        op_str = str(op)

        if op_str == "<:":
            target_type = getattr(node.right, "name", str(node.right))
            if hasattr(node.right, "bits") and node.right.bits:
                target_type = f"{target_type}[{node.right.bits}]"
            if hasattr(node.right, "subtypes") and node.right.subtypes:
                subs = [getattr(s, "name", str(s)) for s in node.right.subtypes]
                target_type = f"{target_type}<{', '.join(subs)}>"
            return self._eval_cast(left, target_type)

        if op_str == "??":
            if left is not None: return left
            return self._evaluate(node.right, environment)

        # Short-circuiting for logical AND / OR
        if op_str == "and":
            if not bool(left): return False
            right: any = self._evaluate(node.right, environment)
            return bool(right)
        if op_str == "or":
            if bool(left): return True
            right: any = self._evaluate(node.right, environment)
            return bool(right)

        right: any = self._evaluate(node.right, environment)
        return self._evaluate_binary_operation(op_str, left, right)

    def _evaluate_binary_operation(self, operation: str, left: Any, right: Any) -> any:
        if operation == "in":
            if isinstance(right, (list, tuple, set)):
                return left in right
            if isinstance(right, dict):
                return left in right
            if isinstance(right, str):
                return str(left) in right
            return False

        if operation == "++":
            if isinstance(left, list) and isinstance(right, list):
                return list(left) + list(right)
            if isinstance(left, list):
                return list(left) + [right]
            if isinstance(right, list):
                return [left] + list(right)
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right

        if operation == "--":
            if isinstance(left, str) and isinstance(right, int):
                n = int(right)
                if n <= 0: return left
                if n >= len(left): return ""
                return left[:-n]
            if isinstance(left, int) and isinstance(right, str):
                n = int(left)
                if n <= 0: return right
                if n >= len(right): return ""
                return right[n:]
            if isinstance(left, list) and isinstance(right, int):
                n = int(right)
                if n <= 0: return list(left)
                if n >= len(left): return []
                return list(left)[:-n]
            if isinstance(left, int) and isinstance(right, list):
                n = int(left)
                if n <= 0: return list(right)
                if n >= len(right): return []
                return list(right)[n:]
            return left - right

        if operation == "+":
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right

        if operation == "-":
            return left - right

        if operation == "*":
            return left * right

        if operation == "/":
            if right == 0:
                if isinstance(left, (int, float)):
                    if left > 0: return float('inf')
                    elif left < 0: return float('-inf')
                    else: return float('nan')
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right

        if operation == "%":
            return left % right

        if operation == "**":
            return left ** right

        if operation in ["==", "="]:
            from .LiteralHandler import DEFAULT_SENTINEL
            if left is DEFAULT_SENTINEL or right is DEFAULT_SENTINEL:
                target = right if left is DEFAULT_SENTINEL else left
                other = left if left is DEFAULT_SENTINEL else right
                if other is DEFAULT_SENTINEL and target is DEFAULT_SENTINEL:
                    return True
                return DEFAULT_SENTINEL == target
            return left == right

        if operation == "!=":
            from .LiteralHandler import DEFAULT_SENTINEL
            if left is DEFAULT_SENTINEL or right is DEFAULT_SENTINEL:
                target = right if left is DEFAULT_SENTINEL else left
                other = left if left is DEFAULT_SENTINEL else right
                if other is DEFAULT_SENTINEL and target is DEFAULT_SENTINEL:
                    return False
                return not (DEFAULT_SENTINEL == target)
            return left != right

        if operation == ">":
            return left > right

        if operation == "<":
            return left < right

        if operation == ">=":
            return left >= right

        if operation == "<=":
            return left <= right

        if operation == "and":
            return bool(left) and bool(right)

        if operation == "or":
            return bool(left) or bool(right)

        if operation in ["&&", "&"]:
            return int(left) & int(right)
        if operation in ["||", "|"]:
            return int(left) | int(right)
        if operation in ["^^", "^"]:
            return int(left) ^ int(right)
        if operation == "<<":
            return int(left) << int(right)
        if operation == ">>":
            return int(left) >> int(right)
        if operation == "%%":
            return int(left) % int(right)

        if operation == "xor":
            return bool(left) ^ bool(right)

        if operation == "nor":
            return not (bool(left) or bool(right))

        if operation == "nand":
            return not (bool(left) and bool(right))

        if operation == "xnor":
            return not (bool(left) ^ bool(right))

        if operation == "!&":
            return ~(left & right)

        if operation == "!|":
            return ~(left | right)

        if operation == "!^":
            return ~(left ^ right)

        if operation in ("..", "..+", "..-", "..."):
            def _range_ints(a: int, b: int, op: str):
                if a <= b:
                    start = a + 1 if op in ("..", "..+") else a
                    end = b + 1 if op in ("..+", "...") else b
                    return list(range(start, end))
                # descending
                start = a - 1 if op in ("..", "..+") else a
                end = b - 1 if op in ("..+", "...") else b
                return list(range(start, end, -1))

            # Integer ranges → List[Integer]
            if isinstance(left, int) and isinstance(right, int):
                return _range_ints(left, right, operation)

            # Single-character string / rune ranges → List[String]
            def _as_char(v):
                if isinstance(v, str) and len(v) == 1:
                    return v
                return None

            cl, cr = _as_char(left), _as_char(right)
            if cl is not None and cr is not None:
                return [chr(i) for i in _range_ints(ord(cl), ord(cr), operation)]

            raise RuntimeError(
                f"Range operator '{operation}' expects integers or single characters, got {type(left).__name__} and {type(right).__name__}"
            )

        raise RuntimeError(f"Unknown binary operator '{operation}'")

    def _evaluate_unary_operation_node(self, node: UnaryOperation, environment: Environment) -> any:
        op = getattr(node.operator, "value", node.operator)
        if op == "source":
            from Parser.AST import Identifier, MemberExpression, IndexExpression
            from Interpreter.Runtime import PointerObject
            if isinstance(node.right, Identifier):
                env = environment._find_env_containing(node.right.name) or environment
                return PointerObject(env, node.right.name, kind="variable")
            elif isinstance(node.right, MemberExpression):
                obj = self._evaluate(node.right.object, environment)
                return PointerObject(obj, node.right.property, kind="member")
            elif isinstance(node.right, IndexExpression):
                obj = self._evaluate(node.right.object, environment)
                idx = self._evaluate(node.right.index, environment)
                return PointerObject(obj, idx, kind="index")
            else:
                raise RuntimeError(f"Cannot take source of non-referenceable expression {node.right}")
                
        if op == "target":
            ptr = self._evaluate(node.right, environment)
            from Interpreter.Runtime import PointerObject
            if isinstance(ptr, PointerObject):
                return ptr.get_value()
            return ptr

        right: any = self._evaluate(node.right, environment)
        return self._evaluate_unary_operation(str(op), right)

    def _evaluate_unary_operation(self, operation: str, right: Any) -> any:
        if operation == "-":
            return -right

        if operation == "not":
             return not bool(right)

        if operation == "!!" or operation == "~":
            return ~right

        return right

    def _evaluate_check_expression(self, node: CheckExpression, environment: Environment) -> Any:
        try:
            return self._evaluate(node.expression, environment)
        except RaiseException as e:
            if hasattr(node, "or_value") and node.or_value:
                return self._evaluate(node.or_value, environment)
            if hasattr(node, "raise_expression") and node.raise_expression:
                raise_val = self._evaluate(node.raise_expression, environment)
                raise RaiseException(raise_val)
            raise e
