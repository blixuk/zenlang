# DOX framework

- DOX is highly performant AGENTS.md hierarchy installed here
- Agent must follow DOX instructions across any edits

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:
- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

1. Re-check changed paths against the DOX chain
2. Update nearest owning docs and any affected parents or children
3. Refresh every affected Child DOX Index
4. Remove stale or contradictory text
5. Run existing verification when relevant
6. Report any docs intentionally left unchanged and why

## User Preferences

When the user requests a durable behavior change, record it here or in the relevant child AGENTS.md

- **Nothing / Default (required language surface):** `Nothing` = absent value; `Default` = type zero-state (`0`, `[]`, empty string, `False`, …). Both assignable and comparable (`== Nothing`, `== Default`). Canonical spelling is **capitalized** (like types); lowercase `nothing` is legacy. Tracked in [selfhost/ENDGAME_PLAN.md](selfhost/ENDGAME_PLAN.md) Phase L; required before host-1.0.
- **Type Casting (`<:` and `Type(val)`) & Sized Primitive Types:** Dual syntax: visual operator `<:` (`val <: Integer`) and constructor syntax `Type(val)` (`Integer(val)`). Strict canonical type enforcement with zero informal aliases (deprecated and forbidden: `Int*`, `Float*`, `Double`, `Str`, `Bool`, `Char`, `Glyph`, `Buffer`, `V`, `L`, `S`, `T`, `M`). Explicit typed collection literals require full canonical names: `Vector{...}`, `List{...}`, `Map{...}`, `Set{...}`, `Tuple{...}` (single-letter collection abbreviations `V{...}`, `L{...}`, `S{...}`, `T{...}`, `M{...}` dropped and forbidden). Official canonical types supported: `Variant`, `Void`, `Nothing`, `Default`, `Boolean`, `Byte`, `Bytes`, `Rune`, `Integer`, `Integer[SIZE]` (8, 16, 32, 64), `Decimal`, `Decimal[SIZE]` (32, 64), `String`, `String[SIZE]` (8, 16, 32, 64), `List`, `Set`, `Vector`, `Vector[LENGTH]`, `Tuple`, `Map`, `Structure`, `Object`, `Class`, `Enumerator`, `Function`, `Task`, `Channel`, `Error`. Unsized `Integer` defaults to 64-bit signed; unsized `Decimal` defaults to 64-bit IEEE 754. Bit-width truncation and wrapping are enforced with 100% parity across C runtime (`ZenValue_cast`, `ZenValue_is_type_name`), selfhost AST Parser/Codegen, selfhost Bytecode VM (`OP_CAST`), selfhost Interpreter, and Python bootstrap.
- **Native Console I/O & Ambient Streams:** Native built-in console I/O replaces imported wrappers. `stdout`, `stderr`, `stdin` are ambient stream instances with member methods (`write`, `writeln`, `flush`, `read`, `readln`, `lines`). Universal built-in preludes `write(...)`, `writeln(...)`, `read(...)`, `readln(...)` are available without import. Replaces `print`/`println`.
- **Dynamic Program Arguments:** Dynamic arity binding allows entry functions to declare `function main(args)` to receive CLI arguments directly, while preserving `function main()` for zero-parameter entry points. Top-level scripts also have ambient access to `args` (list of strings) and `env` (map of environment variables). Full parity across C runtime (`z_stdout`, `z_stderr`, `z_stdin`, `z_args`, `z_env`), selfhost C Codegen, selfhost Bytecode VM, selfhost Interpreter, and Python bootstrap.
- **Binary in Membership Operator:** First-class binary operator `in` evaluates containment across collections and sequences (`val in list`, `key in map`, `item in set`, `needle in string`, `x in range`). Implemented with full parity across C runtime (`ZenValue_in`), selfhost Parser/Codegen, Bytecode VM (`OP_IN`), selfhost Interpreter, and Python bootstrap.
- **Type Introspection (`type(x)`):** Universal built-in prelude `type(x)` (returns type string name) is available without import across C runtime (`ZenValue_get_kind`), selfhost compiler/Codegen, Bytecode VM, and Python bootstrap.
- **Standard Math Library (`zen.math`):** All mathematical operations reside in `lib/zen/math/math.zl` with full descriptive names as primary functions (e.g. `linear_interpolate`, `ceiling`, `square_root`, `hyperbolic_sine`) and standardized short-name aliases (`lerp`, `cil`, `sqrt`, `sinh`). Mathematical functions are strictly housed in `zen.math` (not bare global preludes).
- **String Syntax (Backticks Only):** Zenlang strings ONLY use backticks (`` `...` `` and multiline ```` ```...``` ````). Double quotes (`"`) are NOT used for strings in Zenlang. Formatted/interpolated strings strictly use backtick syntax with the `f` prefix (e.g. `` f`User {name} scored {score}` ``).
- **4-Range Boundary System (SPEC 6.4) & Drop `..=`:** Fully implements the mathematical 4-boundary interval system: `..` (between, $(a, b)$), `..+` (inclusive end, $(a, b]$), `..-` (exclusive end, $[a, b)$), and `...` (full inclusive, $[a, b]$). Legacy `..=` syntax is completely dropped and forbidden. Supported with 100% parity across C runtime (`ZenValue_range_*`), selfhost Lexer/Parser/Codegen/Bytecode VM, bootstrap compiler, stdlib (`zen.math.range`), and tests.
- **First-Class Collection Member Methods:** Member method calls on collection types with 100% parity across C runtime, selfhost C Codegen, Bytecode VM, and Python bootstrap: `List` (`reverse`, `unique`, `flatten`, `chunk`, `take`, `drop`, `join`, `map`, `filter`, `reduce`, `each`, `find`, `any`, `all`), `Map` (`keys`, `values`, `items`, `has`, `get`, `merge`, `invert`), `Set` (`to_list`, `has`, `add`, `remove`, `union`, `intersection`, `difference`).
- **Flow Operators (`??` and `|>`):** First-class binary null-coalescing (`a ?? b`, evaluates fallback if `a == Nothing`) and pipeline operator (`x |> f(...)`, passes `x` as first argument to `f`). Implemented with full 100% parity across C runtime (`OP_COALESCE`), AST/Parser, C Codegen, Bytecode VM, Interpreter, and Python bootstrap.
- **Negative Indexing & Sequence Slicing:** Uniform support for negative indices (`seq[-1]`) and interval slicing (`seq[start:end:step]`, `seq[:end]`, `seq[start:]`, `seq[::step]`, `seq[::-1]`) across `List` and `String`. Implemented with full 100% parity across C runtime (`ZenValue_slice`), selfhost Parser/Codegen, Bytecode VM (`OP_SLICE`), Interpreter, and Python bootstrap.
- **Modernized Standard Library Conventions:** Stdlib modules (`zen.io.io`, `zen.io.file`, `zen.data.json`, `zen.data.csv`, `zen.time`, `zen.math.range`, `zen.sys.env`, `zen.text.string`, `zen.collections.list`, `zen.collections`, `zen.io.path`, `zen.net.http`, `zen.net.url`, `zen.sys.process`) must use modern Zen features: first-class `in` operator, backtick strings, ambient `env`/streams, typed casting constructors, flow operators, sequence slicing, and dual descriptive + ergonomic short-name aliases.
- **Native Terminal Readline & Pure Selfhost Tooling:** Standalone interactive line editor `zen.sys.readline` (`Readline`) implemented in 100% pure Zen with in-line character navigation/editing, command history, and autocompletion; wired into `zen.tooling.repl`. All tool scripts (`scripts/zen doc-pdf`, etc.) execute natively via `bin/zen`; Python bootstrap is demoted to a Stage-0 compiler seed only, with rollback fallbacks removed.
- **Version 1 Beta (`v1.0.0-beta.1`) Unified Developer Platform & Self-Host Closure:** Standalone single-binary `bin/zen` handles all compiler workflows (`compile`, `build`, `run`, `check`, `clean`, `release`), developer tooling (`repl`, `fmt`, `doc`, `dash`, `watch`, `bench`), package management (`pkg`), and diagnostics with zero Python bootstrap dependency and complete Stage 2 native self-hosting closure. Features first-class directional comprehensions (`[for x in list -> expr]`, `{for k, v in map -> k: v}`), collection spreads (`[...list]`, `{...map}`), manifest-driven workflows (`zen.pkg.zd`), built-in terminal man pages (`zen doc <query>`, `zen explain <query>`), educational empty-file compilation diagnostics, optional incremental multi-unit compilation (`--incremental` / `-i`), static (`--static`) / shared (`--shared`) linking, and release archive packaging (`./scripts/zen release`).
- **Coloured Brackets, Rainbow Delimiters & Delimiter Matching:** Interactive line editor (`zen.sys.readline`), stateful REPL (`zen.tooling.repl`), and Terminal Playground (`tools/playground.zl`, `zen playground`) feature 5-color nesting depth cycling (Cyan, Yellow, Magenta, Green, Violet), cursor/partner delimiter matching with inverse standout (`\x1b[1;30;47m`), and unmatched closing delimiter warnings (`\x1b[1;37;41m`). Multi-line continuations carry forward unclosed nesting depth (`base_depth`), with toggles available in Playground Settings (Ctrl+O).
- **ANSI Escape Sequence Format & Terminal Showcase Examples:** Zenlang strings strictly represent terminal escape sequences via `\x1b` hexadecimal notation (never octal `\033`, which is unsupported by the lexer and prints literally). Showcased in `tools/playground.zl` and the terminal Speed Typing Calculator Game `examples/speed_typer.zl` featuring real-time WPM/CPM/accuracy metrics, color-coded per-character feedback, live ASCII sparklines, and 4 game modes (Zen quotes, code, mental math, timed sprint) with headless test coverage (`ZEN_TUI_HEADLESS=1`).
- **AOT C Codegen Optimization & Unboxing:** The selfhost AOT C transpiler (`selfhost/compiler/Codegen.zl`) performs recursive compile-time constant folding across arithmetic, bitwise, comparison, logical short-circuit, and string operations; dead-branch elimination pruning unreachable `when false` blocks and dead `else` clauses; dead-code elimination pruning unreachable statements following block terminators (`return`, `raise`, `break`, `continue`); direct list-iteration unboxing accessing contiguous array buffers `(tit).as.list->items[ti]` without function overhead; and type-aware primitive dispatch emitting inlined `ZenValue_fast_*` operations (`runtime/core/zen_ops.h`) for typed integer, decimal, and boolean operands with 100% ABI and dual-path parity.
- **Direct C Header Imports (`extern use`):** Zero-wrapper C interop allows importing C system and library headers (`extern use '<header.h>'`, `extern use dotted.path`, `extern use name [as alias]`, `extern from <hdr> use func1, func2`) and calling C functions natively. Calls automatically box return types into `ZenValue` via C11 `_Generic` (`ZenValue_from_c(...)`), unbox primitive/typed arguments via `emit_extern_args`, deduplicate `#include` directives, and integrate seamlessly into TypeChecker and C Codegen.
- **Dynamic FFI Loader (`.so` / `dlopen`) & Runtime Interop (`zen.sys.ffi`):** Runtime C dynamic library loading and function invocation across Bytecode VM, AST Interpreter, and Native AOT. Transparently resolves host process symbols via `dlopen(NULL, RTLD_LAZY | RTLD_GLOBAL)`, dynamically boxes returned values, unboxes arguments, and exposes `load`, `open`, `symbol`, `call`, `close`, `error`, `resolve` in standard library `zen.sys.ffi` backed by `runtime/core/zen_ffi.{c,h}`.
- **Zero-Glue System Utility Modules (`hardware`, `meminfo`, `termposix`):** Direct POSIX and Linux system inspection without manual C wrappers: `zen.sys.hardware` (CPU counts, page sizes, available/physical memory pages), `zen.sys.meminfo` (system RAM statistics, usage percentage, MB/GB conversions), and `zen.sys.termposix` (POSIX terminal TTY detection and stream flushes via `<unistd.h>` and `<termios.h>`).
- **Abstract & Union Types (`Number`, `Text`, `Collection`, `Container`):** First-class abstract union types categorize related base types for pattern matching (`val is Number`, `when val is Text`), type annotations (`let x : Number -> 42`), and type casting (`val <: Collection`, `Number(val)`, `Text(val)`): `Number` (`Integer`, `Decimal`, `Byte`), `Text` (`String`, `Rune`), `Collection` (`List`, `Vector`, `Set`, `Tuple`, `Map`), and `Container` (`Structure`, `Object`, `Class`, `Enumerator`). Implemented with 100% parity across C runtime (`ZenValue_is_type_name`, `ZenValue_cast`), selfhost compiler (Lexer, Types, TypeChecker, Bytecode VM, AST Interpreter, C Codegen), and Python bootstrap compiler. Covered in `tests/language/test_abstract_types.zl`.
- **Parameterized Generic Type Annotations (`List<T>`, `Map<K, V>`, `Set<T>`, `Vector[N]<T>`, `Tuple<...>`):** First-class parameterized generic type annotations and casting syntax with compile-time type validation, structural subtype unification, and runtime type checking across `let`/`set` declarations, function parameters, return types, pattern matching (`val is List<Integer>`, `when val is Set<String>`), and type casting (`val <: List<String>`, `List<String>(val)`). Angle brackets `<...>` are canonical for generic type parameters; sized collections use `Vector[N]<T>`. Implemented with 100% parity across C runtime (`ZenValue_is_type_name`, `ZenValue_cast`), selfhost compiler (Lexer, Parser, Types, TypeChecker, Bytecode VM, AST Interpreter, C Codegen), and Python bootstrap compiler (Parser, TypeChecker, Interpreter, Transpiler). Covered in `tests/language/test_generic_type_annotations.zl`.
- **User-Defined Generic Types & Functions (`function f<T>`, `structure Box<T>`, `class Storage<T>`):** First-class user-defined generic functions (`function id<T>(x: T): T`), generic structures (`structure Box<T> { value: T }`, `structure Pair<A, B> { first: A, second: B }`), and generic classes (`class Storage<T> { ... }`). Supports explicit type arguments (`id<Integer>(42)`, `Box<Integer>{ value: 777 }`, `Storage<String>("initial")`) and automatic type inference (`id(42)`, `Box{ value: 777 }`). Preserves strict canonical type checking where informal single-letter aliases (`T`, `L`, `S`, `M`, `V`) are strictly rejected unless declared as active generic type parameters in scope. Implemented with 100% parity across C runtime (`ZenValue_is_type_name`), selfhost compiler (Lexer, Parser, TypeChecker, Bytecode VM, AST Interpreter, C Codegen), and Python bootstrap compiler (Parser, TypeChecker, Interpreter, Transpiler). Covered in `tests/language/test_user_generics.zl`.
- **Pure Zenlang DEFLATE, GZIP, and ZLIB Compression Engines (`zen.data.deflate`, `zen.data.gzip`, `zen.data.zlib`):** 100% pure Zenlang implementations of RFC 1951 (DEFLATE / INFLATE compression with 32KB sliding window, LZ77 hash chains, and canonical fixed Huffman trees), RFC 1952 (GZIP compression and decompression with 10-byte header, filename/timestamp preservation, CRC-32 checksum verification, and `inspect` metadata extractor), and RFC 1950 (ZLIB format with CMF/FLG validation and Adler-32 verification). Full cross-tool interoperability with GNU `gzip`/`gunzip` and Python `gzip`/`zlib`, and dual-execution parity across self-hosted Bytecode VM and native AOT C compiler. Covered in `tests/lib/test_deflate_gzip.zl`.
- **Pure Zenlang PKZIP (.zip) Archive Engine (`zen.data.zip`):** 100% pure Zenlang implementation of standard PKZIP format archive creation and extraction with Deflate (method 8) and Stored (method 0) support, Central Directory parsing, End of Central Directory (EOCD) record resolution, per-file CRC-32 integrity validation, UTF-8 filename encoding (flag 0x0800), MS-DOS timestamp encoding/decoding, metadata extraction (`list_entries`, `inspect`), and direct disk operations (`create_archive`, `extract_archive`). Full two-way cross-tool interoperability with GNU `unzip`/`zip` and Python `zipfile`, and dual-execution parity across self-hosted Bytecode VM and native AOT C compiler. Covered in `tests/lib/test_zip.zl`.
- **Pure Zenlang ZAR Archive Format & Standalone CLI Platform (`zen.data.zar`, `tools/zar`, `bin/zar`):** 100% pure Zenlang implementation of the Next-Generation Zen Archive (`.zar` v1) format featuring opt-in RFC 1951 Deflate compression (levels 1..9, default 0 Stored), opt-in RFC 8439 ChaCha20-Poly1305 AEAD encryption with PBKDF2 key derivation, zero-knowledge encrypted Central Directory hiding metadata, per-file IEEE 802.3 CRC-32 and SHA-256 digests, cryptographic Merkle tree root seal with single-file inclusion audit proofs (`prove_file`, `verify_file_proof`), content-addressable file deduplication, dynamic mutable Archive container operations (`add`, `remove`, `rename`, `get`, `list`, `save`), self-hosted self-extracting executables (`sfx`), and terminal/SVG passkey QR code generation. Accompanied by a standalone multi-module CLI utility (`tools/zar`) with manifest-driven compilation (`zen.pkg.zd`, `.zbuild`) producing native binary `bin/zar`, wired into `./scripts/zen zar`. Verified with 100% dual-path parity across selfhost Bytecode VM and native AOT C compiler in `tests/lib/test_zar.zl`.
- **Tier 1 Usability & Compiler Isolation (CLI Normalization, Strict Numeric Literals & Module Namespacing):** Standardized CLI argument normalization (`zen.sys.sys.user_args`, `program_path`, `program_name`) cleanly separating program paths from user arguments across script runners and native binaries without manual subcommand checks. Strict numeric literal checking (`0x`, `0b`, `0o`) rejecting ambiguous leading zeros in decimal integers (`0644`, `0755`) with `TokenType.ERROR_INVALID_NUMBER` across both bootstrap and selfhost Lexers. Universal module namespacing in `selfhost/compiler/Driver.zl` preventing symbol collisions in multi-module user projects, coupled with `Codegen.zl` member method protection preventing global free functions from hijacking object method calls on local variables and parameters.
- **Tier 2 Area A: Error Inspection & Full Pattern Parity in `check`:** First-class error handling and pattern matching in `check` statements (`check expr { case ... } or { ... }`, `check expr or fallback`, `? expr or fallback`). Supports typed error and type-check cases (`case is Type`), collection membership matching (`case in <coll>`), error alias bindings in fallback recovery (`or (err) { ... }`, `or err { ... }`), and inline `?`/`^` operators. Evaluates with 100% parity across bootstrap compiler, selfhost parser, AST, typechecker, bytecode VM (`OP_IN`, `OP_IS_TYPE`), AST interpreter, and native AOT C transpilation with `ZenExceptionContext` (`setjmp`/`longjmp`). Covered in `tests/language/check_match_test_01.zl`.
- **Intrusive `ZenHeapHeader` & Hybrid ARC Memory Architecture (Phase 1):** 8-byte intrusive header (`int32_t ref_count`, `uint8_t type`, `uint8_t flags`, `uint16_t extra`) embedded at offset 0 across all dynamic heap containers (`ZenList`, `ZenMap`, `ZenSet`, `ZenVariantObject`, `ZenClosureData`, `ZenObject`). Supports strict sentinels: `ZEN_REF_PINNED` (-1, bump-arena allocated; retain and release are no-ops), `ZEN_REF_FROZEN` (-2, deeply immutable; cross-thread safe), `ZEN_REF_DEAD` (0, marked for destruction). `ZenHeapHeader_init` auto-detects active bump arenas via `ZenArena_stack_depth() > 0` to set `ref_count = ZEN_REF_PINNED` and `flags = flags | ZEN_FLAG_PINNED`. Inline `ZenValue_retain` and `ZenValue_release` operate non-atomically on thread-local heaps. Unified destruction dispatcher `ZenValue_destroy_heap_object` routes to container destructors (`ZenList_destroy`, `ZenMap_destroy`, `ZenSet_destroy`, `ZenVariantObject_destroy`, `ZenClosure_destroy`, `ZenObject_destroy`), cascading releases to child references and freeing standard heap allocations while preserving $O(1)$ arena bulk deallocation.
- **Heap Promotion Write Barrier & Arena Suspension (Phase 2):** Unified heap promotion write barrier (`ZenValue_write_barrier_target`, `ZenValue_write_barrier`) intercepts values written into dynamic containers. Evaluates zero-tax pairing when both destination container and value are arena-pinned (`ref_count == ZEN_REF_PINNED`), retaining without copy. When an arena-pinned value escapes into a standard heap container, it triggers `ZenValue_clone_to_heap` using thread-local re-entrant arena suspension (`ZenArena_suspend`, `ZenArena_resume`) to mask active arenas and deep-clone nested containers (`ZenList_deep_clone`, `ZenMap_deep_clone`, `ZenSet_deep_clone`, `ZenVariantObject_deep_clone`) into standard process heap memory with thread-local cycle detection (`zen_clone_enter`, `zen_clone_leave`, `zen_clone_lookup`, `zen_clone_register`) preventing infinite recursion on cyclic scope and container graphs. Dynamic container buffer resizers (`ZenList_append_value`, `ZenMap_set_value_at_key`, `zen_map_rehash`) preserve storage domain isolation: heap containers always resize via process heap (`realloc`/`malloc`) regardless of active arenas, preventing arena chunk pointer contamination during `ZenList_destroy` and `ZenMap_destroy`. Raw C host handles (`ZEN_OBJECT`) remain cleanly excluded from heap header dereferencing in `ZenValue_is_heap_pointer`. Fully verified under `./scripts/zen ci` and `./scripts/zen selfhost-smoke`.
- **Bytecode VM Opcode & Constant Pool ARC Integration (Phase 3):** `ZenChunk_add_constant` permanently freezes heap objects residing in chunk constant pools with sentinel `ref_count = ZEN_REF_FROZEN` (`-2`) and flag `ZEN_FLAG_FROZEN`, completely eliding ARC retain/release churn when constants are pushed onto the VM evaluation stack. Stack and register mutation opcodes strictly enforce reference ownership: `OP_POP` releases discarded stack values (`ZenValue_release(pop(vm))`), `OP_DUP` retains duplicated stack values, `OP_LOAD_LOCAL` retains local references pushed to the evaluation stack, and `OP_STORE_LOCAL` transfers ownership of the popped evaluation stack value to the target slot while safely releasing the slot's prior occupant. Verified with 100% pass across core interpret, parity, native lib smoke, and selfhost smoke.
- **Universal Child Traversal & Deep Freezing (Phase 4 Step 1):** Universal child traversal dispatcher `ZenValue_visit_children(header, visitor, context)` provides a type-agnostic visitor multiplexer across all dynamic heap containers: `ZenList` (all elements in `items`), `ZenMap` (flat insertion entries `key` and `value`), `ZenSet` (inner `list`), `ZenVariantObject` (`enum_name`, `variant_name`, `data`), and `ZenClosureData` (captured locals in `caps`). Deep freezer `ZenValue_freeze(v)` recursively walks container graphs and locks headers to `ref_count = ZEN_REF_FROZEN` (`-2`) and `flags |= ZEN_FLAG_FROZEN` with cycle termination guards (`h->ref_count == ZEN_REF_FROZEN || h->ref_count == ZEN_REF_DEAD`), allowing thread-safe concurrent channel sharing with zero ARC tax and zero copying. Fully verified under `./scripts/zen test-core`, `test-parity`, `test-lib-native`, and `selfhost-smoke`.
- **Deferred Bacon-Rajan Cycle Collector (Phase 4 Step 2):** Synchronous trial-deletion cycle collector (`runtime/memory/zen_gc.{c,h}`) paired with suspect hook in `ZenValue_release` routing alive containers (`h->flags & ZEN_FLAG_CONTAINER`) to `ZenGC_add_suspect(h)`. Operates via 4-phase trial deletion: (1) **Mark Gray:** trial-decrements reference counts along internal edges via `ZenValue_visit_children`; (2) **Scan:** scans and restores external references to `GC_COLOR_BLACK`, coloring isolated unreferenced subgraphs `GC_COLOR_WHITE`; (3) **Sever:** safely zeroes out container sizes (`count = 0`, inner lists/data to `Nothing`, `n_caps = 0`) before freeing memory to eliminate Use-After-Free hazards; (4) **Collect:** dispatches container destructors (`ZenList_destroy`, `ZenMap_destroy`, `ZenSet_destroy`, `ZenVariantObject_destroy`, `ZenClosure_destroy`, `ZenObject_destroy`) without cascading releases, reclaiming cyclic memory cleanly. Suspect buffer tracks objects in $O(1)$ with index-keyed removal in `ZenValue_destroy_heap_object` preventing dangling pointers. Wired into `ZenVM_reset` and verified across `tests/memory/cycle_collection_test.zl` and all test ladders.
- **Unified Task Concurrency Substrate & Frozen Handoff Channel Engine (Step 1):** Cache-line padded MPMC ring buffer channel (`runtime/concurrency/zen_channel.{c,h}`) inheriting intrusive 8-byte `ZenHeapHeader` (`ZEN_CHANNEL`, `ZEN_FLAG_CONTAINER`). Backed by POSIX mutexes and condition variables with blocking and non-blocking operations (`send`, `receive`, `try_send`, `try_receive`, `close`, `is_closed`). Enforces the **Frozen Handoff Boundary** (`prepare_for_handoff`): arena-pinned objects are promoted to standard heap via `ZenValue_clone_to_heap` before recursive `ZenValue_freeze` freezes the entire graph to immutable sentinel `ref_count = ZEN_REF_FROZEN` (`-2`), allowing complex nested data structures to pass across threads with zero lock contention, zero atomic ARC CPU tax, and zero race conditions. Fully verified with multi-threaded stress tests under AddressSanitizer and all test suites.
- **Cooperative Task Engine & Work-Stealing Worker Pool (Step 2 Concurrency Substrate):** Scalable task fiber execution runtime (`runtime/concurrency/zen_task.{c,h}`) replacing legacy pthread-per-task shim with a hardware-scaled work-stealing worker pool. `ZenTaskHandle` inherits intrusive 8-byte `ZenHeapHeader` (`ZEN_TASK`, `ZEN_FLAG_NONE`) managing execution state (`TASK_PENDING`, `TASK_RUNNING`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_CANCELLED`). Evaluates tasks via `ZenTask_spawn` and `ZenTask_wait`, passing callables and arguments across the **Frozen Handoff Boundary** (`zen_task_prepare_handoff`) to enforce complete memory isolation and zero atomic ARC tax during execution. Results and errors are deep-frozen prior to broadcasting completion. Cross-thread task handle reference counting is synchronized via targeted atomic acquire-release primitives (`__atomic_sub_fetch` and `__atomic_add_fetch` for `ZEN_TASK`) in `ZenValue_retain` and `ZenValue_release`, keeping 100% thread-local zero-tax ARC speed for standard values while achieving a clean bill of health under AddressSanitizer (ASAN) and ThreadSanitizer (TSAN) across heavy 1,000-task fan-out/fan-in stress testing (`tests/concurrency/test_task.c`). Integrated into `ZenRuntime_initialize`, `ZenRuntime_terminate`, `ZenValue_destroy_heap_object`, `ZenValue_visit_children`, and cycle collection.
- **Unified Task Concurrency Substrate & Language-Level Integration (Step 3):** Exposes `Task` and `Channel` as first-class language primitives across interpreted and native compiled modes. Fast-path runtime method dispatch (`runtime/core/zen_dispatch.{c,h}`) handles `task.wait()` / `.wait`, `task.cancel()`, `task.is_cancelled()`, `channel.send(val)`, `channel.receive()` / `.receive`, `channel.close()`, and `channel.is_closed()` / `.is_closed`. Selfhost AOT C transpiler (`selfhost/compiler/Codegen.zl`) tracks static `Task` and `Channel` types and emits direct raw C intrinsics (`ZenTask_wait`, `ZenChannel_send`, etc.) bypassing dictionary lookups. Selfhost Bytecode VM (`selfhost/compiler/Bytecode.zl`) features a native worker fiber adapter `run_bytecode_task([fn_chunk, rargs, globals])` that dispatches bytecode chunk execution across work-stealing worker threads with 100% frozen handoff boundary compliance. Standard library facade (`lib/zen/concurrency.zl`) provides ergonomic `channel(capacity)`, `spawn(callable, argument)`, `TaskGroup` structured concurrency context manager (`wait_all`, `cancel_all`), and `task_group()` helper. Verified with 100% dual-path parity across `tests/concurrency/test_concurrency_language.zl`.
- **RFC Governance & Language Specification Canonization:** Strict governance model where any proposed modifications to syntax, type systems, memory model, or semantics must pass through a formal RFC proposal process (`rfcs/`) and be canonized in the authoritative language specification (`doc/SPECIFICATION.md`) before becoming standard implementation.
- **Borrowed Parameters by Default:** Compiler treats all function parameters as borrowed references by default, preventing retain/release churn on call boundaries unless the callee explicitly stores or escapes the reference.
- **Zero-Allocation String Views:** Compiler primitives treat `String` strictly as an immutable UTF-8 byte array with a lightweight `StringView` for zero-allocation parsing and lexing.
- **Non-Blocking C-FFI (`task.spawn_blocking`) & epoll/kqueue I/O Reactor (Step 4 Concurrency Substrate):** Offloads synchronous blocking C-FFI operations and heavy file I/O to a dedicated dynamic OS worker pool (`ZenBlockingPool`, scaling up to 64 threads) via `task.spawn_blocking(callable, argument)`, `conc.spawn_blocking`, and `TaskGroup.spawn_blocking`, keeping cooperative compute worker threads completely unblocked while maintaining the frozen handoff memory boundary. Integrates a native kernel event reactor (`runtime/concurrency/zen_reactor.{c,h}`) using `epoll` (Linux) and `kqueue` (macOS/BSD) with self-pipe wakeup, priority monotonic timer queue, and file descriptor readiness subscriptions. Exposes high-resolution non-blocking timers (`conc.sleep(seconds)`) and asynchronous I/O readiness (`conc.poll_fd(fd, events, timeout)`), updating task state to `TASK_WAITING_TIMER` and `TASK_WAITING_IO`. Implemented with 100% parity across C runtime, AOT C transpilation, Bytecode VM (`conc_spawn_blocking`, `conc_sleep`, `conc_poll_fd`), AST Interpreter, and Python bootstrap. Verified in `tests/concurrency/test_reactor.c` and `tests/concurrency/test_reactor_language.zl`.
- **Formalized Type System, Directional Subtyping & Structural Validation:** Elevates semantic analysis in `selfhost/compiler/TypeChecker.zl` and `selfhost/compiler/Types.zl` with strict directional subtyping (`is_subtype`) and gradual assignability (`is_assignable`). Universal dynamic top types (`Variant`, `Unknown`) obey $\forall T, T \le \top$ and $\top \not\le T$. Directional abstract supertypes (`Number`, `Text`, `Collection`, `Container`) strictly enforce subtype bounds (e.g. `Integer` <: `Number`, rejecting unsound reverse `Number` -> `Integer`). Monotonic numeric widening (`Byte` <: `Integer`, `Integer[16]` <: `Integer[32]` <: `Integer[64]`, `Decimal[32]` <: `Decimal[64]`, `(Integer | Byte)` <: `Decimal`). Parameterized collection subtyping enforces covariant element types across `List`, `Set`, and `Vector`, invariant keys and covariant values for `Map`, and element-wise matching for `Tuple`. Structural record subtyping enforces member subset inclusion with recursive member subtyping. Multi-level nominal class inheritance traverses `base` and resolved `base_type` chains transitively with fallback for `Named` references. Gradual assignability (`is_assignable`) allows `Default` zero-values to materialize to any concrete type and `Nothing` to assign to reference/nullable types (`Option`, `Variant`, `Class`, `Structure`, `Object`). Bidirectional generic unification (`unify_types`) and call-site specialization (`instantiate_generic_call`) infer generic type parameters across multiple arguments with numeric promotion widening (`Integer` + `Decimal` -> `Decimal`) and explicit type arguments (`f<Decimal>(10, 20)`). Automatically unifies unspecialized generic struct fields on initialization (`Box{ value -> 42 }` -> `Box<Integer>`). Return type inference automatically widens to supertype when branches return subtype expressions. Precise AST literal typing (`lit_tok_kind`) prevents string and multi-dot collisions in `looks_decimal`. Verified with 100% dual-path parity across bootstrap and native `bin/zen` (`tests/self_hosting/test_checker_subtyping.zl`, 14 tests).

- Prefer `selfhost/` (not `src/`) for self-hosted compiler sources.
- Prefer top-level `runtime/` shared by bootstrap and self-host (not a private copy only under bootstrap).
- Prefer Zen-owned tooling (`scripts/zen`, future build/pkg/test/docs) over Make as the long-term ecosystem; Makefile is a thin shim only.
- Keep a root `README.md` as the human front door.
- **Local project:** no GitHub Actions, remote CI, or hosted runners. Verification is `./scripts/zen` on this machine (`ci` fast, `ci-soak` handoff+golden).
- **Three-layer execution (product):** (1) **ZenValue** = language values and the compiled↔interpreted ABI; (2) **compiler IR** = native Token/AST structs (not maps) so the host is fast; (3) **bytecode VM** for scripts. **AOT stays C** for shipped programs. Mix: scripts call compiled modules; binaries can load Zen scripts. Not VM-only. Not a MIR half-port. Plan: [selfhost/THREE_LAYER.md](selfhost/THREE_LAYER.md). Hybrid + bootstrap until that is usable.

## Project

### Purpose
Zenlang is a modern, optionally typed, Unix-native programming language for scripts, terminal applications, and networked services. It emphasizes:

- Visual data flow with `->` (assignment) and `<-` (return)
- Explicitness over magic
- Terminal as a primary UI surface
- Unified Task model for concurrency
- Dual execution: interpret scripts **or** AOT-compile to native C binaries; mix compiled and interpreted on one `ZenValue` ABI
- Self-hosting of the compiler (native IR + C AOT + script VM — [selfhost/THREE_LAYER.md](selfhost/THREE_LAYER.md))

This repository holds:

- Python bootstrap compiler (`bootstrap/`) — authoritative today
- Self-hosted compiler sources (`selfhost/`) — migration target
- Shared C runtime (`runtime/`)
- Standard library (`lib/zen/`)
- Tests, docs, examples, scripts, editors
- `archive/` for historical/experimental material

### Ownership
Project-level ownership rests with the Zenlang developers/maintainers. Every agent or contributor must obey this root AGENTS.md plus every applicable child AGENTS.md along the path to any file or directory touched.

### Local Contracts (project-wide)
- The Python bootstrap in `bootstrap/` is the complete authoritative implementation until selfhost stage parity. `selfhost/` targets full parity (see `selfhost/PARITY.md`); Stage 1 = Token+Lexer.
- Canonical C runtime is top-level `runtime/`. `bootstrap/Transpiler/runtime` must remain a symlink (or equivalent) to that tree.
- Follow [doc/SPECIFICATION.md](doc/SPECIFICATION.md) (single source of truth) and [doc/Zen Manifesto.md](doc/Zen%20Manifesto.md). Learner on-ramp: [doc/Getting_Started.md](doc/Getting_Started.md). Standards: [doc/DOCUMENTATION_STANDARDS.md](doc/DOCUMENTATION_STANDARDS.md).
- Transient artifacts (`build/`, `out/`, `bin/`, `output/`, `tmp/`, `venv/`, `__pycache__/`, `*.log`, `*.o`, `*.bak`) are never hand-edited; gitignored.
- `ZEN_PATH` includes project root, `selfhost/`, and `lib/`.
- Dual execution parity (interpreter vs native `-g`) and dual-layer testing remain invariants.
- Every meaningful edit triggers a DOX pass before completion.
- New durable folder boundaries require a child AGENTS.md.

### Work Guidance (project-wide)
- Put broad rules here; put concrete details in the nearest child AGENTS.md.
- Prefer `./scripts/zen` for install/test/run; do not grow a large Makefile again.
- Prefer editing language sources and stdlib in Zenlang idioms.
- Documentation, code, and tests must stay consistent.
- Archive obsolete experiments under `archive/`; do not leave multi-gigabyte logs in-tree.

### Verification (project-wide)
Primary ladder:

- `./scripts/zen install` — `bin/zen` router (native selfhost primary, bootstrap fallback)
- `./scripts/zen test-core`
- `./scripts/zen test-parity`
- `./scripts/zen test-lib`
- `./scripts/zen test-lib-native`
- `./scripts/zen test` — all of the above

Quiet CLI: `python3 bootstrap/Zen.py tests/hello.zl`. Trace: `ZEN_TRACE=1`.

Secondary: experimental `./scripts/zen install-driver` (selfhost/zen.zl); `./scripts/zen install-bootstrap` (pure bootstrap); examples (e.g. zedit). Fast local smoke: `./scripts/zen ci`. Local soak: `./scripts/zen ci-soak` (handoff-soak + golden). Pure selfhost compiler: `./scripts/zen install-selfhost` (`bin/zen-selfhost`).

## Child DOX Index

- bootstrap/: Python bootstrap compiler (authoritative) — bootstrap/AGENTS.md
- selfhost/: Self-hosted Zenlang compiler sources — selfhost/AGENTS.md (three-layer: THREE_LAYER.md)
  - selfhost/compiler/: Ported components — selfhost/compiler/AGENTS.md
  - selfhost/lsp/: Language Server Protocol daemon — selfhost/lsp/AGENTS.md
- runtime/: Shared C runtime — runtime/AGENTS.md
- lib/zen/: Standard library — lib/zen/AGENTS.md
  - lib/zen/ui/: Terminal UI (canvas + map layout) — lib/zen/ui/AGENTS.md
  - lib/zen/tooling/: Developer toolchain & project manager — lib/zen/tooling/AGENTS.md
  - lib/zen/crypto/: Zero-dependency cryptography, ciphers, encodings, Merkle tree & blockchain platform — lib/zen/crypto/AGENTS.md
- doc/: Documentation and specification — doc/AGENTS.md
- tests/: Test suite — tests/AGENTS.md
- scripts/: Host scripts including `scripts/zen` — scripts/AGENTS.md
- editors/: Editor integrations (VS Code/Cursor, Zed, Sublime, Tree-sitter) — editors/AGENTS.md
- archive/: Historical reference only — archive/README.md (no full DOX tree required)
- examples/: Illustrative demos (owned at root until independent contracts appear); learner ladder in examples/getting_started/ (see doc/Getting_Started.md); C extern interop & .zbuild in examples/c_interop/ (examples/c_interop/AGENTS.md)
- tools/: Extra developer tools (zendoc, …)
  - tools/zar/: Standalone Zen Archive (.zar) CLI platform — tools/zar/AGENTS.md
- zenshell/: Standalone modern shell unifying the Zen Trinity (.zl, .zd, .zm) — zenshell/AGENTS.md

Transient: `build/`, `bin/`, `output/`, `tmp/`, logs — never hand-edited.
