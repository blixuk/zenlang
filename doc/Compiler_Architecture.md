# Zenlang Compiler Architecture & Internals

Zenlang employs a high-performance **Three-Layer Architecture** designed to deliver sub-millisecond script startup, instantaneous feedback, and bare-metal AOT native C compilation with 100% behavioral parity.

```
+-------------------------------------------------------------------------+
|                              Zen Source (.zl)                           |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  Layer 2: Compiler IR & Data Structures                 |
|  - Zero-copy 7-tuple Token spans [kind, start, len, line, col, el, ec]   |
|  - Positional AST Node tuples [kind, line, col, ...payload]             |
|  - Chunk-chained bump arena allocation (ZenRuntime_allocate)            |
|  - Clang/Rust-style source-mapped caret diagnostics (Diagnostics.zl)    |
+-------------------------------------------------------------------------+
                        /                         \
                       /                           \
                      v                             v
+-------------------------------+   +------------------------------------+
|  Layer 3: Bytecode Engine     |   | Layer 3: Native C AOT (CLink)      |
|  - Stack VM (zen_vm.c)        |   | - Transpiler (Codegen.zl)          |
|  - Instantaneous script eval  |   | - Standalone ELF Binary via GCC/CC |
|  - Zero-compilation overhead  |   | - Maximum runtime throughput       |
+-------------------------------+   +------------------------------------+
                        \                         /
                         \                       /
                          v                     v
+-------------------------------------------------------------------------+
|                  Layer 1: Unified ZenValue ABI & Runtime                |
|  - Universal NaN-boxed / Tagged Union ZenValue representation           |
|  - Shared C runtime across interpreted scripts and compiled binaries    |
|  - Zero-overhead interoperability (scripts call compiled modules)       |
+-------------------------------------------------------------------------+
```

---

## Layer 1: The Unified `ZenValue` ABI

The foundation of Zenlang is the `ZenValue` struct defined in `runtime/core/zen_value.h`. Every runtime value—whether an integer, decimal, string, list, map, tagged struct, closure, or arena handle—is represented as a uniform 16-byte value:

```c
typedef enum {
    ZEN_NOTHING = 0,
    ZEN_INTEGER,
    ZEN_DECIMAL,
    ZEN_BOOLEAN,
    ZEN_STRING,
    ZEN_LIST,
    ZEN_MAP,
    ZEN_OBJECT,
    ZEN_ARENA,
    ZEN_VARIANT,
    ZEN_SET,
    ZEN_FUNC
} ZenType;

typedef struct {
    ZenType type;
    union {
        int64_t integer;
        double decimal;
        bool boolean;
        char* string;
        struct ZenList* list;
        struct ZenMap* map;
        struct ZenObject* object;
        struct ZenArena* arena;
        struct ZenVariant* variant;
        struct ZenSet* set;
        struct ZenFunc* func;
    } as;
} ZenValue;
```

### ABI Invariant
Because the compiled C code and the bytecode VM/interpreter share the exact same `ZenValue` struct and dispatch table (`ZenValue_add`, `ZenValue_get_at`, `ZenValue_call`), compiled native modules can be loaded and invoked directly by interpreted scripts without glue wrappers or marshalling overhead.

---

## Layer 2: Zero-Overhead Compiler IR

To eliminate garbage-collection pressure and dictionary lookups during compilation, the self-hosted compiler (`selfhost/compiler/`) represents all lexical and syntactic entities as flat positional tuples:

### 1. Zero-Copy Token Spans (`Token.zl`)
Tokens are 7-element positional lists holding integer offsets into the original source text buffer:
```zen
[kind, start, length, line, column, end_line, end_column]
```
Lexeme materialization is deferred until code generation or error reporting, eliminating millions of intermediate string allocations.

### 2. Positional AST Nodes (`AST.zl`)
AST nodes are compact positional lists indexed by integer header offsets:
```zen
[kind, line, column, ...payload]
```
Accessors (`ast_kind(n)`, `ast_line(n)`, `bin_left(n)`, `fn_body(n)`) compile down to direct index lookups in C (`n.as.list->items[i]`).

### 3. Chunk-Chained Bump Arenas
AST nodes and token arrays allocate from thread-local memory arenas via `ZenRuntime_allocate`. Compilation units execute inside a scoped arena (`with memory.create_arena(...)`), providing maximum cache locality during parsing/typechecking and instantaneous $O(1)$ memory reclamation upon code emission.

### 4. Source-Mapped Caret Diagnostics (`Diagnostics.zl`)
When the parser or typechecker encounters an error, `Diagnostics.zl` uses the token's `line`, `col`, and `length` to extract the exact source line and render precise Clang/Rust-style carets:
```
error: Return type mismatch: expected Integer got String
  --> src/main.zl:14:5
  |
14 |     <- result
  |     ^
```

---

## Layer 3: Dual Execution Paths

### 1. The Script & VM Path (`Bytecode.zl` & `zen_vm.c`)
For rapid development, REPL sessions, and short-lived Unix scripts:
- `Bytecode.zl` compiles AST nodes into compact bytecode instruction chunks (`OP_CONST`, `OP_LOAD`, `OP_STORE`, `OP_ADD`, `OP_CALL`, `OP_JUMP_IF_FALSE`).
- The C stack virtual machine (`runtime/concurrency/zen_vm.c`) executes instructions with near-native loop speeds and zero GCC compile latency.

### 2. The Native AOT C Path (`Codegen.zl` & `CLink.zl`)
For production CLI tools, long-running services, and standalone binaries:
- `Codegen.zl` translates AST nodes into clean, readable, ANSI C code.
- Functions, closures, and pattern-matching constructs map directly to optimized C functions.
- `CLink.zl` invokes the host C compiler (`gcc`, `clang`, or `tcc`) with `-O2`/`-O3` optimization, linking directly against the pre-compiled runtime archive (`output/selfhost_rt/bootstrap_runtime.o`).
- Produces a standalone, zero-dependency ELF binary.

---

## Self-Hosting Pipeline & Build Cycle

The Zenlang compiler is fully self-hosting and capable of complete native self-rebuild (`ZEN_SELFHOST_REBUILD=1`):

```bash
# 1. Selfhost binary compiles its own source tree to C
./bin/zen-selfhost compile selfhost/zen.zl output/zen_self.c

# 2. Host C compiler links the secondary compiler executable
gcc output/zen_self.c -I runtime/ -o output/zen_from_self -O2 -lm -lpthread

# 3. Secondary compiler compiles test fixtures and builds working binaries
./output/zen_from_self compile tests/hello.zl output/hello.c
gcc output/hello.c -I runtime/ -o output/hello
./output/hello  # Output: Hello, Zen!
```
