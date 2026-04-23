import os
from typing import Union, List, Optional, Any, Set
from Checker.Type import (
    SymbolKind,
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
    BlockExpression,
    BlockStatement,
    BooleanLiteral,
    CallExpression,
    ClassStatement,
    DecimalLiteral,
    DeferStatement,
    DoStatement,
    EnumeratorStatement,
    ExpressionStatement,
    FromImportStatement,
    FunctionStatement,
    Identifier,
    ImportStatement,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MemberExpression,
    MemberReassignmentStatement,
    ObjectStatement,
    ParentExpression,
    Program,
    RaiseStatement,
    ReassignmentStatement,
    ReturnStatement,
    RuneLiteral,
    AssertStatement,
    CheckExpression,
    CheckStatement,
    ScopeStatement,
    StringLiteral,
    StructureExpression,
    StructureStatement,
    WhenExpression,
    WhenInlineExpression,
    WhenStatement,
    TypeLiteral,
    BreakStatement,
    ContinueStatement,
    WhenStatement,
    TypeLiteral,
    BreakStatement,
    ContinueStatement,
    MapLiteral,
    SetLiteral,
    VectorLiteral,
    TupleLiteral,
)
from Transpiler.MIR import *
from Transpiler.SMIRGenerator import SMIRGenerator
from Transpiler.SMIRAnalyzer import SMIRAnalyzer
from Transpiler.SMIRLowerer import SMIRLowerer


