from dataclasses import dataclass
from typing import Any, List, Optional
import os
import sys
sys.setrecursionlimit(1000000)

from Lexer.Lexer import Lexer
from Parser.Parser import Parser

from Interpreter.Runtime import (
    BaseObject,
    EnumeratorObject,
    Environment,
    FunctionObject,
    StructureObject,
    ModuleObject,
    ClassObject,
    InstanceObject,
    ParentProxy,
    OutputStream,
    InputStream,
    StringCapability,
    FileCapability,
    SysCapability,
    MemoryCapability,
    TimeCapability,
    ProcessCapability,
    MapCapability,
    SetCapability,
    TermCapability,
    RandomCapability,
    VariantObject,
    ProcessInstance,
    FileInstance,
    BuiltinCapability,
)
from Parser.AST import (
    AssignmentStatement,
    ASTNode,
    BlockExpression,
    BlockStatement,
    CallExpression,
    ClassStatement,
    DoStatement,
    ElementLiteral,
    EnumeratorStatement,
    EnumVariant,
    FunctionExpression,
    FunctionStatement,
    FromImportStatement,
    Identifier,
    ImportStatement,
    IndexExpression,
    IndexReassignmentStatement,
    IntegerLiteral,
    IteratorLiteral,
    ListLiteral,
    MemberExpression,
    MemberReassignmentStatement,
    ParentExpression,
    ReassignmentStatement,
    ReturnStatement,
    RuneLiteral,
    StringLiteral,
    StructureStatement,
    StructureExpression,
    ScopeStatement,
    WhenExpression,
    WhenInlineExpression,
    WhenStatement,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    CheckExpression,
    ObjectStatement,
    NothingLiteral,
    BooleanLiteral,
    SetLiteral,
    VectorLiteral,
    MapLiteral,
    TupleLiteral,
    ExportStatement,
    WithStatement,
    InExpression,
    LiteralPattern,
    IdentifierPattern,
    ListPattern,
    MapPattern,
    VariantPattern,
    WildcardPattern,
    IsMatchPattern,
    Pattern,
    CaseBranch,
    IsExpression,
)


@dataclass
class ReturnException(Exception):
    value: Any


@dataclass
class RaiseException(Exception):
    value: Any
    with_value: Optional[Any] = None


class RuntimeBreak(Exception):
    pass


class RuntimeContinue(Exception):
    pass


