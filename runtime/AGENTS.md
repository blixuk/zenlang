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
- **Opt-in path:** user push → `ZenRuntime_allocate` prefers user arena (class instances under `-g`). Grow-on-full; free_arena reclaims + clears both stacks of that pointer. Escape rule: no use after free.
- **Introspection:** `ZenMemory_using_arena` / `arena_depth` report **user** stack only.
- Layout: `core/`, `collections/`, `concurrency/`, `io/`, `memory/`, `bootstrap_runtime.*`, plus `main_wrapper.c` for host entry where needed.
- Public surface via `bootstrap_runtime.h` / `zen_*.h` and `ZenTerm_*` / `ZenProcess_*` / `ZenTime_*` / `ZenMemory_*` / `ZenRegex_*` sys APIs in `core/`.
- File IO (`io/zen_io.c`): `ZenIO_list_dir` returns empty list on failure; `ZenIO_file_exists` uses `stat`; `ZenIO_mkdir` / `ZenIO_mkdir_p` for directories.
- Net (`core/zen_net.c`): `ZenNet_http_request` via curl (`-g`); interpret uses urllib. Returns `{status, body, headers}`.
- Built-in `module` map: global `ZenValue module` + `ZenModule_initialize(...)` in `core/zen_sys.c` (entry file context for `-g`; `module.entry` set by generated host after init).
- Maps: open-addressed hash index + insertion-order `entries` (`ZenMap_get`/`has`/`set` are O(1) average). `ZenMap_get_items` / `ZenValue_get_items` → list of `{key,value}` maps (for `m.items()` / `zen.reflect`).
- Reflect: `core/zen_reflect.c` — type registry, `ZenReflect_tag_object`, `ZenReflect_register_method` + `ZenReflect_call` for map plugins and class method tables.
- Bytecode VM & Mixed ABI: `core/zen_vm.h` and `core/zen_vm.c` — Three-Layer Phase 3 & 4 script VM and interop ABI. Compact bytecode instruction set (`ZenChunk`, `ZenVM_interpret`, `OP_*` stack VM) executing on the unified `ZenValue` ABI. `OP_CALL` supports native C functions and closures with arbitrary arities; host embedding API provides `ZenVM_register_global`, `ZenVM_register_native_func`, `ZenVM_load_native_module`, and `ZenVM_call_named`. Linked with `-ldl`.
- `core/zen_ops.c` & `core/zen_sys.c`: Arithmetic (`ZenValue_power`), bitwise, comparison, range (`ZenValue_range`, `ZenValue_range_inclusive`, `ZenValue_range_open_start_inclusive` for `..`, `..-`, `..=`, `...`, `..+`), and extended operators (`ZenValue_op_append` for string/list concat and append/prepend, `ZenValue_op_remove` for string/list drop start/end). `ZenValue_to_number` in `core/zen_dispatch.c` strips `_` separators.
- `core/zen_regex.c`: POSIX ERE for `zen.text.regex` (`\s`/`\d`/`\w` expanded; find_all with groups).
- `core/zen_bytes.c`: byte lists + pack/unpack for `zen.data.bytes`.
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
