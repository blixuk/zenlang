# Purpose

Shared C runtime for native Zenlang executables. Used by bootstrap `-g` (CCompile) and by self-host native builds. Single high-level tree — not nested under bootstrap.

# Ownership

Runtime / native execution maintainers.

# Local Contracts

- **Canonical path:** repository root `runtime/`.
- `bootstrap/Transpiler/runtime` is a **symlink** to this tree (compat for older relative paths).
- High-level language semantics belong in `lib/zen/` or the compiler, not here.
- **Memory product (project-wide):** automatic lifetime by default; opt-in regions/arenas/pointers for sensitive code. Selfhost does not depend on a MIR mid-end — see `selfhost/PARITY.md` *Backend & memory decision*.
- **ZenValue** is the language value ABI (compiled ↔ interpreted mix). A script **bytecode VM** belongs here when THREE_LAYER phase 3 starts. Compiler Token/AST structs may live here or as typed Zen classes — see [selfhost/THREE_LAYER.md](../selfhost/THREE_LAYER.md).
- **Automatic path:** `ZenRuntime_allocate` → process `malloc` when neither stack has an arena. Lists/maps/strings use process heap. No user free for ordinary values.
- **Global String Interning Pool (Phase 5.4):** `ZenValue_make_string` interns identifiers, keywords, AST keys, and qualified symbols up to 512 bytes (with a 1,048,576 live symbol capacity and dynamic table resizing) using length-prefixed slot matching. String comparisons in `ZenValue_equal`, `zen_map_keys_equal`, and `ZenValue_is_variant` evaluate via single-instruction pointer equality `a.as.string == b.as.string`. Long emitted C source strings remain separate heap allocations.
- **Two stacks:** SMIR **frame** stack (`ZenArena_push/pop` for function regions) is separate from **user** stack (`ZenMemory_push_arena` / `pop_arena`). RegionExit must not undo user pushes.
- **Chunk-chained Arena Allocator (Phase 5.3):** `ZenArena` manages a linked chain of contiguous memory blocks (`ZenArenaChunk`). Allocations bump a pointer within the active chunk without `realloc`, guaranteeing stable pointer addresses for AST nodes and collections.
- **Collections Arena Integration:** `ZenList_make_from_arguments` performs single-pass exact-size allocation via `ZenRuntime_allocate`. When an arena is active, list and map nodes/entries are bump-allocated in contiguous cache lines.
- **Introspection & Profiling:** `ZenMemory_using_arena` / `arena_depth` report **user** stack depth. `ZenMemory_arena_allocated`, `ZenMemory_arena_capacity`, `ZenMemory_arena_chunks`, and `ZenMemory_arena_stats` inspect memory footprint across arena chunk chains (`allocated`, `capacity`, `chunks`). `ZenString_byte_at` provides fast 0-indexed byte code inspection.
- Layout: `core/`, `collections/`, `concurrency/`, `io/`, `memory/`, `bootstrap_runtime.*`, plus `main_wrapper.c` for host entry where needed.
- Public surface via `bootstrap_runtime.h` / `zen_*.h` and `ZenTerm_*` / `ZenProcess_*` / `ZenTime_*` / `ZenMemory_*` / `ZenRegex_*` sys APIs in `core/`. `ZenTerm_poll_key` caches a `zen_term_none_key_singleton` map on poll timeout to achieve zero-allocation key polling in game and event loops.
- File IO (`io/zen_io.c`): `ZenIO_list_dir` returns empty list on failure; `ZenIO_file_exists` uses `stat`; `ZenIO_mkdir` / `ZenIO_mkdir_p` for directories.
- Net (`core/zen_net.c`): `ZenNet_http_request` via curl (`-g`); interpret uses urllib. Returns `{status, body, headers}`.
- Ambient Streams & CLI Globals (`core/zen_sys.c`, `io/zen_io.c`): `z_stdout`, `z_stderr`, `z_stdin` are ambient stream map instances exposing `write`, `writeln`, `flush`, `read`, `readln`, `lines`. `z_args` holds CLI arguments list (`module.args` attached). `z_env` holds process environment map. `ZenIO_write_stderr`, `ZenIO_write_line_stderr`, `ZenIO_flush_stderr`, `ZenIO_read`, `ZenIO_stdin_lines`, and `ZenSystem_get_env_map`.
- Built-in `module` map: global `ZenValue module` + `ZenModule_initialize(...)` in `core/zen_sys.c` (entry file context for `-g`; `module.entry` set by generated host after init).
- Maps: open-addressed hash index + insertion-order `entries` (`ZenMap_get`/`has`/`set` are O(1) average). `ZenMap_get_items` / `ZenValue_get_items` → list of `{key,value}` maps (for `m.items()` / `zen.reflect`).
- Reflect: `core/zen_reflect.c` — type registry, `ZenReflect_tag_object`, `ZenReflect_register_method` + `ZenReflect_call` for map plugins and class method tables.
- Bytecode VM & Mixed ABI: `core/zen_vm.h` and `core/zen_vm.c` — Three-Layer Phase 3 & 4 script VM and interop ABI. Compact bytecode instruction set (`ZenChunk`, `ZenVM_interpret`, `OP_*` stack VM) executing on the unified `ZenValue` ABI. Opcode parity with `Bytecode.zl`: `OP_RANGE_EXCL`, `OP_RANGE_INCL`, `OP_CONCAT_APPEND`, `OP_DROP`, `OP_CHECK_UNWRAP`, `OP_RANGE_INCL_END`, `OP_RANGE_BETWEEN`, `OP_IN`, `OP_COALESCE`, `OP_SLICE`. `ZenChunk_load_file` supports both binary bytecode and portable text chunks (`ZENB:1:...`). Execution bridge: `ZenValue_run_bytecode_file` in `core/zen_dispatch.c` / `zen_vm.c`. `OP_CALL` supports native C functions and closures with arbitrary arities; host embedding API provides `ZenVM_register_global`, `ZenVM_register_native_func`, `ZenVM_load_native_module`, and `ZenVM_call_named`. Linked with `-ldl`.
- **Layer 2 Native AST & Token Engine (`core/zen_ast.h`, `core/zen_ast.c`):** Contiguous arena-allocated C structures (`ZenAstNode` 112 bytes with 6 direct value slots, `ZenToken` 24 bytes) replacing dynamic heap lists in selfhost IR. Fully index-compatible (`node[0..N]`, `token[0..6]`) via `ZenValue_get_at`, `ZenValue_set_at`, and `ZenValue_get_length` dispatch. Transparently compatible with `val is List`, `val is AstNode`, and `val is Token`.
- `core/zen_ops.c`, `core/zen_dispatch.c`, `core/zen_math.c` & `core/zen_sys.c`: Arithmetic (`ZenValue_power`, `ZenMath_min`, `ZenMath_max`, `ZenMath_clamp`, `ZenMath_round`, `ZenMath_abs`, `ZenMath_floor`, `ZenMath_ceil`, `ZenMath_sqrt`), type introspection (`ZenValue_get_kind`, `ZenValue_type`), bitwise, comparison, membership (`ZenValue_in` / `ZenValue_contains` for `in`), range (`ZenValue_range`, `ZenValue_range_inclusive`, `ZenValue_range_open_start_inclusive` for `..`, `..-`, `..=`, `...`, `..+`), and extended operators (`ZenValue_op_append` for string/list concat and append/prepend, `ZenValue_op_remove` for string/list drop start/end). `ZenValue_to_number` in `core/zen_dispatch.c` strips `_` separators.
- **First-Class Sized & Abstract Types (`core/zen_ops.c`, `core/zen_variant.c`):** Canonical types only (zero informal aliases): `Integer[8..64]`, `Byte`, `Decimal[32..64]`, `String[N]`, `Vector[N]`, `Tuple`, and abstract union types `Number` (`Integer`, `Decimal`), `Text` (`String`, `Rune`), `Collection` (`List`, `Vector`, `Set`, `Tuple`, `Map`), and `Container` (`Structure`, `Object`, `Class`, `Enumerator`). `ZenValue_cast` strictly enforces bit-width truncation, modular wrapping for sized types, and abstract type conversions. `ZenValue_is_type_name` maps sized, abstract, and user structure/class type names (matching `__type__`, `__type`, and `kind` fields on map/struct instances) with 100% parity across interpreted and compiled runtimes.
- **Fast Inlined Primitive Operations (`core/zen_ops.h`):** `ZenValue_fast_add_int`, `ZenValue_fast_sub_int`, `ZenValue_fast_mul_int`, `ZenValue_fast_div_int`, `ZenValue_fast_mod_int`, `ZenValue_fast_eq_int`, `ZenValue_fast_neq_int`, `ZenValue_fast_lt_int`, `ZenValue_fast_gt_int`, `ZenValue_fast_lte_int`, `ZenValue_fast_gte_int`, `ZenValue_fast_bitand_int`, `ZenValue_fast_bitor_int`, `ZenValue_fast_bitxor_int`, `ZenValue_fast_shl_int`, `ZenValue_fast_shr_int`, `ZenValue_fast_add_dec`, `ZenValue_fast_sub_dec`, `ZenValue_fast_mul_dec`, `ZenValue_fast_eq_bool`, `ZenValue_fast_neq_bool`. Inline primitives execute unboxed C operations with zero function call overhead while preserving the standard `ZenValue` ABI.
- `core/zen_regex.c`: POSIX ERE for `zen.text.regex` (`\s`/`\d`/`\w` expanded; find_all with groups).
- `core/zen_bytes.c`: byte lists + pack/unpack for `zen.data.bytes`.
- **C Interop Boxing & Unboxing (`core/zen_value.h`):** `ZenValue_from_c(expr)` macro uses C11 `_Generic` to automatically box primitive C return values (integers of all widths signed and unsigned, floats, doubles, booleans, `const char*` / `char*`, pointers `void*`, and `ZenValue`) into `ZenValue` with zero wrapper overhead. Unboxers `ZenValue_to_c_int`, `ZenValue_to_c_dec`, `ZenValue_to_c_str`, `ZenValue_to_c_bool`, and `ZenValue_to_c_ptr` provide ergonomic extraction of underlying C representations.
- **Dynamic FFI Shared Runtime (`core/zen_ffi.h`, `core/zen_ffi.c`):** Dynamic shared library loader and runtime function call dispatcher. Features `ZenFFI_dlopen` with automatic host process symbol fallback (`dlopen(NULL, RTLD_LAZY | RTLD_GLOBAL)`), `ZenFFI_dlsym`, `ZenFFI_call` (unboxing up to 16 arguments and boxing returns), `ZenFFI_make_callable` creating closures, and builtin API bindings `ZenFFI_builtin_load`, `ZenFFI_builtin_symbol`, `ZenFFI_builtin_call`, `ZenFFI_builtin_close`, `ZenFFI_builtin_error`, and `ZenFFI_builtin_resolve` backing `zen.sys.ffi` and `__builtin_ffi`.
- Legacy pre-unification trees: `archive/runtime-legacy/`, `archive/bootstrap-transpiler-runtime/`.

# Work Guidance

- Use `zen_` / `Zen` prefixes; keep ABI stable when possible.
- Extend here for OS primitives (termios, process, time); keep stdlib wrappers in `lib/zen/`.
- After changes, smoke: `python3 bootstrap/Zen.py -g tests/hello.zl` and memory tests below.

# Verification

- Native `-g` programs link and run (`./scripts/zen test-parity`, `test-lib-native`).
- Memory dual-path:
  ```bash
  export ZEN_PATH=$PWD:$PWD/lib
  python3 bootstrap/Zen.py tests/memory/auto_path_01.zl
  python3 bootstrap/Zen.py -g tests/memory/auto_path_01.zl
  python3 bootstrap/Zen.py tests/memory/manual_arena_01.zl
  python3 bootstrap/Zen.py -g tests/memory/manual_arena_01.zl
  ```

# Child DOX Index

- core/: value, object, ops, dispatch, zen_sys (term/process/time)
- collections/: list, map, set, string
- concurrency/: zen_task
- io/, memory/
- main_wrapper.c: optional host main
- REFERENCE.md: runtime notes
