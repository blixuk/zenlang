import os
from typing import Union, Any, List
from Parser.AST import (
    StructureStatement,
    ClassStatement,
    ObjectStatement,
    EnumeratorStatement,
    FunctionStatement,
    ImportStatement,
    FromImportStatement,
    Program,
    AssignmentStatement,
    ReassignmentStatement,
    Identifier,
    ScopeStatement,
    ExportStatement
)
from Checker.Type import TypeStructure, TypeInteger, TypeDecimal, TypeBoolean, TypeString
from Transpiler.Handlers.ExpressionHandler import TOKEN_TYPE_IDS

class StructuralHandler:
    def setup_global_structures(self, program: Program) -> None:
        for statement in program.statements:
            if isinstance(statement, ExportStatement) or statement.__class__.__name__ == "ExportStatement":
                statement = statement.statement
            if isinstance(statement, StructureStatement):
                self.generate_structure_statement(statement)
            elif isinstance(statement, (ClassStatement, ObjectStatement)):
                self.generate_class_declaration(statement)
                if isinstance(statement, ObjectStatement):
                    self.singletons.append(statement)
            elif isinstance(statement, EnumeratorStatement):
                self.generate_enumerator_statement(statement)

    def generate_structure_statement(self, statement: StructureStatement):
        name = self.get_mangled_name(statement)
        # Track structures so field access can prefer map get_field when needed.
        if not hasattr(self, "global_structures"):
            self.global_structures = set()
        self.global_structures.add(name)

        # Keep a C struct typedef for documentation / sizeof; instances are maps
        # so native `obj.field` works without static types (ZenValue_get_field).
        self.emit(f"struct {name} {{")
        self.indent_level += 1
        for member in statement.members:
            m_name = self.sanitize_name(member.name)
            m_type = self.map_type(member.declared_type)
            self.emit(f"{m_type} {m_name};")
        self.indent_level -= 1
        self.emit("};")
        self.emit("")
        
        # Constructor — map-backed record; include `kind` so ECS/type checks work.
        params = []
        for member in statement.members:
            m_name = self.sanitize_name(member.name)
            m_type = self.map_type(member.declared_type)
            params.append(f"{m_type} {m_name}")
        params_str = ", ".join(params)
        self.emit(f"ZenValue {name}_new({params_str}) {{")
        self.indent_level += 1
        bare = statement.name  # unmangled type name for .kind
        n = len(statement.members) + 1  # + kind
        args = [f'ZenValue_make_string("kind")', f'ZenValue_make_string("{bare}")']
        for member in statement.members:
            m_name = self.sanitize_name(member.name)
            args.append(f'ZenValue_make_string("{m_name}")')
            args.append(m_name)
        args_joined = ", ".join(args)
        self.emit(f"return ZenMap_make_from_arguments({n}, {args_joined});")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

        # Register reflectable type metadata for zen.reflect
        if getattr(statement, "reflectable", False):
            field_names = [m.name for m in (statement.members or [])]
            self._emit_reflect_register(bare, field_names, [])

    def _emit_reflect_register(self, type_name: str, field_names: list, method_names: list) -> None:
        """Append registration into init_singletons for reflectable types."""
        def esc(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        lines = []
        lines.append("{")
        lines.append(f'  ZenValue __rf = ZenList_make_from_arguments(0);')
        for fn in field_names:
            lines.append(
                f'  ZenList_append_value(__rf, ZenValue_make_string("{esc(fn)}"));'
            )
        lines.append(f'  ZenValue __rm = ZenList_make_from_arguments(0);')
        for mn in method_names:
            lines.append(
                f'  ZenList_append_value(__rm, ZenValue_make_string("{esc(mn)}"));'
            )
        lines.append(
            f'  ZenReflect_register_type(ZenValue_make_string("{esc(type_name)}"), __rf, __rm);'
        )
        lines.append("}")
        if not hasattr(self, "init_singletons_code"):
            self.init_singletons_code = []
        self.init_singletons_code.extend(lines)

    def generate_class_declaration(self, statement: Union[ClassStatement, ObjectStatement]):
        name = self.get_mangled_name(statement)
        self.emit(f"struct {name} {{")
        self.indent_level += 1
        
        # Parent inheritance
        if getattr(statement, "parent", None):
             parent_name = statement.parent
             parent_mangled = self.sanitize_name(parent_name)
             p_stmt = None
             for s in self.program.statements:
                  if isinstance(s, (ClassStatement, ObjectStatement)) and s.name == parent_name:
                       p_stmt = s
                       break
                  elif s.__class__.__name__ == "ScopeStatement":
                       for ss in s.body.statements:
                            if isinstance(ss, (ClassStatement, ObjectStatement)) and ss.name == parent_name:
                                 p_stmt = ss
                                 break
                       if p_stmt: break
             
             if p_stmt:
                  parent_mangled = self.get_mangled_name(p_stmt)
             self.emit(f"struct {parent_mangled} base;")

        # Track types for boxing
        if not hasattr(self, "variable_types"): self.variable_types = {}
             
        for member in statement.members:
            if isinstance(member, FunctionStatement):
                continue
            m_name = self.sanitize_name(member.name)
            m_type = self.map_type(member.declared_type)
            self.emit(f"{m_type} {m_name};")
            self.variable_types[f"{name}.{member.name}"] = member.declared_type
            
        self.indent_level -= 1
        self.emit("};")
        self.emit("")

        if getattr(statement, "reflectable", False):
            field_names = []
            for member in getattr(statement, "members", []) or []:
                if isinstance(member, FunctionStatement):
                    continue
                field_names.append(getattr(member, "name", None) or "")
            field_names = [f for f in field_names if f]
            method_names = [
                m.name for m in (getattr(statement, "methods", None) or []) if getattr(m, "name", None)
            ]
            bare = statement.name
            self._emit_reflect_register(bare, field_names, method_names)

    def generate_enumerator_statement(self, statement: EnumeratorStatement):
        mangled_enum_name = self.get_mangled_name(statement)
        self.global_enums.add(mangled_enum_name)
        # 1. Generate the C enum typedef
        self.emit(f"typedef enum {mangled_enum_name} {{")
        self.indent_level += 1
        for i, variant in enumerate(statement.members):
            comma = "," if i < len(statement.members) - 1 else ""
            self.emit(f"{mangled_enum_name}_{variant.name}{comma}")
        self.indent_level -= 1
        self.emit(f"}} {mangled_enum_name};")
        self.emit("")

        # 2. Generate variant constructors/globals
        for variant in statement.members:
            if not variant.params:
                # Constant variant
                var_name = f"ZenVariant_{mangled_enum_name}_{variant.name}"
                self.emit(f"ZenValue {var_name} = {{ZEN_NOTHING, {{0}}}};")
                self.global_functions_code.append(f"// Constant variant {var_name} defined globally")
            else:
                # Parameterized variant: function constructor
                p_names = [f"p{i}" for i in range(len(variant.params))]
                p_list = ", ".join([f"ZenValue {p}" for p in p_names])
                func_name = f"ZenVariant_{mangled_enum_name}_{variant.name}"
                
                self.global_functions_code.append(f"ZenValue {func_name}({p_list}) {{\n"
                                                 f"    return ZenValue_make_variant(ZenValue_make_string(\"{statement.name}\"), ZenValue_make_string(\"{variant.name}\"), {len(variant.params)}, {', '.join(p_names)});\n"
                                                 f"}}\n")

    def emit_forward_declarations(self, program: Program) -> None:
        self.emit("// Forward Declarations")
        def process_forward_decls(statements, prefix=""):
            for statement in statements:
                actual_stmt = statement
                if isinstance(statement, ExportStatement) or statement.__class__.__name__ == "ExportStatement":
                    actual_stmt = statement.statement
                
                # print(f"DEBUG [ForwardDecl]: type={actual_stmt.__class__.__name__} name={getattr(actual_stmt, 'name', 'None')} prefix={prefix}")
                if isinstance(actual_stmt, ClassStatement):
                    name = self.get_mangled_name(actual_stmt)
                    self.emit(f"struct {name};")
                    self.emit(f"typedef struct {name} {name};")
                
                if isinstance(actual_stmt, EnumeratorStatement):
                    name = self.get_mangled_name(actual_stmt)
                    self.emit(f"typedef enum {name} {name};")
                    for variant in actual_stmt.members:
                         var_name = f"ZenVariant_{name}_{variant.name}"
                         if not variant.params:
                              self.emit(f"extern ZenValue {var_name};")
                         else:
                              p_list = ", ".join(["ZenValue" for _ in variant.params])
                              self.emit(f"ZenValue {var_name}({p_list});")
                
                if isinstance(actual_stmt, FunctionStatement):
                    # temporarily set current_scope for mangling
                    old_scope = self.current_scope
                    if prefix: self.current_scope = prefix.rstrip("_")
                    
                    params = self.generate_parameters(actual_stmt)
                    rtype = self.get_function_return_type(actual_stmt)
                    if actual_stmt.name == "main":
                        # User main is zen_user_main; C main is the host dispatcher
                        self.emit(f"ZenValue zen_user_main({params});")
                    else:
                        name = self.get_mangled_name(actual_stmt)
                        self.emit(f"{rtype} {name}({params});")
                    
                    self.current_scope = old_scope
                
                if actual_stmt.__class__.__name__ == "TaskStatement":
                    old_scope = self.current_scope
                    if prefix: self.current_scope = prefix.rstrip("_")
                    
                    params = self.generate_parameters(actual_stmt)
                    name = self.get_mangled_name(actual_stmt)
                    self.emit(f"ZenValue {name}({params});")
                    self.emit(f"ZenValue {name}_wrapper(ZenValue* args);")
                    
                    self.current_scope = old_scope
                
                if isinstance(actual_stmt, (ClassStatement, ObjectStatement)):
                    m_name = self.get_mangled_name(actual_stmt)
                    methods = getattr(actual_stmt, "methods", [])
                    members = getattr(actual_stmt, "members", [])
                    for m_list in (methods, members):
                        for member in m_list:
                            if isinstance(member, FunctionStatement):
                                method_name = f"{m_name}_{self.sanitize_name(member.name)}"
                                params_list = [f"{m_name}* self"]
                                for param in member.parameters:
                                    params_list.append(f"ZenValue {self.get_mangled_name(param, should_prefix=False)}")
                                param_str = ", ".join(params_list)
                                rtype = self.get_function_return_type(member)
                                self.emit(f"{rtype} {method_name}({param_str});")
                    
                    # Constructor prototype
                    init_method = next((m for m in methods if m.name == "init"), None)
                    c_params = []
                    if init_method:
                        for param in init_method.parameters:
                            c_params.append(f"ZenValue {self.get_mangled_name(param, should_prefix=False)}")
                    c_param_str = ", ".join(c_params)
                    self.emit(f"ZenValue {m_name}_new({c_param_str});")
                
                if isinstance(actual_stmt, ScopeStatement):
                    new_prefix = f"{prefix}{actual_stmt.name}_"
                    process_forward_decls(actual_stmt.body.statements if hasattr(actual_stmt.body, "statements") else actual_stmt.body, new_prefix)

        process_forward_decls(program.statements)
        self.emit()

    def setup_global_variables(self, program: Program) -> None:
        for statement in program.statements:
            if isinstance(statement, ExportStatement) or statement.__class__.__name__ == "ExportStatement":
                statement = statement.statement
            if isinstance(statement, ImportStatement):
                name = statement.alias if statement.alias else statement.name
                
                # Mangle global name with module name if not in main file
                import os
                if hasattr(statement, "filename") and statement.filename and self.main_file:
                     if os.path.abspath(statement.filename) != os.path.abspath(self.main_file):
                          module_name = os.path.basename(statement.filename).replace(".zl", "")
                          if module_name not in ("bootstrap_runtime"):
                               name = f"{module_name}_{name}"
                
                self.imported_modules.add(name)
                # Map alias to the real module name (last component of dotted or path import).
                # `import zen.io as IO` → io; `import `lib/zen/io` as IO` → io
                path_key = statement.path or ""
                if "/" in path_key:
                    real_module_name = path_key.rstrip("/").split("/")[-1]
                else:
                    real_module_name = path_key.split(".")[-1]
                # Prefer resolved file basename when available (matches function mangling).
                resolved = getattr(statement, "resolved_path", None) or getattr(statement, "filename", None)
                if resolved:
                    import os as _os
                    base = _os.path.basename(str(resolved)).replace(".zl", "")
                    if base and base not in ("bootstrap_runtime",):
                        real_module_name = base
                self.module_aliases[name] = real_module_name
                
                if name not in self.global_variable_names:
                     # self.emit(f"ZenValue {name} = {{ZEN_NOTHING, {{0}}}};")
                     self.global_variable_names.add(name)
                
            elif isinstance(statement, (AssignmentStatement, ReassignmentStatement)) and self.indent_level == 0:
                name = self.sanitize_name(statement.name)
                # Mangle with module name if not main file
                import os
                if hasattr(statement, "filename") and statement.filename and self.main_file:
                     if os.path.abspath(statement.filename) != os.path.abspath(self.main_file):
                          module_name = os.path.basename(statement.filename).replace(".zl", "")
                          if module_name not in ("bootstrap_runtime"):
                               name = f"{module_name}_{name}"
                
                if name not in self.global_variable_names:
                     self.emit(f"ZenValue {name} = {{ZEN_NOTHING, {{0}}}};")
                     self.global_variable_names.add(name)
                
                # Store the statement for later emission in init_singletons
                self.init_singletons_code.append(statement)
            elif isinstance(statement, ObjectStatement):
                name = self.get_mangled_name(statement)
                if name not in self.global_variable_names:
                     self.emit(f"ZenValue {name} = {{ZEN_NOTHING, {{0}}}};")
                     self.global_variable_names.add(name)
                
                # Store the statement for later emission in init_singletons
                self.init_singletons_code.append(statement)
            elif isinstance(statement, EnumeratorStatement):
                m_name = self.get_mangled_name(statement)
                for variant in statement.members:
                    if not variant.params:
                        var_name = f"ZenVariant_{m_name}_{variant.name}"
                        if var_name not in self.global_variable_names:
                            self.global_variable_names.add(var_name)
        
        # Recursively handle ScopeStatements
        from Parser.AST import ScopeStatement
        for statement in program.statements:
             if isinstance(statement, ScopeStatement):
                  self._setup_scope_recursive(statement)

    def _setup_scope_recursive(self, node: ScopeStatement, prefix: str = ""):
        scope_name = node.name
        self.imported_modules.add(scope_name)
        new_prefix = f"{prefix}{scope_name}_"
        
        for stmt in node.body.statements:
            if isinstance(stmt, ScopeStatement):
                self._setup_scope_recursive(stmt, new_prefix)
            elif isinstance(stmt, (AssignmentStatement, ReassignmentStatement)):
                name = self.sanitize_name(stmt.name)
                mangled_name = f"{new_prefix}{name}"
                
                if mangled_name not in self.global_variable_names:
                    self.emit(f"ZenValue {mangled_name} = {{ZEN_NOTHING, {{0}}}};")
                    self.global_variable_names.add(mangled_name)

                # Force init_singletons to write the global, not a local E_L1.
                stmt._force_c_name = mangled_name
                self.init_singletons_code.append(stmt)
            elif isinstance(stmt, EnumeratorStatement):
                m_name = f"{new_prefix}{stmt.name}"
                for variant in stmt.members:
                    if not variant.params:
                        var_name = f"ZenVariant_{m_name}_{variant.name}"
                        if var_name not in self.global_variable_names:
                            self.global_variable_names.add(var_name)

    def generate_init_singletons(self):
        self.emit("void init_singletons() {")
        self.indent_level += 1
        for obj in self.singletons:
            name = self.get_mangled_name(obj)
            self.emit(f"{name} = {name}_new();")
        
        # Enums initialization
        for stmt in self.program.statements:
             if isinstance(stmt, EnumeratorStatement):
                  m_name = self.get_mangled_name(stmt)
                  for variant in stmt.members:
                       if not variant.params:
                            var_name = f"ZenVariant_{m_name}_{variant.name}"
                            tid = TOKEN_TYPE_IDS.get(variant.name) if stmt.name == "TokenType" else None
                            if tid is not None:
                                self.emit(f"{var_name} = ZenValue_make_integer({tid}LL);")
                            else:
                                self.emit(f"{var_name} = ZenValue_make_variant(ZenValue_make_string(\"{stmt.name}\"), ZenValue_make_string(\"{variant.name}\"), 0);")
        
        for stmt in self.init_singletons_code:
            if isinstance(stmt, str):
                self.emit(stmt)
            else:
                # stmt is an ASTNode (Assignment or Reassignment)
                name = self.sanitize_name(stmt.name)
                # Handle module prefixing if needed
                if hasattr(stmt, "filename") and stmt.filename and self.main_file:
                     if os.path.abspath(stmt.filename) != os.path.abspath(self.main_file):
                          module_name = os.path.basename(stmt.filename).replace(".zl", "")
                          if module_name not in ("bootstrap_runtime"):
                               name = f"{module_name}_{name}"
                
                # We want to emit: name = expression;
                # We can use generate_lmir_block on the statement itself
                self.generate_lmir_block(stmt, filename=getattr(stmt, "filename", self.main_file))
            
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

    def scan_for_defers(self, node: Any, visited=None):
        if not node: return
        if visited is None: visited = set()
        node_id = id(node)
        if node_id in visited: return
        visited.add(node_id)

        from Parser.AST import DeferStatement
        if isinstance(node, DeferStatement):
            func_name = f"defer_block_{len(self.defer_prototypes)}"
            self.defer_prototypes.append(f"static void {func_name}(void* data);")
        
        if hasattr(node, "__dict__"):
            for val in node.__dict__.values():
                if isinstance(val, list):
                    for item in val: self.scan_for_defers(item, visited)
                elif hasattr(val, "__dict__"):
                    self.scan_for_defers(val, visited)
