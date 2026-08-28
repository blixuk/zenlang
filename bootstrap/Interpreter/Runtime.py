from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


class Environment:
    def __init__(self, parent: Optional["Environment"] | None = None, file_path: Optional[str] = None) -> None:
        self.parent: Environment | None = parent
        self.values: Dict[str, Dict[str, Any]] = {}
        self.file_path: Optional[str] = file_path

    def define(
        self, name: str, value: Any, mutable: bool = True, type: Optional[str] = None
    ) -> None:
        if name in self.values:
            pass # raise RuntimeError(f"Variable '{name}' already defined in this scope")
        # if name == "Symbol" or name == "ZenTypeVariable" or name == "ZenSymbol":
        # print(f"DEBUG: Defining '{name}' of type '{type}' in environment {id(self)}")
        
        self.values[name] = {"value": value, "mutable": mutable, "type": type}

    def assign(self, name: str, value: Any) -> None:
        environment: Environment | None = self._find_env_containing(name)

        if not environment:
            raise RuntimeError(f"Undefined variable '{name}'")

        if not environment.values[name]["mutable"]:
            raise RuntimeError(f"Cannot assign to immutable variable '{name}'")

        environment.values[name]["value"] = value

    def has(self, name: str) -> bool:
        return self._find_env_containing(name) is not None

    def get(self, name: str) -> Any:
        environment: Environment | None = self._find_env_containing(name)

        if not environment:
            raise RuntimeError(f"Undefined variable '{name}'")

        return environment.values[name]["value"]

    def _find_env_containing(self, name: str) -> Optional["Environment"]:
        environment: Environment = self
        while environment is not None:
            if name in environment.values:
                return environment
            environment = environment.parent
        return None


@dataclass
class FunctionObject:
    name: Optional[str]
    parameters: List[dict]
    body: Any
    closure: Environment
    return_type: Optional[str] = None


@dataclass
class TaskObject:
    name: Optional[str]
    parameters: List[dict]
    body: Any
    closure: Environment
    return_type: Optional[str] = None


class TaskHandleObject:
    def __init__(self, task_func):
        import threading
        self.result = None
        self.exception = None
        self.completed = False
        self.lock = threading.Lock()
        self.event = threading.Event()
        
        def run_task():
            try:
                self.result = task_func()
            except Exception as e:
                self.exception = e
            finally:
                self.completed = True
                self.event.set()
        
        self.thread = threading.Thread(target=run_task)
        self.thread.start()

    def await_result(self):
        self.event.wait()
        if self.exception:
            raise self.exception
        return self.result


# @dataclass
# class StructureObject:
#     name: Optional[str]
#     members: List[dict]
#     closure: Environment


class BaseObject:
    def __init__(self, name, members, closure, parent=None):
        self.name = name
        self.members = members
        self.closure = closure
        self.parent = parent

    def get_member(self, name):
        pass

    def set_member(self, name, value):
        pass


class StructureObject(BaseObject):
    def __init__(self, name, members, closure, parent=None, reflectable: bool = False):
        super().__init__(name, members, closure, parent)
        self.reflectable = reflectable

    def field_names(self) -> list:
        return list(self.members.keys()) if isinstance(self.members, dict) else []

    def method_names(self) -> list:
        return []

    def get_member(self, name):
        if name == "classname":
            return self.name

        if name in self.members:
            return self.members[name]["value"]
        
        if self.parent:
            return self.parent.get_member(name)

        raise RuntimeError(f"Structure '{self.name}' has no member '{name}'")

    def set_member(self, name, value):
        if name not in self.members:
            raise RuntimeError(f"Structure '{self.name}' has no member '{name}'")

        if not self.members[name]["mutable"]:
            raise RuntimeError(
                f"Member '{name}' of structure '{self.name}' is immutable"
            )

        self.members[name]["value"] = value


class EnumeratorObject(BaseObject):
    def __init__(self, name, members, closure):
        super().__init__(name, members, closure)

    def get_member(self, name):
        if name not in self.members:
            raise RuntimeError(f"Enumerator '{self.name}' has no member '{name}'")

        return self.members[name]["value"]


@dataclass
class VariantObject:
    enum_name: str
    variant_name: str
    data: List[Any]

    def __repr__(self):
        if not self.data:
            return f"{self.enum_name}.{self.variant_name}"
        return f"{self.enum_name}.{self.variant_name}({', '.join(map(str, self.data))})"


class ModuleObject(BaseObject):
    def __init__(self, name: str, environment: Environment):
        self.name = name
        self.environment = environment
        self.closure = environment
        self.members = environment.values

    def get_member(self, name):
        if not self.environment.has(name):
            # print(f"DEBUG: Module '{self.name}' MISSING member '{name}'. Env keys: {list(self.environment.values.keys())}")
            raise RuntimeError(f"Module '{self.name}' has no member '{name}'")
        val = self.environment.get(name)
        # print(f"DEBUG: Module '{self.name}' get_member '{name}' -> {val}")
        return val

    def set_member(self, name, value):
        if not self.environment.has(name):
             raise RuntimeError(f"Module '{self.name}' has no member '{name}'")
        self.environment.assign(name, value)