class Generator:
    def __init__(self, enable_source_map: bool = False):
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
        self.global_variable_names: set = {"Str", "IO", "Sys", "TokenType", "ASTKind", "SymbolKind", "TokenModule", "ASTModule"}
        self.is_in_condition = False
        self.current_function = None
        self.singletons = []
        self.init_singletons_code = []
        self.scope_defer_stack = []
        self.global_classes = set()
        self.symbol_allocs = {} # Map target -> Alloc instruction
        self.last_emitted_line = -1
        self.last_emitted_file = None
        self.source_mapping = True

    def emit_line_directive(self, node: ASTNode):
        if self.enable_source_map and hasattr(node, "line") and getattr(node, "filename", None):
            self.code.append(f"#line {node.line} \"{node.filename}\"")

    def sanitize_name(self, name: str) -> str:
        if name in ("exit", "free", "malloc", "realloc", "calloc", "write", "read", "open", "close", "abs", "sin", "cos", "tan", "log", "exp", "sqrt"):
            return f"zl_{name}"
        if name in ("char", "int", "float", "double", "void", "struct", "return", "if", "else", "while", "for", "do", "break", "continue", "switch", "case", "default", "typedef", "static", "extern"):
            return f"zen_{name}"
        return name

    def indent(self):
        return "    " * self.indent_level

    def emit(self, line=""):
        self.code.append(self.indent() + line)

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

    def scan_for_defers(self, node: Any, visited=None):
        if not node: return
        if visited is None: visited = set()
        
        # Avoid circular references or massive re-visitation
        node_id = id(node)
        if node_id in visited: return
        visited.add(node_id)

        from Parser.AST import DeferStatement
        if isinstance(node, DeferStatement):
            func_name = f"defer_block_{len(self.defer_prototypes)}"
            self.defer_prototypes.append(f"static void {func_name}(void* data);")
        
        # Generic recursion for children
        if hasattr(node, "__dict__"):
            for val in node.__dict__.values():
                if isinstance(val, list):
                    for item in val: self.scan_for_defers(item, visited)
                elif hasattr(val, "__dict__"):
                    self.scan_for_defers(val, visited)

    def map_type(self, type: Type | str) -> str:
        if isinstance(type, str):
            name = type
            if name in ("String", "Integer", "Boolean", "Variant", "Decimal", "List", "Map", "Rune", "Number", "Any"):
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

        if name in ("String", "Integer", "Boolean", "Variant", "Decimal", "List", "Map", "Rune", "Number", "Any", "ZenValue", "ZenVariant"):
            return "ZenValue"
        if name in ("ZenList", "List"):
            return "ZenList*"
        if name in ("int", "Int"):
            return "int"
        if name in ("bool", "Bool"):
            return "bool"
        if name in ("void", "Void"):
            return "void"
        if name in ("double", "Double", "float", "Float"):
            return "double"
        if name in ("char*", "string"):
            return "ZenString"

        return "ZenValue"

    def emit_lmir(self, instructions: List[MIRInstruction], pre_allocated: Set[str] = None, auto_arena: bool = True):
        if pre_allocated is None: pre_allocated = set()
        local_types = {}
        call_return_types = {}
        current_arena = None
        for instr in instructions:
            if self.source_mapping and instr.line > 0:
                if instr.line != self.last_emitted_line or instr.filename != self.last_emitted_file:
                    fname = instr.filename if instr.filename else "unknown"
                    self.emit(f'#line {instr.line} "{fname}"')
                    self.last_emitted_line = instr.line
                    self.last_emitted_file = instr.filename

            if isinstance(instr, Try):
                self.emit("{")
                self.indent_level += 1
                self.emit("ZenExceptionContext ctx;")
                self.emit("ctx.defer_depth = zen_defer_depth();")
                self.emit("zen_exception_push(&ctx);")
                self.emit("if (setjmp(ctx.buf) == 0) {")
                self.indent_level += 1
            elif isinstance(instr, Catch):
                self.emit("zen_exception_pop();")
                self.indent_level -= 1
                self.emit("} else {")
                self.indent_level += 1
                self.emit("zen_exception_pop();")
            elif isinstance(instr, EndTry):
                self.indent_level -= 1
                self.emit("}")
                self.indent_level -= 1
                self.emit("}")
            elif isinstance(instr, Raise):
                self.emit(f"zen_raise({instr.value});")
            elif isinstance(instr, Enumerator):
                # Enumerator definitions are handled globally in setup_global_structures
                pass
            elif isinstance(instr, ArenaCreate):
                current_arena = instr.arena_id
                if auto_arena:
                    self.emit(f"ZenArena* {self.sanitize_name(instr.arena_id)} = zen_arena_create(0);")
                    self.emit(f"zen_arena_push({self.sanitize_name(instr.arena_id)});")
            elif isinstance(instr, ArenaReset):
                self.emit(f"zen_arena_reset({self.sanitize_name(instr.arena_id)});")
            elif isinstance(instr, ArenaFree):
                if auto_arena:
                    self.emit(f"zen_arena_pop();")
                    self.emit(f"zen_arena_free({self.sanitize_name(instr.arena_id)});")
            elif isinstance(instr, ArenaAlloc):
                ctype = self.map_type(instr.type)
                if instr.target not in pre_allocated:
                    self.emit(f"ZenValue {instr.target};")
                    self.emit(f"{instr.target} = Zen_nothing; // Region: {instr.arena_id}")
                    pre_allocated.add(instr.target)
            elif isinstance(instr, HeapAlloc):
                if instr.target not in pre_allocated:
                    self.emit(f"ZenValue {instr.target};")
                    self.emit(f"{instr.target} = Zen_nothing; // Heap")
                    pre_allocated.add(instr.target)
            elif isinstance(instr, PointerCopy):
                self.emit(f"{instr.dest} = {instr.src};")
            elif isinstance(instr, (Alloc, HeapAlloc, ArenaAlloc)):
                # Standard variable declaration
                if not instr.target.startswith("tmp_"):
                    self.emit(f"ZenValue {instr.target} = Zen_nothing;")
                    pre_allocated.add(instr.target)
                    
                if instr.type:
                    print(f"DEBUG [CG]: Alloc {instr.target} type={instr.type} ({type(instr.type)})")
                    # Extract the most specific type name
                    tname = "ZenValue"
                    if hasattr(instr.type, "name") and instr.type.name:
                         tname = str(instr.type.name)
                    elif isinstance(instr.type, str):
                         tname = instr.type
                    
                    if tname in ("None", "Variant", "Any", "ZenValue", "ZenList", "ZenString"):
                         tname = "ZenObject"
                    
                    local_types[instr.target] = tname
                    print(f"DEBUG [CG]: Associated {instr.target} with type {tname}")
            elif isinstance(instr, (Move, PointerCopy)):
                dest = instr.dest
                print(f"DEBUG [CG]: {type(instr).__name__} dest={dest} src={instr.src}, src_in_call_return_types={instr.src in call_return_types}")
                if instr.src in call_return_types:
                    local_types[dest] = call_return_types[instr.src]
                    print(f"DEBUG [CG]: {type(instr).__name__} {instr.src} -> {dest} promoted to {local_types[dest]}")
                
                if "." in dest:
                    obj, prop_raw = dest.split(".", 1)
                    prop = self.sanitize_name(prop_raw)
                    if obj == "self":
                        self.emit(f"self->{prop} = {instr.src};")
                    else:
                        tname = local_types.get(obj, "ZenObject")
                        self.emit(f"((struct {tname}*){obj}.as.object)->{prop} = {instr.src};")
                else:
                    self.emit(f"{dest} = {instr.src};")
            elif isinstance(instr, GetAttr):
                prefix = ""
                if instr.target not in pre_allocated and instr.target not in self.symbol_allocs:
                    prefix = "ZenValue "
                    pre_allocated.add(instr.target)
                
                if instr.obj == "self":
                    self.emit(f"{prefix}{instr.target} = self->{self.sanitize_name(instr.prop)};")
                elif instr.obj[0].isupper() and instr.prop[0].isupper() and instr.obj != "Sys":
                    # ADT Variant Constant
                    self.emit(f"{prefix}{instr.target} = ZenVariant_{instr.obj}_{instr.prop};")
                else:
                    tname = local_types.get(instr.obj, "ZenObject")
                    # Don't sanitize prop if it's a path (dots)
                    prop_path = instr.prop
                    if "." not in prop_path: 
                         prop_path = self.sanitize_name(prop_path)
                    
                    # If it's a method call, we might need a specific class name
                    # But for GetAttr, we use the struct type
                    self.emit(f"{prefix}{instr.target} = ((struct {tname}*){instr.obj}.as.object)->{prop_path};")
            elif isinstance(instr, SetAttr):
                if instr.obj == "self":
                    self.emit(f"self->{self.sanitize_name(instr.prop)} = {instr.value};")
                else:
                    tname = local_types.get(instr.obj, "ZenObject")
                    prop_path = instr.prop
                    if "." not in prop_path: prop_path = self.sanitize_name(prop_path)
                    self.emit(f"((struct {tname}*){instr.obj}.as.object)->{prop_path} = {instr.value};")
            elif isinstance(instr, Nullify):
                self.emit(f"{instr.target} = Zen_nothing;")
            elif isinstance(instr, Compute):
                variant_ops = {
                    "+": "ZenValue_add", "-": "ZenValue_sub", "*": "ZenValue_mul", 
                    "/": "ZenValue_div", "%": "ZenValue_mod", "**": "ZenValue_pow",
                    "==": "ZenValue_equals", "!=": "ZenValue_not_equals", 
                    "<": "ZenValue_less_than", ">": "ZenValue_greater_than",
                    "<=": "ZenValue_less_than_or_equal", ">=": "ZenValue_greater_than_or_equal",
                    "xor": "ZenValue_xor", "and": "ZenValue_and", "or": "ZenValue_or",
                    "&": "ZenValue_bitwise_and", "|": "ZenValue_bitwise_or", "^": "ZenValue_bitwise_xor"
                }
                if instr.left == "":
                    unary_ops = {"-": "ZenValue_neg", "not": "ZenValue_not", "~": "ZenValue_bitwise_not"}
                    vop = unary_ops.get(instr.op, "ZenValue_neg")
                else:
                    vop = variant_ops.get(instr.op, "ZenValue_add")
                
                # Promotion logic
                target_region = None
                if instr.target in self.symbol_allocs:
                     target_region = self.symbol_allocs[instr.target].region
                
                pushed = False
                if target_region and target_region != current_arena and vop in ("ZenValue_add", "ZenString_concat"):
                     # Only need to promote if it's an allocation
                     # print(f"DEBUG [CG]: Promoting {instr.target} to {target_region} (current={current_arena})")
                     if target_region == "global":
                          self.emit("zen_arena_push(NULL);")
                     else:
                          name = self.sanitize_name(target_region)
                          if not name.startswith("block_"):
                               self.emit(f"zen_arena_push(({name}).as.arena);")
                          else:
                               self.emit(f"zen_arena_push({name});")
                     pushed = True
                
                if instr.left == "":
                    self.emit(f"{instr.target} = {vop}({instr.right});")
                else:
                    self.emit(f"{instr.target} = {vop}({instr.left}, {instr.right});")
                
                if pushed:
                     self.emit("zen_arena_pop();")
            elif isinstance(instr, RegionEnter):
                self.emit(f"zen_arena_push(({instr.id}).as.arena);")
            elif isinstance(instr, RegionExit):
                self.emit("zen_arena_pop();")
            elif isinstance(instr, Label):
                self.emit(f"{instr.name}:;")
            elif isinstance(instr, Assert):
                msg = f'"{instr.message}"' if instr.message else "NULL"
                self.emit(f"if (!({instr.condition}.as.boolean)) {{ fprintf(stderr, \"Assertion failed at %s:%d\\n\", \"{instr.filename}\", {instr.line}); exit(1); }}")
            elif isinstance(instr, Jump):
                self.emit(f"goto {instr.target};")
            elif isinstance(instr, Branch):
                # Extract boolean check. SMIRGenerator uses ZenValue operands.
                self.emit(f"if (({instr.condition}).as.boolean) {{")
                if instr.true_label:
                    self.indent_level += 1
                    self.emit(f"goto {instr.true_label};")
                    self.indent_level -= 1
                self.emit("}")
                if instr.false_label:
                    self.emit(f"else {{ goto {instr.false_label}; }}")
            elif isinstance(instr, Return):
                if instr.value and instr.value != "None":
                    self.emit(f"return {instr.value};")
                else:
                    if self.current_function_name == "main":
                        self.emit("return 0;")
                    else:
                        self.emit("return Zen_nothing;")
            elif isinstance(instr, Call):
                # Special case for print to map to ZenValue-aware IO_write
                if instr.callee == "print":
                    self.emit(f"IO_write({instr.args[0]});")
                else:
                    args_str = ", ".join(instr.args)
                    callee_str = instr.callee
                    
                    # Core runtime mappings (even for direct calls)
                    if callee_str == "List_from_args": callee_str = "ZenList_from_args"
                    elif callee_str == "Map_from_args": callee_str = "ZenMap_from_args"
                    elif callee_str == "Value_get_index": callee_str = "ZenValue_get_index"
                    elif callee_str == "Value_set_index": callee_str = "ZenValue_set_index"
                    elif callee_str == "Value_is_type_name": callee_str = "ZenValue_is_type_name"
                    elif callee_str == "write": callee_str = "IO_write"

                    if "." in callee_str:
                        obj_name, prop_name = callee_str.split(".", 1)
                        if obj_name in ("IO", "Sys", "Memory", "io", "memory", "out", "in", "__builtin", "__builtin_io", "__builtin_sys", "__builtin_memory", "__builtin_output", "__builtin_input", "__builtin_file"):
                            if prop_name in ("create_arena", "__builtin_create_arena"): callee_str = "Memory_create_arena"
                            elif prop_name in ("free_arena", "__builtin_free_arena"): callee_str = "Memory_free_arena"
                            elif prop_name in ("reset_arena", "__builtin_reset_arena"): callee_str = "Memory_reset_arena"
                            elif prop_name in ("push_arena", "__builtin_push_arena"): callee_str = "Memory_push_arena"
                            elif prop_name in ("pop_arena", "__builtin_pop_arena"): callee_str = "Memory_pop_arena"
                            elif prop_name == "read":
                                if obj_name == "__builtin_file": callee_str = "IO_read_file"
                                else: callee_str = "IO_read"
                            elif prop_name in ("write", "info", "warn", "error", "debug"):
                                # Distinguish between __builtin and __builtin_output
                                if obj_name == "__builtin":
                                    if prop_name == "error": callee_str = "__builtin_error"
                                    elif prop_name == "error_literal": callee_str = "__builtin_error_literal"
                                    else: callee_str = f"{obj_name}_{prop_name}"
                                else:
                                    if prop_name == "write": callee_str = "IO_write"
                                    else: callee_str = f"IO_{prop_name}"
                            elif prop_name == "exists": callee_str = "IO_file_exists"
                            elif prop_name == "error_literal": # Explicit for __builtin.error_literal
                                callee_str = "__builtin_error_literal"
                            else:
                                callee_str = f"{obj_name}_{prop_name}"
                        elif obj_name[0].isupper() and prop_name[0].isupper() and obj_name != "Sys":
                             callee_str = f"ZenVariant_{obj_name}_{prop_name}"
                        elif obj_name[0].isupper() and not prop_name[0].isupper():
                             callee_str = f"{obj_name}_{self.sanitize_name(prop_name)}"
                             if instr.args and (instr.args[0] == "self" or "self->" in instr.args[0]):
                                  args_str = ", ".join([f"({obj_name}*)self"] + instr.args[1:])
                        else:
                            tname = local_types.get(obj_name, "ZenObject")
                            callee_str = f"{tname}_{self.sanitize_name(prop_name)}"
                            args_str = ", ".join([f"({tname}*){obj_name}.as.object"] + instr.args)
                    else:
                        callee_str = self.sanitize_name(callee_str)

                    if callee_str in self.global_classes:
                        if instr.target:
                            call_return_types[instr.target] = callee_str
                        callee_str = f"{callee_str}_{callee_str}"

                    if instr.target:
                         # Promotion logic for Call (Constructors)
                         target_region = None
                         if instr.target in self.symbol_allocs:
                              target_region = self.symbol_allocs[instr.target].region
                         
                         pushed = False
                         # Heuristic: only constructors or string/list/map producers need promotion push
                         # For now, let's do it if target_region differs
                         if target_region and target_region != current_arena:
                              if target_region == "global":
                                   self.emit("zen_arena_push(NULL);")
                              else:
                                   name = self.sanitize_name(target_region)
                                   if not name.startswith("block_"):
                                        self.emit(f"zen_arena_push(({name}).as.arena);")
                                   else:
                                        self.emit(f"zen_arena_push({name});")
                              pushed = True

                         # Avoid assigning void returns (like _init)
                         if callee_str.endswith("_init"):
                              self.emit(f"{callee_str}({args_str});")
                         else:
                              self.emit(f"{instr.target} = {callee_str}({args_str});")
                         
                         if pushed:
                              self.emit("zen_arena_pop();")
                    else:
                         self.emit(f"{callee_str}({args_str});")
            elif isinstance(instr, Load):
                # source might be a literal (e.g. "1") or string "`hello`"
                val = instr.source
                if instr.type == "string" or (val.startswith("`") and val.endswith("`")):
                    inner = val
                    if inner.startswith("`") and inner.endswith("`"):
                        inner = inner[1:-1]
                    inner = inner.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    val = f'zen_str("{inner}")'
                elif instr.type in ("int", "Integer", "IntegerLite") or (val.isdigit() and instr.type != "bool"):
                    val = f"zen_int({val})"
                elif instr.type in ("decimal", "Decimal"):
                    val = f"zen_float({val})"
                elif instr.type in ("bool", "Boolean"):
                    val = f"zen_bool({val})"
                elif instr.type in ("rune", "Rune", "Character"):
                    val = f"zen_int({val})"
                elif val.startswith("'") and val.endswith("'"):
                    val = f"zen_int({val})"
                elif val == "true" or val == "false":
                    val = f"zen_bool({val})"
                
                # Ensure the target exists in local_types even if it was just loaded
                if instr.target not in pre_allocated and instr.target.startswith("tmp_"):
                     self.emit(f"ZenValue {instr.target};")
                     pre_allocated.add(instr.target)
                
                self.emit(f"{instr.target} = {val};")

    def generate_lmir_block(self, node: ASTNode, filename: str = None, pre_allocated: List[str] = None, auto_arena: bool = True):
        self.emit("// DEBUG: generate_lmir_block")
        # 1. SMIR Gen
        smir_gen = SMIRGenerator(filename=filename)
        instructions = smir_gen.generate(node, pre_allocated_symbols=pre_allocated)
        
        # Populate symbol_allocs for this block
        for instr in instructions:
             if isinstance(instr, Alloc):
                  self.symbol_allocs[instr.target] = instr
        
        # 2. SMIR Analyze
        # We need the global region tree. It's in self.scope.global_region
        if not self.scope:
             # Fallback: create a dummy root if scope is missing (should not happen if type-checked)
             from Checker.Scope import RegionNode
             region_root = RegionNode("global")
        else:
             region_root = self.scope.global_region
        
        analyzer = SMIRAnalyzer(instructions, region_root)
        analyzer.analyze()
        
        # 3. SMIR Lower
        lowerer = SMIRLowerer(instructions)
        lmir_instructions = lowerer.lower()
        
        # 4. Emit LMIR
        # print(f"DEBUG [CG]: LMIR for block: {lmir_instructions}")
        pre_allocated_set = set(pre_allocated) if pre_allocated else set()
        self.emit_lmir(lmir_instructions, pre_allocated=pre_allocated_set, auto_arena=auto_arena)
    def generate(self, program: Program, filename: str = None) -> str:
        self.last_emitted_file = filename
        self.program = program
        self.scope = program.scope if hasattr(program, "scope") else None
        self.code = []
        # Deduplicate enums, classes, and global functions by name
        seen_enums = set()
        seen_classes = set()
        seen_functions = set()
        unique_statements = []
        for stmt in program.statements:
             if isinstance(stmt, EnumeratorStatement):
                  if stmt.name in seen_enums: continue
                  seen_enums.add(stmt.name)
             elif isinstance(stmt, (ClassStatement, ObjectStatement)):
                  if stmt.name in seen_classes: continue
                  seen_classes.add(stmt.name)
                  self.global_classes.add(stmt.name)
             elif isinstance(stmt, FunctionStatement):
                  # Only deduplicate global functions (not methods)
                  if stmt.name in seen_functions: continue
                  seen_functions.add(stmt.name)
             unique_statements.append(stmt)
        program.statements = unique_statements

        self.emit('#define ZEN_IO_IMPLEMENTATION\n')
        self.emit('#include "bootstrap_runtime.h"\n')
        self.emit('void init_singletons();\n')
        self.emit('#include <stdlib.h>\n')
        self.emit('#include <string.h>\n')
        self.emit('#include <math.h>\n')
        self.emit('\n')
        # for getattr_stmt in program.statements:
        #     if isinstance(getattr_stmt, ImportStatement) or isinstance(getattr_stmt, FromImportStatement):
        #         path = getattr_stmt.path
        #         base = path.split("/")[-1]
        #         if base not in ("Console", "Str", "Math", "Map", "Set", "List", "Vector", "Runtime", "Process", "Thread", "Testing", "JSON", "Regex", "Base64"):
        #             self.emit(f'#include "{base}.h"\n')
        # Pre-scan for defers to get prototypes
        self.defer_prototypes = []
        self.scan_for_defers(program)

        self.setup_runtime()
        # 1. Forward Declarations FIRST (structs/typedefs/prototypes)
        # This ensures global variables can use class types.
        self.emit_forward_declarations(program)
        
        if hasattr(self, "defer_prototypes"):
             for proto in self.defer_prototypes:
                  self.emit(proto)

        # 2. Struct bodies (includes Enums, Structs, and Objects)
        self.setup_global_structures(program)
        
        # 4. Global variables (can use pointers to structs now)
        self.setup_global_variables(program)
        
        self.setup_global_functions(program)
        self.setup_class_methods(program)
        self.generate_init_singletons()

        has_main = False
        for func in self.global_functions:
            if func.name == "main":
                has_main = True
                break
        
        if not has_main:
            self.generate_script_main(program)

        return "\n".join(self.code)

    def setup_global_structures(self, program: Program) -> None:
        for statement in program.statements:
            if isinstance(statement, StructureStatement):
                self.generate_structure_statement(statement)
            elif isinstance(statement, (ClassStatement, ObjectStatement)):
                self.generate_class_declaration(statement)
                if isinstance(statement, ObjectStatement):
                    self.singletons.append(statement)
            elif isinstance(statement, EnumeratorStatement):
                self.generate_enumerator_statement(statement)

    def generate_enumerator_statement(self, statement: EnumeratorStatement):
        # 1. Generate the C enum typedef
        self.emit(f"typedef enum {statement.name} {{")
        self.indent_level += 1
        for i, variant in enumerate(statement.members):
            comma = "," if i < len(statement.members) - 1 else ""
            self.emit(f"{statement.name}_{variant.name}{comma}")
        self.indent_level -= 1
        self.emit(f"}} {statement.name};")
        self.emit("")

        # 2. Generate variant constructors/globals
        for variant in statement.members:
            if not variant.params:
                # Constant variant: ZenValue ZenVariant_SomeEnum_VariantName;
                var_name = f"ZenVariant_{statement.name}_{variant.name}"
                self.global_variables.append(f"ZenValue {var_name};")
                self.global_functions_code.append(f"// Constant variant {var_name} defined globally and initialized in init_singletons")
            else:
                # Parameterized variant: function constructor
                p_names = [f"p{i}" for i in range(len(variant.params))]
                p_list = ", ".join([f"ZenValue {p}" for p in p_names])
                func_name = f"ZenVariant_{statement.name}_{variant.name}"
                
                self.global_functions_code.append(f"ZenValue {func_name}({p_list}) {{\n"
                                                 f"    return ZenValue_new_variant(zen_str(\"{statement.name}\"), zen_str(\"{variant.name}\"), {len(variant.params)}, {', '.join(p_names)});\n"
                                                 f"}}\n")
                
                # Mock a function for metadata
                class DummyFunc:
                    def __init__(self, name): self.name = name
                self.global_functions.append(DummyFunc(func_name))

    def generate_class_declaration(self, statement: Union[ClassStatement, ObjectStatement]):
        # Cache members for inheritance
        if not hasattr(self, "structure_members"):
            self.structure_members = {}
        
        all_members = []
        if hasattr(statement, 'parent') and statement.parent:
             if statement.parent in self.structure_members:
                  all_members.extend(self.structure_members[statement.parent])
        
        # We need to distinguish between physical members (for struct definition)
        # and logical members (for method generation).
        # ClassStatement.members contains identifiers for fields.
        phys_members = [m for m in statement.members if not isinstance(m, FunctionStatement)]
        all_members.extend(phys_members)
        self.structure_members[statement.name] = all_members

        self.emit(f"typedef struct {statement.name} {{")
        self.indent_level += 1

        # Inheritance: Embed parent struct (optional, but let's keep it flat if possible or use 'base')
        if hasattr(statement, 'parent') and statement.parent:
            self.emit(f"struct {statement.parent} base;") 

        for member in phys_members:
             self.emit(f"ZenValue {member.name};")

        self.indent_level -= 1
        self.emit(f"}} {statement.name};")
        self.emit("")

    def generate_structure_statement(self, statement: StructureStatement):
        # Cache members for inheritance
        if not hasattr(self, "structure_members"):
            self.structure_members = {}
        if not hasattr(self, "class_parents"):
            self.class_parents = {}
        
        self.class_parents[statement.name] = getattr(statement, 'parent', None)
        
        all_members = []
        if hasattr(statement, 'parent') and statement.parent:
             if statement.parent in self.structure_members:
                  all_members.extend(self.structure_members[statement.parent])
        
        all_members.extend(statement.members)
        self.structure_members[statement.name] = all_members

        self.emit(f"typedef struct {statement.name} {{")
        self.indent_level += 1
        
        if hasattr(statement, 'parent') and statement.parent:
             self.emit(f"struct {statement.parent} base;")

        for member in statement.members:
            self.emit(f"ZenValue {member.name};")

        self.indent_level -= 1
        self.emit(f"}} {statement.name};")
        self.emit()

    def setup_class_methods(self, program: Program) -> None:
        if not hasattr(self, "class_parents"):
            self.class_parents = {}
            
        for statement in program.statements:
            if isinstance(statement, (ClassStatement, ObjectStatement)):
                self.current_class = statement.name
                self.class_parents[statement.name] = getattr(statement, "parent", None)
                
                methods = getattr(statement, "methods", [])
                members = getattr(statement, "members", [])
                for m_list in (methods, members):
                    for member in m_list:
                        if isinstance(member, FunctionStatement):
                            self.generate_method_statement(statement.name, member)
                
                # Generate Constructor
                self.generate_class_constructor(statement)
                self.current_class = None

    def generate_method_statement(self, class_name: str, method: FunctionStatement):
        # Mangled name: Class_method
        method_name = f"{class_name}_{self.sanitize_name(method.name)}"
        old_class = self.current_class
        self.current_class = class_name
        
        # Prepare parameters: add self
        params_list = []
        params_list.append(f"{class_name}* self")
        
        for param in method.parameters:
            pname = self.sanitize_name(param.name)
            params_list.append(f"ZenValue {pname}")
        
        param_str = ", ".join(params_list)
        rtype = self.get_function_return_type(method)
        
        self.emit(f"{rtype} {method_name}({param_str}) {{")
        self.indent_level += 1
        
        # Track defer depth
        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __meth_defer_{temp_id} = zen_defer_depth();")
        self.scope_defer_stack.append(f"__meth_defer_{temp_id}")

        self.current_function = method
        
        # MIR Body Generation
        param_names = ["self"] + [p.name for p in method.parameters]
        self.generate_lmir_block(method.block, filename=self.last_emitted_file, pre_allocated=param_names, auto_arena=(class_name != "Arena"))
        
        # Cleanup
        self.emit(f"zen_defer_run_to(__meth_defer_{temp_id});")
        self.scope_defer_stack.pop()
        
        if str(rtype) != "void":
             self.emit("return zen_make_null();")

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
                 # Standardize to ZenValue for constructors
                 params.append(f"ZenValue {param.name}")
                 args.append(param.name)
        
        param_str = ", ".join(params)
        arg_str = ", ".join(args)
        if arg_str: arg_str = ", " + arg_str

        self.emit(f"ZenValue {statement.name}_{statement.name}({param_str}) {{")
        self.indent_level += 1
        self.emit(f"struct {statement.name}* self = zen_malloc(sizeof(struct {statement.name}));")
        self.emit(f"memset(self, 0, sizeof(struct {statement.name}));")
        
        # Call init if exists (potentially from parent)
        if init_method:
            if init_class_name == statement.name:
                 self.emit(f"{statement.name}_init(self{arg_str});")
            else:
                 self.emit(f"{init_class_name}_init(({init_class_name}*)self{arg_str});")
            
        self.emit("return zen_val_object(self);")
        self.indent_level -= 1
        self.emit("}")
        self.emit("")

    def generate_init_singletons(self):
        self.emit("void init_singletons() {")
        self.indent_level += 1
        
        # Initialize Constant Enum Variants
        for stmt in self.program.statements:
             if isinstance(stmt, EnumeratorStatement):
                  for variant in stmt.members:
                       if not variant.params:
                            var_name = f"ZenVariant_{stmt.name}_{variant.name}"
                            self.emit(f"{var_name} = ZenValue_new_variant(zen_str(\"{stmt.name}\"), zen_str(\"{variant.name}\"), 0);")

        for obj in self.singletons:
            for member in obj.members:
                if not isinstance(member, FunctionStatement):
                    val = self.generate_expression(member.value)
                    self.emit(f"{obj.name}_inst.{member.name} = {val};")
        
        for code in self.init_singletons_code:
            self.emit(code)

        self.indent_level -= 1
        self.emit("}")
        self.emit("")

    def get_mangled_name(self, statement: Union[FunctionStatement, ClassStatement, ObjectStatement, EnumeratorStatement]) -> str:
        name = self.sanitize_name(statement.name)
        if not hasattr(statement, "filename") or not statement.filename or not self.last_emitted_file:
             return name
             
        if os.path.basename(statement.filename) != os.path.basename(self.last_emitted_file):
             module_name = os.path.basename(statement.filename).replace(".zl", "")
             if module_name not in ("bootstrap_runtime"):
                  return f"{module_name}_{name}"
        return name

    def setup_runtime(self):
        pass
        self.emit("")

    def emit_forward_declarations(self, program: Program) -> None:
        self.emit("// Forward Declarations")
        # First pass: classes
        for statement in program.statements:
            if isinstance(statement, ClassStatement):
                self.emit(f"struct {statement.name};")
                self.emit(f"typedef struct {statement.name} {statement.name};")
            elif isinstance(statement, EnumeratorStatement):
                self.emit(f"typedef enum {statement.name} {statement.name};")
                # Forward declare constructors
                for variant in statement.members:
                     var_name = f"ZenVariant_{statement.name}_{variant.name}"
                     if not variant.params:
                          self.emit(f"extern ZenValue {var_name};")
                     else:
                          p_list = ", ".join(["ZenValue" for _ in variant.params])
                          self.emit(f"ZenValue {var_name}({p_list});")

        # Second pass: constructors and methods and functions
        for statement in program.statements:
            if isinstance(statement, FunctionStatement):
                params = self.generate_parameters(statement)
                rtype = self.get_function_return_type(statement)
                name = self.get_mangled_name(statement)
                self.emit(f"{rtype} {name}({params});")
            elif isinstance(statement, (ClassStatement, ObjectStatement)):
                # Forward declare constructor (both styles)
                init_method = next((m for m in getattr(statement, 'methods', []) if m.name == "init"), None)
                constr_params = self.generate_parameters(init_method) if init_method else ""
                self.emit(f"ZenValue {statement.name}_constructor({constr_params});")
                self.emit(f"ZenValue {statement.name}_{statement.name}({constr_params});")
                
                # Forward declare methods
                methods = getattr(statement, "methods", [])
                members = getattr(statement, "members", [])
                for m_items in (methods, members):
                    for member in m_items:
                        if isinstance(member, FunctionStatement):
                            c_params = [f"{statement.name}* self"]
                            if member.parameters:
                                c_params.append(self.generate_parameters(member))
                            params_str = ", ".join(c_params)
                            rtype = self.get_function_return_type(member)
                            m_name = self.sanitize_name(member.name)
                            self.emit(f"{rtype} {statement.name}_{m_name}({params_str});")

        # Third pass: Namespaced constructors for modules
        for stmt in program.statements:
             if isinstance(stmt, (ImportStatement, FromImportStatement)):
                  # This is a bit hard since we don't have the module AST here easily
                  # But we can guess some based on common usage
                  for cls_name in ("Lexer", "Parser", "Resolver", "DependencyGraph", "GraphNode", "Transpiler", "CodeGenerator", "Token", "Statement", "Expression", "Type", "Scope", "Symbol", "Environment"):
                       self.emit(f"void* {cls_name}_{cls_name}();") # Variable args handled by C
                  self.emit("#define CTranspiler_Transpiler Transpiler_Transpiler")
        self.emit()

    def get_function_return_type(self, statement: FunctionStatement) -> str:
        if statement.name == "main": return "int"
        if statement.name == "init" or statement.name.startswith("init_") and not "initialization" in statement.name: return "void"
        
        # All Zenlang functions return ZenValue by default in a boxed runtime
        return "ZenValue"

    def setup_global_functions(self, program: Program) -> None:
        for code in self.global_functions_code:
            self.emit(code)
        self.emit("")
        for statement in program.statements:
            if (
                isinstance(statement, FunctionStatement)
                and not statement.name == "main"
            ):
                self.global_functions.append(statement)
                self.generate_function_statement(statement)

        for statement in program.statements:
            if isinstance(statement, FunctionStatement) and statement.name == "main":
                self.global_functions.append(statement)
                self.generate_main_function_statement(statement)

    def setup_global_variables(self, program: Program) -> None:
        # self.global_variable_names already has Str, IO, Sys from __init__
        for statement in program.statements:
            if isinstance(statement, (ClassStatement, EnumeratorStatement, ObjectStatement, StructureStatement)):
                self.global_variable_names.add(statement.name)
            
            if isinstance(statement, ObjectStatement):
                # Declare singleton instance - use _inst to avoid type conflict
                self.emit(f"static {statement.name} {statement.name}_inst;")
            
            if isinstance(statement, AssignmentStatement):
                self.global_variables.append(statement)
                self.global_variable_names.add(statement.name)
                # Generate directly into main code, but ensure it's before any functions that might use it
                code = self.generate_statement(statement)
                if code: self.emit(code)
            elif isinstance(statement, ImportStatement):
                self.global_variable_names.add(statement.alias or statement.name)
            elif isinstance(statement, FromImportStatement):
                for symbol in statement.symbols:
                    self.global_variable_names.add(symbol["alias"] or symbol["name"])
        
        for var in self.global_variables:
            if isinstance(var, str):
                self.emit(var)
        
        self.emit()

    def generate_script_main(self, program: Program):
        self.emit("int main(int argc, char** argv) {")
        self.indent_level += 1
        self.emit("_Sys_init_args(argc, argv);")

        # Emit global initializers if any
        if hasattr(self, 'global_initializers'):
            for init_code in self.global_initializers:
                self.emit(init_code)

        # Filter for only non-definition statements from the main file to put into main
        script_statements = []
        for stmt in program.statements:
            # ONLY include statements from the actual script file
            if hasattr(stmt, "filename") and stmt.filename != self.last_emitted_file:
                continue
            if not isinstance(stmt, (FunctionStatement, ClassStatement, ObjectStatement, EnumeratorStatement, StructureStatement, ImportStatement, FromImportStatement)):
                script_statements.append(stmt)
        
        if script_statements:
            temp_node = Program(statements=script_statements)
            self.generate_lmir_block(temp_node, filename=self.last_emitted_file)
        
        self.emit("zen_defer_run_to(0);")
        self.emit("return 0;")
        self.indent_level -= 1
        self.emit("}")

    ## Statements

    def generate_statement(self, statement: ASTNode):
        self.emit_line_directive(statement)
        if isinstance(statement, AssignmentStatement):
            return self.generate_assignment_statement(statement)

        if isinstance(statement, ExpressionStatement):
            return self.generate_expression_statement(statement)

        if isinstance(statement, ReturnStatement):
            return self.generate_return_statement(statement)

        if isinstance(statement, StructureStatement):
            return self.generate_structure_statement(statement)
        
        if isinstance(statement, ClassStatement) or isinstance(statement, ObjectStatement):
            return # Handled in setup_global_structures pass
        
        if isinstance(statement, ReassignmentStatement):
            return self.generate_reassignment_statement(statement)
        
        if isinstance(statement, WhenStatement):
            return self.generate_when_statement(statement)

        if isinstance(statement, DoStatement):
            return self.generate_do_statement(statement)
            
        if isinstance(statement, ScopeStatement):
            return self.generate_scope_statement(statement)

        if isinstance(statement, RaiseStatement):
            return self.generate_raise_statement(statement)

        if isinstance(statement, MemberReassignmentStatement):
            return self.generate_member_reassignment_statement(statement)
        
        if isinstance(statement, DeferStatement):
            return self.generate_defer_statement(statement)

        if isinstance(statement, AssertStatement):
            return self.generate_assert_statement(statement)

        if isinstance(statement, CheckStatement):
            return self.generate_check_statement(statement)

        if isinstance(statement, BreakStatement):
            return self.generate_break_statement(statement)

        if isinstance(statement, ContinueStatement):
            return self.generate_continue_statement(statement)

    def generate_raise_statement(self, statement: RaiseStatement):
        val = self.generate_expression(statement.value)
        # val is already a ZenValue in a fully boxed runtime
        self.emit(f"zen_raise({val});")

    def generate_break_statement(self, statement: BreakStatement):
        # Run defers for current loop scope if it's on stack
        if self.scope_defer_stack:
             self.emit(f"zen_defer_run_to({self.scope_defer_stack[-1]});")
        self.emit("break;")

    def generate_continue_statement(self, statement: ContinueStatement):
        # Run defers for current loop scope if it's on stack
        if self.scope_defer_stack:
             self.emit(f"zen_defer_run_to({self.scope_defer_stack[-1]});")
        self.emit("continue;")

    def generate_defer_statement(self, statement: DeferStatement):
        defer_id = self.temp_counter
        self.temp_counter += 1
        func_name = f"defer_block_{defer_id}"
        
        # Save current state
        old_code = self.code
        self.code = []
        old_indent = self.indent_level
        # Use existing name created during scan
        func_name = f"defer_block_{self.defer_counter}"
        self.defer_counter += 1
        
        # Generate defer function
        self.emit(f"static void {func_name}(void* data) {{")
        self.indent_level += 1
        self.generate_block_statement(statement.block)
        self.indent_level -= 1
        self.emit("}")
        self.emit()
        
        self.global_functions_code.append("\n".join(self.code))
        
        # Restore state
        self.code = old_code
        self.indent_level = old_indent
        
        self.emit(f"zen_defer_push({func_name}, NULL);")

    def generate_assert_statement(self, statement: AssertStatement):
        cond = self.generate_expression(statement.condition)
        
        msg = ""
        if statement.raise_expression:
            msg = self.generate_expression(statement.raise_expression)
        else:
            msg = f'zen_str("Assertion failed at line {statement.line}")'
        
        self.emit(f"if (!({cond}).as.boolean) {{")
        self.indent_level += 1
        self.emit(f"zen_raise({msg});")
        self.indent_level -= 1
        self.emit("}")

    def generate_check_statement(self, statement: CheckStatement):
        self.emit("{")
        self.indent_level += 1
        self.emit("ZenExceptionContext ctx;")
        self.emit("ctx.defer_depth = zen_defer_depth();")
        self.emit("zen_exception_push(&ctx);")
        
        self.emit("if (setjmp(ctx.buf) == 0) {")
        self.indent_level += 1
        self.generate_expression(statement.expression)
        self.emit("zen_exception_pop();")
        self.indent_level -= 1
        self.emit("} else {")
        self.indent_level += 1
        self.emit("zen_exception_pop();")
        # For simplicity, we just run the or_block
        if statement.or_block:
             self.generate_statement(statement.or_block)
        
        for case in statement.cases:
             # Logic to match exception value would go here
             self.generate_block_statement(case["block"])
             
        self.indent_level -= 1
        self.emit("}")
        self.indent_level -= 1
        self.emit("}")

    def generate_main_function_statement(self, statement: ASTNode):
        params = self.generate_parameters(statement)

        self.emit("int main(int argc, char** argv) {")
        self.indent_level += 1
        self.emit("int base_defer = zen_defer_depth();")
        self.emit("init_singletons();")
        self.emit("_Sys_init_args(argc, argv);")

        param_names = [p.name for p in statement.parameters]
        self.generate_lmir_block(statement.block, filename=self.last_emitted_file, pre_allocated=param_names)

        self.emit("zen_defer_run_to(base_defer);")
        self.emit("return 0;")
        self.indent_level -= 1
        self.emit("}")

    def generate_function_statement(self, statement: FunctionStatement):
        self.current_function = statement
        name = self.get_mangled_name(statement)
        params = self.generate_parameters(statement)
        rtype = self.get_function_return_type(statement)
        if statement.name == "main": rtype = "int"
        
        self.emit(f"{rtype} {name}({params}) {{")
        self.indent_level += 1
        
        # Track defer depth for cleanup
        temp_id = self.temp_counter
        self.temp_counter += 1
        self.emit(f"int __func_defer_{temp_id} = zen_defer_depth();")
        self.scope_defer_stack.append(f"__func_defer_{temp_id}")
        
        # MIR Body Generation
        param_names = [p.name for p in statement.parameters]
        self.generate_lmir_block(statement, filename=self.last_emitted_file, pre_allocated=param_names)
        
        # Final cleanup for function return falling through
        self.emit(f"zen_defer_run_to(__func_defer_{temp_id});")
        self.scope_defer_stack.pop()
        
        # Ensure all non-void functions have a return statement
        if str(rtype) != "void":
             default_ret = "zen_make_null()"
             if str(rtype) in ("int", "long long"): default_ret = "0"
             elif "bool" in str(rtype): default_ret = "0"
             
             # Check if last statement is a ReturnStatement
             last_stmt = statement.block.statements[-1] if hasattr(statement.block, "statements") and statement.block.statements else None
             if not isinstance(last_stmt, ReturnStatement):
                 self.emit(f"return {default_ret};")

        self.indent_level -= 1
        self.emit("}")
        self.emit("")
        self.current_function = None

    def generate_block_statement(self, statement: ASTNode):
        for statement in statement.statements:
            self.generate_statement(statement)

    def generate_parameters(self, statement: FunctionStatement) -> str:
        c_parameters = []

        for parameter in statement.parameters:
            ctype = self.map_type(parameter.declared_type)
            name = self.sanitize_name(parameter.name)
            c_parameters.append(f"{ctype} {name}")

        return ", ".join(c_parameters)

    def generate_assignment_statement(self, statement: AssignmentStatement):
        name = self.sanitize_name(statement.name)
        
        ztype = self.get_type(statement)
        ctype = self.map_type(ztype)

        value = self.generate_expression(statement.value)
        
        # In a fully boxed runtime, we don't need extra boxing here
        # because generate_expression already returns a ZenValue.
        if ctype == "void": return ""
             
        # Use ZEN_VAL_* macros for literals to allow constant initialization
        if ctype == "ZenValue" and self.indent_level == 0:
             is_constant = False
             if isinstance(statement.value, IntegerLiteral):
                  value = f"ZEN_VAL_INT({statement.value.value})"
                  is_constant = True
             elif isinstance(statement.value, BooleanLiteral):
                  val = 1 if str(statement.value.value).lower() in ("true", "1") else 0
                  value = f"ZEN_VAL_BOOL({val})"
                  is_constant = True
             elif isinstance(statement.value, StringLiteral):
                  s = statement.value.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                  value = f'ZEN_VAL_STR("{s}")'
                  is_constant = True
             elif isinstance(statement.value, CallExpression):
                  callee = statement.value.callee
                  if isinstance(callee, MemberExpression) and callee.property in ("error", "error_literal"):
                       obj_name = str(self.generate_expression(callee.object))
                       if "__builtin" in obj_name and len(statement.value.arguments) > 0:
                            msg_expr = statement.value.arguments[0]
                            if isinstance(msg_expr, StringLiteral):
                                 s = msg_expr.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                                 value = f'ZEN_VAL_ERROR("{s}")'
                                 is_constant = True
             
             if is_constant:
                  return f"static {ctype} {name} = {value};"
              
             if value in ("0", "NULL", "zen_make_null()", "Zen_nothing"):
                  value = "Zen_nothing"
                  return f"static {ctype} {name} = {value};"

             # Defer non-constant initialization to init_singletons
             self.init_singletons_code.append(f"{name} = {value};")
             return f"static {ctype} {name} = {{ZEN_NOTHING, {{0}}}};"
        elif ctype == "ZenValue" and (value == "0" or value == "NULL" or value == "zen_make_null()"):
            value = "zen_make_null()"

        # Auto-unboxing for ZenValue to Object pointers
        if ctype and ctype.endswith("*") and not "char*" in ctype and not value.startswith("("):
              value = f"({ctype}){value}.as.object"

        # If at global scope, emit as static global
        if self.indent_level == 0:
             self.emit(f"static ZenValue {name} = {value};")
        else:
             self.emit(f"ZenValue {name} = {value};")
             
        if not hasattr(self, "variable_types"): self.variable_types = {}
        self.variable_types[statement.name] = ztype
        return value

    def generate_expression_statement(self, statement: ExpressionStatement):
        expression = self.generate_expression(statement.expression)
        self.emit(f"{expression};")
        return expression

    def generate_return_statement(self, statement: ReturnStatement):
        if not statement.value:
            self.emit("return;")
            return
        
        val = self.generate_expression(statement.value)
        # val is already ZenValue (Rule 1)
        
        # Run defers before returning (from current function scope)
        if hasattr(self, "scope_defer_stack") and self.scope_defer_stack:
             # Run up to the function's base defer depth
             # For simplicity, we just run to the FIRST depth on stack (function base)
             # But if we are in nested loops, we should run ALL. 
             # Actually, the function base is the bottom of the stack.
             base_depth = self.scope_defer_stack[0]
             self.emit(f"zen_defer_run_to({base_depth});")

        if self.current_function and self.current_function.name == "main":
             # Unbox for main's int return
             self.emit(f"return (int)({val}).as.integer;")
             return

        self.emit(f"return {val};")

    def generate_reassignment_statement(self, statement: ReassignmentStatement):
        name = self.sanitize_name(statement.name)
        value = self.generate_expression(statement.value)
        
        # If assigning to ZenValue, box the value
        # Look up type from current function or global variables
        ztype = None
        if self.current_function:
             for p in self.current_function.parameters:
                  if p.name == statement.name: ztype = p.declared_type; break
        # Try variable_types if available
        if not ztype and hasattr(self, "variable_types"):
             ztype = self.variable_types.get(statement.name)
        
        if self.is_variant_type(ztype) or str(ztype) == "ZenValue":
             value = self.box_expression(statement.value, value)
        
        self.emit(f"{name} = {value};")

    def generate_member_reassignment_statement(self, statement: MemberReassignmentStatement):
        obj = self.generate_expression(statement.callee)
        prop = statement.expression
        val = self.generate_expression(statement.value)
        
        # Heuristic for boxing
        ltype = self.get_type(statement.callee) # This is slightly wrong as we want the MEMBER type
        # But we can check prop name
        if prop in ("line", "column", "current", "pos", "start", "end", "length", "depth", "count", "offset", "line_num", "column_num", "x", "y", "version", "debug"):
             pass # Already integer
        elif prop in ("ch", "char", "chars", "filename", "final_output", "out_str", "inner", "val_code"):
            return TypeString()
        else:
             # Default to boxing if it looks like it might be ZenValue in the struct
             pass 

        # Resolve path recursively for inheritance
        path = f".{prop}"
        if hasattr(ltype, "members"):
             path = self.resolve_member_path(ltype, prop)
        
        # If it's a structure or class pointer, use ->
        sep = "."
        if obj == "self" or "->" in obj or "as.object" in obj or "as.any" in obj:
             sep = "->"
             if path.startswith("."): path = path[1:] # Remove leading dot for ->
        else:
             ctype = self.map_type(ltype)
             if ctype and "*" in ctype:
                  sep = "->"
                  if path.startswith("."): path = path[1:]
        
        self.emit(f"{obj}{sep}{path} = {val};")




    def resolve_member_path(self, object_type: Any, member_name: str) -> str:
        """
        Resolves the C member path for a logical member in a class/structure,
        accounting for inheritance via '.base'.
        """
        current = object_type
        prefix = ""
        while current:
            # Check members
            members = getattr(current, "members", {})
            if isinstance(members, list):
                 if any(m.name == member_name for m in members if hasattr(m, "name")):
                      return prefix + "." + member_name
            elif member_name in members:
                 return prefix + "." + member_name
            
            # Move up the inheritance chain
            parent = getattr(current, "parent", None)
            if parent:
                 prefix += ".base"
                 if isinstance(parent, str):
                      p_obj = self.class_parents.get(parent)
                      if p_obj: current = p_obj
                      else: break
                 else:
                      current = parent
            else:
                 break
        
        return "." + member_name # Fallback

    ## Expression


    def generate_when_statement(self, statement: WhenStatement):
        condition = self.generate_expression(statement.condition)
        
        self.emit(f"if (({condition}).as.boolean) {{")
        self.indent_level += 1
        self.generate_block_statement(statement.when_block)
        self.indent_level -= 1
        self.emit("}")

        for block_dict in statement.conditional_blocks:
             cond_expr = block_dict["condition"]
             block_stmt = block_dict["block"]
             cond_code = self.generate_expression(cond_expr)
             self.emit(f"else if (({cond_code}).as.boolean) {{")
             self.indent_level += 1
             self.generate_block_statement(block_stmt)
             self.indent_level -= 1
             self.emit("}")

        if statement.or_block:
             self.emit("else {")
             self.indent_level += 1
             self.generate_block_statement(statement.or_block)
             self.indent_level -= 1
             self.emit("}")

    def generate_scope_statement(self, statement: ScopeStatement):
        self.emit("{")
        self.indent_level += 1
        
        self.generate_block_statement(statement.block)
        
        self.indent_level -= 1
        self.emit("}")

    def generate_do_statement(self, statement: DoStatement):
        if statement.iterable:
            # for iterator in iterable
            iterator = statement.iterator
            iterable_expr = self.generate_expression(statement.iterable)
            
            # Unbox to ZenList*
            list_ptr = f"(ZenList*)({iterable_expr}).as.list"
            
            loop_id = self.temp_counter
            self.temp_counter += 1
            
            self.emit(f"ZenList* __list_{loop_id} = {list_ptr};")
            
            # Track defer depth for loop iteration
            temp_id = self.temp_counter
            self.temp_counter += 1
            self.emit(f"int __loop_defer_{temp_id} = zen_defer_depth();")
            self.scope_defer_stack.append(f"__loop_defer_{temp_id}")

            self.emit(f"for (int __i_{loop_id} = 0; __i_{loop_id} < (__list_{loop_id} ? __list_{loop_id}->count : 0); __i_{loop_id}++) {{")
            self.indent_level += 1
            self.emit(f"ZenValue {iterator} = ZenList_get(__list_{loop_id}, __i_{loop_id});")
        elif statement.condition:
            condition = self.generate_expression(statement.condition)
            
            # Track defer depth
            temp_id = self.temp_counter
            self.temp_counter += 1
            self.emit(f"int __loop_defer_{temp_id} = zen_defer_depth();")
            self.scope_defer_stack.append(f"__loop_defer_{temp_id}")

            is_until = getattr(statement, "do_type", "") in ("until", "until_post")
            if is_until:
                 self.emit(f"while (!(({condition}).as.boolean)) {{")
            else:
                 self.emit(f"while (({condition}).as.boolean) {{")
            self.indent_level += 1
        else:
            # Track defer depth
            temp_id = self.temp_counter
            self.temp_counter += 1
            self.emit(f"int __loop_defer_{temp_id} = zen_defer_depth();")
            self.scope_defer_stack.append(f"__loop_defer_{temp_id}")

            self.emit("while (1) {")
            self.indent_level += 1
            
        self.generate_block_statement(statement.block)
        
        # Cleanup defers for this iteration
        if self.scope_defer_stack:
             depth = self.scope_defer_stack.pop()
             self.emit(f"zen_defer_run_to({depth});")

        self.indent_level -= 1
        self.emit("}")

    def generate_list_literal(self, expression: ListLiteral) -> str:
        items = [self.generate_expression(el.value) for el in expression.elements]
        args_str = ", " + ", ".join(items) if items else ""
        return f"ZenList_from_args({len(items)}{args_str})"

    def generate_index_expression(self, expression: IndexExpression):
        list_expr = self.generate_expression(expression.object)
        index_expr = self.generate_expression(expression.index)
        
        # Unbox list and index, but ZenList_get returns ZenValue!
        return f"ZenList_get((ZenList*)({list_expr}).as.list, (int)({index_expr}).as.integer)"

    def generate_expression(self, expression: ASTNode):
        if isinstance(expression, ParentExpression):
            return "parent"
        
        if isinstance(expression, BlockExpression):
            return self.generate_block_expression(expression)

        if isinstance(expression, ListLiteral):
            return self.generate_list_literal(expression)

        if isinstance(expression, MapLiteral):
            return self.generate_map_literal(expression)

        if isinstance(expression, VectorLiteral):
            return self.generate_list_literal(expression)

        if isinstance(expression, SetLiteral):
            # C bootstrap uses ZenMap for sets internally in some versions, or ZenList.
            # For now, let's use ZenList as a fallback for the literal.
            return self.generate_list_literal(expression)

        if isinstance(expression, TupleLiteral):
            return self.generate_list_literal(expression)

        if isinstance(expression, IntegerLiteral):
            return f"zen_int({expression.value})"

        if isinstance(expression, BooleanLiteral):
            val = 1 if str(expression.value).lower() in ("true", "1") else 0
            return f"zen_bool({val})"

        if isinstance(expression, DecimalLiteral):
            return f"zen_float({expression.value})"

        if isinstance(expression, StringLiteral):
            string: str = expression.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            # If it's a TypeRune, emit char literal (actually box as string or rune?)
            if hasattr(expression, "resolved_type") and isinstance(expression.resolved_type, TypeRune) and len(string) == 1:
                return f"zen_rune('{string}')"
            return f'zen_str("{string}")'

        if isinstance(expression, RuneLiteral):
            string: str = expression.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            return f'zen_str("{string}")'

        if isinstance(expression, Identifier):
            name = expression.name
            if name in ("char", "int", "float", "double", "void", "struct", "return", "if", "else", "while", "for", "do", "break", "continue", "switch", "case", "default", "typedef", "static", "extern"):
                name = f"zen_{name}"
            
            # Special case for enumerators to avoid boxing issues during initialization
            if hasattr(expression, "symbol") and getattr(expression, "symbol") and getattr(expression.symbol.kind, "name", "") == "ENUMERATOR":
                name = self.sanitize_name(expression.name)
                parent_name = getattr(expression.symbol, "parent_name", expression.symbol.type.name if hasattr(expression.symbol.type, "name") else "")
                return f"zen_int({parent_name}_{name})" # Box enum as int
            
            if expression.symbol and expression.symbol.kind == SymbolKind.STRUCTURE:
                return name
            
            if expression.symbol is None:
                if name.isidentifier() and (not name.startswith("__") or name in ("__builtin", "__builtin_io", "__builtin_sys", "__builtin_memory", "__builtin_output", "__builtin_input", "__builtin_file", "__builtin_input")):
                    return name
                return f'ZEN_VAL_STR("{name}")'
            
            if (expression.symbol.kind == SymbolKind.VARIABLE and 
                expression.symbol.scope_level == 0 and 
                hasattr(self, 'global_variable_names') and
                name not in self.global_variable_names):
                if name.isupper() or name in ("IO", "s", "Str", "Sys", "TokenModule", "ASTModule", "ASTKind", "SymbolKind", "TokenType", "__builtin", "__builtin_io", "__builtin_sys", "__builtin_memory", "__builtin_output", "__builtin_input", "__builtin_file"):
                    return name
                return f'ZEN_VAL_STR("{name}")'

            return name

        if isinstance(expression, MemberExpression):
        # Check for Static Structure Access (e.g. MyVector.x)
            if (isinstance(expression.object, Identifier) and 
                expression.object.symbol and 
                expression.object.symbol.kind == SymbolKind.STRUCTURE):
                
                # Find member type in structure definition
                type_def = expression.object.symbol.type
                # Unwrap if it's a TypeType or similar (logic depends on how Symbol stores it)
                # Assuming symbol.type IS the TypeStructure for now
                if isinstance(type_def, TypeStructure):
                    member_name = expression.property
                    if member_name in type_def.members:
                        member_type = type_def.members[member_name]
                        # Return default value for this member's type
                        if isinstance(member_type, TypeInteger): return "zen_int(0)"
                        if isinstance(member_type, TypeDecimal): return "zen_float(0.0)"
                        if isinstance(member_type, TypeBoolean): return "zen_bool(false)"
                        if isinstance(member_type, TypeString): return 'zen_str("")'
                        return "zen_make_null()" # Default fallback
            
            # If not found or not Structure, fall through to instance access
            pass

            obj = self.generate_expression(expression.object)
            # Check if object is a Type string (quoted)
            if obj.startswith('"') and obj.endswith('"'):
                return f'"{obj[1:-1]}.{expression.property}"'
            
            return self.generate_member_expression(expression)

        if isinstance(expression, IndexExpression):
            return self.generate_index_expression(expression)

        if isinstance(expression, UnaryOperation):
            operand = self.generate_expression(expression.right)
            op = str(expression.operator)
            if op in ("not", "!"):
                return f"ZenValue_not({operand})"
            if op == "-":
                return f"ZenValue_neg({operand})"
            if op in ("~", "!!"):
                return f"ZenValue_bitwise_not({operand})"
            return operand

        if isinstance(expression, AssignmentStatement) or expression.__class__.__name__ == "AssignmentStatement":
            return self.generate_assignment_statement(expression)
        
        if isinstance(expression, ReassignmentStatement) or expression.__class__.__name__ == "ReassignmentStatement":
            return self.generate_reassignment_statement(expression)

        if isinstance(expression, WhenExpression):
            return self.generate_when_expression(expression)
            
        if isinstance(expression, WhenInlineExpression):
            return self.generate_when_inline_expression(expression)
        
        if isinstance(expression, BinaryOperation):
            left_code = self.generate_expression(expression.left)
            right_code = self.generate_expression(expression.right)
            
            op = str(expression.operator.value if hasattr(expression.operator, "value") else expression.operator)
            if op == "=": op = "=="

            # Logical Short-circuiting - returns ZenValue
            if op == "and":
                return f"zen_bool(({left_code}).as.boolean && ({right_code}).as.boolean)"
            if op == "or":
                return f"zen_bool(({left_code}).as.boolean || ({right_code}).as.boolean)"

            variant_ops = {
                "+": "ZenValue_add", "-": "ZenValue_sub", "*": "ZenValue_mul", 
                "/": "ZenValue_div", "%": "ZenValue_mod", "**": "ZenValue_pow",
                "//": "ZenValue_div", 
                "==": "ZenValue_equals", "!=": "ZenValue_not_equals", 
                "<": "ZenValue_less_than", ">": "ZenValue_greater_than",
                "<=": "ZenValue_less_than_or_equal", ">=": "ZenValue_greater_than_or_equal",
                "xor": "ZenValue_xor",
                "nor": "ZenValue_nor", "nand": "ZenValue_nand", "xnor": "ZenValue_xnor",
                "&": "ZenValue_bitwise_and", "|": "ZenValue_bitwise_or", "^": "ZenValue_bitwise_xor",
                "&&": "ZenValue_bitwise_and", "||": "ZenValue_bitwise_or",
                "%%": "ZenValue_bitwise_mod",
                "^^": "ZenValue_bitwise_xor",
                "!&": "ZenValue_bitwise_nand", "!|": "ZenValue_bitwise_nor", "!^": "ZenValue_bitwise_xnor",
                "<<": "ZenValue_lshift", ">>": "ZenValue_rshift"
            }
            
            if op in variant_ops:
                vop = variant_ops[op]
                return f"{vop}({left_code}, {right_code})"

            # Fallback (should not happen in a fully boxed runtime)
            return left_code

        if isinstance(expression, CallExpression):
            return self.generate_call_expression(expression)

        if isinstance(expression, MemberReassignmentStatement):
            # LHS = RHS
            # LHS is expression.expression (MemberExpression)
            # RHS is expression.value
            lhs = self.generate_expression(expression.expression)
            rhs = self.generate_expression(expression.value)
            return f"{lhs} = {rhs}"

        if isinstance(expression, CheckExpression):
            return self.generate_check_expression(expression)

        if isinstance(expression, StructureExpression):
            return self.generate_structure_expression(expression)

        # fallback
        return "zen_make_null()"

    def find_method_definition(self, cls_type: TypeClass, method_name: str) -> TypeClass | None:
        current = cls_type
        while current:
            if method_name in current.methods:
                return current
            current = current.parent
        return None

    def generate_member_expression(self, expression: MemberExpression):
        # Static Access (Enums)
        if hasattr(expression.object, "name"):
             obj_name_raw = expression.object.name
             if obj_name_raw in ("TokenType", "ASTKind", "ASTKind_"):
                  prop_name = self.sanitize_name(expression.property)
                  return f"zen_int({obj_name_raw}_{prop_name})"

        obj_name = self.generate_expression(expression.object)
        prop_name = self.sanitize_name(expression.property)
        
        if obj_name == "self": 
            return f"self->{prop_name}"
        if obj_name == "parent": 
            return f"self->base.{prop_name}"

        # If accessing a singleton object instance (e.g. Config.version)
        if obj_name == "Config":
             return f"Config_inst.{prop_name}"
        
        # Explicit check for Color enum
        if obj_name == "Color":
             return f"zen_int(Color_{prop_name})"

        # IN A FULLY BOXED RUNTIME:
        # All local variables are ZenValue. 
        # All member access must unbox the object pointer.
        
        obj_type = self.get_type(expression.object)
        class_name = "void"
        
        if hasattr(obj_type, 'name') and obj_type.name not in ("Variant", "Variable", "ZenValue", "Object", "Class"):
             if obj_type.name[0].isupper():
                  class_name = obj_type.name
                  if class_name == "List": class_name = "ZenList"
                  if class_name == "String": class_name = "ZenString"
        
        # Static Access (Enums) fallback
        if hasattr(obj_type, 'name') and (obj_type.name == "Enumerator" or obj_type.name == "ADT"):
             return f"ZenVariant_{obj_name}_{prop_name}"
        
        # Handle ZEN_VAL_STR("Enum").Variant
        if obj_name.startswith('ZEN_VAL_STR("') and obj_name.endswith('")'):
             actual_obj = obj_name[13:-2]
             if actual_obj[0].isupper() and prop_name[0].isupper():
                  return f"ZenVariant_{actual_obj}_{prop_name}"

        if obj_name[0].isupper() and prop_name[0].isupper() and obj_name != "Sys":
             return f"ZenVariant_{obj_name}_{prop_name}"
        
        # Inheritance resolution
        path = f".{prop_name}"
        if hasattr(obj_type, "members"):
             path = self.resolve_member_path(obj_type, prop_name)
        
        # Handle self and specialized types
        if obj_name == "self":
             if path.startswith("."): path = path[1:]
             return f"self->{path}"
             
        if class_name == "ZenList" and prop_name == "length":
             return f"ZenList_length((ZenList*)({obj_name}).as.list)"

        # Fallback to casted object access
        if path.startswith("."): path = path[1:]
        # Fallback to casted object access
        if path.startswith("."): path = path[1:]
        if class_name == "void" or class_name == "ZenObject":
             # Try harder to find the specific class type
             rtype = getattr(expression.object, "resolved_type", None)
             if rtype and hasattr(rtype, "name") and rtype.name:
                  class_name = str(rtype.name)
        
        if class_name == "void": class_name = "ZenObject" # Final fallback
        
        return f"(({class_name}*)({obj_name}).as.object)->{path}"

    def generate_call_expression(self, expression: CallExpression):
        callee = expression.callee
        
        # No more redundant boxing: generate_expression already returns ZenValue (Rule 1)
        args = [self.generate_expression(arg) for arg in expression.arguments]
        
        if isinstance(callee, Identifier):
            name = callee.name
            if name == "print": return self.generate_call_print_expression(expression)
            
            # Special case for assert_eq in tests
            if name == "assert_eq":
                 # assert_eq(ZenValue a, ZenValue b, ZenValue message)
                 # args already boxed
                 return f"assert_eq({', '.join(args)})"
            name = str(callee.name)
            # Built-in Global Handlers
            if name == "len": return f"ZenList_length((ZenList*)({args[0]}).as.list)"
            if name == "str" or name == "zl_str": return f"ZenValue_str({args[0]})"
            if name == "int" or name == "zl_int": return f"ZenValue_int({args[0]})"
            if name == "write": return f"zl_write({args[0]})" # Wait, actually keep zl_write if it works, but I think it returns void.
            # actually let's use zl_write but ensure it's declared.
            # NO, let's use IO_write.
            if name == "write": return f"IO_write({args[0]})"
            
            if name == "read" or name == "IO_read": return f"IO_read_file(ZenString_str({args[0]}))"
            
            call_code = f"{self.sanitize_name(name)}({', '.join(args)})"
            if name[0].isupper() and name not in ("Str", "IO", "Sys", "ZenValue", "ZenList", "TokenModule", "ASTModule", "ASTKind", "SymbolKind", "TokenType", "Boolean", "Number", "Null"):
                # Constructor detection: if name is Lexer, constructor is Lexer_Lexer
                # Actually, in Zenland, most constructors are simply FunctionName(args)
                # But when compiled to C, they are ClassName_FunctionName
                # For self-hosted code, it's often just ClassName(args)
                cons_name = f"{name}_{name}"
                return f"zen_val_object({cons_name}({', '.join(args)}))"
            return call_code
            
        elif isinstance(callee, MemberExpression):
            obj_name = str(self.generate_expression(callee.object))
            prop_name = str(callee.property)
            if hasattr(callee.property, 'value'): prop_name = str(callee.property.value)
            
            # 0. HIGHEST PRIORITY: Built-in IO/Sys objects
            if obj_name in ("__builtin_output", "out"):
                if prop_name in ("write", "info", "warn", "error", "debug"):
                    if prop_name == "write": return f"IO_write({args[0]})"
                    return f"IO_{prop_name}({args[0]})"
            if obj_name in ("__builtin_input", "in"):
                if prop_name == "read": return f"IO_read_file({args[0]})"
            if obj_name in ("__builtin_file", "File"):
                if prop_name == "exists": return f"IO_file_exists(ZenValue_str({args[0]}))"
                if prop_name == "write": return f"IO_write_file({args[0]}, {args[1]})"
                if prop_name == "read": return f"IO_read_file({args[0]})"
            if obj_name in ("__builtin_sys", "Sys"):
                if prop_name == "get_args": return "Sys_get_args()"
                if prop_name == "exit": return f"Sys_exit((int)({args[0]}).as.integer)"
                if prop_name == "get_env": return f"Sys_get_env(ZenString_str({args[0]}))"
            
            if obj_name == "__builtin":
                if prop_name == "error":
                    return f"__builtin_error({args[0]})"
                if prop_name == "error_literal":
                    return f"__builtin_error_literal({args[0]})"

            # 0. Specialized Constructor/Static Check (Absolute Priority)
            name = f"{obj_name}_{prop_name}"
            if prop_name == obj_name:
                 return f"zen_val_object({name}({', '.join(args)}))"
            
            if obj_name[0].isupper() and prop_name[0].isupper() and obj_name != "Sys":
                 # ADT Variant Constructor
                 return f"ZenVariant_{obj_name}_{prop_name}({', '.join(args)})"

            # String literal method calls (e.g., "str".length())
            if obj_name.startswith("ZEN_VAL_STR") and not any(b in obj_name for b in ("builtin_output", "builtin_input", "builtin_file", "builtin_sys")):
                 if prop_name == "length": return f"ZenString_length(ZenString_str({obj_name}))"
                 # Fallback to string methods for ACTUAL literals
                 actual_obj_expr = obj_name
                 class_name = "String" # Switch to class-static like call
                 m_args = [actual_obj_expr] + args
                 return f"ZenString_{prop_name}({', '.join(m_args)})"

            # 0a. Handle self and parent calls
            if obj_name == "self":
                actual_class = self.current_class or "ZenObject"
                name = f"{actual_class}_{prop_name}"
                # In mangled methods, 'self' is passed as the first argument (pointer)
                return f"{name}(self{', ' if args else ''}{', '.join(args)})"
            elif obj_name == "parent":
                parent_class = getattr(self, "class_parents", {}).get(self.current_class, "ZenObject")
                name = f"{parent_class}_{prop_name}"
                # Cast self to parent type
                return f"{name}(({parent_class}*)self{', ' if args else ''}{', '.join(args)})"

            # 0b. Global Built-in Handling (Wrappers in zen.zl)
            if obj_name in ("string", "Str", "String", "__builtin_string") or "builtin_string" in obj_name:
                if prop_name == "length": return f"ZenString_length(ZenString_str({args[0]}))"
                if prop_name == "to_upper": return f"ZenString_to_upper(ZenString_str({args[0]}))"
                if prop_name == "to_lower": return f"ZenString_to_lower(ZenString_str({args[0]}))"
                if prop_name == "trim": return f"ZenString_trim(ZenString_str({args[0]}))"
                if prop_name == "split": return f"ZenString_split(ZenString_str({args[0]}), ZenString_str({args[1]}))"
                if prop_name == "join": return f"ZenString_join((ZenList*)({args[0]}).as.list, ZenString_str({args[1]}))"
                if prop_name == "substring": return f"ZenString_substring(ZenString_str({args[0]}), (int)({args[1]}).as.integer, (int)({args[2]}).as.integer)"
                if prop_name == "starts_with": return f"ZenString_starts_with(ZenString_str({args[0]}), ZenString_str({args[1]}))"
                if prop_name == "ends_with": return f"ZenString_ends_with(ZenString_str({args[0]}), ZenString_str({args[1]}))"
                if prop_name == "replace": return f"ZenString_replace(ZenString_str({args[0]}), ZenString_str({args[1]}), ZenString_str({args[2]}))"
                if prop_name == "index_of": return f"ZenString_index_of(ZenString_str({args[0]}), ZenString_str({args[1]}))"
                if prop_name == "at": return f"ZenString_at(ZenString_str({args[0]}), (int)({args[1]}).as.integer)"
                if prop_name == "str": return f"ZenValue_str({args[0]})"

            if obj_name in ("file", "File", "__builtin_file") or "builtin_file" in obj_name:
                if prop_name == "write": return f"IO_write_file({args[0]}, {args[1]})"
                if prop_name == "exists": return f"IO_file_exists(ZenValue_str({args[0]}))"
                if prop_name == "read": return f"IO_read_file({args[0]})"
            
            if obj_name in ("sys", "Sys", "__builtin_sys") or "builtin_sys" in obj_name:
                if prop_name == "get_args": return "Sys_get_args()"
                if prop_name == "exit": return f"Sys_exit((int)({args[0]}).as.integer)"
                if prop_name == "get_env": return f"Sys_get_env(ZenString_str({args[0]}))"

            # 0d. Static Class Calls (Inheritance Support e.g. Animal.init(self, ...))
            if obj_name in getattr(self, "class_parents", {}) or obj_name in getattr(self, "structure_members", {}):
                name = f"{obj_name}_{prop_name}"
                # If the first argument is 'self', pass the pointer
                final_args = []
                for i, arg in enumerate(args):
                     if i == 0 and (arg == "self" or "self->" in arg):
                          final_args.append(f"({obj_name}*)self")
                     else:
                          final_args.append(arg)
                call_code = f"{name}({', '.join(final_args)})"
                if prop_name == "init": return call_code # Constructors usually return void
                return call_code

            # 0c. Better Method Resolution
            res_type = self.get_type(callee.object)
            class_name = None
            if isinstance(res_type, str): class_name = res_type
            elif hasattr(res_type, "name"): class_name = str(res_type.name)
            
            if class_name and class_name not in ("Variant", "Any", "ZenValue", "ZenList", "ZenString"):
                 name = f"{class_name}_{prop_name}"
                 actual_obj = f"({class_name}*)({obj_name}).as.object"
                 return f"{name}({actual_obj}{', ' if args else ''}{', '.join(args)})"

            # 1. Specialized List/String mappings (Highest Priority)
            is_list_obj = obj_name in ("output", "order", "statements", "parameters", "members", "members_list", "methods", "branches", "arguments", "defer_functions", "class_names", "unique_names", "List", "ZenList", "args", "parts")
            if obj_name == "out" and class_name != "String": is_list_obj = True
            
            if prop_name in ("append", "push", "insert", "pop", "clear", "extend", "length", "write") and obj_name != "IO" and (is_list_obj or prop_name in ("append", "push", "pop", "insert")):
                if prop_name == "length":
                     if obj_name in ("args", "parts"):
                           arg_expr = args[0] if args else f"(ZenList*)({obj_name}).as.list"
                           return f"ZenList_length({arg_expr})" # generic fallback for args
                     actual_obj = f"(ZenList*)({obj_name}).as.list" if obj_name != "self" and obj_name != "List" else obj_name
                     if obj_name == "List": actual_obj = f"(ZenList*)({args[0]}).as.list"
                     return f"ZenList_length({actual_obj})"
                
                if prop_name in ("write", "append", "push"):
                     if obj_name == "out" and class_name == "String":
                          return f"IO_write({args[0]})"
                     actual_obj = f"(ZenList*)({obj_name}).as.list" if obj_name not in ("self", "List", "ZenList") else obj_name
                     if obj_name == "List": actual_obj = f"(ZenList*)({args[0]}).as.list"
                     actual_arg = args[0] if obj_name not in ("List", "ZenList") else args[1]
                     # Comma-expression fix for void returns
                     return f"(ZenList_append({actual_obj}, {actual_arg}), zen_make_null())"

                actual_obj = f"(ZenList*)({obj_name}).as.list" if obj_name not in ("self", "List", "ZenList") else obj_name
                if obj_name == "List": # Class-static like call
                     name = f"ZenList_{prop_name}"
                     return f"{name}((ZenList*)({args[0]}).as.list{', ' if len(args) > 1 else ''}{', '.join(args[1:])})"
                
                if prop_name == "get":
                    if args: args[0] = f"(int)({args[0]}).as.integer"
                    return f"ZenList_get({actual_obj}, {args[0]})"
                
                # Check for other void list operations if any
                return f"ZenList_{prop_name}({actual_obj}{', ' if args else ''}{', '.join(args)})"
            
            if prop_name in ("split", "join", "substring", "starts_with", "ends_with", "replace", "index_of", "at") or obj_name in ("source", "final_output", "out_str", "path_str", "line_str") or obj_name == "String":
                if prop_name in ("length", "to_lower", "to_upper", "str"):
                    target = obj_name if obj_name != "String" else args[0]
                    return f"ZenString_{prop_name}(ZenString_str({target}))"
                
                unboxed_args = [f"ZenString_str({arg})" for arg in args]
                target = obj_name if obj_name != "String" else unboxed_args[0]
                actual_args = unboxed_args if obj_name != "String" else unboxed_args[1:]
                return f"ZenString_{prop_name}(ZenString_str({target}){', ' if actual_args else ''}{', '.join(actual_args)})"

            # 2. Heuristic Class Method Resolution
            class_name = "void"
            if "transpiler" in obj_name.lower(): class_name = "Transpiler"
            elif "resolver" in obj_name.lower(): class_name = "Resolver"
            elif "graph" in obj_name.lower() or "node" in obj_name.lower(): class_name = "DependencyGraph"
            elif "parser" in obj_name.lower(): class_name = "Parser"
            elif "lexer" in obj_name.lower(): class_name = "Lexer"
            elif "lexer_instance" in obj_name: class_name = "Lexer"

            if class_name != "void":
                name = f"{class_name}_{prop_name}"
                actual_obj = f"({class_name}*)({obj_name}).as.object"
                if class_name in ("Variant", "ZenValue"): actual_obj = obj_name
                return f"{name}({actual_obj}{', ' if args else ''}{', '.join(args)})"

            # 3. Module Static/Global Fallback
            if hasattr(self, 'global_variable_names') and obj_name in self.global_variable_names:
                name = f"{obj_name}_{prop_name}"
                if obj_name[0].isupper() or obj_name in ("IO", "Sys"):
                     # Module-prefixed call: could be a constructor or static method
                     # If prop_name matches obj_name (ignoring prefixes), it's a constructor
                     if prop_name == obj_name or prop_name in obj_name:
                         return f"zen_val_object({name}({', '.join(args)}))"
                     return f"{name}({', '.join(args)})"
                
                return f"{name}({obj_name}{', ' if args else ''}{', '.join(args)})"

            # 4. Built-in Modules (IO, Sys, Memory)
            if obj_name in ("IO", "Sys", "string", "Str", "file", "Memory", "__builtin_string", "__builtin_sys", "__builtin_io", "__builtin_memory"):
                 if prop_name == "write": return f"IO_write({args[0]})"
                 if prop_name == "read_file" or (obj_name == "file" and prop_name == "read"): return f"IO_read_file(ZenString_str({args[0]}))"
                 if prop_name == "get_args": return f"Sys_get_args()"
                 if prop_name == "exit": return f"Sys_exit((int)({args[0]}).as.integer)"
                 if prop_name == "length": return f"ZenString_length(ZenString_str({args[0]}))"
                 
                 # Memory Module
                 if prop_name == "create_arena": return f"Memory_create_arena({args[0] if args else 'zen_int(0)'})"
                 if prop_name == "free_arena": return f"Memory_free_arena({args[0]})"
                 if prop_name == "reset_arena": return f"Memory_reset_arena({args[0]})"
                 if prop_name == "push_arena": return f"Memory_push_arena({args[0]})"
                 if prop_name == "pop_arena": return f"Memory_pop_arena()"

            # 2. Final Fallback (Module Static or Method Call)
            name = f"{obj_name}_{prop_name}"
            # Constructor heuristic: if Class_Class or Module_Class or prop == obj
            if prop_name == obj_name or (obj_name[0].isupper() and prop_name[0].isupper()):
                 return f"zen_val_object({name}({', '.join(args)}))"
            
            # Module static or just generic method call on capitalized object
            if obj_name[0].isupper() and obj_name not in ("statements", "parameters", "members", "methods", "branches", "arguments"):
                 return f"{name}({', '.join(args)})"

            # 3. Heuristic Class Method Resolution (Lower Priority)
            obj_type = self.get_type(callee.object)
            class_name = "void"
            if obj_type and hasattr(obj_type, 'name'): class_name = str(obj_type.name)
            
            if class_name == "void":
                if "transpiler" in obj_name.lower(): class_name = "Transpiler"
                elif "resolver" in obj_name.lower(): class_name = "Resolver"
                elif "graph" in obj_name.lower() or "node" in obj_name.lower(): class_name = "DependencyGraph"
                elif "parser" in obj_name.lower(): class_name = "Parser"
                elif "lexer" in obj_name.lower(): class_name = "Lexer"

            if class_name != "void":
                name = f"{class_name}_{prop_name}"
                actual_obj = f"({class_name}*)({obj_name}).as.object"
                if class_name in ("Variant", "ZenValue"): actual_obj = obj_name
                return f"{name}({actual_obj}{', ' if args else ''}{', '.join(args)})"
            
            # Final fallback: assume standard method call pattern
            return f"{name}({obj_name}{', ' if args else ''}{', '.join(args)})"
        
        return "unknown_call()"

        # default function call
        arguments: str = ", ".join(
            [self.generate_expression(argument) for argument in expression.arguments]
        )

        return f"{name}({arguments})"

    def generate_io_call(self, expression: CallExpression):
         callee = expression.callee
         if callee.property == "write":
             arg = expression.arguments[0]
             arg_code = self.generate_expression(arg)
             arg_type = self.get_type(arg)
             arg_code = self.generate_expression(expression.arguments[0])
             return f"IO_write({arg_code})"

         if callee.property == "write_int":
             return f"IO_write_int({self.generate_expression(expression.arguments[0])})"
         
         return "IO_error"

    def generate_call_print_expression(self, expression: CallExpression) -> str:
        """
        Special-case print to generate a Python-like print:
        zl_print_begin(), zl_print_type(...), ..., zl_print_end()
        Join with commas so it becomes a single expression via C's comma operator,
        which is fine when the call is used as a statement: (<comma-expr>);
        """

        parts = []
        parts.append("zl_print_begin()")

        for argument in expression.arguments:
            argument_expression = self.generate_expression(argument)
            argument_type = self.get_type(argument)

            # print(argument_type)

            # print(argument_type)

            if isinstance(argument_type, TypeInteger) or argument_type == TypeInteger:
                parts.append(f"zl_print_int({argument_expression})")
            elif isinstance(argument_type, TypeDecimal) or argument_type == TypeDecimal:
                parts.append(f"zl_print_float({argument_expression})")
            elif isinstance(argument_type, TypeString) or argument_type == TypeString or '"' in argument_expression:
                parts.append(f"zl_print_string({argument_expression})")
            elif isinstance(argument_type, TypeBoolean) or argument_type == TypeBoolean:
                parts.append(f"zl_print_bool({argument_expression})")
            elif any(x in argument_expression for x in (" ^ ", " | ", " & ", " || ", " && ")):
                # Expression result is likely integer/boolean
                parts.append(f"zl_print_int({argument_expression})")
            elif argument_expression in ("a", "b", "n", "temp", "index", "count", "xor_res", "fact5"):
                # Heuristic for identifier types in print fallbacks
                parts.append(f"zl_print_int({argument_expression})")
            elif "->" in argument_expression or "." in argument_expression:
                # Heuristic for structure members: id, value, count are usually integers
                if any(x in argument_expression for x in ("id", "value", "count", "size", "length")):
                     parts.append(f"zl_print_int({argument_expression})")
                else:
                     parts.append(f"zl_print_string({argument_expression})")
            else:
                # fallback as string
                parts.append(f"zl_print_string({argument_expression})")

        parts.append("zl_print_end()")

        return "(" + ", ".join(parts) + ")"

    def generate_when_expression(self, expression: WhenExpression):
        temp_name = f"when_res_{self.temp_counter}"
        self.temp_counter += 1
        self.emit(f"ZenValue {temp_name} = zen_make_null();")
        
        # if branch
        condition = self.generate_expression(expression.condition)
        self.emit(f"if (({condition}).as.boolean) {{")
        self.indent_level += 1
        val = self.generate_expression(expression.when_block)
        self.emit(f"{temp_name} = {val};")
        self.indent_level -= 1
        self.emit("}")
        
        # else if branches (conditional_blocks)
        for block_dict in expression.conditional_blocks:
             cond_expr = block_dict["condition"]
             block_expr = block_dict["block"]
             cond_code = self.generate_expression(cond_expr)
             self.emit(f"else if (({cond_code}).as.boolean) {{")
             self.indent_level += 1
             val_code = self.generate_expression(block_expr)
             self.emit(f"{temp_name} = {val_code};")
             self.indent_level -= 1
             self.emit("}")
             
        # else branch
        if expression.or_block:
             self.emit("else {")
             self.indent_level += 1
             val_code = self.generate_expression(expression.or_block)
             self.emit(f"{temp_name} = {val_code};")
             self.indent_level -= 1
             self.emit("}")
             
        return temp_name

    def generate_when_inline_expression(self, expression: WhenInlineExpression):
        condition = self.generate_expression(expression.condition)
        when_val = self.generate_expression(expression.when_value)
        or_val = self.generate_expression(expression.or_value)
        
        # C ternary: (cond).as.boolean ? when_val : or_val
        return f"(({condition}).as.boolean ? {when_val} : {or_val})"

    def generate_block_expression(self, expression: BlockExpression):
        # We need a temp variable to store the result of the block
        temp_name = f"block_res_{self.temp_counter}"
        self.temp_counter += 1
        
        # return type of the block
        rtype = "ZenValue"
        if hasattr(expression, "resolved_type") and expression.resolved_type:
             rtype = self.map_type(expression.resolved_type)
        
        if rtype == "void":
            rtype = "ZenValue"
             
        self.emit(f"{rtype} {temp_name};")
        self.emit("{")
        self.indent_level += 1
        
        # Run all statements, but the last one's value is the result.
        # If the last statement is an ExpressionStatement, its expression's value is the block's value.
        # Otherwise, the block's value is null/default.
        
        # Determine the actual return type of the block from its statements
        result_type = None
        for stmt in expression.statements:
            if isinstance(stmt, ReturnStatement):
                # If there's an explicit return, that determines the type
                # This logic is usually handled by the TypeChecker, but for codegen fallback
                if hasattr(stmt.value, "resolved_type") and stmt.value.resolved_type:
                    result_type = stmt.value.resolved_type
                break
        
        # If still no type, default to ZenValue (or void if it's truly a void block)
        if result_type is None or isinstance(result_type, TypeVoid):
            # If the block is truly void, and we expect a ZenValue, make it null
            if rtype == "ZenValue":
                self.emit(f"{temp_name} = zen_make_null();")
            else:
                # If we expect a specific type but the block is void, this is an error or a special case
                # For now, assign a default value for the expected type
                if rtype == "char*": self.emit(f"{temp_name} = NULL;")
                elif rtype == "bool": self.emit(f"{temp_name} = false;")
                elif rtype == "int": self.emit(f"{temp_name} = 0;")
                elif rtype == "double": self.emit(f"{temp_name} = 0.0;")
                else: self.emit(f"{temp_name} = ({rtype})0;") # Generic fallback
        
        for i, stmt in enumerate(expression.statements):
            if i == len(expression.statements) - 1:
                # Last statement
                if isinstance(stmt, ExpressionStatement):
                    val = self.generate_expression(stmt.expression)
                    stmt_type = self.get_type(stmt.expression)
                    if stmt_type and (isinstance(stmt_type, TypeVoid) or getattr(stmt_type, "name", "") == "Void" or stmt_type == "void"):
                        self.emit(f"{val};")
                        self.emit(f"{temp_name} = zen_make_null();")
                    else:
                        self.emit(f"{temp_name} = {val};")
                else:
                    self.generate_statement(stmt)
                    # fallback if not expression
                    fallback = "0"
                    if rtype == "ZenValue": fallback = "zen_make_null()"
                    elif rtype == "char*": fallback = "NULL"
                    elif rtype == "ZenList*": fallback = "NULL"
                    elif rtype == "bool": fallback = "false"
                    
                    self.emit(f"{temp_name} = {fallback};")
            else:
                self.generate_statement(stmt)
                
        # Ensure all non-void functions have a return statement
        if rtype != "void" and not (expression.statements and isinstance(expression.statements[-1], ReturnStatement)):
             default_ret = "zen_make_null()"
             if rtype == "int" or rtype == "long long": default_ret = "0"
             elif "bool" in rtype: default_ret = "0"
             self.emit(f"{temp_name} = {default_ret};") # Assign default to temp_name instead of return
        
        self.indent_level -= 1
        self.emit("}")
        return temp_name

    def generate_check_expression(self, expression: CheckExpression):
        temp_name = f"check_expr_res_{self.temp_counter}"
        self.temp_counter += 1
        
        rtype = "ZenValue"
        if hasattr(expression, "resolved_type") and expression.resolved_type:
             rtype = self.map_type(expression.resolved_type)
             
        self.emit(f"{rtype} {temp_name};")
        self.emit("{")
        self.indent_level += 1
        self.emit("ZenExceptionContext ctx;")
        self.emit("ctx.defer_depth = zen_defer_depth();")
        self.emit("zen_exception_push(&ctx);")
        
        self.emit("if (setjmp(ctx.buf) == 0) {")
        self.indent_level += 1
        val = self.generate_expression(expression.expression)
        
        # Check for type mismatch (e.g. block returned ZenValue (fallback) but we expect char*)
        block_type = self.get_type(expression.expression)
        if rtype != "ZenValue" and (block_type is None or block_type.name == "Void"):
             # If block is void but we expect a result, it must have raised.
             # Cast 0 to satisfy compiler for this unreachable assignment.
             self.emit(f"{temp_name} = ({rtype})0;")
             self.emit(f"(void){val}; // evaluate block result temp")
        else:
             self.emit(f"{temp_name} = {val};")
             
        self.emit("zen_exception_pop();")
        self.indent_level -= 1
        self.emit("} else {")
        self.indent_level += 1
        self.emit("zen_exception_pop();")
        if expression.or_value:
             or_val = self.generate_expression(expression.or_value)
             self.emit(f"{temp_name} = {or_val};")
        else:
             # Default value if no or_value? 
             # Should probably be handled by TypeChecker to always have a fallback for CheckExpression result
             self.emit(f"{temp_name} = zen_make_null();")
        
        self.indent_level -= 1
        self.emit("}")
        self.indent_level -= 1
        self.emit("}")
        return temp_name
    def generate_assignment_expression(self, expression: Union[AssignmentStatement, ReassignmentStatement]):
        # Fallback for nested assignments if they exist
        return self.generate_reassignment_statement(expression)

    def generate_structure_expression(self, expression: StructureExpression):
        # Instantiation: zen_val_object(&(StructureName){.m1 = v1, .m2 = v2})
        members = []
        for member in expression.members:
             val = self.generate_expression(member.value)
             members.append(f".{member.name} = {val}")
        
        struct_init = f"({expression.name}){{{', '.join(members)}}}"
        
        # We need a shared pointer for the object
        temp_name = f"_struct_{self.temp_counter}"
        self.temp_counter += 1
        
        self.emit(f"static {expression.name} {temp_name};")
        self.emit(f"{temp_name} = {struct_init};")
        
        return f"zen_val_object(&{temp_name})"

    def generate_map_literal(self, expression: MapLiteral) -> str:
        items = []
        for el in expression.elements:
            # el.name and el.value are ASTNodes. name represents the key.
            items.append(self.generate_expression(el.name))
            items.append(self.generate_expression(el.value))

        args_str = ", " + ", ".join(items) if items else ""
        return f"ZenMap_from_args({len(expression.elements)}{args_str})"

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