class Interpreter:
    def __init__(
        self, AST: ASTNode, source_path: str, strict: bool = False, debug: bool = False, resolver = None
    ) -> None:
        self.debugging: bool = debug
        self.strict: bool = strict

        self.source_path: str = source_path
        self.AST: ASTNode = AST
        self.resolver = resolver

        self.execution_arguments: list = []
        self.global_environment: Environment = Environment(file_path=source_path)
        self.depth: int = 0
        self.modules: dict[str, any] = {} # path -> ModuleObject
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.global_environment.define("nothing", None, mutable=False, type="Void")
        def _input_read(prompt=""):
            try:
                return input(prompt)
            except EOFError:
                return ""
 
        in_obj = InputStream("in", {
            "read": _input_read
        })
 
        self.global_environment.define(
            "__builtin_input", in_obj, mutable=False, type="InputStream"
        )
 
        # Register 'out' capability
        def _out_write(value, data=None):
            if data and isinstance(data, dict):
                # Simple interpolation for structured output
                for k, v in data.items():
                    value = str(value).replace(f"{{{k}}}", str(v))
            print(value, end="", flush=True)
            return None
 
        def _out_info(value):
            print(f"\033[34m[INFO]\033[0m {value}")
            return None
 
        def _out_warn(value):
            print(f"\033[33m[WARN]\033[0m {value}")
            return None
 
        def _out_error(value):
            import sys
            print(f"\033[31m[ERROR]\033[0m {value}", file=sys.stderr)
            return None
 
        def _out_debug(value):
            if self.debugging:
                print(f"\033[36m[DEBUG]\033[0m {value}")
            return None

        out_obj = OutputStream("out", {
            "write": _out_write,
            "info": _out_info,
            "warn": _out_warn,
            "error": _out_error,
            "debug": _out_debug
        })

        self.global_environment.define(
            "__builtin_output", out_obj, mutable=False, type="OutputStream"
        )

        # Register '__builtin' object
        def _builtin_error(msg):
            raise RaiseException(msg)
            
        builtin_obj = BuiltinCapability("__builtin", {
            "error": _builtin_error,
            "error_literal": lambda msg: {"__type__": "Error", "message": msg},
            "range": lambda start, end: list(range(start, end)),
        })
        self.global_environment.define("__builtin", builtin_obj, mutable=False, type="BuiltinCapability")
 
        self.global_environment.define("__builtin_output", out_obj, mutable=False, type="OutputStream")
        
 
        # Register 'string' capability
        string_obj = StringCapability("string", {
            "split": lambda s, sep: s.split(sep),
            "join": lambda parts, sep: sep.join(parts),
            "trim": lambda s: s.strip(),
            "substring": lambda s, start, end=None: s[start:end] if end is not None else s[start:],
            "starts_with": lambda s, prefix: s.startswith(prefix),
            "ends_with": lambda s, suffix: s.endswith(suffix),
            "replace": lambda s, old, new: s.replace(old, new),
            "length": lambda s: len(s),
            "to_lower": lambda s: s.lower(),
            "to_upper": lambda s: s.upper(),
            "index_of": lambda s, sub: s.find(sub),
            "at": lambda s, i: s[i] if 0 <= i < len(s) else "",
            "to_string": lambda x: str(x),
            "to_number": lambda s: float(s) if '.' in s else int(s),
        })
 
        self.global_environment.define("__builtin_string", string_obj, mutable=False, type="StringCapability")

        # Register 'memory' capability
        memory_obj = MemoryCapability("memory", {
            "create_arena": lambda size: None,
            "free_arena": lambda a: None,
            "reset_arena": lambda a: None,
            "push_arena": lambda a: None,
            "pop_arena": lambda: None,
        })
        self.global_environment.define("__builtin_memory", memory_obj, mutable=False, type="MemoryCapability")
        self.global_environment.define("string", string_obj, mutable=False, type="StringCapability")
 
        # Register 'file' capability
        def read_file(path):
            with open(path, 'r') as f:
                return f.read()
 
        def write_file(path, content, mode='w'):
            with open(path, mode) as f:
                f.write(content)
                return True
 
        class FileInstanceObject(FileInstance):
            def __init__(self, path, mode):
                self.handle = open(path, mode)
                super().__init__("File", {
                    "read": lambda: self.handle.read(),
                    "write": lambda v: self.handle.write(v),
                    "close": lambda: self.handle.close(),
                })

        def append_file(path, content):
            with open(path, 'a') as f:
                f.write(content)
                return True
 
        file_obj = FileCapability("file", {
            "open": lambda path, mode="r": FileInstanceObject(path, mode),
            "read": read_file,
            "write": write_file,
            "append": lambda path, content: write_file(path, content, 'a'),
            "exists": lambda path: os.path.exists(path),
            "remove": lambda path: os.remove(path) if os.path.exists(path) else None,
            "is_file": lambda path: os.path.isfile(path),
            "is_dir": lambda path: os.path.isdir(path),
        })
 
        self.global_environment.define("__builtin_file", file_obj, mutable=False, type="FileCapability")
        self.global_environment.define("file", file_obj, mutable=False, type="FileCapability")
 
        # Register 'sys' capability
        sys_obj = SysCapability("sys", {
            "get_args": lambda: self.execution_arguments,
            "exit": lambda code=0: os._exit(code),
            "get_env": lambda key: os.environ.get(key, ""),
            "get_cwd": lambda: os.getcwd(),
            "platform": lambda: sys.platform,
            "version": lambda: "0.1.0-bootstrap",
        })
 
        self.global_environment.define("__builtin_sys", sys_obj, mutable=False, type="SysCapability")
        self.global_environment.define("sys", sys_obj, mutable=False, type="SysCapability")

        # Register 'time' capability
        import time
        time_obj = TimeCapability("time", {
            "now": lambda: time.time(),
            "monotonic": lambda: time.monotonic(),
            "wallclock": lambda: time.time(),
            "sleep": lambda s: time.sleep(s),
        })
        self.global_environment.define("__builtin_time", time_obj, mutable=False, type="TimeCapability")
        self.global_environment.define("time", time_obj, mutable=False, type="TimeCapability")

        # Register 'process' capability
        import subprocess
        
        class ProcessInstanceObject(ProcessInstance):
            def __init__(self, cmd, args):
                self.proc = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                super().__init__("Process", {
                    "wait": lambda: self.proc.wait(),
                    "get_stdout": lambda: self.proc.stdout.read(),
                    "get_stderr": lambda: self.proc.stderr.read(),
                    "get_code": lambda: self.proc.returncode,
                    "kill": lambda: self.proc.kill(),
                })

        process_obj = ProcessCapability("process", {
            "spawn": lambda cmd, args=[]: ProcessInstanceObject(cmd, args),
            "run": lambda cmd, args=[]: subprocess.check_output([cmd] + args, text=True),
            "get_id": lambda: os.getpid(),
        })
        self.global_environment.define("__builtin_process", process_obj, mutable=False, type="ProcessCapability")
        self.global_environment.define("process", process_obj, mutable=False, type="ProcessCapability")

        # Register 'math' capability
        import math
        math_obj = BuiltinCapability("math", {
            "abs": lambda x: abs(x),
            "sqrt": lambda x: math.sqrt(x),
            "pow": lambda x, y: math.pow(x, y),
            "sin": lambda x: math.sin(x),
            "cos": lambda x: math.cos(x),
            "floor": lambda x: math.floor(x),
            "ceil": lambda x: math.ceil(x),
            "pi": math.pi,
            "e": math.e,
        })
        self.global_environment.define("__builtin_math", math_obj, mutable=False, type="MathCapability")

        # Register 'dictionary' capability
        map_obj = MapCapability("map", {
            "keys": lambda d: list(d.keys()),
            "values": lambda d: list(d.values()),
            "has": lambda d, k: k in d,
        })
        self.global_environment.define("__builtin_map", map_obj, mutable=False, type="MapCapability")

        # Register 'term' capability
        def _term_color(fg=None, bg=None):
            colors = {
                "black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4, "magenta": 5, "cyan": 6, "white": 7
            }
            code = ""
            if fg in colors:
                code += f"\033[3{colors[fg]}m"
            if bg in colors:
                code += f"\033[4{colors[bg]}m"
            if code:
                print(code, end="")
            return None

        def _term_size():
            import os
            try:
                size = os.get_terminal_size()
                return {"width": size.columns, "height": size.lines}
            except:
                return {"width": 80, "height": 24}

        term_obj = TermCapability("term", {
            "clear": lambda: print("\033[2J\033[H", end=""),
            "move": lambda x, y: print(f"\033[{y};{x}H", end=""),
            "color": _term_color,
            "reset": lambda: print("\033[0m", end=""),
            "get_size": _term_size,
        })
        self.global_environment.define("__builtin_term", term_obj, mutable=False, type="TermCapability")

        # Register 'set' capability
        set_obj = SetCapability("set", {
            "from_list": lambda l: set(l),
            "to_list": lambda s: list(s),
            "add": lambda s, v: s.add(v),
            "has": lambda s, v: v in s,
        })
        self.global_environment.define("__builtin_set", set_obj, mutable=False, type="SetCapability")

        # Register 'json' capability
        import json
        json_obj = SysCapability("json", {
            "parse": lambda s: json.loads(s),
            "stringify": lambda v: json.dumps(v),
        })
        self.global_environment.define("__builtin_json", json_obj, mutable=False, type="JSONCapability")
        self.global_environment.define("json", json_obj, mutable=False, type="JSONCapability")

        # Register 'random' capability
        import random as py_random
        
        class RNGObject(BuiltinCapability):
            def __init__(self, seed_val):
                self.rng = py_random.Random(seed_val)
                super().__init__("RNG", {
                    "next": lambda: self.rng.random(),
                    "integer": lambda min_val, max_val: self.rng.randint(min_val, max_val),
                    "decimal": lambda min_val, max_val: self.rng.uniform(min_val, max_val),
                    "range": lambda min_val, max_val: self.rng.randint(min_val, max_val) if isinstance(min_val, int) and isinstance(max_val, int) else self.rng.uniform(min_val, max_val),
                })
        
        random_obj = RandomCapability("random", {
            "seed": lambda s: RNGObject(s),
            "integer": lambda min_val, max_val: py_random.randint(min_val, max_val),
            "decimal": lambda min_val, max_val: py_random.uniform(min_val, max_val),
            "range": lambda min_val, max_val: py_random.randint(min_val, max_val) if isinstance(min_val, int) and isinstance(max_val, int) else py_random.uniform(min_val, max_val),
        })
        self.global_environment.define("__builtin_random", random_obj, mutable=False, type="RandomCapability")

    def interpret(
        self,
        program: ASTNode | None = None,
        environment: Environment | None = None,
        arguments: list = [],
    ) -> any:
        print(f"DEBUG: Interpreter starting with {len(arguments)} arguments")
        self.execution_arguments = arguments
        try:
            if program is None:
                program = self.AST

            if environment is None:
                environment = self.global_environment

            return self._evaluate_program(program, environment, arguments)

        except ReturnException as return_exception:
            return f"Return value: '{return_exception.value}'"

    def evaluate_program(
        self,
        program: ASTNode,
        environment: Environment | None = None,
        arguments: list = [],
    ) -> any:
        if environment is None:
            environment = self.environment

        self._evaluate_program(program, environment, arguments)

    def _evaluate_program(
        self, program: ASTNode, environment: Environment, arguments: list = []
    ) -> any:
        result = None
        entry_point: str | None = (
            program.entry_point if hasattr(program, "entry_point") else None
        )
        definitions: tuple = (
            FunctionStatement,
            ClassStatement,
            ImportStatement,
            FromImportStatement,
            StructureStatement,
            ObjectStatement,
            EnumeratorStatement,
            ScopeStatement,
            AssignmentStatement,
            ExportStatement,
        )

        # Pass 1: Register all definitions
        # print(f"DEBUG: Definitions tuple: {definitions}")
        for statement in program.statements:
            # print(f"DEBUG: Inspecting statement {type(statement).__name__}")
            if isinstance(statement, definitions):
                # print(f"DEBUG: Defining {statement.__class__.__name__} in {environment.file_path}")
                self._evaluate(statement, environment)
            else:
                # print(f"DEBUG: Ignoring {statement.__class__.__name__} in Pass 1 in {environment.file_path}")
                pass

        # Pass 2: Execute entry point or fall back to sequential
        if entry_point:
            main_function: FunctionObject | None = environment.get(entry_point)
            input_arguments: list = [self.source_path]
            input_arguments.extend(arguments)
            main_arguments: list = [input_arguments]

            if not main_function:
                # Fall back to sequential if main not found
                for statement in program.statements:
                    if not isinstance(statement, definitions):
                        result = self._evaluate(statement, environment)
            else:
                result = self._call_function(main_function, main_arguments)
        else:
            for statement in program.statements:
                if isinstance(statement, definitions):
                    continue  # already registered
                elif isinstance(statement, ReturnStatement):
                    result = self._evaluate(statement, environment)
                    break
                else:
                    # print(f"DEBUG: Executing {statement.__class__.__name__}")
                    result = self._evaluate(statement, environment)

        return result

    def evaluate_repl(
        self, program: ASTNode, environment: Environment, arguments: list = []
    ) -> any:
        result = None

        for statement in program.statements:
            if isinstance(statement, ReturnStatement):
                result = self._evaluate(statement, environment)
                break
            else:
                result = self._evaluate(statement, environment)

        return result

    # def _evaluate_program(self, program: Program, environment: Environment) -> any:
    #     result: any = None

    #     if program.entry_point:
    #             for statement in program.statements:
    #                 if isinstance(statement, ExpressionStatement) and isinstance(statement.expression, CallExpression):
    #                     if statement.expression.callee.name == program.entry_point:
    #                         result = self._evaluate(statement, environment)
    #                         break
    #                     else:
    #                         continue
    #                 else:
    #                     result: any = self._evaluate(statement, environment)
    #     else:
    #         for statement in program.statements:
    #             if isinstance(statement, ReturnStatement):
    #                 result = self._evaluate(statement, environment)
    #                 break
    #             else:
    #                 result: any = self._evaluate(statement, environment)

    #     return result

    def evaluate(self, node: ASTNode, environment: Environment = None) -> any:
        if environment is None:
            environment = self.global_environment

        return self._evaluate(node, environment)

    def _evaluate(self, node: Any, environment: Environment) -> any:
        self.depth += 1
        
        node_type: str = type(node).__name__
        
        # Guard against extreme recursion
        if self.depth > 1000000:
             raise RuntimeError(f"Interpreter: Maximum recursion depth exceeded (depth={self.depth}, node={node_type})")

        try:
            return self._evaluate_node(node, node_type, environment)
        finally:
            self.depth -= 1

    def _evaluate_node(self, node: ASTNode, node_type: str, environment: Environment) -> any:
        if node is None:
            return None

        node_type: str = getattr(node, "node_type", None) or node.__class__.__name__

        # Statements

        if node_type == "AssignmentStatement":
            return self._evaluate_assignment_statement(node, environment)

        if node_type == "ReassignmentStatement":
            return self._evaluate_reassignment_statement(node, environment)

        if node_type == "MemberReassignmentStatement":
            return self._evaluate_member_reassignment_statement(node, environment)

        if node_type == "IndexReassignmentStatement":
            return self._evaluate_index_reassignment_statement(node, environment)

        if node_type == "ExpressionStatement":
            return self._evaluate(node.expression, environment)

        if node_type == "BlockStatement":
            return self._evaluate_block_statement(node, environment)

        if node_type == "FunctionStatement":
            return self._evaluate_function_statement(node, environment)

        if node_type == "StructureStatement":
            return self._evaluate_structure_statement(node, environment)

        if node_type == "ClassStatement":
            return self._evaluate_class_statement(node, environment)

        if node_type == "EnumeratorStatement":
            return self._evaluate_enumerator_statement(node, environment)

        if node_type == "ScopeStatement":
            return self._evaluate_scope_statement(node, environment)

        if node_type == "ImportStatement":
            return self._evaluate_import_statement(node, environment)

        if node_type == "FromImportStatement":
            return self._evaluate_from_import_statement(node, environment)

        if node_type == "ReturnStatement":
            return self._evaluate_return_statement(node, environment)

        if node_type == "WhenStatement":
            return self._evaluate_when_statement(node, environment)

        if node_type == "DoStatement":
            return self._evaluate_do_statement(node, environment)

        if node_type == "DeferStatement":
            return self._evaluate_defer_statement(node, environment)

        if node_type == "RaiseStatement":
            return self._evaluate_raise_statement(node, environment)

        if node_type == "AssertStatement":
            return self._evaluate_assert_statement(node, environment)

        if node_type == "CheckStatement":
            return self._evaluate_check_statement(node, environment)

        if node_type == "ObjectStatement":
            return self._evaluate_object_statement(node, environment)

        if node_type == "ExportStatement":
            return self._evaluate_export_statement(node, environment)

        if node_type == "WithStatement":
            return self._evaluate_with_statement(node, environment)

        if node_type == "BreakStatement":
             # print("DEBUG [Interpreter]: Executing break statement")
             raise RuntimeBreak()
        
        if node_type == "ContinueStatement":
             raise RuntimeContinue()

        # Expressions

        if node_type == "BlockExpression":
            return self._evaluate_block_expression(node, environment)

        if node_type == "FunctionExpression":
            return self._evaluate_function_expression(node, environment)

        if node_type == "WhenExpression":
            return self._evaluate_when_expression(node, environment)

        if node_type == "WhenInlineExpression":
            return self._evaluate_when_inline_expression(node, environment)

        if node_type == "CheckExpression":
            return self._evaluate_check_expression(node, environment)

        if node_type == "CallExpression":
            return self._evaluate_call_expression(node, environment)

        if node_type == "StructureExpression":
            return self._evaluate_structure_expression(node, environment)

        if node_type == "MemberExpression":
            return self._evaluate_member_expression(node, environment)

        if node_type == "IndexExpression":
            return self._evaluate_index_expression(node, environment)

        if node_type == "ParentExpression":
            return self._evaluate_parent_expression(node, environment)

        if node_type == "InExpression":
            return self._evaluate_in_expression(node, environment)

        if node_type == "IsExpression":
            return self._evaluate_is_expression(node, environment)

        # Operations
        if node_type == "BinaryOperation":
            left: any = self._evaluate(node.left, environment)
            op = getattr(node.operator, "value", node.operator)
            op_str = str(op)

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

        if node_type == "UnaryOperation":
            right: any = self._evaluate(node.right, environment)
            op = getattr(node.operator, "value", node.operator)
            return self._evaluate_unary_operation(str(op), right)

        # Literals

        if node_type == "IntegerLiteral":
            return getattr(node, "value")

        if node_type == "DecimalLiteral":
            return getattr(node, "value")

        if node_type == "StringLiteral":
            return getattr(node, "value")

        if node_type == "RuneLiteral":
            return getattr(node, "value")

        if node_type == "BooleanLiteral":
            val = getattr(node, "value")
            if val in ["true", "True"]:
                return True
            if val in ["false", "False"]:
                return False
            return val

        if node_type == "ListLiteral":
            return self._evaluate_list_literal(node, environment)

        if node_type == "VectorLiteral":
            return self._evaluate_vector_literal(node, environment)

        if node_type == "MapLiteral":
            return self._evaluate_map_literal(node, environment)

        if node_type == "SetLiteral":
            return self._evaluate_set_literal(node, environment)

        if node_type == "TupleLiteral":
            return self._evaluate_tuple_literal(node, environment)

        if node_type == "Identifier":
            return self._evaluate_identifier(node, environment)

        # Literals
        if node_type == "VoidLiteral":
            return node.value

        if node_type == "NothingLiteral":
            return None

        if node_type == "IntegerLiteral":
            return int(node.value)

        if node_type == "DecimalLiteral":
            return float(node.value)

        if node_type == "RuneLiteral":
            return str(node.value)

        if node_type == "StringLiteral":
            return str(node.value)

        if node_type == "BooleanLiteral":
            return node.value == "true" or node.value is True

        if node_type == "VariantLiteral":
            return node.value

        if node_type == "ElementLiteral":
            return self._evaluate_element_literal(node, environment)

        if node_type == "ListLiteral":
            return self._evaluate_list_literal(node, environment)

        # TODO: MemberExpression, IndexExpression, StructureExpression, others...

        raise NotImplementedError(
            f"Interpreter: node type not implemented: {node_type}"
        )

    ## Statement handlers

    def _evaluate_import_statement(self, node: ImportStatement, environment: Environment) -> any:
        module_object = self._load_module(node.path, node.name, caller_path=environment.file_path)
        environment.define(node.name, module_object, False, "module")
        return module_object

    def _evaluate_from_import_statement(self, node: FromImportStatement, environment: Environment) -> any:
        module_object = self._load_module(node.path, node.path, caller_path=environment.file_path)
        
        for symbol_info in node.symbols:
            name = symbol_info["name"]
            alias = symbol_info.get("alias") or name
            
            try:
                value = module_object.get_member(name)
            except RuntimeError:
                 raise RuntimeError(f"Module '{node.path}' has no member '{name}'")
            
            environment.define(alias, value, False, "imported_symbol")
        
        return None

    def _load_module(self, path: str, alias: str, caller_path: str | None = None) -> ModuleObject:
        if "." in path and os.sep not in path and not path.startswith("."):
            path = path.replace(".", os.sep)

        # 1. Resolve Path
        if self.resolver:
            try:
                full_path = self.resolver.resolve(path, os.path.dirname(caller_path or self.source_path))
            except FileNotFoundError:
                full_path = path # Fallback
        else:
            full_path = path

        if not os.path.isabs(full_path):
            current_dir = os.path.dirname(caller_path or self.source_path)
            full_path = os.path.abspath(os.path.join(current_dir, full_path))

        # print(f"DEBUG: Loading module from {full_path}")
        if not os.path.exists(full_path) and os.path.exists(full_path + ".zl"):
            full_path += ".zl"
        
        # 1.5 Check Cache
        if full_path in self.modules:
            if self.debugging:
                print(f"DEBUG [Interpreter]: Returning cached module for {full_path}")
            return self.modules[full_path]
        
        print(f"DEBUG [Interpreter]: Loading module from {full_path}")
        
        if not os.path.exists(full_path):
             raise RuntimeError(f"Module not found: {path} (checked {full_path}) Caller: {caller_path} CurrentDir: {current_dir} Full: {os.path.abspath(full_path)}")

        # 2. Read Source
        try:
            with open(full_path, "r") as f:
                source = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read module {path}: {e}")

        # 3. Compile
        lexer = Lexer(source, source_path=full_path)
        tokens = lexer.tokenize()
        parser = Parser(tokens, full_path)
        module_ast = parser.parse()
        stmt_count = len(module_ast.statements) if hasattr(module_ast, "statements") else (len(module_ast) if isinstance(module_ast, list) else "Unknown")
        stmt_types = [type(s).__name__ for s in (module_ast.statements if hasattr(module_ast, "statements") else module_ast)] if isinstance(stmt_count, int) else "N/A"
        if self.debugging:
            print(f"DEBUG: Parsed module '{alias}' from '{full_path}': {stmt_count} statements. Types: {stmt_types}")

        # 4. Create Module Environment and ModuleObject
        module_env = Environment(parent=self.global_environment, file_path=full_path)
        result = ModuleObject(alias, module_env)
        
        # 1.5.5 Register in cache BEFORE execution to handle circular imports
        self.modules[full_path] = result

        # 5. Execute Module
        self._evaluate_program(module_ast, module_env)
        
        return result

    def _evaluate_assignment_statement(
        self, node: AssignmentStatement, environment: Environment
    ) -> any:
        value: any = None

        try:
            value = self._evaluate(node.value, environment)
        except ReturnException as return_exception:
            value = return_exception.value

        type: str = getattr(node, "resolved_type", None) or getattr(
            node, "declared_type", None
        )

        # If it's a 'set' (reassignment target in some contexts)
        # or if it's already in the environment, we might want to assign instead?
        # Actually, assignment_statement ALWAYS defines.
        # But if we are in a method and the variable is NOT in the local env but IS in self...
        # Wait, the parser uses AssignmentStatement for 'set name -> ...'
        
        # If the variable is NOT in the local environment, check if it's in 'self'
        if not environment.has(node.name) and environment.has("self"):
             self_object = environment.get("self")
             if isinstance(self_object, BaseObject):
                  try:
                       self_object.set_member(node.name, value)
                       return value
                  except Exception:
                       pass

        environment.define(node.name, value, mutable=node.mutable, type=type)
        return value

    def _evaluate_reassignment_statement(
        self, node: ReassignmentStatement, environment: Environment
    ) -> any:
        value: any = self._evaluate(node.value, environment)

        if environment.has(node.name):
             environment.assign(node.name, value)
             return value

        if environment.has("self"):
             self_object = environment.get("self")
             if isinstance(self_object, BaseObject):
                  try:
                       self_object.set_member(node.name, value)
                       return value
                  except Exception:
                       pass

        raise RuntimeError(f"Undefined variable '{node.name}'")

        return value

    def _evaluate_member_reassignment_statement(
        self, node: MemberReassignmentStatement, environment: Environment
    ):
        object: BaseObject = self._evaluate(node.callee, environment)
        value: any = self._evaluate(node.value, environment)
        member_name: str = node.expression # In bootstrap AST it's a str

        if isinstance(object, (StructureObject, InstanceObject)):
            object.set_member(member_name, value)
            return value

        print(f"DEBUG: Member Reassignment ERROR. Object: {object} (type={type(object)}). Member: {member_name}")
        print(f"DEBUG: Node: {node.callee} (line={getattr(node, 'line', '?')}, col={getattr(node, 'column', '?')})")
        raise RuntimeError(
            f"Cannot assign to member '{member_name}' of non-structure/non-instance object"
        )

    def _evaluate_index_reassignment_statement(
        self, node: IndexReassignmentStatement, environment: Environment
    ):
        object_val: BaseObject | list | dict = self._evaluate(node.callee, environment)
        index_val: any = self._evaluate(node.index, environment)
        value: any = self._evaluate(node.value, environment)

        if isinstance(object_val, list):
            if not isinstance(index_val, int):
                raise RuntimeError(f"Index must be an integer for List, got {type(index_val).__name__}")
            if index_val < 0 or index_val >= len(object_val):
                 raise RuntimeError(f"Index out of bounds: {index_val}")
            object_val[index_val] = value
            return value
        
        if isinstance(object_val, dict):
             object_val[index_val] = value
             return value

        raise RuntimeError(f"Cannot assign by index to object of type {type(object_val)}")

    def _evaluate_block_statement(
        self, node: BlockStatement, environment: Environment
    ) -> any:
        # create new nested environment
        new_environment = Environment(parent=environment)
        new_environment.defers = []

        result: any = None

        try:
            for statement in node.statements:
                try:
                    result = self._evaluate(statement, new_environment)

                except ReturnException as return_exception:
                    # bubble up return to caller
                    raise return_exception

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
                    self._evaluate(defer_node.body, environment) # Use outer env or new_environment? Spec usually says outer.

    def _evaluate_with_statement(self, node: WithStatement, environment: Environment) -> any:
        # 1. Evaluate the resource (e.g. Region())
        resource = self._evaluate(node.expression, environment)
        
        # 2. If it's an Arena/Region object, push it
        if hasattr(resource, "get_member"):
            try:
                push_fn = resource.get_member("push")
                if push_fn:
                    self._call_function(push_fn, [])
            except:
                pass

        # 3. Create nested environment
        new_env = Environment(parent=environment)
        if node.alias:
            new_env.define(node.alias, resource, False, "resource")
            
        try:
            # 4. Evaluate the block
            result = self._evaluate(node.body, new_env)
            return result
        finally:
            # 5. Pop if we pushed
            if hasattr(resource, "get_member"):
                try:
                    pop_fn = resource.get_member("pop")
                    if pop_fn:
                        self._call_function(pop_fn, [])
                except:
                    pass

    def _evaluate_function_statement(
        self, node: FunctionStatement, environment: Environment
    ) -> FunctionObject:
        function_object: FunctionObject = FunctionObject(
            name=node.name,
            parameters=node.parameters,
            body=node.body,
            closure=environment,
            return_type=getattr(node, "resolved_type", None)
            or getattr(node, "inferred_return_type", None),
        )

        environment.define(node.name, function_object, False, "function")

        return function_object

    def _evaluate_structure_statement(
        self, node: StructureStatement, environment: Environment
    ) -> any:
        members: dict = {}

        # new_environment = Environment(parent=environment)

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

        parent_obj = None
        if hasattr(node, "parent") and node.parent:
            parent_obj = environment.get(node.parent)

        structure_object: StructureObject = StructureObject(
            name=node.name, members=members, closure=environment, parent=parent_obj
        )

        environment.define(node.name, structure_object, False, "structure")

        return structure_object

    def _evaluate_class_statement(self, node: ClassStatement, environment: Environment) -> ClassObject:
        if self.debugging:
            print(f"DEBUG: Evaluating class '{node.name}'")
        parent: ClassObject | None = None
        if node.parent:
            parent = environment.get(node.parent)
            if not isinstance(parent, ClassObject):
                 raise RuntimeError(f"Parent '{node.parent}' is not a class")

        # Create Class Object
        class_object = ClassObject(
            name=node.name,
            parent=parent,
            members=node.members,
            methods=node.methods,
            closure=environment
        )

        # Pre-process methods into FunctionObjects
        # We need to compile them but NOT bind them yet.
        # They should be stored in class_object.methods_map
        
        for method_ast in node.methods:
             # Create function object
             # We use the class definition environment as closure for now
             # But when called, we need to bind 'self' to the instance.
             function_object = FunctionObject(
                name=method_ast.name,
                parameters=method_ast.parameters,
                body=method_ast.body,
                closure=environment, # Closure is where class is defined
                return_type=getattr(method_ast, "resolved_type", None)
             )
             if self.debugging:
                 print(f"DEBUG: Adding method '{method_ast.name}' to class '{node.name}'")
             class_object.methods_map[method_ast.name] = function_object

        environment.define(node.name, class_object, False, "class")
        return class_object

    def _evaluate_enumerator_statement(
        self, node: EnumeratorStatement, environment: Environment
    ) -> any:
        members: dict = {}

        for variant in node.members:
            # variant is EnumVariant
            variant_name = variant.name
            params = variant.params
            
            if not params:
                # Constant variant
                members[variant_name] = {
                    "type": "Variant",
                    "value": VariantObject(node.name, variant_name, []),
                    "mutable": False,
                }
            else:
                # Variant with data needs a constructor
                def make_constructor(e_name, v_name, v_params):
                    def constructor(*args_eval):
                        if len(args_eval) != len(v_params):
                            raise Exception(
                                f"Variant {v_name} expects {len(v_params)} arguments, got {len(args_eval)}"
                            )
                        return VariantObject(e_name, v_name, list(args_eval))

                    return constructor
                
                members[variant_name] = {
                    "type": "Function",
                    "value": make_constructor(node.name, variant_name, params),
                    "mutable": False,
                }

        structure_object: EnumeratorObject = EnumeratorObject(
            name=node.name, members=members, closure=environment
        )

        environment.define(node.name, structure_object, False, "Enumerator")

        return structure_object

    def _evaluate_scope_statement(self, node: ScopeStatement, environment: Environment) -> any:
        # Create scope definition environment
        # It should probably inherit from current environment to access globals? Yes.
        scope_env = Environment(parent=environment, file_path=environment.file_path)

        # Evaluate statements in the scope block directly into this environment
        # node.body is a BlockStatement
        if hasattr(node.body, "statements"):
             for statement in node.body.statements:
                 self._evaluate(statement, scope_env)

        # Create Scope Object (reusing ModuleObject as it is a namespace/env wrapper)
        scope_object = ModuleObject(node.name, scope_env)

        environment.define(node.name, scope_object, False, "scope")
        return scope_object

    def _evaluate_return_statement(
        self, node: ReturnStatement, environment: Environment
    ) -> any:
        value: any = (
            self._evaluate(node.value, environment) if node.value is not None else None
        )
        raise ReturnException(value)

    def _evaluate_when_statement(
        self, node: WhenStatement, environment: Environment
    ) -> any:
        condition_val = self._evaluate(node.condition, environment)
        
        # New: Structural pattern match branches (match-like)
        if hasattr(node, "branches") and node.branches is not None:
            for branch in node.branches:
                # Create a local environment for the branch to support bindings
                branch_env = Environment(parent=environment)
                if self._evaluate_pattern_match(condition_val, branch.pattern, branch_env):
                    return self._evaluate(branch.body, branch_env)
            
            if node.or_block:
                return self._evaluate(node.or_block, environment)
            return None

        # Traditional conditional when-block
        if condition_val:
            if node.when_block:
                return self._evaluate(node.when_block, environment)

        for condition_statement in node.conditional_blocks or []:
            if self._evaluate(condition_statement["condition"], environment):
                return self._evaluate(condition_statement["block"], environment)

        if node.or_block:
            return self._evaluate(node.or_block, environment)

        return None

    def _evaluate_do_statement(
        self, node: DoStatement, environment: Environment
    ) -> any:
        do_type: str = node.do_type
        result: any = None
        loop_cycled: bool = False

        # create loop-local environment
        new_environment = Environment(parent=environment)

        try:
            if do_type == "while":
                while self._evaluate(node.condition, new_environment):
                    loop_cycled = True

                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

            elif do_type == "until":
                while not self._evaluate(node.condition, new_environment):
                    loop_cycled = True

                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

            elif do_type == "while_post":
                # run block first, then check condition
                while True:
                    loop_cycled = True

                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        pass
                    except RuntimeBreak:
                        break

                    if not self._evaluate(node.condition, new_environment):
                        break

            elif do_type == "until_post":
                while True:
                    loop_cycled = True

                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        pass
                    except RuntimeBreak:
                        break

                    if self._evaluate(node.condition, new_environment):
                        break

            elif do_type == "for":
                iterable_value: any = self._evaluate(node.iterable, new_environment)

                # allow iterables like lists, strings, dicts
                if not hasattr(iterable_value, "__iter__"):
                    raise RuntimeError(f"Object '{iterable_value}' is not iterable")

                for item in iterable_value:
                    loop_cycled = True
                    loop_environment: Environment = Environment(new_environment)

                    try:
                        if isinstance(node.iterator, list):
                            # destructure tuple e.g. (a, b)
                            if isinstance(item, (list, tuple)):
                                for i, variable in enumerate(node.iterator):
                                    loop_environment.define(
                                        variable.name, item[i], True
                                    )
                            else:
                                raise RuntimeError(
                                    "Cannot destructure non-tuple value in for loop"
                                )

                        elif isinstance(node.iterator, IteratorLiteral):
                            # destructure tuple e.g. (a, b))
                            if isinstance(item, (list, tuple)):
                                for i, variable in enumerate(node.iterator.value):
                                    name: str = None
                                    if hasattr(variable, "name"):
                                        name = variable.name
                                    elif hasattr(variable, "value"):
                                        name = variable.value

                                    loop_environment.define(
                                        name, item[i], True, variable.type
                                    )
                            else:
                                raise RuntimeError(
                                    "Cannot destructure non-tuple value in for loop"
                                )

                        else:
                            loop_environment.define(node.iterator, item, mutable=True)

                        result = self._evaluate(node.body, loop_environment)

                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

                # handle optional else { } (only runs if loop never executes)
                if not loop_cycled and node.or_block:
                    result = self._evaluate(node.or_block, new_environment)

            elif do_type == "when":
                # Future: reactive/event-based execution
                if self._evaluate(node.condition, new_environment):
                    loop_cycled = True
                    result = self._evaluate(node.body, new_environment)

            elif do_type == "block":
                # plain do { ... } is an infinite loop in Zenlang
                while True:
                    loop_cycled = True
                    try:
                        result = self._evaluate(node.body, new_environment)
                    except RuntimeContinue:
                        continue
                    except RuntimeBreak:
                        break

        except ReturnException as return_exception:
            # propagate return up
            raise return_exception

        # run optional else { } after while/until if never entered
        if (
            (do_type in ("while", "until", "while_post", "until_post"))
            and node.or_block
            and not loop_cycled
        ):
            result = self._evaluate(node.or_block, new_environment)

        return result

    ## Expression handlers

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

    def _evaluate_function_expression(
        self, node: FunctionExpression, environment: Environment
    ) -> FunctionObject:
        function_object: FunctionObject = FunctionObject(
            name=node.name,
            parameters=node.parameters,
            body=node.body,
            closure=environment,
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

        # Lookup the definition to get the parent
        parent_obj = None
        try:
            definition = environment.get(node.name)
            if isinstance(definition, StructureObject):
                parent_obj = definition
        except RuntimeError:
            pass

        structure_object: StructureObject = StructureObject(
            name=node.name, members=members, closure=environment, parent=parent_obj
        )

        # Do NOT define it in environment; it's an instance expression, not a statement.
        return structure_object

    def _evaluate_member_expression(
        self, node: MemberExpression, environment: Environment
    ) -> any:
        # Evaluate the object (left side of the dot)
        object: BaseObject = self._evaluate(node.object, environment)
        member_name: str = getattr(node.property, "name", node.property)

        # --- 1. If it's a StructureObject ---
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
                      return self._bind_method(object, value, defining_class)
                 return value

            if isinstance(member_value, FunctionObject):
                return self._bind_method(object, member_value, object)
                # Bind self
                bound_function: FunctionObject = FunctionObject(
                    name=member_value.name,
                    parameters=member_value.parameters,
                    body=member_value.body,
                    closure=object.closure, # closure is the object's closure (class scope or struct scope)
                    return_type=member_value.return_type,
                )
                
                # Check if closure has 'self' defined, if not define it.
                # Use a new environment for the bound function to avoid polluting the original function's closure?
                # Actually, FunctionObject creation normally reuses closure.
                # But for methods, we want to inject 'self' into the scope lookup chain.
                # The standard way is to return a new FunctionObject with a new Environment that has 'self' and parent=original_closure.
                
                bound_env = Environment(parent=member_value.closure)
                bound_env.define("self", object, mutable=False, type="instance")
                bound_function.closure = bound_env

                return bound_function

            return member_value


        # --- 2. If it's a dictionary (Map) ---
        elif isinstance(object, dict):
            if member_name == "has":
                return lambda k: k in object
            elif member_name == "keys":
                return lambda: list(object.keys())
            elif member_name == "values":
                return lambda: list(object.values())
            
            if member_name not in object:
                raise RuntimeError(f"Object has no key '{member_name}'")

            return object[member_name]

        # --- 3. Collection Length Properties ---
        if isinstance(object, (list, set, dict, str)) and member_name in ["size", "length", "count", "len"]:
            return len(object)

        # --- 4. Special methods for other built-ins ---
        if isinstance(object, list):
            if member_name == "append":
                return object.append
            elif member_name == "pop":
                return object.pop
            elif member_name == "at":
                return lambda idx: object[idx]
            elif member_name == "remove_at":
                return lambda idx: object.pop(idx)

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

        # --- 5. If it's a built-in Python object (temporary feature) ---

        # --- 4. If it's a built-in Python object (temporary feature) ---
        elif hasattr(object, member_name) or (member_name == "kind" and hasattr(object, "type")):
            real_member_name = member_name if hasattr(object, member_name) else "type"
            val = getattr(object, real_member_name)
            from enum import Enum
            if isinstance(val, Enum):
                return val.name
            return val

        elif isinstance(object, str):
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
            elif member_name == "to_number":
                return lambda: float(object) if "." in object else int(object)
            elif member_name == "to_integer":
                return lambda: int(object)
            elif member_name == "to_decimal":
                return lambda: float(object)
            raise RuntimeError(f"String has no member '{member_name}'")
        elif isinstance(object, (list, tuple)) and member_name == "at":
            return lambda idx: object[idx]
        elif isinstance(object, list):
            if member_name == "append":
                return lambda v: object.append(v)
            elif member_name == "pop":
                return lambda: object.pop()
            elif member_name == "remove_at":
                return lambda i: object.pop(i)
            raise RuntimeError(f"List has no member '{member_name}'")
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
                 return object # For retry(3.times, ...)
            raise RuntimeError(f"Number has no member '{member_name}'")

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
        
        # We need to know WHICH class we are currently in, because 'parent' is relative to the class where the code is defined.
        # But wait, if we are in Dog.bark(), 'parent' should use Animal.
        # If Animal has bark() and Dog has bark() calling parent.bark().
        # We need to tag the FunctionObject with which class it belongs to?
        # Yes, let's add 'defining_class' to FunctionObject.
        
        # For now, let's assume we can find it from the closure.
        # Or better, the bound function knows its class.
        
        # Let's check if the current environment has 'defining_class'
        if not environment.has("__class__"):
             # Fallback to instance's class? No, that's wrong for nested inheritance.
             # If Cat extends Animal, and domesticCat extends Cat.
             # If domesticCat calls parent, it should get Cat.
             # If Cat calls parent, it should get Animal.
             # So 'parent' MUST be relative to where the method is defined.
             raise RuntimeError("'parent' used in unknown class context")
        
        defining_class = environment.get("__class__")
        return ParentProxy(instance, defining_class)

    ## Call handling
    def _evaluate_identifier(self, node: Identifier, environment: Environment) -> any:
        name: str = node.name
        # Try normal variable lookup
        try:
            return environment.get(name)
        except RuntimeError:
            pass

        # --- NEW: Fallback to structure context ---
        # If we’re in a structure method, automatically look for member variables
        if environment.has("self"):
            self_object: StructureObject = environment.get("self")

            if hasattr(self_object, "members") and name in self_object.members:
                res = self_object.get_member(name)
                if isinstance(res, tuple):
                     return res[0]
                return res

        # Still not found
        raise RuntimeError(f"Undefined variable '{name}'")

    def _evaluate_index_expression(
        self, node: IndexExpression, environment: Environment
    ) -> any:
        object_val: BaseObject | list | dict = self._evaluate(node.object, environment)
        index_val: any = self._evaluate(node.index, environment)

        if not isinstance(index_val, int) and not isinstance(object_val, dict):
            raise RuntimeError(f"Index must be an integer for {type(object_val).__name__}, got {type(index_val).__name__}")

        if isinstance(object_val, list):
            if index_val < 0 or index_val >= len(object_val):
                 raise RuntimeError(f"Index out of bounds: {index_val}")
            return object_val[index_val]
        
        if isinstance(object_val, dict):
             if index_val not in object_val:
                  raise RuntimeError(f"Key error: {index_val}")
             return object_val[index_val]

        raise RuntimeError(f"Cannot index object of type {type(object_val)}")

    def _evaluate_call_expression(
        self, node: CallExpression, environment: Environment
    ) -> any:
        # print(f"DEBUG: CallExpression callee: {node.callee}")

        
        callee: Any = self._evaluate(node.callee, environment)

        arguments: List[Any] = [
            self._evaluate(arg, environment) for arg in node.arguments
        ]

        # builtin python-callable
        if callable(callee) and not isinstance(callee, FunctionObject):
            return callee(*arguments)

        if isinstance(callee, FunctionObject):
            return self._call_function(callee, arguments)

        if isinstance(callee, ClassObject):
            # Instantiate Class
            instance_members = {}
            
            # Collect hierarchy to initialize members from parent to child
            hierarchy = []
            curr = callee
            while curr:
                hierarchy.append(curr)
                curr = curr.parent
            hierarchy.reverse()

            for cls in hierarchy:
                for member_node in cls.members_ast:
                     # Evaluate default values in the context of the class definition
                     value = self._evaluate(member_node.value, cls.closure)
                     instance_members[member_node.name] = {
                         "value": value,
                         "type": getattr(member_node, "declared_type", "Variant"),
                         "mutable": member_node.mutable
                     }
            
            instance = InstanceObject(callee, instance_members)
            
            # --- Call init if exists ---
            init_result = instance._find_method_in_class("init", callee)
            if init_result[0]:
                 method, defining_class = init_result
                 bound_init = self._bind_method(instance, method, defining_class)
                 self._call_function(bound_init, arguments)
            elif len(arguments) > 0:
                 raise RuntimeError(f"Class '{callee.name}' has no 'init' method but received {len(arguments)} arguments")

            return instance

            print(f"DEBUG: Call Error Node: {node}")
            print(f"DEBUG: Callee evaluated to: {callee}")
            raise RuntimeError(f"Attempted to call a non-function value: {callee}")

    def _call_function(self, function: FunctionObject, arguments: List[Any]) -> any:
        # create function env with closure parent
        function_environment: Environment = Environment(parent=function.closure)

        # only bind self if not already defined (methods)
        if not function_environment.has("self"):
            function_environment.define("self", None, False, "structure_instance")

        # bind parameters
        for i, parameter in enumerate(function.parameters):
            # param may be a dict or AST node describing param - adapt as needed
            name: str | None = (
                parameter.get("name")
                if isinstance(parameter, dict)
                else getattr(parameter, "name", None)
            )
            value: Any = arguments[i] if i < len(arguments) else None
            type: Any = parameter.get("type") if isinstance(parameter, dict) else None

            function_environment.define(name, value, True, type)

        try:
            # evaluate function block (which is a BlockStatement or similar)
            return self._evaluate(function.body, function_environment)
        except ReturnException as return_exception:
            return return_exception.value

    ## Literals
    def _evaluate_list_literal(
        self, node: ListLiteral, environment: Environment
    ) -> any:
        if not node.elements:
            return []

        result = []
        result = []
        for element in node.elements:
            evaluated = self._evaluate(element, environment)
            result.append(evaluated)

        return result

    def _evaluate_element_literal(
        self, node: ElementLiteral, environment: Environment
    ) -> any:
        return self._evaluate(node.value, environment)

    def _evaluate_vector_literal(self, node: Any, environment: Environment) -> list:
        return [self._evaluate(el.value, environment) for el in node.elements]

    def _evaluate_map_literal(self, node: Any, environment: Environment) -> dict:
        result = {}
        for element in node.elements:
            key = self._evaluate(element.name, environment)
            value = self._evaluate(element.value, environment)
            result[key] = value
        return result

    def _evaluate_set_literal(self, node: Any, environment: Environment) -> set:
        return {self._evaluate(el.value, environment) for el in node.elements}

    def _evaluate_tuple_literal(self, node: Any, environment: Environment) -> tuple:
        return tuple(self._evaluate(el.value, environment) for el in node.elements)

    def _evaluate_export_statement(self, node: Any, environment: Environment) -> None:
        # In the interpreter, export doesn't do much differently than executing the statement,
        # but it could mark symbols as exported if we had a module system.
        return self._evaluate(node.statement, environment)

    ## Operators
    def _evaluate_binary_operation(self, operation: str, left: Any, right: Any) -> any:
        if operation == "+":
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right

        if operation == "-":
            return left - right

        if operation == "*":
            return left * right

        if operation == "/":
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right

        if operation == "%":
            return left % right

        if operation == "**":
            return left ** right

        if operation == "==" or operation == "=":
            return left == right

        if operation == "!=":
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

        if operation == "&&":
            return int(left) & int(right)
        if operation == "||":
            return int(left) | int(right)
        if operation == "^^":
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

        if operation == "&&":
            return left & right

        if operation == "||":
            return left | right

        if operation == "^^":
            return left ^ right

        if operation == "!&":
            return ~(left & right)

        if operation == "!|":
            return ~(left | right)

        if operation == "!^":
            return ~(left ^ right)

        if operation == "<<":
            return left << right

        if operation == ">>":
            return left >> right

        raise RuntimeError(f"Unknown binary operator '{operation}'")

    def _evaluate_unary_operation(self, operation: str, right: Any) -> any:
        if operation == "-":
            return -right

        if operation == "not":
             # print(f"DEBUG: unary not input: {right} (type: {type(right)})")
             return not bool(right)

        if operation == "!!" or operation == "~":
            return ~right

        return right

    def _evaluate_object_statement(
        self, node: Any, environment: Environment
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

        parent_obj = None
        if node.parent:
            parent_obj = environment.get(node.parent)

        object_object: StructureObject = StructureObject(
            name=node.name, members=members, closure=environment, parent=parent_obj
        )

        environment.define(node.name, object_object, False, "object")

        return object_object

    def _evaluate_defer_statement(self, node: Any, environment: Environment) -> None:
        if not hasattr(environment, "defers"):
            environment.defers = []
        environment.defers.append(node)
        return None

    def _evaluate_raise_statement(self, node: Any, environment: Environment) -> None:
        value = self._evaluate(node.value, environment)
        with_value = self._evaluate(node.with_value, environment) if node.with_value else None
        raise RaiseException(value, with_value)

    def _evaluate_assert_statement(self, node: Any, environment: Environment) -> None:
        condition = self._evaluate(node.condition, environment)
        if not condition:
            if node.raise_expression:
                self._evaluate(node.raise_expression, environment)
            else:
                raise RaiseException("AssertionError", f"Assertion failed at {node.line}:{node.column}")
        return None
    def _evaluate_check_statement(self, node: Any, environment: Environment) -> Any:
        try:
            result = self._evaluate(node.expression, environment)
            # Normal return path: match cases
            if hasattr(node, "cases") and node.cases:
                for case in node.cases:
                    if self._evaluate_pattern_match(result, case.pattern, environment):
                        return self._evaluate(case.body, environment)
            return result
        except RaiseException as e:
            # Exception path: match cases against the exception
            if hasattr(node, "cases") and node.cases:
                for case in node.cases:
                    if self._evaluate_pattern_match(e, case.pattern, environment):
                        return self._evaluate(case.body, environment)
            
            if hasattr(node, "or_block") and node.or_block:
                return self._evaluate(node.or_block, environment)
            if hasattr(node, "raise_expression") and node.raise_expression:
                raise_val = self._evaluate(node.raise_expression, environment)
                raise RaiseException(raise_val)
            raise e

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

    def _evaluate_is_expression(self, node: IsExpression, environment: Environment) -> bool:
        value = self._evaluate(node.left, environment)
        return self._evaluate_pattern_match(value, node.right, environment)

    def _evaluate_pattern_match(self, value: Any, pattern: Any, environment: Environment) -> bool:
        if isinstance(pattern, WildcardPattern):
            return True
            
        if isinstance(pattern, IdentifierPattern):
            environment.define(pattern.name, value, mutable=False, type="Variant")
            return True

        if isinstance(pattern, IsMatchPattern):
            # Check type name
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
            if len(pattern.elements) != len(value):
                return False
            
            for i, elem_pattern in enumerate(pattern.elements):
                if not self._evaluate_pattern_match(value[i], elem_pattern, environment):
                    return False
            return True

        if isinstance(pattern, VariantPattern):
            if not isinstance(value, VariantObject):
                return False
            
            # Check the variant name (tag)
            # Support both "Some" and "Option.Some"
            if "." in pattern.name:
                 enum_part, variant_part = pattern.name.split(".", 1)
                 if value.enum_name != enum_part or value.variant_name != variant_part:
                      return False
            else:
                 if value.variant_name != pattern.name:
                      return False
            
            # Match parameters
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
    def _evaluate_in_expression(self, node: InExpression, environment: Environment) -> any:
        # The interpreter doesn't strictly enforce arenas for every allocation yet,
        # but we could potentially set a 'current_arena' in the environment.
        # For now, just evaluate the expression.
        return self._evaluate(node.expression, environment)
