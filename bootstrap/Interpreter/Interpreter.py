import os
import sys
from typing import Any, List, Optional, Dict, Callable

# Increase recursion limit for deep ASTs
sys.setrecursionlimit(1000000)

from Lexer.Lexer import Lexer
from Parser.Parser import Parser
from Interpreter.Runtime import Environment, ModuleObject, FunctionObject, BaseObject, MemoryManager
from Interpreter.Exceptions import ReturnException, RaiseException, RuntimeBreak, RuntimeContinue
from Parser.AST import (
    ASTNode,
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
    ReturnStatement,
    ExpressionStatement,
    TaskStatement,
)

# Import Handlers
from Interpreter.Handlers.LiteralHandler import LiteralHandler
from Interpreter.Handlers.ExpressionHandler import ExpressionHandler
from Interpreter.Handlers.StatementHandler import StatementHandler
from Interpreter.Handlers.BuiltinHandler import BuiltinHandler
from Interpreter.Handlers.PatternHandler import PatternHandler

class Interpreter(
    LiteralHandler,
    ExpressionHandler,
    StatementHandler,
    BuiltinHandler,
    PatternHandler
):
    def __init__(
        self, AST: ASTNode, source_path: str, strict: bool = False, debug: bool = False, resolver = None
    ) -> None:
        import threading
        self.debugging: bool = debug
        self.strict: bool = strict

        self.source_path: str = source_path
        self.AST: ASTNode = AST
        self.resolver = resolver

        self.execution_arguments: list = []
        self.global_environment: Environment = Environment(file_path=source_path)
        self._depth: int = 0
        self._node_stack: list = []
        self.modules: dict[str, any] = {} # path -> ModuleObject
        self.memory_manager = MemoryManager()

        self._build_dispatch_table()
        # Built-in `module` map for the entry file (overridden per import in _load_module)
        self._install_module_info(
            self.global_environment,
            file_path=os.path.abspath(source_path) if source_path else "",
            logical_path=self._logical_name_from_file(source_path),
            is_entry=True,
        )
        # Allow module.entry reassignment for custom entry points
        if "module" in self.global_environment.values:
            self.global_environment.values["module"]["mutable"] = True
        self._register_builtins()

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value

    def _build_dispatch_table(self) -> None:
        self.dispatch_table: Dict[str, Callable] = {
            # Statements
            "AssignmentStatement": self._evaluate_assignment_statement,
            "ReassignmentStatement": self._evaluate_reassignment_statement,
            "MemberReassignmentStatement": self._evaluate_member_reassignment_statement,
            "IndexReassignmentStatement": self._evaluate_index_reassignment_statement,
            "MemberReassignment": self._evaluate_member_reassignment_statement,
            "IndexReassignment": self._evaluate_index_reassignment_statement,
            "ExpressionStatement": lambda node, env: self._evaluate(node.expression, env),
            "BlockStatement": self._evaluate_block_statement,
            "FunctionStatement": self._evaluate_function_statement,
            "StructureStatement": self._evaluate_structure_statement,
            "ClassStatement": self._evaluate_class_statement,
            "EnumeratorStatement": self._evaluate_enumerator_statement,
            "ScopeStatement": self._evaluate_scope_statement,
            "ImportStatement": self._evaluate_import_statement,
            "FromImportStatement": self._evaluate_from_import_statement,
            "ReturnStatement": self._evaluate_return_statement,
            "WhenStatement": self._evaluate_when_statement,
            "DoStatement": self._evaluate_do_statement,
            "DeferStatement": self._evaluate_defer_statement,
            "RaiseStatement": self._evaluate_raise_statement,
            "AssertStatement": self._evaluate_assert_statement,
            "CheckStatement": self._evaluate_check_statement,
            "TaskStatement": self._evaluate_task_statement,
            "ObjectStatement": self._evaluate_object_statement,
            "ExportStatement": self._evaluate_export_statement,
            "WithStatement": self._evaluate_with_statement,
            "BreakStatement": self._handle_break,
            "ContinueStatement": self._handle_continue,
            "DereferenceReassignmentStatement": self._evaluate_dereference_reassignment_statement,

            # Expressions
            "BlockExpression": self._evaluate_block_expression,
            "FunctionExpression": self._evaluate_function_expression,
            "WhenExpression": self._evaluate_when_expression,
            "WhenInlineExpression": self._evaluate_when_inline_expression,
            "CheckExpression": self._evaluate_check_expression,
            "CallExpression": self._evaluate_call_expression,
            "StructureExpression": self._evaluate_structure_expression,
            "MemberExpression": self._evaluate_member_expression,
            "IndexExpression": self._evaluate_index_expression,
            "SliceExpression": self._evaluate_slice_expression,
            "ParentExpression": self._evaluate_parent_expression,
            "InExpression": self._evaluate_in_expression,
            "IsExpression": self._evaluate_is_expression,
            "AwaitExpression": self._evaluate_await_expression,
            "BinaryOperation": self._evaluate_binary_operation_node,
            "UnaryOperation": self._evaluate_unary_operation_node,

            # Literals
            "IntegerLiteral": self._evaluate_integer_literal,
            "DecimalLiteral": self._evaluate_decimal_literal,
            "StringLiteral": self._evaluate_string_literal,
            "RuneLiteral": self._evaluate_rune_literal,
            "BooleanLiteral": self._evaluate_boolean_literal,
            "ListLiteral": self._evaluate_list_literal,
            "VectorLiteral": self._evaluate_vector_literal,
            "MapLiteral": self._evaluate_map_literal,
            "SetLiteral": self._evaluate_set_literal,
            "TupleLiteral": self._evaluate_tuple_literal,
            "Identifier": self._evaluate_identifier,
            "VoidLiteral": self._evaluate_void_literal,
            "NothingLiteral": self._evaluate_nothing_literal,
            "DefaultLiteral": self._evaluate_default_literal,
            "VariantLiteral": self._evaluate_variant_literal,
            "ElementLiteral": self._evaluate_element_literal,
        }

    def _handle_break(self, node, env):
        raise RuntimeBreak()

    def _handle_continue(self, node, env):
        raise RuntimeContinue()

    def interpret(
        self,
        program: ASTNode | None = None,
        environment: Environment | None = None,
        arguments: list = [],
    ) -> any:
        self.execution_arguments = arguments
        try:
            if program is None:
                program = self.AST

            if environment is None:
                environment = self.global_environment

            return self._evaluate_program(program, environment, arguments)

        except ReturnException as return_exception:
            return f"Return value: '{return_exception.value}'"

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
            TaskStatement,
        )

        # Pass 1: Register all definitions
        for statement in program.statements:
            if isinstance(statement, definitions):
                self._evaluate(statement, environment)

        # Pass 2: Top-level statements of the *entry file only*
        # (merged multi-file ASTs include other modules' statements; skip their
        # top-level calls so e.g. a dependency's stray main() is not executed.)
        entry_file = None
        try:
            if environment.has("module"):
                m = environment.get("module")
                if isinstance(m, dict):
                    entry_file = m.get("file")
        except Exception:
            entry_file = None
        if not entry_file:
            entry_file = getattr(environment, "file_path", None) or self.source_path
        if entry_file:
            entry_file = os.path.abspath(entry_file)

        def _stmt_file(stmt) -> str | None:
            fn = getattr(stmt, "filename", None)
            if not fn and hasattr(stmt, "symbol") and stmt.symbol:
                fn = getattr(stmt.symbol, "filename", None)
            return os.path.abspath(fn) if fn else None

        for statement in program.statements:
            if isinstance(statement, definitions):
                continue
            sf = _stmt_file(statement)
            # Only run top-level init from the entry source file.
            # Orphan statements (filename None) from merged deps are skipped —
            # they can include spurious top-level main() calls.
            if entry_file:
                if not sf or sf != entry_file:
                    continue
            if isinstance(statement, ReturnStatement):
                result = self._evaluate(statement, environment)
                return result
            result = self._evaluate(statement, environment)

        # Pass 3: entry only for the process entry module (not imported libraries)
        is_entry_module = True
        try:
            if environment.has("module"):
                m = environment.get("module")
                if isinstance(m, dict) and "is_entry" in m:
                    is_entry_module = bool(m.get("is_entry"))
        except Exception:
            pass

        if not is_entry_module:
            return result

        input_arguments: list = [self.source_path]
        input_arguments.extend(arguments)
        self.execution_arguments = input_arguments

        entry_fn = self._resolve_entry_function(environment, entry_point)
        if entry_fn is not None:
            params = getattr(entry_fn, "parameters", None) or []
            if len(params) >= 1 and getattr(entry_fn, "name", None) == "main":
                result = self._call_function(entry_fn, [input_arguments])
            else:
                result = self._call_function(entry_fn, [])
        return result

    def _resolve_entry_function(
        self, environment: Environment, default_entry: str | None
    ):
        """module.entry overrides default entry_point (usually `main`)."""
        from Interpreter.Runtime import FunctionObject

        mod = None
        try:
            if environment.has("module"):
                mod = environment.get("module")
        except Exception:
            mod = None

        if isinstance(mod, dict) and "entry" in mod:
            entry_val = mod["entry"]
            if isinstance(entry_val, FunctionObject):
                return entry_val
            if isinstance(entry_val, str) and entry_val:
                try:
                    fn = environment.get(entry_val)
                    if isinstance(fn, FunctionObject):
                        return fn
                except Exception:
                    pass
                raise RuntimeError(
                    f"module.entry is `{entry_val}` but no function with that name is defined"
                )

        name = default_entry or "main"
        if name:
            try:
                fn = environment.get(name)
                if isinstance(fn, FunctionObject):
                    return fn
            except Exception:
                pass
        return None

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

    def evaluate(self, node: ASTNode, environment: Environment = None) -> any:
        if environment is None:
            environment = self.global_environment
        return self._evaluate(node, environment)

    def _evaluate(self, node: Any, environment: Environment) -> any:
        self._depth += 1
        self._node_stack.append((node, environment))
        
        # Guard against extreme recursion
        if self._depth > 100000:
             raise RuntimeError(f"Interpreter: Maximum recursion depth exceeded (depth={self._depth})")

        try:
            return self._evaluate_node(node, environment)
        except Exception as e:
            if not hasattr(e, '_zen_trace_printed') and not isinstance(e, (ReturnException, RaiseException, RuntimeBreak, RuntimeContinue)):
                e._zen_trace_printed = True
                print("=== ZENSTACK TRACE ===")
                for stack_node, env in self._node_stack:
                    fn_name = getattr(env, 'file_path', 'unknown')
                    node_cls = stack_node.__class__.__name__
                    line_num = getattr(stack_node, 'line', 'unknown')
                    extra = ""
                    if hasattr(stack_node, 'name') and stack_node.name:
                        extra += f" name={stack_node.name}"
                    elif hasattr(stack_node, 'value') and stack_node.value is not None:
                        extra += f" value={stack_node.value!r}"
                    print(f"  File {fn_name}, line {line_num}, in {node_cls}{extra}")
                print("======================")
            raise
        finally:
            self._node_stack.pop()
            self._depth -= 1

    def _evaluate_node(self, node: ASTNode, environment: Environment) -> any:
        if node is None:
            return None

        node_type: str = getattr(node, "node_type", None) or node.__class__.__name__
        
        handler = self.dispatch_table.get(node_type)
        if handler:
            return handler(node, environment)

        raise NotImplementedError(
            f"Interpreter: node type not implemented: {node_type}"
        )

    @staticmethod
    def _logical_name_from_file(file_path: str | None) -> str:
        if not file_path:
            return ""
        base = os.path.basename(file_path)
        if base.endswith(".zl") or base.endswith(".zs"):
            base = base.rsplit(".", 1)[0]
        return base

    @staticmethod
    def make_module_info(
        *,
        name: str,
        path: str,
        file: str,
        directory: str,
        is_entry: bool,
    ) -> dict:
        """Map-shaped module context: name, path, file, dir, is_entry."""
        return {
            "name": name or "",
            "path": path or "",
            "file": file or "",
            "dir": directory or "",
            "is_entry": bool(is_entry),
        }

    def _install_module_info(
        self,
        environment: Environment,
        *,
        file_path: str,
        logical_path: str,
        is_entry: bool,
    ) -> dict:
        file_abs = os.path.abspath(file_path) if file_path else ""
        directory = os.path.dirname(file_abs) if file_abs else ""
        name = logical_path.split(".")[-1] if logical_path else self._logical_name_from_file(file_abs)
        info = self.make_module_info(
            name=name,
            path=logical_path or name,
            file=file_abs,
            directory=directory,
            is_entry=is_entry,
        )
        environment.define("module", info, mutable=False, type="Map")
        return info

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

        if os.path.exists(full_path + ".zl"):
            full_path += ".zl"
        elif os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "mod.zl")):
            full_path = os.path.join(full_path, "mod.zl")
        elif os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "module.zl")):
            full_path = os.path.join(full_path, "module.zl")
        
        # 1.5 Check Cache
        if full_path in self.modules:
            return self.modules[full_path]
        
        if self.debugging:
            print(f"DEBUG [Interpreter]: Loading module from {full_path}")
        
        if not os.path.exists(full_path):
             raise RuntimeError(f"Module not found: {path} (checked {full_path})")

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

        # 4. Create Module Environment and ModuleObject
        module_env = Environment(parent=self.global_environment, file_path=full_path)
        result = ModuleObject(alias, module_env)

        # Per-module `module` context (not the process entry)
        dotted = path.replace(os.sep, ".") if path else alias
        if dotted.endswith(".zl"):
            dotted = dotted[:-3]
        self._install_module_info(
            module_env,
            file_path=full_path,
            logical_path=dotted or alias or self._logical_name_from_file(full_path),
            is_entry=False,
        )

        # 1.5.5 Register in cache BEFORE execution to handle circular imports
        self.modules[full_path] = result

        # 5. Execute Module
        self._evaluate_program(module_ast, module_env)

        return result