class ClassObject(BaseObject):
    def __init__(
        self,
        name: str,
        parent: Optional["ClassObject"],
        members: list,
        methods: list,
        closure: Environment,
        reflectable: bool = False,
    ):
        super().__init__(name, members, closure, parent)
        self.members_ast = members # List of AssignmentStatement
        self.methods_ast = methods # List of FunctionStatement
        self.methods_map = {} # Cache for FunctionObjects
        self.reflectable = reflectable

    def field_names(self) -> list:
        names = []
        for m in self.members_ast or []:
            n = getattr(m, "name", None)
            if n:
                names.append(n)
        if self.parent and hasattr(self.parent, "field_names"):
            names = self.parent.field_names() + names
        return names

    def method_names(self) -> list:
        names = list(self.methods_map.keys())
        if self.parent and hasattr(self.parent, "method_names"):
            for n in self.parent.method_names():
                if n not in names:
                    names.append(n)
        return names

    def get_member(self, name):
        # Class objects can have methods (like init)
        # print(f"DEBUG: ClassObject({self.name}).get_member({name}). methods_map keys: {list(self.methods_map.keys())}")
        if name in self.methods_map:
            return self.methods_map[name]
        
        if self.parent:
            return self.parent.get_member(name)
            
        raise RuntimeError(f"Class '{self.name}' has no member '{name}'")

    def __repr__(self):
        return f"<Class {self.name}>"


class InstanceObject(BaseObject):
    def __init__(self, class_object: ClassObject, members: dict):
        super().__init__(class_object.name, members, class_object.closure)
        self.class_object = class_object

    def get_member(self, name):
        if name in self.members:
            return self.members[name]["value"], self.class_object
        
        # Look for method in class
        method, defining_class = self._find_method_in_class(name, self.class_object)
        if method:
            return method, defining_class
        
        raise RuntimeError(f"Instance of '{self.class_object.name}' has no member '{name}'")

    def set_member(self, name, value):
        if name in self.members:
             self.members[name]["value"] = value
             return
        
        raise RuntimeError(f"Instance of '{self.class_object.name}' has no member '{name}'")

    def _find_method_in_class(self, name: str, class_obj: ClassObject):
        # Check methods
        if name in class_obj.methods_map:
             return class_obj.methods_map[name], class_obj
        
        if class_obj.parent:
            return self._find_method_in_class(name, class_obj.parent)
            
        return None, None


class ParentProxy(BaseObject):
    def __init__(self, instance: InstanceObject, start_class: ClassObject):
        self.instance = instance
        self.start_class = start_class
        self.name = f"parent({instance.class_object.name})"
        self.closure = instance.closure

    def get_member(self, name):
        # Look for method starting from parent of start_class
        if not self.start_class.parent:
             raise RuntimeError(f"Class '{self.start_class.name}' has no parent to access member '{name}'")
        
        method, defining_class = self.instance._find_method_in_class(name, self.start_class.parent)
        if method:
            return method, defining_class
        
        raise RuntimeError(f"Parent of '{self.start_class.name}' has no member '{name}'")


class BuiltinCapability(BaseObject):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        self.name = name
        self.handlers = handlers
        self.closure = None # Builtin objects have no closure

    def get_member(self, name):
        if name in self.handlers:
            return self.handlers[name]
        raise RuntimeError(f"Capability '{self.name}' has no member '{name}'")

    def set_member(self, name, value):
        raise RuntimeError(f"Cannot set member on builtin object '{self.name}'")


class OutputStream(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class InputStream(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class StringCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class FileCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class SysCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class MemoryCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class MemoryArenaObject(BuiltinCapability):
    def __init__(self, name: str, size: int):
        self.size = size
        self.data = bytearray(size)
        self.cursor = 0
        
        super().__init__(name, {
            "size": lambda: self.size,
            "cursor": lambda: self.cursor,
            "reset": self.reset,
            "read_byte": self.read_byte,
            "write_byte": self.write_byte,
            "read_word": self.read_word,
            "write_word": self.write_word,
        })

    def reset(self):
        self.cursor = 0
        for i in range(len(self.data)):
            self.data[i] = 0

    def read_byte(self, offset):
        return self.data[offset]

    def write_byte(self, offset, value):
        self.data[offset] = value & 0xFF

    def read_word(self, offset):
        # 32-bit little endian
        return int.from_bytes(self.data[offset:offset+4], "little")

    def write_word(self, offset, value):
        self.data[offset:offset+4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


class MemoryManager:
    def __init__(self):
        self.arenas = {}
        self.arena_stack = []
        self.next_id = 1

    def create_arena(self, size):
        arena_id = self.next_id
        self.next_id += 1
        arena = MemoryArenaObject(f"Arena#{arena_id}", size)
        self.arenas[arena_id] = arena
        return arena

    def free_arena(self, arena):
        # In this simple model, we just remove it
        pass

    def push_arena(self, arena):
        self.arena_stack.append(arena)

    def pop_arena(self):
        if self.arena_stack:
            return self.arena_stack.pop()
        return None

    def get_current_arena(self):
        if self.arena_stack:
            return self.arena_stack[-1]
        return None



class TimeCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class ProcessCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class MapCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class SetCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class TermCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class RandomCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class NetCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class CryptoCapability(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class ProcessInstance(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class FileInstance(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class SocketInstance(BuiltinCapability):
    def __init__(self, name: str, handlers: Dict[str, callable]):
        super().__init__(name, handlers)


class PointerObject(BaseObject):
    def __init__(self, container: Any, key: Any, kind: str = "variable"):
        # kind can be "variable", "member", "index"
        super().__init__("Pointer", {}, None)
        self.container = container
        self.key = key
        self.kind = kind

    def get_value(self) -> Any:
        if self.kind == "variable":
            return self.container.get(self.key)
        elif self.kind == "member":
            res = self.container.get_member(self.key)
            if isinstance(res, tuple):
                return res[0]
            return res
        elif self.kind == "index":
            return self.container[self.key]
        return None

    def set_value(self, value: Any):
        if self.kind == "variable":
            self.container.assign(self.key, value)
        elif self.kind == "member":
            self.container.set_member(self.key, value)
        elif self.kind == "index":
            self.container[self.key] = value

    def __repr__(self):
        return f"<Pointer to {self.kind} '{self.key}'>"
