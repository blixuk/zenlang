import os
from typing import Union, Any
from Parser.AST import (
    FunctionStatement,
    ClassStatement,
    ObjectStatement,
    Program,
    EnumeratorStatement,
    StructureStatement,
    ImportStatement,
    FromImportStatement,
    ReturnStatement,
    AssignmentStatement,
    ReassignmentStatement,
    ExportStatement,
    ScopeStatement,
    BlockStatement,
    TaskStatement
)

class FunctionalHandler:
    def setup_class_methods(self, program: Program) -> None:
        if not hasattr(self, "class_parents"):
            self.class_parents = {}
            
        for statement in program.statements:
            if isinstance(statement, ExportStatement) or statement.__class__.__name__ == "ExportStatement":
                statement = statement.statement
            if isinstance(statement, (ClassStatement, ObjectStatement)):
                m_name = self.get_mangled_name(statement)
                self.current_class = m_name
                self.class_parents[m_name] = getattr(statement, "parent", None)
                
                methods = getattr(statement, "methods", [])
                members = getattr(statement, "members", [])
                for m_list in (methods, members):
                    for member in m_list:
                        if isinstance(member, FunctionStatement):
                            self.generate_method_statement(m_name, member)
                
                # Generate Constructor
                self.generate_class_constructor(statement)
                # Method invoker table for reflect.call under -g
                if getattr(statement, "reflectable", False):
                    self._emit_reflect_method_thunks(statement, m_name)
                self.current_class = None

    def _emit_reflect_method_thunks(self, statement: Any, class_name: str) -> None:
        """Emit static thunks + init registration for ZenReflect_call on class instances."""
        bare = statement.name.replace("\\", "\\\\").replace('"', '\\"')
        method_nodes = []
        for m_list in (
            getattr(statement, "methods", None) or [],
            getattr(statement, "members", None) or [],
        ):
            for member in m_list:
                if isinstance(member, FunctionStatement) and getattr(member, "name", None):
                    method_nodes.append(member)

        if not hasattr(self, "init_singletons_code"):
            self.init_singletons_code = []

        for method in method_nodes:
            m_san = self.sanitize_name(method.name)
            thunk = f"__reflect_{class_name}_{m_san}"
            method_c = f"{class_name}_{m_san}"
            n_params = len(method.parameters or [])
            rtype = self.get_function_return_type(method)

            self.emit(f"static ZenValue {thunk}(void* __self, ZenValue __args) {{")
            self.indent_level += 1
            self.emit(f"{class_name}* self = ({class_name}*)__self;")
            arg_names = []
            for i in range(n_params):
                an = f"__a{i}"
                arg_names.append(an)
                self.emit(
                    f"ZenValue {an} = ZenList_get_value_at_index("
                    f"__args, ZenValue_make_integer({i}));"
                )
            call_args = ", ".join(["self"] + arg_names)
            if str(rtype) == "void":
                self.emit(f"{method_c}({call_args});")
                self.emit("return ZenValue_make_nothing();")
            else:
                self.emit(f"return {method_c}({call_args});")
            self.indent_level -= 1
            self.emit("}")
            self.emit("")

            m_esc = method.name.replace("\\", "\\\\").replace('"', '\\"')
            self.init_singletons_code.append(
                f'ZenReflect_register_method("{bare}", "{m_esc}", {thunk});'
            )

    def generate_method_statement(self, class_name: str, method: FunctionStatement):
        # Mangled name: Class_method
        method_name = f"{class_name}_{self.sanitize_name(method.name)}"
        old_class = self.current_class
        self.current_class = class_name
        
        # Prepare parameters: add self
        params_list = []
        params_list.append(f"{class_name}* self")
        
        for param in method.parameters:
            pname = self.get_mangled_name(param, should_prefix=False)
            params_list.append(f"ZenValue {pname}")
        
        param_str = ", ".join(params_list)
        rtype = self.get_function_return_type(method)
        
        self.emit(f"{rtype} {method_name}({param_str}) {{")
        # Method-entry tracing is opt-in (keeps demos and tests free of DEBUG spam).
        self.emit(f"#ifdef ZEN_TRACE_METHODS")
        self.emit(f'    printf("DEBUG: Method Enter: {method_name} self=%p\\n", (void*)self);')
        self.emit(f"#endif")
        self.indent_level += 1
        
        # Track defer depth
        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __meth_defer_{temp_id} = ZenRuntime_get_defer_depth();")
        self.scope_defer_stack.append(f"__meth_defer_{temp_id}")
        if rtype != "void":
             self.emit(f"{rtype} __ret_val = ZEN_NOTHING_VAL;")
        exit_label = f"__exit_{temp_id}"
        self.current_exit_label = exit_label

        self.current_function = method
        
        # MIR Body Generation
        param_names = ["self"] + [p.name for p in method.parameters]
        method_filename = getattr(method, "filename", self.main_file)
        self.generate_lmir_block(method.body, filename=method_filename, pre_allocated=param_names, auto_arena=(class_name != "Arena"))
        
        # Cleanup
        self.emit(f"{exit_label}:;")
        self.emit(f"ZenRuntime_defer_run_to(__meth_defer_{temp_id});")
        self.scope_defer_stack.pop()
        
        if str(rtype) != "void":
             self.emit("return __ret_val;")

        self.indent_level -= 1
        self.emit("}")
        self.emit()
        self.current_class = old_class

    def generate_class_constructor(self, statement: Union[ClassStatement, ObjectStatement]):
        # Resolve init recursively if not found in current class
        init_method = next((m for m in getattr(statement, "methods", []) if m.name == "init"), None)
        init_class_name = statement.name
        
        if not init_method and getattr(statement, "parent", None):
             current_parent = statement.parent
             while current_parent:
                  parent_stmt = next((s for s in self.program.statements if isinstance(s, (ClassStatement, ObjectStatement)) and s.name == current_parent), None)
                  if parent_stmt:
                       init_method = next((m for m in getattr(parent_stmt, "methods", []) if m.name == "init"), None)
                       if init_method:
                            init_class_name = parent_stmt.name
                            break
                       current_parent = parent_stmt.parent
                  else:
                       break

        params = []
        args = []
        if init_method:
             for param in init_method.parameters:
                 sname = self.sanitize_name(param.name)
                 params.append(f"ZenValue {sname}")
                 args.append(sname)
        
        param_str = ", ".join(params)
        arg_str = ", ".join(args)
        if arg_str: arg_str = ", " + arg_str

        name = self.get_mangled_name(statement)
        self.emit(f"ZenValue {name}_new({param_str}) {{")
        self.indent_level += 1
        self.emit(f"struct {name}* self = ZenRuntime_allocate(sizeof(struct {name}));")
        self.emit(f"memset(self, 0, sizeof(struct {name}));")
        if getattr(statement, "reflectable", False):
            bare = statement.name.replace("\\", "\\\\").replace('"', '\\"')
            self.emit(f'ZenReflect_tag_object(self, "{bare}");')

        # Call init if exists (potentially from parent)
        if init_method:
            if init_class_name == statement.name:
                 self.emit(f"{name}_init(self{arg_str});")
            else:
                  mangled_init_class = init_class_name
                  p_stmt = None
                  for s in self.program.statements:
                       if isinstance(s, (ClassStatement, ObjectStatement)) and s.name == init_class_name:
                            p_stmt = s
                            break
                       elif s.__class__.__name__ == "ScopeStatement":
                            for ss in s.body.statements:
                                 if isinstance(ss, (ClassStatement, ObjectStatement)) and ss.name == init_class_name:
                                      p_stmt = ss
                                      break
                            if p_stmt: break
                  
                  if p_stmt:
                       mangled_init_class = self.get_mangled_name(p_stmt)
                  self.emit(f"{mangled_init_class}_init(({mangled_init_class}*)self{arg_str});")
            
        self.emit("return ZenValue_from_object(self);")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

    def get_function_return_type(self, statement: FunctionStatement) -> str:
        # User main is a normal ZenValue function; C host main converts exit codes.
        if statement.name == "main":
            return "ZenValue"
        if (statement.name == "init" or 
            (statement.name.startswith("init_") and not "initialization" in statement.name)): 
            return "void"
        
        # All Zenlang functions return ZenValue by default in a boxed runtime
        return "ZenValue"

    def setup_global_functions(self, program: Program) -> None:
        for code in self.global_functions_code:
            self.emit(code)
        self.emit("")
        
        def process_functions(statements, prefix=""):
            for stmt in statements:
                actual_stmt = stmt
                if isinstance(stmt, ExportStatement) or stmt.__class__.__name__ == "ExportStatement":
                    actual_stmt = stmt.statement
                
                if isinstance(actual_stmt, FunctionStatement) and actual_stmt.name != "main":
                    self.global_functions.append(actual_stmt)
                    # We need to temporarily set current_scope for mangling
                    old_scope = self.current_scope
                    if prefix:
                        self.current_scope = prefix.rstrip("_")
                    self.generate_function_statement(actual_stmt)
                    self.current_scope = old_scope
                elif isinstance(actual_stmt, ScopeStatement):
                    new_prefix = f"{prefix}{actual_stmt.name}_"
                    process_functions(actual_stmt.body.statements if hasattr(actual_stmt.body, "statements") else actual_stmt.body, new_prefix)

        process_functions(program.statements)
        
        # Process Tasks
        for stmt in program.statements:
            actual_stmt = stmt
            if isinstance(stmt, ExportStatement) or stmt.__class__.__name__ == "ExportStatement":
                actual_stmt = stmt.statement
            if isinstance(actual_stmt, TaskStatement):
                self.generate_task_statement(actual_stmt)
        
        # Process lambdas collected during non-main generation
        self._flush_pending_lambdas()

        # User `main` as zen_user_main (callable entry), not C main
        for statement in program.statements:
            if isinstance(statement, ExportStatement) or statement.__class__.__name__ == "ExportStatement":
                statement = statement.statement
            if isinstance(statement, FunctionStatement) and statement.name == "main":
                self.global_functions.append(statement)
                self.generate_user_main_function(statement)

        # Lambdas discovered inside main (or nested during prior flush)
        self._flush_pending_lambdas()
        # Host main is emitted after class methods (see CodeGenerator.generate)

    def _flush_pending_lambdas(self) -> None:
        """Emit C functions for collected FunctionExpressions (closures)."""
        while getattr(self, "pending_lambdas", []):
             current_lambdas = self.pending_lambdas
             self.pending_lambdas = []
             for name, node in current_lambdas:
                  from Parser.AST import Identifier, ParameterLiteral
                  from Checker.Type import TypeVariant

                  captures = getattr(node, "_closure_captures", None) or []

                  # Prepend by-value captures as leading parameters so the body
                  # can reference them under their original names.
                  capture_params = []
                  for cap in captures:
                       capture_params.append(
                            ParameterLiteral(
                                 line=getattr(node, "line", 0) or 0,
                                 column=getattr(node, "column", 0) or 0,
                                 name=cap["name"],
                                 value=None,
                                 declared_type=TypeVariant(),
                                 type=None,
                            )
                       )
                  all_params = list(capture_params) + list(node.parameters or [])

                  # Lambda parameters must be level-0 so body identifiers match
                  # the C parameter names (not x_L3 nested-scope mangling).
                  param_names = set()
                  for p in all_params:
                       param_names.add(getattr(p, "name", None))
                       p.scope_level = 0
                       if hasattr(p, "symbol") and p.symbol is not None:
                            p.symbol.scope_level = 0

                  def _reset_param_levels(n, names=param_names):
                       if n is None:
                            return
                       if isinstance(n, Identifier) and n.name in names:
                            n.scope_level = 0
                            if hasattr(n, "symbol") and n.symbol is not None:
                                 n.symbol.scope_level = 0
                       if isinstance(n, list):
                            for item in n:
                                 _reset_param_levels(item, names)
                            return
                       # Nested lambdas handle their own captures; still rewrite
                       # identifiers that belong to *this* lambda's params.
                       if hasattr(n, "__dict__"):
                            for key, val in n.__dict__.items():
                                 if key.startswith("_"):
                                      continue
                                 _reset_param_levels(val, names)

                  _reset_param_levels(node.body)

                  # Create a FunctionStatement from FunctionExpression for generation
                  func_stmt = FunctionStatement(
                       scope_level=0,
                       name=name, 
                       parameters=all_params, 
                       body=node.body, 
                       return_type=node.return_type,
                       line=node.line, column=node.column
                  )
                  # Prototype already emitted via lambda_forward_decls when possible.
                  self.generate_function_statement(func_stmt)

    def generate_function_statement(self, statement: FunctionStatement):
        self.current_function = statement
        name = self.get_mangled_name(statement)
        params = self.generate_parameters(statement)
        rtype = self.get_function_return_type(statement)
        
        self.emit(f"{rtype} {name}({params}) {{")
        self.indent_level += 1
        
        # Track defer depth for cleanup
        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __func_defer_{temp_id} = ZenRuntime_get_defer_depth();")
        self.scope_defer_stack.append(f"__func_defer_{temp_id}")
        
        exit_label = f"__exit_{temp_id}"
        self.current_exit_label = exit_label
        if rtype != "void":
             if rtype == "int":
                  self.emit(f"{rtype} __ret_val = 0;")
             else:
                  self.emit(f"{rtype} __ret_val = ZEN_NOTHING_VAL;")
        
        # MIR Body Generation
        param_names = []
        for p in statement.parameters:
            p_name = self.sanitize_name(p.name)
            p_level = getattr(p, "scope_level", 0)
            if p_level > 0:
                p_name = f"{p_name}_L{p_level}"
            param_names.append(p_name)

        func_filename = getattr(statement, "filename", self.main_file)
        self.generate_lmir_block(statement, filename=func_filename, pre_allocated=param_names)
        
        # Final cleanup for function return falling through
        self.emit(f"{exit_label}:;")
        self.emit(f"ZenRuntime_defer_run_to(__func_defer_{temp_id});")
        self.scope_defer_stack.pop()
        
        # Ensure all non-void functions have a return statement
        if str(rtype) != "void":
             self.emit("return __ret_val;")

        self.indent_level -= 1
        self.emit("}")
        self.emit("")
        self.current_function = None

    def generate_task_statement(self, statement: TaskStatement):
        # Tasks are generated as normal functions for now, 
        # but with a prefix that the fiber system can use.
        self.current_function = statement
        name = self.get_mangled_name(statement)
        params = self.generate_parameters(statement)
        
        # Prototype
        self.emit(f"ZenValue {name}({params});")
        
        self.emit(f"ZenValue {name}({params}) {{")
        self.indent_level += 1
        
        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __task_defer_{temp_id} = ZenRuntime_get_defer_depth();")
        self.scope_defer_stack.append(f"__task_defer_{temp_id}")
        
        exit_label = f"__exit_{temp_id}"
        self.current_exit_label = exit_label
        self.emit(f"ZenValue __ret_val = ZEN_NOTHING_VAL;")
        
        param_names = [self.sanitize_name(p.name) for p in statement.parameters]
        task_filename = getattr(statement, "filename", self.main_file)
        self.generate_lmir_block(statement.body, filename=task_filename, pre_allocated=param_names)
        
        self.emit(f"{exit_label}:;")
        self.emit(f"ZenRuntime_defer_run_to(__task_defer_{temp_id});")
        self.scope_defer_stack.pop()
        self.emit("return __ret_val;")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

        # Generate the wrapper for ZenTask_spawn
        self.emit(f"ZenValue {name}_wrapper(ZenValue* args) {{")
        self.indent_level += 1
        arg_list = []
        for i in range(len(statement.parameters)):
            arg_list.append(f"args[{i}]")
        args_str = ", ".join(arg_list)
        self.emit(f"return {name}({args_str});")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

        self.current_function = None

    def emit_module_initialize(self) -> None:
        """Initialize built-in `module` map for the entry compilation unit."""
        import os

        file_path = self.main_file or ""
        if file_path and not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        directory = os.path.dirname(file_path) if file_path else ""
        base = os.path.basename(file_path) if file_path else ""
        if base.endswith(".zl") or base.endswith(".zs"):
            name = base.rsplit(".", 1)[0]
        else:
            name = base or "main"
        path = name

        def c_str(s: str) -> str:
            escaped = (
                s.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )
            return f'"{escaped}"'

        self.emit(
            f"ZenModule_initialize({c_str(name)}, {c_str(path)}, "
            f"{c_str(file_path)}, {c_str(directory)}, 1);"
        )

    def generate_user_main_function(self, statement: Any):
        """Emit user `function main` as zen_user_main (not C main)."""
        self.current_function = statement
        params = self.generate_parameters(statement)
        self.emit(f"ZenValue zen_user_main({params}) {{")
        self.indent_level += 1

        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __main_defer_{temp_id} = ZenRuntime_get_defer_depth();")
        self.scope_defer_stack.append(f"__main_defer_{temp_id}")

        exit_label = f"__exit_{temp_id}"
        self.current_exit_label = exit_label
        self.emit("ZenValue __ret_val = ZEN_NOTHING_VAL;")

        param_names = [p.name for p in statement.parameters]
        main_filename = getattr(statement, "filename", self.main_file)
        self.generate_lmir_block(statement.body, filename=main_filename, pre_allocated=param_names)

        self.emit(f"{exit_label}:;")
        self.emit(f"ZenRuntime_defer_run_to(__main_defer_{temp_id});")
        self.scope_defer_stack.pop()
        self.emit("return __ret_val;")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")
        self.current_function = None

    def generate_parameters(self, statement: FunctionStatement) -> str:
        c_parameters = []
        if not statement: return ""
        for parameter in statement.parameters:
            ctype = self.map_type(parameter.declared_type)
            name = self.get_mangled_name(parameter, should_prefix=False)
            c_parameters.append(f"{ctype} {name}")

        return ", ".join(c_parameters)

    def _collect_entry_callables(self, program: Program):
        """Entry-file top-level functions usable as module.entry (name → C symbol)."""
        entries = []  # list of (zen_name, c_name, n_params)
        seen = set()
        main_file = os.path.abspath(self.main_file) if self.main_file else None
        for stmt in program.statements:
            actual = stmt
            if isinstance(stmt, ExportStatement) or stmt.__class__.__name__ == "ExportStatement":
                actual = stmt.statement
            if not isinstance(actual, FunctionStatement) and actual.__class__.__name__ != "FunctionStatement":
                continue
            # Only process-entry file functions (not stdlib helpers)
            raw_fn = getattr(actual, "filename", None) or getattr(stmt, "filename", None)
            if main_file:
                if not raw_fn or os.path.abspath(raw_fn) != main_file:
                    continue
            name = actual.name
            if name in seen:
                continue
            seen.add(name)
            n_params = len(actual.parameters or [])
            if name == "main":
                entries.append(("main", "zen_user_main", n_params))
            else:
                c_name = self.get_mangled_name(actual)
                entries.append((name, c_name, n_params))
        return entries

    def generate_host_main(self, program: Program):
        """C main: runtime init, top-level side effects, module.entry / main dispatch."""
        from Parser.AST import (
            FunctionStatement as FS,
            ClassStatement,
            ObjectStatement,
            EnumeratorStatement,
            StructureStatement,
            ImportStatement,
            FromImportStatement,
            ScopeStatement,
            ExportStatement,
            TaskStatement,
            AssignmentStatement,
            ReassignmentStatement,
            MemberReassignmentStatement,
            Program as ProgramNode,
        )

        has_user_main = False
        user_main_params = 0
        for s in program.statements:
            actual = s.statement if (isinstance(s, ExportStatement) or s.__class__.__name__ == "ExportStatement") else s
            if isinstance(actual, FS) and actual.name == "main":
                has_user_main = True
                user_main_params = len(actual.parameters or [])
                break
        entry_callables = self._collect_entry_callables(program)

        self.emit("int main(int argc, char** argv) {")
        self.indent_level += 1
        self.emit("ZenValue __ret_val = ZEN_NOTHING_VAL;")
        self.emit("int base_defer = ZenRuntime_get_defer_depth();")
        self.emit("ZenRuntime_initialize();")
        self.emit("ZenSystem_initialize_arguments(argc, argv);")
        self.emit("init_singletons();")
        self.emit_module_initialize()

        temp_id = self.temp_counter
        self.temp_counter += 1
        exit_label = f"__exit_{temp_id}"
        self.current_exit_label = exit_label

        if hasattr(self, "global_initializers"):
            for init_code in self.global_initializers:
                self.emit(init_code)

        # Top-level side effects from the entry file only.
        # Lets / rebinds already ran in init_singletons — skip those.
        # Keep MemberReassignment (module.entry), control flow, expression stmts.
        # Match interpreter: skip orphans (filename None) from merged deps — they
        # can include spurious top-level main() calls.
        skip_types = (
            FS,
            ClassStatement,
            ObjectStatement,
            EnumeratorStatement,
            StructureStatement,
            ImportStatement,
            FromImportStatement,
            ScopeStatement,
            ExportStatement,
            TaskStatement,
            AssignmentStatement,
            ReassignmentStatement,
        )
        script_statements = []
        main_file = os.path.abspath(self.main_file) if self.main_file else None
        for stmt in program.statements:
            raw_fn = getattr(stmt, "filename", None)
            stmt_file = os.path.abspath(raw_fn) if raw_fn else None
            if main_file:
                if not stmt_file or stmt_file != main_file:
                    continue
            if isinstance(stmt, skip_types):
                continue
            # Also skip by class name (handles AST re-export mismatches)
            if getattr(stmt, "node_type", None) in (
                "FunctionStatement",
                "ClassStatement",
                "ObjectStatement",
                "EnumeratorStatement",
                "StructureStatement",
                "ImportStatement",
                "FromImportStatement",
                "ScopeStatement",
                "ExportStatement",
                "TaskStatement",
                "AssignmentStatement",
                "ReassignmentStatement",
            ) or stmt.__class__.__name__ in (
                "FunctionStatement",
                "ClassStatement",
                "ObjectStatement",
                "EnumeratorStatement",
                "StructureStatement",
                "ImportStatement",
                "FromImportStatement",
                "ScopeStatement",
                "ExportStatement",
                "TaskStatement",
                "AssignmentStatement",
                "ReassignmentStatement",
            ):
                continue
            script_statements.append(stmt)

        if script_statements:
            temp_node = ProgramNode(statements=script_statements)
            self.generate_lmir_block(temp_node, filename=self.main_file)

        # Resolve module.entry → call target; default to user main when present
        self.emit("{")
        self.indent_level += 1
        self.emit('ZenValue __entry_key = ZenValue_make_string("entry");')
        self.emit("ZenValue __entry = ZenValue_make_nothing();")
        self.emit(
            "if (module.type == ZEN_MAP && ZenMap_has_key(module, __entry_key).as.boolean) {"
        )
        self.emit("  __entry = ZenMap_get_value_at_key(module, __entry_key);")
        self.emit("}")
        self.emit("if (__entry.type == ZEN_FUNCTION) {")
        self.emit("  __ret_val = ZenValue_apply(__entry, 0);")
        self.emit("} else if (__entry.type == ZEN_STRING) {")
        self.emit("  const char* __en = ZenString_get_pointer(__entry);")
        self.emit("  int __entry_found = 0;")
        for zen_name, c_name, n_params in entry_callables:
            if n_params != 0:
                # Only zero-arg entry functions (main with argv is rare under -g)
                continue
            esc = zen_name.replace("\\", "\\\\").replace('"', '\\"')
            self.emit(f'  if (!__entry_found && __en && strcmp(__en, "{esc}") == 0) {{')
            self.emit(f"    __ret_val = {c_name}();")
            self.emit("    __entry_found = 1;")
            self.emit("  }")
        self.emit("  if (!__entry_found) {")
        self.emit(
            '    fprintf(stderr, "module.entry: unknown or non-zero-arity function \'%s\'\\n",'
        )
        self.emit('            __en ? __en : "?");')
        self.emit("  }")
        self.emit("} else {")
        if has_user_main:
            if user_main_params > 0:
                self.emit("  __ret_val = zen_user_main(ZenSystem_get_args());")
            else:
                self.emit("  __ret_val = zen_user_main();")
        else:
            # Script-only: top-level already ran; optional zen_entry
            self.emit("  /* no function main; top-level only */")
            has_zen_entry = any(
                isinstance(s, FS) and s.name == "zen_entry"
                for s in program.statements
            )
            if has_zen_entry:
                self.emit("  __ret_val = zen_entry();")
        self.emit("}")
        self.indent_level -= 1
        self.emit("}")

        self.emit(f"{exit_label}:;")
        self.emit("ZenRuntime_defer_run_to(base_defer);")
        self.emit(
            "return (__ret_val.type == ZEN_INTEGER) ? (int)__ret_val.as.integer : 0;"
        )
        self.indent_level -= 1
        self.emit("}")

    def generate_script_main(self, program: Program):
        """Backward-compat alias: host main always handles script entry."""
        self.generate_host_main(program)

    def generate_main_function_statement(self, statement: Any):
        """Backward-compat: emit user main body as zen_user_main only."""
        self.generate_user_main_function(statement)


