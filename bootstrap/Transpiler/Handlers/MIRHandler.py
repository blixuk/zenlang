from typing import List, Set, Any, Dict, Callable
from Transpiler.MIR import *
from Transpiler.SMIRGenerator import SMIRGenerator
from Transpiler.SMIRAnalyzer import SMIRAnalyzer
from Transpiler.SMIRLowerer import SMIRLowerer
from Parser.AST import ASTNode

class MIRHandler:
    def _format_zen_value_arg(self, arg: str) -> str:
        # Class methods take `Class* self` — keep the raw pointer. Boxing as
        # ZenValue_from_object(self) breaks process_Pipeline_result(self) etc.
        if arg in ("self", "ctx"):
            return arg
        if arg.startswith('"'):
            return arg
        if arg.startswith("`") and arg.endswith("`"):
            inner = arg[1:-1]
            inner = inner.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\x1b", "\\x1b")
            return f'ZenValue_make_string("{inner}")'
        if arg.isdigit():
            return f"ZenValue_make_integer({arg})"
        if arg in ("true", "false"):
            return f"ZenValue_make_boolean({1 if arg == 'true' else 0})"
        return arg

    def _build_lmir_dispatch_table(self):
        self.lmir_dispatch_table: Dict[type, Callable] = {
            Try: self._emit_try,
            Catch: self._emit_catch,
            EndTry: self._emit_end_try,
            Raise: self._emit_raise,
            Enumerator: lambda instr: None, # Handled globally
            ArenaCreate: self._emit_arena_create,
            ArenaReset: self._emit_arena_reset,
            ArenaFree: self._emit_arena_free,
            ArenaAlloc: self._emit_arena_alloc,
            HeapAlloc: self._emit_heap_alloc,
            PointerCopy: self._emit_pointer_copy,
            Alloc: self._emit_alloc,
            Borrow: self._emit_borrow,
            Move: self._emit_move,
            GetAttr: self._emit_get_attr,
            SetAttr: self._emit_set_attr,
            Nullify: self._emit_nullify,
            Compute: self._emit_compute,
            RegionEnter: self._emit_region_enter,
            RegionExit: self._emit_region_exit,
            Label: self._emit_label,
            Assert: self._emit_assert,
            Jump: self._emit_jump,
            Branch: self._emit_branch,
            Return: self._emit_return,
            Call: self._emit_call,
            Spawn: self._emit_spawn,
            Await: self._emit_await,
            Load: self._emit_load,
        }

    def emit_lmir(self, instructions: List[MIRInstruction], pre_allocated: Set[str] = None, auto_arena: bool = False):
        if not hasattr(self, "lmir_dispatch_table"):
            self._build_lmir_dispatch_table()
            
        if pre_allocated is None: pre_allocated = set()
        self.local_types = {}
        if getattr(self, "current_class", None):
            self.local_types["self"] = self.current_class
        if getattr(self, "current_function", None) and hasattr(self.current_function, "parameters"):
            for p in self.current_function.parameters:
                p_name = self.sanitize_name(p.name) if hasattr(p, "name") else ""
                if not p_name:
                    continue
                p_level = getattr(p, "scope_level", 0)
                if p_level > 0:
                    p_name = f"{p_name}_L{p_level}"
                p_decl_type = getattr(p, "resolved_type", getattr(p, "declared_type", None))
                p_type = self.get_mangled_type_name(p_decl_type) if p_decl_type else "ZenValue"
                if p_type in ("None", "Variant", "Any", "ZenValue", "ZenList", "ZenString", "ZenObject"):
                    p_type = "ZenValue"
                self.local_types[p_name] = p_type
        self.call_return_types = {}
        self.current_arena = None
        self.pre_allocated_lmir = pre_allocated
        self.auto_arena_lmir = auto_arena

        for instr in instructions:
            if self.source_mapping and instr.line > 0:
                if instr.line != self.last_emitted_line or instr.filename != self.last_emitted_file:
                    fname = instr.filename if instr.filename else "unknown"
                    self.emit(f'#line {instr.line} "{fname}"')
                    self.last_emitted_line = instr.line
                    self.last_emitted_file = instr.filename

            handler = self.lmir_dispatch_table.get(type(instr))
            if handler:
                handler(instr)
            else:
                print(f"WARNING: No handler for LMIR instruction {type(instr)}")

    def _emit_try(self, instr: Try):
        self.emit("{")
        self.indent_level += 1
        self.emit("ZenExceptionContext ctx;")
        self.emit("ctx.defer_depth = ZenRuntime_get_defer_depth();")
        self.emit("ZenException_push_context(&ctx);")
        self.emit("if (setjmp(ctx.buf) == 0) {")
        self.indent_level += 1

    def _emit_catch(self, instr: Catch):
        self.emit("ZenException_pop_context();")
        self.indent_level -= 1
        self.emit("} else {")
        self.indent_level += 1
        self.emit("ZenException_pop_context();")

    def _emit_end_try(self, instr: EndTry):
        self.indent_level -= 1
        self.emit("}")
        self.indent_level -= 1
        self.emit("}")

    def _emit_raise(self, instr: Raise):
        self.emit(f"ZenException_raise({instr.value});")

    def _emit_arena_create(self, instr: ArenaCreate):
        self.current_arena = instr.arena_id
        if self.auto_arena_lmir:
            self.emit(f"{self.sanitize_name(instr.arena_id)} = ZenArena_create(0);")
            self.emit(f"ZenArena_push({self.sanitize_name(instr.arena_id)});")

    def _emit_arena_reset(self, instr: ArenaReset):
        self.emit(f"ZenArena_reset({self.sanitize_name(instr.arena_id)});")

    def _emit_arena_free(self, instr: ArenaFree):
        if self.auto_arena_lmir:
            self.emit(f"ZenArena_pop();")
            self.emit(f"ZenArena_free({self.sanitize_name(instr.arena_id)});")

    def _emit_arena_alloc(self, instr: ArenaAlloc):
        if instr.target not in self.pre_allocated_lmir:
            self.emit(f"ZenValue {instr.target};")
            self.emit(f"{instr.target} = ZEN_NOTHING_VAL; // Region: {instr.arena_id}")
            self.pre_allocated_lmir.add(instr.target)
        
        if instr.type:
             tname = self.get_mangled_type_name(instr.type)
             if tname in ("None", "Variant", "Any", "ZenValue", "ZenList", "ZenString"):
                  tname = "ZenObject"
             self.local_types[instr.target] = tname

    def _emit_heap_alloc(self, instr: HeapAlloc):
        if instr.target not in self.pre_allocated_lmir:
            self.emit(f"ZenValue {instr.target};")
            self.emit(f"{instr.target} = ZEN_NOTHING_VAL; // Heap")
            self.pre_allocated_lmir.add(instr.target)

    def _emit_pointer_copy(self, instr: PointerCopy):
        # SMIR lowers many assignments to PointerCopy — preserve class types.
        if instr.src in self.call_return_types:
            self.local_types[instr.dest] = self.call_return_types[instr.src]
            self.call_return_types[instr.dest] = self.call_return_types[instr.src]
        elif instr.src in self.local_types:
            self.local_types[instr.dest] = self.local_types[instr.src]
        self.emit(f"{instr.dest} = {instr.src};")

    def _emit_alloc(self, instr: Alloc):
        # Declarations are now handled at the start of the block in generate_lmir_block
        if instr.type:
            tname = self.get_mangled_type_name(instr.type)
            if tname in ("None", "Variant", "Any", "ZenValue", "ZenList", "ZenString", "ZenObject"):
                 tname = "ZenValue"
            
            self.local_types[instr.target] = tname

    def _emit_move(self, instr: Move):
        dest = instr.dest
        if instr.src in self.call_return_types:
            self.local_types[dest] = self.call_return_types[instr.src]
        elif instr.src in self.local_types:
            # Preserve class type through SSA moves (p2 = tmp_call_…)
            self.local_types[dest] = self.local_types[instr.src]
        
        if "." in dest:
            obj, prop_raw = dest.split(".", 1)
            prop = self.sanitize_name(prop_raw)
            if obj == "self":
                self.emit(f"self->{prop} = {instr.src};")
            else:
                tname = self.local_types.get(obj, "ZenObject")
                self.emit(f"((struct {tname}*){obj}.as.object)->{prop} = {instr.src};")
        else:
            self.emit(f"{dest} = {instr.src};")

    def _emit_borrow(self, instr: Borrow):
        self.emit(f"{instr.dest} = {instr.src};")

    def _module_key_for_attr(self, obj: str):
        """Resolve mangled/unmangled import alias to module basename for log.LEVEL_*.

        Package modules (lib/zen/log/log.zl) often mangle the alias `log` to
        `log_log` in GetAttr obj slots; map those back so we emit log_LEVEL_WARN.
        """
        aliases = getattr(self, "module_aliases", {}) or {}
        imported = getattr(self, "imported_modules", set()) or set()
        if obj in imported or obj in aliases:
            return aliases.get(obj, obj)
        for alias, mod in aliases.items():
            if obj in (alias, mod, f"{mod}_{alias}", f"{mod}_{mod}", f"{alias}_{alias}"):
                return mod
        return None

    def _emit_get_attr(self, instr: GetAttr):
        prefix = ""
        if instr.target not in self.pre_allocated_lmir and instr.target not in self.symbol_allocs:
            prefix = "ZenValue "
            self.pre_allocated_lmir.add(instr.target)
        
        if instr.obj in ("__builtin_math", "Math", "math"):
             if instr.prop == "pi":
                  self.emit(f"{prefix}{instr.target} = ZenValue_make_decimal(3.14159265358979323846);")
             elif instr.prop == "e":
                  self.emit(f"{prefix}{instr.target} = ZenValue_make_decimal(2.71828182845904523536);")
             else:
                  self.emit(f"{prefix}{instr.target} = ZenValue_make_nothing();")
        elif instr.obj == "self":
            self.emit(f"{prefix}{instr.target} = self->{self.sanitize_name(instr.prop)};")
        elif self._module_key_for_attr(instr.obj) is not None or instr.obj == "math" or (instr.obj[0].isupper() and instr.prop[0].isupper() and instr.obj != "Sys"):
             name = self.sanitize_name(instr.prop)
             if instr.obj[0].isupper() and name[0].isupper() and instr.obj != "Sys" and self._module_key_for_attr(instr.obj) is None:
                  self.emit(f"{prefix}{instr.target} = ZenVariant_{instr.obj}_{name};")
             else:
                  m_name = self._module_key_for_attr(instr.obj) or self.module_aliases.get(instr.obj, instr.obj)
                  self.emit(f"{prefix}{instr.target} = {m_name}_{name};")
        else:
            # Handle special virtual properties
            if instr.prop in ("length", "count"):
                 self.emit(f"{prefix}{instr.target} = ZenValue_get_length({instr.obj});")
            elif instr.prop == "kind":
                 # Type introspection; maps may also store a `kind` field (checked first).
                 self.emit(
                     f'{prefix}{instr.target} = ZenValue_get_kind({instr.obj});'
                 )
            else:
                tname = instr.type if (instr.type and instr.type not in ("ZenValue", "ZenObject", "Variant")) else self.local_types.get(instr.obj, "ZenObject")
                if tname in ("Variant", "ZenValue"):
                    tname = self.call_return_types.get(instr.obj, "ZenObject")
                if tname in ("Variant", "ZenValue"):
                    tname = "ZenObject"
                prop_path = instr.prop
                if "." not in prop_path: 
                     prop_path = self.sanitize_name(prop_path)
                # Structures are map-backed (see StructuralHandler); classes use C structs.
                global_structs = getattr(self, "global_structures", set()) or set()
                is_structure = tname in global_structs or (
                    tname
                    and any(
                        str(tname).endswith("_" + s) or str(tname) == s
                        for s in global_structs
                    )
                )
                # Also treat known structure simple names (Word) when module-prefixed type is text_Word
                if not is_structure and tname:
                    bare = str(tname).rsplit("_", 1)[-1]
                    if bare in global_structs or any(
                        str(s).endswith("_" + bare) or str(s) == bare for s in global_structs
                    ):
                        is_structure = True
                    # Module-prefixed structure: text_Word ∈ global_structures
                    if tname in global_structs:
                        is_structure = True

                # Boxed class instances (point_Point, …): struct fields
                if (
                    tname
                    and tname not in ("ZenObject", "Map", "ZenValue", None, "")
                    and not str(tname).startswith("tmp_")
                    and not is_structure
                ):
                    self.emit(
                        f"{prefix}{instr.target} = ((struct {tname}*){instr.obj}.as.object)->{prop_path};"
                    )
                # Maps / structures / unknown records: dynamic field lookup
                else:
                    self.emit(
                        f'{prefix}{instr.target} = ZenValue_get_field({instr.obj}, "{prop_path}");'
                    )
        
        if instr.target and instr.target.startswith("tmp_"):
             self.emit(f"(void){instr.target};")

    def _emit_set_attr(self, instr: SetAttr):
        if instr.obj == "self":
            self.emit(f"self->{self.sanitize_name(instr.prop)} = {instr.value};")
        elif instr.obj == "module":
            # Built-in module map (module.entry -> …)
            prop_path = instr.prop
            if "." not in prop_path:
                prop_path = self.sanitize_name(prop_path)
            self.emit(
                f'(void)ZenMap_set_value_at_key(module, ZenValue_make_string("{prop_path}"), {instr.value});'
            )
        elif instr.obj in self.imported_modules:
             m_name = self.module_aliases.get(instr.obj, instr.obj)
             self.emit(f"{m_name}_{self.sanitize_name(instr.prop)} = {instr.value};")
        else:
            tname = instr.type if (instr.type and instr.type not in ("ZenValue", "ZenObject", "Variant")) else self.local_types.get(instr.obj, "ZenObject")
            if tname in ("Variant", "ZenValue"): tname = "ZenObject"
            prop_path = instr.prop
            if "." not in prop_path: prop_path = self.sanitize_name(prop_path)
            # Maps / unknown records: dynamic key set (structures are map-backed)
            global_structs = getattr(self, "global_structures", set()) or set()
            is_structure = tname in global_structs or (
                tname
                and any(
                    str(tname).endswith("_" + s) or str(tname) == s
                    for s in global_structs
                )
            )
            if (
                tname in ("ZenObject", "Map", "ZenValue", None, "")
                or is_structure
                or str(tname).startswith("tmp_")
            ):
                self.emit(
                    f'(void)ZenMap_set_value_at_key({instr.obj}, ZenValue_make_string("{prop_path}"), {instr.value});'
                )
            else:
                self.emit(f"((struct {tname}*){instr.obj}.as.object)->{prop_path} = {instr.value};")

    def _emit_nullify(self, instr: Nullify):
        self.emit(f"{instr.target} = ZEN_NOTHING_VAL;")

    def _emit_compute(self, instr: Compute):
        variant_ops = {
            "+": "ZenValue_add", "-": "ZenValue_subtract", "*": "ZenValue_multiply", 
            "/": "ZenValue_divide", "%": "ZenValue_modulo", "**": "ZenValue_power",
            "==": "ZenValue_equal", "=": "ZenValue_equal", "!=": "ZenValue_not_equal", 
            "<": "ZenValue_less_than", ">": "ZenValue_greater_than",
            "<=": "ZenValue_less_than_or_equal", ">=": "ZenValue_greater_than_or_equal",
            "xor": "ZenValue_xor", "and": "ZenValue_and", "or": "ZenValue_or",
            # C-style && / || are common in stdlib; map to logical ops (bitwise
            # on booleans returns Nothing in the runtime).
            "&&": "ZenValue_and", "||": "ZenValue_or",
            "&": "ZenValue_bitwise_and", "|": "ZenValue_bitwise_or", "^": "ZenValue_bitwise_xor", "^^": "ZenValue_bitwise_xor",
            "<<": "ZenValue_left_shift", ">>": "ZenValue_right_shift",
            "..": "ZenValue_range_between",
            "..+": "ZenValue_range_open_start_inclusive",
            "..-": "ZenValue_range_exclusive_end",
            "...": "ZenValue_range_inclusive",
            "++": "ZenValue_op_append",
            "--": "ZenValue_op_remove",
            "in": "ZenValue_in",
        }
        if instr.left == "":
            unary_ops = {"-": "ZenValue_negate", "not": "ZenValue_not", "~": "ZenValue_bitwise_not"}
            vop = unary_ops.get(instr.op, "ZenValue_negate")
        else:
            vop = variant_ops.get(instr.op, "ZenValue_add")
        
        target_region = None
        if instr.target in self.symbol_allocs:
             target_region = self.symbol_allocs[instr.target].region
        
        pushed = False
        if target_region and target_region != self.current_arena and vop in ("ZenValue_add", "ZenString_concat"):
             if target_region == "global":
                  self.emit("ZenArena_push(NULL);")
             else:
                  name = self.sanitize_name(target_region)
                  if not name.startswith("block_"):
                       self.emit(f"ZenArena_push(({name}).as.arena);")
                  else:
                       self.emit(f"ZenArena_push({name});")
             pushed = True
        
        if instr.left == "":
            self.emit(f"{instr.target} = {vop}({self._format_zen_value_arg(instr.right)});")
        else:
            left = self._format_zen_value_arg(instr.left)
            right = self._format_zen_value_arg(instr.right)
            self.emit(f"{instr.target} = {vop}({left}, {right});")
        
        if instr.target and instr.target.startswith("tmp_"):
             self.emit(f"(void){instr.target};")
        
        if pushed:
             self.emit("ZenArena_pop();")

    def _emit_region_enter(self, instr: RegionEnter):
        self.emit("{")
        self.indent_level += 1
        if isinstance(instr.id, str) and (instr.id.startswith("block_") or instr.id.startswith("loop_") or instr.id.startswith("when_") or instr.id.startswith("func_")):
             self.emit(f"{instr.id} = ZenArena_create(0);")
             self.emit(f"ZenArena_push({instr.id});")
        else:
             self.emit(f"ZenArena_push(({instr.id}).as.arena);")

    def _emit_region_exit(self, instr: RegionExit):
        self.emit("ZenArena_pop();")
        if isinstance(instr.id, str) and (instr.id.startswith("block_") or instr.id.startswith("loop_") or instr.id.startswith("when_") or instr.id.startswith("func_")):
             self.emit(f"ZenArena_free({instr.id});")
        self.indent_level -= 1
        self.emit("}")

    def _emit_label(self, instr: Label):
        self.emit(f"{instr.name}:;")

    def _emit_assert(self, instr: Assert):
        # msg = f'"{instr.message}"' if instr.message else "NULL"
        self.emit(f"if (!({instr.condition}).as.boolean) {{ fprintf(stderr, \"Assertion failed at %s:%d\\n\", \"{instr.filename}\", {instr.line}); exit(1); }}")

    def _emit_jump(self, instr: Jump):
        self.emit(f"goto {instr.target};")

    def _emit_branch(self, instr: Branch):
        self.emit(f"if (({instr.condition}).as.boolean) {{")
        if instr.true_label:
            self.indent_level += 1
            self.emit(f"goto {instr.true_label};")
            self.indent_level -= 1
        self.emit("}")
        if instr.false_label:
            self.emit(f"else {{ goto {instr.false_label}; }}")

    def _emit_return(self, instr: Return):
        if instr.value and instr.value != "None":
            # Class methods that `<- self` yield a raw pointer; box as ZenValue.
            if instr.value == "self":
                self.emit("__ret_val = ZenValue_from_object(self);")
            else:
                self.emit(f"__ret_val = {instr.value};")
        else:
            if hasattr(self, "current_function_name") and self.current_function_name == "main":
                self.emit("__ret_val = 0;")
            else:
                self.emit("__ret_val = ZEN_NOTHING_VAL;")
        
        self.emit(f"goto {self.current_exit_label};")

    def _emit_call(self, instr: Call):
        is_dynamic = False
        callee_str = instr.callee
            
        if callee_str in (
            "write_line", "writeln", "io_write_line", "io_writeln",
            "ZenIO_writeln", "ZenIO_write_line",
        ):
            callee_str = "ZenIO_write_line"
        elif callee_str in ("write", "io_write") and not callee_str.startswith("Zen"):
            # Prefer value write for bare write when not already mapped.
            if callee_str == "write":
                callee_str = "ZenIO_write_value"
        elif callee_str in ("read", "readln", "read_line", "io_read", "io_readln"):
            callee_str = "ZenIO_read_value"
        elif callee_str == "type":
            callee_str = "ZenValue_get_kind"
        elif callee_str == "math_abs":
            callee_str = "ZenMath_abs"
        elif callee_str == "math_min":
            callee_str = "ZenMath_min"
        elif callee_str == "math_max":
            callee_str = "ZenMath_max"
        elif callee_str == "math_clamp":
            callee_str = "ZenMath_clamp"
        elif callee_str == "math_round":
            callee_str = "ZenMath_round"
        elif callee_str == "math_floor":
            callee_str = "ZenMath_floor"
        elif callee_str == "math_ceil":
            callee_str = "ZenMath_ceil"
        elif callee_str == "math_sqrt":
            callee_str = "ZenMath_sqrt"
        elif callee_str in ("math_pow", "math_power"):
            callee_str = "ZenMath_power"
        if callee_str == "List_from_args": callee_str = "ZenList_make_from_arguments"
        elif callee_str == "Map_from_args": callee_str = "ZenMap_make_from_arguments"
        elif callee_str == "Value_get_index": callee_str = "ZenValue_get_at"
        elif callee_str == "Value_set_index": callee_str = "ZenValue_set_at"
        elif callee_str == "Value_is_type_name": callee_str = "ZenValue_is_type_name"
        elif callee_str == "write": callee_str = "ZenIO_write_line"

        if callee_str == "ZenList_make_from_arguments" or callee_str == "ZenMap_make_from_arguments":
            formatted_args = []
            if instr.args:
                formatted_args.append(instr.args[0])
                formatted_args.extend(self._format_zen_value_arg(arg) for arg in instr.args[1:])
            call_args = formatted_args
        elif callee_str == "ZenValue_make_variant":
            # (enum_name, variant_name, n_params:int, ...values)
            formatted_args = []
            if instr.args and len(instr.args) >= 3:
                formatted_args.append(self._format_zen_value_arg(instr.args[0]))
                formatted_args.append(self._format_zen_value_arg(instr.args[1]))
                formatted_args.append(str(instr.args[2]))  # raw int count
                formatted_args.extend(self._format_zen_value_arg(a) for a in instr.args[3:])
            call_args = formatted_args
        elif callee_str == "ZenValue_from_closure":
            # (void* fn, int arity, int n_caps, ZenValue cap0, ...)
            formatted_args = []
            if instr.args and len(instr.args) >= 3:
                formatted_args.append(str(instr.args[0]))  # raw fn pointer cast
                formatted_args.append(str(instr.args[1]))  # arity
                formatted_args.append(str(instr.args[2]))  # n_caps
                formatted_args.extend(self._format_zen_value_arg(a) for a in instr.args[3:])
            call_args = formatted_args
        elif callee_str == "ZenValue_from_function":
            # Keep raw function-pointer cast; do not box as ZenValue.
            call_args = [str(a) for a in instr.args]
        else:
            call_args = [self._format_zen_value_arg(arg) for arg in instr.args]

        if "." in callee_str:
            obj_name, prop_name = callee_str.split(".", 1)
            if obj_name in self.imported_modules or obj_name in getattr(self, "module_aliases", {}):
                 m_name = self.module_aliases.get(obj_name, obj_name)
                 # Prefer stdlib module function (io_writeln) over ZenIO_* freestanding.
                 callee_str = f"{m_name}_{self.sanitize_name(prop_name)}"
                 # io.writeln → ZenIO_write_line (no phantom receiver)
                 if callee_str in ("io_writeln", "io_write_line"):
                     callee_str = "ZenIO_write_line"
                     if call_args and call_args[0] in ("IO", "io", obj_name):
                         call_args = call_args[1:]
                 elif callee_str in ("io_write",):
                     callee_str = "ZenIO_write_value"
                     if call_args and call_args[0] in ("IO", "io", obj_name):
                         call_args = call_args[1:]
                 elif callee_str.startswith("io_") and prop_name in ("info", "warn", "error", "debug", "flush", "read"):
                     # Map common io module methods to freestanding runtime when useful
                     pass
            elif obj_name in self.global_enums and prop_name and prop_name[0].isupper():
                callee_str = f"ZenVariant_{obj_name}_{prop_name}"
            elif obj_name in ("IO", "Sys", "Memory", "io", "memory", "out", "in", "stdout", "stderr", "stdin", "z_stdout", "z_stderr", "z_stdin", "__builtin", "__builtin_io", "__builtin_sys", "__builtin_memory", "__builtin_output", "__builtin_input", "__builtin_file", "__builtin_math", "math", "Math", "__builtin_range", "Str", "String", "__builtin_string", "List", "__builtin_list", "Map", "__builtin_map", "sys", "file", "string", "__builtin_time", "time", "__builtin_term", "term", "__builtin_process", "process", "__builtin_regex", "__builtin_reflect", "__builtin_net", "net", "__builtin_vm", "vm", "VM"):
                if prop_name in ("create_arena", "__builtin_create_arena"):
                    callee_str = "ZenMemory_create_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("free_arena", "__builtin_free_arena"):
                    callee_str = "ZenMemory_free_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("reset_arena", "__builtin_reset_arena"):
                    callee_str = "ZenMemory_reset_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("push_arena", "__builtin_push_arena"):
                    callee_str = "ZenMemory_push_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("pop_arena", "__builtin_pop_arena"):
                    callee_str = "ZenMemory_pop_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("using_arena", "__builtin_using_arena"):
                    callee_str = "ZenMemory_using_arena"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif prop_name in ("arena_depth", "__builtin_arena_depth"):
                    callee_str = "ZenMemory_arena_depth"
                    if call_args and call_args[0] in ("__builtin_memory", "Memory", "memory", "__builtin"):
                        call_args = call_args[1:]
                elif obj_name == "__builtin_regex" or (
                    prop_name in ("match", "search", "replace", "split", "find_all")
                    and obj_name in ("__builtin_regex",)
                ):
                    callee_str = f"ZenRegex_{prop_name}"
                    if call_args and call_args[0] in ("__builtin_regex",):
                        call_args = call_args[1:]
                elif prop_name == "read" and obj_name.startswith("__builtin"):
                    if obj_name == "__builtin_file": callee_str = "ZenIO_read_file"
                    else: callee_str = "ZenIO_read"
                elif obj_name == "__builtin" and prop_name in ("error", "error_literal", "raise"):
                    # Error constructors are free functions; drop any phantom receiver.
                    if prop_name == "error_literal":
                        callee_str = "ZenValue_make_error_literal"
                    else:
                        callee_str = "ZenValue_make_error_message"
                    if call_args and call_args[0] in ("__builtin", "ZenValue_make_nothing()"):
                        call_args = call_args[1:]
                elif prop_name in ("write", "writeln", "write_line", "info", "warn", "error", "debug", "flush", "read", "append", "write_file", "read_file", "exists", "list_dir", "mkdir", "mkdir_p", "remove", "is_file", "is_dir", "open") and obj_name in (
                    "IO", "io", "__builtin_io", "__builtin_output", "__builtin_input",
                ) or (
                    prop_name in ("write", "writeln", "write_line", "info", "warn", "error", "debug", "append", "write_file", "read_file", "exists", "list_dir", "mkdir", "mkdir_p", "remove", "is_file", "is_dir", "open")
                    and obj_name.startswith("__builtin")
                ):
                    # Parenthesize intent: IO/io aliases + builtins → free ZenIO_* funcs
                    if prop_name == "write":
                        callee_str = "ZenIO_write_value"
                    elif prop_name in ("writeln", "write_line"):
                        callee_str = "ZenIO_write_line"
                    elif prop_name == "flush":
                        callee_str = "ZenIO_flush"
                    elif prop_name == "read":
                        callee_str = "ZenIO_read_value"
                    elif prop_name == "warn":
                        callee_str = "ZenIO_write_warning"
                    elif prop_name in ("info", "error", "debug"):
                        callee_str = f"ZenIO_write_{prop_name}"
                    else:
                        callee_str = f"ZenIO_{prop_name}"
                    # Drop module/capability receiver — free C functions.
                    if call_args and (
                        call_args[0] in ("IO", "io")
                        or str(call_args[0]).startswith("__builtin")
                        or (instr.args and instr.args[0] == obj_name and obj_name in ("IO", "io"))
                    ):
                        call_args = call_args[1:]
                elif obj_name in ("stdout", "z_stdout"):
                    if prop_name == "write":
                        callee_str = "ZenIO_write_value"
                    elif prop_name in ("writeln", "write_line"):
                        callee_str = "ZenIO_write_line"
                    elif prop_name == "flush":
                        callee_str = "ZenIO_flush"
                    if call_args and call_args[0] in ("stdout", "z_stdout", obj_name):
                        call_args = call_args[1:]
                elif obj_name in ("stderr", "z_stderr"):
                    if prop_name == "write":
                        callee_str = "ZenIO_write_stderr"
                    elif prop_name in ("writeln", "write_line"):
                        callee_str = "ZenIO_write_line_stderr"
                    elif prop_name == "flush":
                        callee_str = "ZenIO_flush_stderr"
                    if call_args and call_args[0] in ("stderr", "z_stderr", obj_name):
                        call_args = call_args[1:]
                elif obj_name in ("stdin", "z_stdin"):
                    if prop_name in ("read", "readln", "read_line"):
                        callee_str = "ZenIO_read_value"
                    elif prop_name == "lines":
                        callee_str = "ZenIO_stdin_lines"
                    if call_args and call_args[0] in ("stdin", "z_stdin", obj_name):
                        call_args = call_args[1:]
                elif obj_name in ("__builtin_math", "Math", "math"):
                     if prop_name == "pow": prop_name = "power"
                     callee_str = f"ZenMath_{prop_name}"
                     # ZenMath_* take ZenValue args only (no receiver object).
                     if call_args and call_args[0] in ("__builtin_math", "Math", "math"):
                         call_args = call_args[1:]
                elif obj_name == "__builtin_range" or obj_name == "Range":
                     callee_str = f"range_{prop_name}"
                elif obj_name in ("Str", "String", "__builtin_string", "string"):
                     if prop_name == "length": callee_str = "ZenString_get_length"
                     elif prop_name == "to_upper": callee_str = "ZenString_to_uppercase"
                     elif prop_name == "to_lower": callee_str = "ZenString_to_lowercase"
                     elif prop_name == "at": callee_str = "ZenString_get_character_at_index"
                     elif prop_name == "substring": callee_str = "ZenString_get_substring"
                     elif prop_name == "to_string": callee_str = "ZenValue_to_string"
                     elif prop_name == "index_of": callee_str = "ZenString_find_index"
                     else: callee_str = f"ZenString_{prop_name}"
                elif obj_name in ("List", "__builtin_list"):
                     callee_str = f"ZenList_{prop_name}"
                elif obj_name in ("Map", "__builtin_map"):
                     callee_str = f"ZenMap_{prop_name}"
                elif obj_name in ("file", "__builtin_file"):
                     if prop_name == "write": callee_str = "ZenIO_write_file"
                     elif prop_name == "read": callee_str = "ZenIO_read_file"
                     elif prop_name == "exists": callee_str = "ZenIO_file_exists"
                     else: callee_str = f"ZenIO_{prop_name}"
                elif obj_name in ("sys", "Sys", "__builtin_sys"):
                     callee_str = f"ZenSystem_{prop_name}"
                     # Free functions unless first arg is already the receiver placeholder
                     if call_args and call_args[0] in ("__builtin_sys", "sys", "Sys"):
                         call_args = call_args[1:]
                elif obj_name in ("time", "__builtin_time"):
                     callee_str = f"ZenTime_{prop_name}"
                     if call_args and call_args[0] in ("__builtin_time", "time"):
                         call_args = call_args[1:]
                elif obj_name in ("term", "__builtin_term"):
                     callee_str = f"ZenTerm_{prop_name}"
                     if call_args and call_args[0] in ("__builtin_term", "term"):
                         call_args = call_args[1:]
                elif obj_name in ("process", "__builtin_process"):
                     callee_str = f"ZenProcess_{prop_name}"
                     if call_args and call_args[0] in ("__builtin_process", "process"):
                         call_args = call_args[1:]
                elif obj_name in ("__builtin_net", "net"):
                    if prop_name == "http_request":
                        callee_str = "ZenNet_http_request"
                        if call_args and call_args[0] in ("__builtin_net", "net"):
                            call_args = call_args[1:]
                        # Pad optional body/headers so C always gets 4 args
                        while len(call_args) < 4:
                            call_args.append("ZenValue_make_nothing()")
                    else:
                        callee_str = f"ZenNet_{prop_name}"
                        if call_args and call_args[0] in ("__builtin_net", "net"):
                            call_args = call_args[1:]
                elif obj_name in ("__builtin_reflect",):
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
                     callee_str = mapping.get(prop_name, f"ZenReflect_{prop_name}")
                     # Drop capability receiver — free C functions.
                     if call_args and call_args[0] in ("__builtin_reflect",):
                         call_args = call_args[1:]
                elif obj_name in ("__builtin_vm", "vm", "VM"):
                     if prop_name in ("run_file", "run_bytecode", "run"):
                         callee_str = "ZenValue_run_bytecode_file"
                     else:
                         callee_str = f"ZenVM_{prop_name}"
                     if call_args and call_args[0] in ("__builtin_vm", "vm", "VM"):
                         call_args = call_args[1:]
                else:
                    callee_str = f"Zen{obj_name}_{prop_name}"
            elif obj_name[0].isupper() and prop_name[0].isupper() and obj_name != "Sys":
                 callee_str = f"ZenVariant_{obj_name}_{prop_name}"
            elif obj_name[0].isupper() and not prop_name[0].isupper():
                 # Bare Type.method → prefer module-prefixed if structure lives in another file
                 callee_str = f"{obj_name}_{self.sanitize_name(prop_name)}"
                 global_structs = getattr(self, "global_structures", set()) or set()
                 for s in global_structs:
                     if s.endswith("_" + obj_name) or s == obj_name:
                         # Use full mangled structure name (text_Paragraph_wrap)
                         if s != obj_name:
                             callee_str = f"{s}_{self.sanitize_name(prop_name)}"
                         break
                 if instr.args and (instr.args[0] == "self" or "self->" in instr.args[0]):
                      args_str = ", ".join([f"({obj_name}*)self"] + instr.args[1:])
            else:
                # Real class/struct types only — NOT ZenValue/List/Map (closures
                # capture lists as ZenValue; treating them as classes emitted
                # `(ZenValue*)seen.as.object` into ZenValue_append and broke -g).
                _opaque = {
                    "ZenObject", "ZenValue", "List", "Map", "Variant", "Any",
                    "String", "string", "Integer", "Decimal", "Boolean",
                    "Nothing", "nothing", "",
                }
                t_local = self.local_types.get(obj_name, "ZenObject")
                is_known_class = (
                    obj_name in self.local_types
                    and t_local not in _opaque
                )
                coll_methods = (
                    "length", "size", "count", "at", "append", "push", "enqueue",
                    "remove", "remove_at", "pop", "dequeue", "peek", "keys",
                    "values", "items", "contains", "has", "join", "get",
                    # string methods on ZenValue receivers
                    "substring", "slice", "starts_with", "ends_with", "trim",
                    "to_upper", "to_lower", "to_number", "to_integer", "to_decimal",
                    "index_of", "replace", "split", "to_string",
                )
                if prop_name in coll_methods and not is_known_class:
                    mapping = {
                        "length": "get_length", "size": "get_length", "count": "get_length",
                        "at": "get_at", "keys": "get_keys", "values": "get_values",
                        "items": "get_items",
                        "pop": "pop_dispatch", "dequeue": "pop_dispatch",
                        "push": "append", "enqueue": "append",
                        "has": "contains",
                        "get": "get_at",  # Map/List get(key|index)
                        "substring": "get_substring",
                        "slice": "get_substring",
                        "index_of": "index_of",
                        "to_upper": "to_upper",
                        "to_lower": "to_lower",
                        "to_number": "to_number",
                        "to_integer": "to_number",
                        "to_decimal": "to_number",
                        "to_string": "to_string_dispatch",
                    }
                    m_prop = mapping.get(prop_name, prop_name)
                    # Prefer ZenString_* free functions when available; else ZenValue_*
                    string_direct = {
                        "trim": "ZenString_trim",
                        "replace": "ZenString_replace",
                        "split": "ZenString_split",
                        "starts_with": "ZenString_starts_with",
                        "ends_with": "ZenString_ends_with",
                        "to_upper": "ZenString_to_uppercase",
                        "to_lower": "ZenString_to_lowercase",
                        "index_of": "ZenString_find_index",
                        "substring": "ZenString_get_substring",
                        "slice": "ZenString_get_substring",
                        "contains": "ZenString_contains",
                    }
                    if prop_name in string_direct:
                        callee_str = string_direct[prop_name]
                    elif prop_name in ("to_number", "to_integer", "to_decimal"):
                        callee_str = "ZenValue_to_number"
                    elif prop_name == "to_string":
                        callee_str = "ZenValue_to_string"
                    elif prop_name == "slice":
                        # List or string: unified dispatcher
                        callee_str = "ZenValue_slice"
                    else:
                        callee_str = f"ZenValue_{m_prop}"
                    # Receiver must be ZenValue (by name), never Class* / as.object.
                    if instr.args and (
                        instr.args[0] == obj_name
                        or str(instr.args[0]).startswith(obj_name)
                    ):
                        call_args = list(instr.args)
                    else:
                        call_args = [obj_name] + list(instr.args)
                    # substring/slice(start) → (start, length) for C runtime arity
                    if prop_name in ("substring", "slice") and len(call_args) == 2:
                        end_tmp = f"__substr_end_{instr.target}" if instr.target else "__substr_end"
                        if end_tmp not in self.pre_allocated_lmir:
                            self.emit(f"ZenValue {end_tmp} = ZenValue_get_length({call_args[0]});")
                            self.pre_allocated_lmir.add(end_tmp)
                        else:
                            self.emit(f"{end_tmp} = ZenValue_get_length({call_args[0]});")
                        call_args = [call_args[0], call_args[1], end_tmp]
                    if prop_name == "slice":
                        callee_str = "ZenValue_slice"
                else:
                    tname = self.local_types.get(obj_name, "ZenObject")
                    tname = tname.replace(".", "_")
                    callee_str = f"{tname}_{self.sanitize_name(prop_name)}"
                    if obj_name == "self":
                         call_args = ["self"] + instr.args[1:]
                    else:
                         call_args = [f"({tname}*){obj_name}.as.object"] + instr.args[1:]
        else:
            if callee_str.startswith("tmp_") or callee_str in self.local_types or callee_str in self.pre_allocated_lmir:
                # Dynamic callable (lambda / first-class function value).
                is_dynamic = True
                argc = len(call_args)
                if argc == 0:
                    callee_str = f"ZenValue_call({callee_str})"
                else:
                    args_joined = ", ".join(call_args)
                    callee_str = f"ZenValue_apply({callee_str}, {argc}, {args_joined})"
                call_args = []
            else:
                # Remap bare math names that escaped mangling (avoid libm collision).
                math_map = {
                    "sin": "ZenMath_sin", "cos": "ZenMath_cos", "sqrt": "ZenMath_sqrt",
                    "floor": "ZenMath_floor", "ceil": "ZenMath_ceil", "abs": "ZenMath_abs",
                    "pow": "ZenMath_power", "power": "ZenMath_power",
                }
                # Bare memory ops if capability path was stripped to just the method.
                mem_map = {
                    "create_arena": "ZenMemory_create_arena",
                    "free_arena": "ZenMemory_free_arena",
                    "reset_arena": "ZenMemory_reset_arena",
                    "push_arena": "ZenMemory_push_arena",
                    "pop_arena": "ZenMemory_pop_arena",
                    "using_arena": "ZenMemory_using_arena",
                    "arena_depth": "ZenMemory_arena_depth",
                }
                if callee_str in math_map:
                    callee_str = math_map[callee_str]
                elif callee_str in mem_map:
                    callee_str = mem_map[callee_str]
                else:
                    callee_str = self.sanitize_name(callee_str)

        if callee_str == "ZenIO_zl_read" and getattr(self.current_function, "name", None) == "read_file":
            callee_str = "ZenIO_read_file"
        elif callee_str == "ZenIO_zl_write" and getattr(self.current_function, "name", None) == "write_file" and len(instr.args) == 2:
            callee_str = "ZenIO_write_file"

        if callee_str.startswith("ZenVariant_") and call_args:
            enum_name = callee_str[len("ZenVariant_"):].rsplit("_", 1)[0]
            if call_args and call_args[0] == enum_name:
                call_args = call_args[1:]

        if callee_str in ("ZenIO_write_line", "ZenIO_write_line_stderr") and len(call_args) == 0:
            call_args = ['ZenValue_make_string("")']
        elif callee_str in ("ZenIO_write_value", "ZenIO_write_stderr", "ZenIO_read_value") and len(call_args) == 0:
            call_args = ['ZenValue_make_nothing()']
        
        args_str = ", ".join(call_args)

        if callee_str in self.global_classes:
            if instr.target:
                self.call_return_types[instr.target] = callee_str
            callee_str = f"{callee_str}_{callee_str}"

        # Track return class type so field access (p.x) and methods (rng.next)
        # use real Class_* symbols instead of ZenObject_* / Map get_field.
        if instr.target and not is_dynamic:
            ret_type = None
            if callee_str.endswith("_new"):
                ret_type = callee_str[: -len("_new")]
            elif callee_str.endswith("_seed"):
                # random_seed → random_RNG (constructor wrapper)
                ret_type = callee_str[: -len("_seed")] + "_RNG"
            else:
                # Heuristic: module_Class_method → module_Class when method returns instance
                parts = callee_str.rsplit("_", 1)
                if len(parts) == 2:
                    class_cand, meth = parts[0], parts[1]
                    # Same-type fluent / scope helpers (Point.translate → Point,
                    # text_Word_capitalize → text_Word). Skip methods that return
                    # a different type (e.g. center → Point, to_words → List).
                    if meth in (
                        "new", "translate", "scale", "add", "sub", "normalize",
                        "to_vector", "midpoint", "direction",
                        "capitalize", "wrap",
                    ):
                        if "_" in class_cand or (class_cand and class_cand[0].isupper()):
                            ret_type = class_cand
            # Prefer resolved TypeClass on the Call temp (Alloc type) when present.
            if instr.target in getattr(self, "symbol_allocs", {}):
                alloc = self.symbol_allocs[instr.target]
                at = getattr(alloc, "type", None)
                if at is not None:
                    t_alloc = self.get_mangled_type_name(at)
                    if t_alloc and t_alloc not in (
                        "ZenValue", "ZenObject", "Variant", "Any", "None",
                        "List", "Map", "String", "Integer", "Decimal", "Boolean",
                    ):
                        ret_type = t_alloc
            if ret_type:
                self.call_return_types[instr.target] = ret_type
                self.local_types[instr.target] = ret_type

        if instr.target:
             target_region = None
             if instr.target in self.symbol_allocs:
                  target_region = self.symbol_allocs[instr.target].region
             
             pushed = False
             if target_region and target_region != self.current_arena:
                  if target_region == "global":
                       self.emit("ZenArena_push(NULL);")
                  else:
                       name = self.sanitize_name(target_region)
                       if not name.startswith("block_"):
                            self.emit(f"ZenArena_push(({name}).as.arena);")
                       else:
                            self.emit(f"ZenArena_push({name});")
                  pushed = True

             target_str = f"{instr.target} = "
             if is_dynamic:
                  # callee_str already includes full call expression
                  self.emit(f"{target_str}{callee_str};")
             else:
                  self.emit(f"{target_str}{callee_str}({args_str});")
             
             if instr.target and instr.target.startswith("tmp_"):
                  self.emit(f"(void){instr.target};")
             
             if pushed:
                  self.emit("ZenArena_pop();")
        else:
             if is_dynamic:
                  self.emit(f"{callee_str};")
             else:
                  self.emit(f"{callee_str}({args_str});")

    def _emit_spawn(self, instr: Spawn):
        callee_str = self.sanitize_name(instr.callee)
        wrapper_str = f"{callee_str}_wrapper"
        call_args = [self._format_zen_value_arg(arg) for arg in instr.args]
        args_str = ", ".join(call_args)
        
        target_str = ""
        if instr.target:
             target_str = f"{instr.target} = "
        
        if args_str:
             self.emit(f"{target_str}ZenTask_spawn({wrapper_str}, {len(instr.args)}, (ZenValue[]){{{args_str}}});")
        else:
             self.emit(f"{target_str}ZenTask_spawn({wrapper_str}, 0, NULL);")

    def _emit_await(self, instr: Await):
        self.emit(f"{instr.target} = ZenTask_wait({instr.handle});")

    def _emit_load(self, instr: Load):
        val = instr.source
        if instr.type == "string" or (val.startswith("`") and val.endswith("`")):
            inner = val
            if inner.startswith("`") and inner.endswith("`"):
                inner = inner[1:-1]
            inner = inner.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\x1b", "\\x1b")
            val = f'ZenValue_make_string("{inner}")'
        elif instr.type in ("int", "Integer", "IntegerLite") or (val.isdigit() and instr.type != "bool"):
            val = f"ZenValue_make_integer({val})"
        elif instr.type in ("decimal", "Decimal"):
            val = f"ZenValue_make_decimal({val})"
        elif instr.type in ("bool", "Boolean"):
            val = 1 if str(val).lower() in ("true", "1") else 0
            val = f"ZenValue_make_boolean({val})"
        elif instr.type in ("rune", "Rune", "Character"):
            val = f"ZenValue_make_integer({val})"
        elif val.startswith("'") and val.endswith("'"):
            val = f"ZenValue_make_integer({val})"
        elif val == "true" or val == "false":
            val = 1 if val == "true" else 0
            val = f"ZenValue_make_boolean({val})"
        
        if instr.target not in self.pre_allocated_lmir and instr.target.startswith("tmp_"):
             self.emit(f"ZenValue {instr.target};")
             self.pre_allocated_lmir.add(instr.target)
        
        self.emit(f"{instr.target} = {val};")

    def generate_lmir_block(self, node: ASTNode, filename: str = None, pre_allocated: List[str] = None, auto_arena: bool = False):
        self.emit("// DEBUG: generate_lmir_block")
        smir_gen = SMIRGenerator(
            filename=filename, 
            main_file=self.main_file, 
            global_variable_names=getattr(self, "global_variable_names", set()),
            pending_lambdas=getattr(self, "pending_lambdas", []),
            module_aliases=getattr(self, "module_aliases", {}),
            current_scope=getattr(self, "current_scope", None),
            imported_modules=getattr(self, "imported_modules", set()),
        )
        # Share lambda prototype collection with the outer CodeGenerator.
        smir_gen.lambda_forward_decls = getattr(self, "lambda_forward_decls", [])
        smir_gen._lambda_fwd_names = getattr(self, "_lambda_fwd_names", set())
        self.lambda_forward_decls = smir_gen.lambda_forward_decls
        self._lambda_fwd_names = smir_gen._lambda_fwd_names
        instructions = smir_gen.generate(node, pre_allocated_symbols=pre_allocated)
        
        # 1. Collect and emit ALL declarations at the top
        seen_decls = set(pre_allocated) if pre_allocated else set()
        globals_set = getattr(self, "global_variable_names", set()) or set()
        for instr in instructions:
             if isinstance(instr, Alloc):
                  # Globals are declared at file scope; do not redeclare as locals.
                  if instr.target in globals_set or instr.target.startswith("ZenVariant_"):
                       seen_decls.add(instr.target)
                       continue
                  if instr.target not in seen_decls:
                       self.emit(f"ZenValue {instr.target} = ZEN_NOTHING_VAL;")
                       seen_decls.add(instr.target)
             elif isinstance(instr, RegionEnter):
                  if isinstance(instr.id, str) and (instr.id.startswith("block_") or instr.id.startswith("loop_") or instr.id.startswith("when_") or instr.id.startswith("func_")):
                       if instr.id not in seen_decls:
                            self.emit(f"ZenArena* {instr.id} = NULL;")
                            seen_decls.add(instr.id)
        
        if not self.scope:
             from Checker.Scope import RegionNode
             region_root = RegionNode("global")
        else:
             region_root = self.scope.global_region
        
        analyzer = SMIRAnalyzer(instructions, region_root)
        analyzer.analyze()
        
        lowerer = SMIRLowerer(instructions, global_variable_names=getattr(self, "global_variable_names", set()))
        lmir_instructions = lowerer.lower()
        
        self.emit_lmir(lmir_instructions, pre_allocated=seen_decls, auto_arena=auto_arena)
