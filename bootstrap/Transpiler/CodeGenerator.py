import os
from typing import Union, List, Optional, Any, Set
from Parser.AST import (
    ASTNode,
    Program,
    FunctionStatement,
    ClassStatement,
    ObjectStatement,
    EnumeratorStatement,
    StructureStatement,
    TaskStatement,
    ImportStatement,
    FromImportStatement,
)

from Transpiler.BaseGenerator import BaseGenerator
from Transpiler.Handlers.TypeHandler import TypeHandler
from Transpiler.Handlers.StructuralHandler import StructuralHandler
from Transpiler.Handlers.FunctionalHandler import FunctionalHandler
from Transpiler.Handlers.MIRHandler import MIRHandler
from Transpiler.Handlers.StatementHandler import StatementHandler
from Transpiler.Handlers.ExpressionHandler import ExpressionHandler
from Transpiler.Handlers.MangleHandler import MangleHandler

class Generator(MangleHandler, BaseGenerator, TypeHandler, StructuralHandler, FunctionalHandler, MIRHandler, StatementHandler, ExpressionHandler):
    def __init__(self, enable_source_map: bool = False):
        super().__init__()
        self.enable_source_map = enable_source_map
        self.AST: ASTNode | None = None
        self.indent_level: int = 0
        self.temp_counter: int = 0
        self.defer_counter: int = 0
        self.code: list = []
        self.imports: list = []
        self.global_variables: list = []
        self.global_functions: list = []
        self.global_functions_code: list = []
        self.current_class: str | None = None
        self.current_scope: str | None = None
        self.scope_stack: list = []
        self.current_region = "global"
        self.local_types: dict = {}
        self.global_variable_names: set = {"Str", "IO", "Sys", "module", "TokenType", "ASTKind", "SymbolKind", "TokenModule", "ASTModule", "__builtin", "__builtin_ast", "__builtin_io", "__builtin_sys", "__builtin_memory", "__builtin_output", "__builtin_input", "__builtin_file", "__builtin_math", "__builtin_list", "__builtin_map", "__builtin_set", "__builtin_string", "__builtin_range", "__builtin_array", "__builtin_time", "__builtin_term", "__builtin_process", "__builtin_random", "__builtin_error", "__builtin_reflect", "__builtin_net", "__builtin_vm", "vm", "VM", "__builtin_ffi", "ffi", "__builtin_concurrency", "concurrency", "__builtin_channel", "__builtin_task", "channel", "spawn", "spawn_blocking", "sleep", "poll_fd", "Task", "Channel", "stdout", "stderr", "stdin", "args", "env"}
        self.is_in_condition = False
        self.current_function = None
        self.singletons = []
        self.init_singletons_code = []
        self.scope_defer_stack = []
        self.global_classes = set()
        self.symbol_allocs = {} 
        self.module_aliases = {}
        self.last_emitted_line = -1
        self.last_emitted_file = None
        self.main_file = None
        self.source_mapping = True
        self.pending_lambdas = []
        self.lambda_forward_decls = []
        self._lambda_fwd_names = set()
        self.defer_prototypes = []
        self.pending_lambdas = []

    def generate(self, program: Program, filename: str = None) -> str:
        self.main_file = filename
        self.last_emitted_file = filename
        self.program = program
        self.scope = program.scope if hasattr(program, "scope") else None
        self.code = []
        
        # Deduplicate by (module file, name) so list.contains and string.contains both live.
        seen_enums = set()
        seen_classes = set()
        seen_functions = set()
        unique_statements = []
        for stmt in program.statements:
             if isinstance(stmt, EnumeratorStatement):
                  key = (getattr(stmt, "filename", None), stmt.name)
                  if key in seen_enums: continue
                  seen_enums.add(key)
             elif isinstance(stmt, (ClassStatement, StructureStatement)):
                  key = (getattr(stmt, "filename", None), stmt.name)
                  if key in seen_classes: continue
                  seen_classes.add(key)
                  self.global_classes.add(stmt.name)
             elif isinstance(stmt, FunctionStatement):
                  key = (getattr(stmt, "filename", None), stmt.name)
                  if key in seen_functions: continue
                  seen_functions.add(key)
             unique_statements.append(stmt)
        program.statements = unique_statements

        self.emit('#define ZEN_IO_IMPLEMENTATION\n')
        self.emit('#include "bootstrap_runtime.h"\n')
        self.emit('void init_singletons();\n')
        self.emit('#include <stdlib.h>\n')
        self.emit('#include <string.h>\n')
        self.emit('#include <math.h>\n')
        self.emit('\n')
        
        self.defer_prototypes = []
        self.scan_for_defers(program)
        for stmt in program.statements:
            if isinstance(stmt, ImportStatement):
                name = stmt.alias if stmt.alias else stmt.name
                path_key = stmt.path or ""
                if "/" in path_key:
                    real_module_name = path_key.rstrip("/").split("/")[-1]
                else:
                    real_module_name = path_key.split(".")[-1]
                resolved = getattr(stmt, "resolved_path", None) or getattr(stmt, "filename", None)
                if resolved:
                    import os as _os
                    base = _os.path.basename(str(resolved)).replace(".zl", "")
                    if base and base not in ("bootstrap_runtime",):
                        real_module_name = base
                self.module_aliases[name] = real_module_name

        self.setup_runtime()
        # 1. Forward Declarations FIRST
        self.emit_forward_declarations(program)
        
        if hasattr(self, "defer_prototypes"):
             for proto in self.defer_prototypes:
                  self.emit(proto)

        # 2. Struct bodies
        self.setup_global_structures(program)
        
        # 4. Global variables
        self.setup_global_variables(program)
        
        # Mark where lambda prototypes should be inserted (before function bodies).
        prototype_insert_at = len(self.code)

        self.setup_global_functions(program)
        self.setup_class_methods(program)
        # Host C main after all functions/methods (module.entry dispatch)
        self.generate_host_main(program)
        self.generate_init_singletons()

        # Insert lambda prototypes collected during body generation.
        if getattr(self, "lambda_forward_decls", None):
            insert = list(dict.fromkeys(self.lambda_forward_decls))  # stable unique
            for i, proto in enumerate(insert):
                self.code.insert(prototype_insert_at + i, proto)
            self.code.insert(prototype_insert_at + len(insert), "")

        return "\n".join(self.code)

    def setup_runtime(self):
        pass
        self.emit("")
