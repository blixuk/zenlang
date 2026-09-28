# Purpose

Self-hosted compiler components ported from `bootstrap/`.

# Ownership

Part of `selfhost/` parity effort.

# Local Contracts

- Map 1:1 to bootstrap packages where possible (Token/Lexer ↔ `bootstrap/Lexer/`).
- **Stage 1:** `Token.zl`, `Lexer.zl` — dual-path.
  - Tokens are native contiguous C structures `ZenToken` (24 bytes) allocated via arena bumps in native mode, or flat positional tuples `[kind, start, length, line, column, end_line, end_column]` in interpret mode via `Tok.token` calling `__builtin_ast.token`. Accessor helpers `tok_kind`, `tok_start`, `tok_length`, `tok_lexeme(src, t)`, `tok_line`, `tok_column`, `tok_end_line`, `tok_end_column` index `t[0..6]`.
  - State `LEX` is a flat positional list `[src, pos, len, line, col, tokens]` indexed via `LEX_SRC..LEX_TOKENS` integer constants (Phase 5.2 state de-indirection).
  - Supported token spectrum: 4-boundary ranges (`..`, `..=`, `..+`, `..-`, `...`), number base literals (`0x`, `0b`, `0o`, `_` digit separators), visual symbols (`->`, `<-`, `<~`, `:>`, `<:`), triple-backtick multiline strings (```` ```...``` ````), scalar types (`Byte`, `Bytes`). Leading zeros on decimal integer literals (`0644`, `0755`) are strictly forbidden and emit `TokenType.ERROR_INVALID_NUMBER` instructing the use of `0o` octal prefix.
  - `ZEN_PROFILE=1` on parse/compile/interpret prints stage ms (`profile lex` … `profile total`).
  - Native host: bootstrap emits `TokenType.X` as integer ids 0–123; Parser `is_kind` is `k == name`.
  - Interpret host: `kind` stays the TokenType variant; same `k == name` (no `kind_id` on the lex/parse hot path).
  - Lexer identifier lookup uses zero-allocation length-switch character matcher `match_keyword(src, start, len)`.
  - API: `Lexer.tokenize_source(src)`.
  - Module & Method Call Isolation: `Driver.zl` applies universal module namespacing (`should_namespace_path`, `import_should_rewrite`) across all non-fixture imported modules. `Codegen.zl` restricts `is_free_fn` method call hijacking so member calls on local variables and parameters (`obj.meth()`) are preserved.
- **Stage 2:** `AST.zl`, `Parser.zl` — dual-path MVP. AST nodes are native contiguous C structures `ZenAstNode` (112 bytes with 6 direct value slots) allocated via arena bump allocation in native mode, created via `make_node0..5` calling `__builtin_ast.create0..5`, or positional list structs in interpret mode. Accessors `AST.*` (`ast_kind`, `ast_line`, `ast_col`, `fn_name`, `expr_left`, `prog_stmts`, etc.) index `n[0..N]`. Node validation via `AST.is_node(n)` and transparent `is List` compatibility via `ZenValue_is_type_name`. Parser result helpers are `parser_ok` / `parser_ok_list` (not `ok`) so native C does not collide with `zen.sys.process.ok`. Statement lists via `stmt_push`; enumerator `->` payloads via `parse_enum_member_value` (nested `j` rebind hangs Token.zl under `-g`). Supports parameterless functions (`function foo { ... }`), arrow function bodies (`function foo -> expr`, `function foo(x) -> expr`), return type preceding parameters (`function foo : Type (params)`), and arrow lambdas (`function(x) -> expr`).
  - State `G` is a flat positional list `[src, tokens, len]` indexed via `G_SRC..G_LEN` integer constants (Phase 5.2 state de-indirection).
  - Lexeme materialization is deferred: `is_val(t, v)` compares `Tok.tok_lexeme(G[G_SRC], t) == v`, and `val_of(t)` extracts slices and unescapes strings on-demand.
  - AST Bump Allocation (Phase 5.3): AST nodes and token arrays allocate from chunk-chained arenas via `ZenRuntime_allocate` with single-pass exact sizing. `Driver.compile_cli` scopes unit compilation within an arena, providing high cache locality and $O(1)$ reclamation upon code generation.
- **Diagnostics & Error Carets:** `Diagnostics.zl` — Clang/Rust-style source-mapped error reporting. `get_source_line(src, line)`, `make_carets(col, len)`, and `format_error`/`format_diagnostic` extract exact source lines and compute caret underlines `^` from zero-copy 7-tuple token spans and positional AST nodes. Integrated directly into `Parser.zl` (`fail`), `TypeChecker.zl` (`push_node_error`), and `Driver.zl` (`check_string_file`).
- **Stage 3:** `Module/` — resolve + dependency graph + builder.
- **Stage 4:** `Types.zl`, `TypeChecker.zl` — `check_source` → `{ok, errors, notes}`.
  - Depth: `WithStatement` alias scope; `ClassStatement` + `self`/`parent`; enumerator; `IsExpression`; `FunctionExpression`; `IndexAssign`.
  - **C1:** class method table; `Class()` ctor type; `obj.meth` resolution; arity; unknown method.
  - **C2:** with-alias typed from resource; soft `notes` if resource is not an arena.
  - **C3:** `owned`/`borrowed` type qualifiers; use-after-move; borrowed escape from `with` (untyped Variant aliases are not borrowed).
  - **C+ (Generics & Container Methods):** Standard bracket notation for generic types (`List[T]`, `Map[K, V]`, `Set[T]`, `Option[T]`, `Result[T, E]`, `Task[T]`) with recursive parameterized `type_equal` and string parsing in `Types.zl`. Container element type tracking across `List` and `Map`, typed indexing and index assignment validation, member method signatures (`List.append`, `get`, `has`, `length`, `reverse`; `Map.keys`, `values`, `has`, `get`; `Set.has`, `add`, `remove`, `to_list`), function call argument type matching against parameters, and return type consistency verification. Full dual-path parity across interpreter and native `-g` (`tests/self_hosting/test_checker.zl`, 24 tests).
- **Type Casting & Sized Primitive Types:** `AST.K_CAST` (47), `AST.cast(expr, target_type, l, c)`, `<:` operator token (`TokenType.TYPE_CAST`), and type constructor calls (`Integer(val)`, `Byte(val)`, `Integer[16](val)`, `Number(val)`, `Text(val)`, `Collection(val)`). Strictly canonical type names only (informal aliases `Int*`, `Float*`, `Double`, `Str`, `Bool`, `Char`, `Buffer`, `V`, `L`, `S`, `T`, `M` prohibited). Explicit typed collection literals require full canonical names: `Vector{...}`, `List{...}`, `Map{...}`, `Set{...}`, `Tuple{...}` (single-letter collection abbreviations `V{...}`, `L{...}`, `S{...}`, `T{...}`, `M{...}` dropped and forbidden). Sized types include `Integer[8|16|32|64]`, `Byte`, `Decimal[32|64]`, `String[N]`, `Vector[N]`, `Tuple`. First-class abstract union types supported across pattern matching, type annotations, and casting: `Number` (`Integer`, `Decimal`), `Text` (`String`, `Rune`), `Collection` (`List`, `Vector`, `Set`, `Tuple`, `Map`), and `Container` (`Structure`, `Object`, `Class`, `Enumerator`). Evaluates with high precedence via `parse_cast`. Emits `ZenValue_cast(val, "Type")` in C Codegen, `OP_CAST` (0x56) in Bytecode VM, and `eval_cast` in Interpreter with exact bit-width truncation, modular wrapping, and union validation. Full Type Cast Matrix documented in `doc/Zenlang Explained.md`. Tests: `tests/language/test_sized_types.zl`, `tests/language/test_canonical_collection_literals.zl`, `tests/language/test_forbidden_types_reject.py`, `tests/language/test_abstract_types.zl`.
- **Parameterized Generic Type Annotations (`List<T>`, `Map<K, V>`, `Set<T>`, `Vector[N]<T>`, `Tuple<...>`):** Generic parameter angle brackets `<...>` parsed across `parse_type_name`, `parse_let`, `parse_function`, pattern matching `is` (`parse_equality_tail`, `parse_when_pattern_match_block`), and constructor calls in `parse_primary`. Structural collection subtype checking in `TypeChecker.zl` rejecting element type clashes at compile time. Runtime type testing in `Bytecode.zl` (`eval_is_type_vm`), `Interpreter.zl` (`eval_cast`), `Codegen.zl` (`emit_is_expression`), and C runtime (`ZenValue_is_type_name`, `ZenValue_cast`). Covered in `tests/language/test_generic_type_annotations.zl`.
- **User-Defined Generic Types & Functions (`function f<T>`, `structure Box<T>`, `class Storage<T>`):** User-defined generic function definitions (`parse_function`), generic structures (`parse_structure`), and generic classes (`parse_class`) parsing optional type parameters `<T, ...>`. Call sites support explicit type arguments `f<Integer>(x)`, `Box<Integer>{ ... }`, `Storage<String>(...)` and automatic type argument inference. `is_builtin_cast_type_name` in `Bytecode.zl` and `Codegen.zl` distinguishes built-in primitive/abstract casts from user struct/class constructors and local variables. Class member field AST unwrap in `Bytecode.zl` for typed members. Covered in `tests/language/test_user_generics.zl`.
- **Native Console I/O & Dynamic CLI Arguments (Phase 1 Builtins):** Ambient streams (`stdout`, `stderr`, `stdin`) are native Stream instances supporting `.write()`, `.writeln()`, `.flush()`, `.read()`, `.readln()`, `.lines()`. Built-in preludes `write(...)`, `writeln(...)`, `read(...)`, `readln(...)` are universally available without importing stdlib. Dynamic arity binding allows entry functions to declare `function main(args)` to receive command-line arguments directly (with `function main()` preserved for zero-arg entries), and exposes ambient `args` and `env` globals. Supported with full parity across C Codegen (`Codegen.zl`), Bytecode VM (`Bytecode.zl`), Interpreter (`Interpreter.zl`), and TypeChecker (`TypeChecker.zl`). Tests: `tests/language/test_io_native.zl`.
- **Binary in Membership Operator (Phase 2 Builtins):** First-class binary operator `in` evaluates containment across collections (`List`, `Map`, `Set`), strings (substring containment), and ranges (`1..=10`). Evaluated at comparison precedence. Emits `ZenValue_in` in C Codegen (`Codegen.zl`), `OP_IN` (0x5F, 95) in Bytecode VM (`Bytecode.zl`), `eval_binary` in Interpreter (`Interpreter.zl`), and checked as `Ty.t_boolean()` in TypeChecker (`TypeChecker.zl`). Tests: `tests/language/test_in_operator.zl`.
- **Type Introspection (`type(x)`):** Universal built-in prelude `type(x)` (returns type string name) universally available without import. Dispatched directly in C Codegen (`Codegen.zl` to `ZenValue_get_kind`), Bytecode VM (`Bytecode.zl` via `builtin_type`), Interpreter (`Interpreter.zl` via `reflect.type`), and TypeChecker (`TypeChecker.zl`). Tests: `tests/language/test_type_introspection.zl`. Mathematical operations reside in standard library `zen.math` with full descriptive names as primary functions and short aliases.
- **Direct C Header Imports (`extern use`):** Zero-wrapper C interop allowing direct import of C system headers (`extern use '<header.h>'`, `extern use dotted.path`, `extern use name [as alias]`, `extern from <hdr> use func1, func2`). `TokenType.EXTERN` (kind id 124), `AST.K_EXTERN_IMPORT` (kind id 49), `parse_extern_declaration` in `Parser.zl`, `TypeChecker.zl` variable resolution fallback under `has_extern`, and C Codegen `Codegen.zl` which emits deduplicated `#include` directives, maps module or direct calls to raw C function symbols, unboxes typed/literal arguments via `emit_extern_args`, and wraps return values in C11 `ZenValue_from_c(...)`. Tests: `tests/language/extern_c_01.zl`, `tests/language/extern_c_02.zl`.
- **Dynamic FFI Loader (`__builtin_ffi` & VM/Interpreter Interop):** Dynamic loading and invocation of shared libraries (`.so` / `.dylib`) across Bytecode VM (`Bytecode.zl`) and AST Interpreter (`Interpreter.zl`). Exposes `__builtin_ffi` and `ffi` modules with `load(path)`, `open(path)`, `symbol(h, name, ret_type)`, `call(fn, args, ret_type)`, `close(h)`, `error()`, and `resolve(name)`. `Bytecode.zl` handles direct and flattened member calls (`__builtin_ffi_load`, etc.) and dispatches global symbol resolution in `OP_LOAD_GLOBAL`. `Interpreter.zl` provides dynamic foreign closure calls in `call_fn` and module member lookups in `guest_get`. C Codegen (`Codegen.zl`) maps `__builtin_ffi.*` calls directly to `ZenFFI_builtin_*`. Tests: `tests/lib/test_ffi.zl`.
- **Stage 2.x / 7.x parser:** exact `is_kind`; map literals; `export`/`from import`; soft-keyword names (`scope`/`self`); kind-only operators; `with` / enum / lambda / `is`.
- **Stage 5 / 5.x / 7.x:** `Codegen.zl` — functions, module lets→globals+init, lists/maps, for-in, builtins→ZenIO_*.
  - API: `transpile_source` / `transpile_program` (single unit + host main)
  - Multi-unit: `transpile_unit` / `transpile_unit_ex`; `proto_block_for_program`; `emit_multi_host_main`; register `z_*` protos as free fns (direct C call, not `ZenValue_apply`)
  - **Classes MVP + inheritance:** map instance + `z_Class_method`; `extends` / `base`; field chain; init from base; `parent.meth` → base free fn
  - **with/region:** `emit_with_statement` — `ZenMemory_push_arena`/`pop` when `ZEN_ARENA`; memory builtins mapped
  - CG: `classes`, `methods` (last-wins override), `class_info`, `current_class`/`current_base`
  - Parser: `EXTENDS` token kind (not only KEYWORD extends); `parse_let` marks `AST.let_mut(node) = true` on `set` statements so Codegen emits mutation assignments (`x = val;`) rather than variable re-declarations (`ZenValue x = val;`)
  - Codegen statements: `break;` and `continue;` emit genuine C loop jump statements; `emit_when_cases` uses nested `else { if (...) }` blocks ensuring condition temporaries are evaluated in-scope; `.kind` property maps to `ZenValue_get_kind(obj)`
  - **AOT C Codegen Optimizations & Unboxing:**
    - **Constant Folding (`try_eval_const`):** Recursively evaluates compile-time literal expressions across arithmetic (`+`, `-`, `*`, `/`, `%`), comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), bitwise (`&`, `|`, `^^`, `<<`, `>>`), logical short-circuit (`and`, `or`, `not`), and string concatenation, directly emitting folded literals.
    - **Dead Branch Elimination (`emit_when_cases`, `emit_when_expr_cases`):** Statically evaluates `when` conditions; unconditionally emits matching branch body and prunes all subsequent cases for constant `true`, or skips dead branches completely for constant `false`.
    - **Dead Code Elimination (`is_terminating_stmt`, `walk_block`):** Prunes unreachable statements in statement blocks following terminal statements (`K_RETURN`, `K_RAISE`, `break`, `continue`).
    - **Fast Primitive Dispatch (`emit_binary_fast_int`, `emit_binary_fast_dec`):** Type-aware AST inspection (`is_int_expr`, `is_dec_expr`, `is_bool_expr`, `CG["var_types"]`) emits inlined unboxed operations (`ZenValue_fast_add_int`, `ZenValue_fast_mul_int`, `ZenValue_fast_lt_int`, etc.) bypassing generic runtime dispatch.
    - **Language-Level Concurrency Intrinsics & VM Fiber Bridge (Step 3 Concurrency Substrate):**
      - **AOT C Codegen (`Codegen.zl`):** Statically tracks `Task` and `Channel` types in `CG["var_types"]` (inferred from `conc.spawn`, `conc.channel`, constructor calls, and annotations). Emits direct C runtime intrinsics bypassing dynamic method lookups: `ZenTask_wait((ZenTaskHandle*)obj.as.object)` for `task.wait()` / `.wait`, `ZenTask_cancel` for `task.cancel()`, `ZenTask_is_cancelled` for `task.is_cancelled()`, `ZenChannel_send((ZenChannel*)obj.as.object, val)` for `channel.send(val)`, `ZenChannel_receive` for `channel.receive()` / `.receive`, `ZenChannel_close` for `channel.close()`, and `ZenChannel_is_closed` for `channel.is_closed()`. Free-function calls `channel(...)` and `spawn(...)` compile to `ZenChannel_make` and `ZenTask_spawn_val`.
      - **Bytecode VM (`Bytecode.zl`):** Dynamic method dispatch in `invoke_callable_g` supports `send`, `receive`, `wait`, `cancel`, `is_cancelled`, `is_closed`, and `close`. Handles task fiber execution bridge `run_bytecode_task([fn_chunk, rargs, globals])`: wraps interpreted function chunks and closures in a native C worker adapter, seamlessly dispatching bytecode execution across worker pool threads with 100% frozen handoff boundary compliance. Registers flattened VM prelude symbols (`__builtin_concurrency_channel`, `__builtin_concurrency_spawn`, `__builtin_channel_make`, `__builtin_task_spawn`).
  - Builtins: `__builtin_term`, `__builtin_math`, `__builtin_reflect`, and `__builtin_file`/`File` mapped to exact C runtime functions (`ZenMath_power`, `ZenIO_write_raw`, `ZenIO_read_file`, `ZenMap_get_values`, `ZenMap_get_items`, etc.)
  - Driver alias rewriter: `rewrite_alias_calls_node` traverses `K_ASSIGN`, `K_SET`, `K_LIST`, and `K_MAP` nodes to namespace module aliases inside assignments
- **Enums / lambdas / is / pattern matching:** enumerator members → variant globals; `FunctionExpression` + capture/apply; `IsExpression` → equal; **B1** `when x is [a,b]` / map binds / list spreads `[h, ...t]` / struct destructuring / pattern guards / `check` statements; **B2** `Enum.Var(x)` payload + `is` extract; **B4** nested lambdas flushed after queue
  - **B3 class dispatch:** `obj.meth` uses instance `__type` comparison ternary chain against `z_Class_method` free functions when multiple classes share a short name; last-wins fallback
  - Inits non-static (`zen_module_init` / `zen_mod_init_<stem>`)
  - `int_to_str` → `Str.to_string`; looks_int / looks_dec rules
  - Get: `AST.K_*` → bare global integer kind id; `TokenType.X` integer; `.length` → `ZenValue_get_length`
  - AST node `kind` is `AST.K_*` integer (not a class-name string)
  - Call: module alias `Mod.fn` → free `z_fn`; class method before runtime `has`/`append`
- **Stage 2 class parse:** `parse_class` — let/set fields + functions; optional `extends` → AST `base` (not `parent`)
- **Stage 6/7+:** `Driver.zl` — merge default; multi-unit; **`build` / `run`/`-g`** via `CLink.zl`; **`vm`** / **`interpret`/`eval`** accelerated by `Bytecode.zl` with `Interpreter.zl` fallback; **`test`/`--test`** via `Interpreter.zl`
  - **Incremental & Multi-Unit Compilation:** `Driver.compile_file_multi` / `build_file_multi` with `-i` / `--incremental` and `-m` / `--multi`. Unit invalidation in `.cache.zd` combines exact byte length with a 32-bit FNV-1a hash (`<len>_<hash>`) via `compute_content_sig`, sensitive to any character edit. Dependency-aware invalidation tracks `__shared__` prototypes across TUs, invalidating all units when shared signatures change.
  - **Object Caching:** `CLink.build_multi_units` compiles modified units (`.c` → `.o`) and reuses existing unchanged `.o` files, linking with cached `bootstrap_runtime.o` into the standalone binary.
  - **Arena Profiling:** `ZEN_PROFILE=1` outputs stage timing and arena memory footprint (`allocated`, `capacity`, `chunks`) via `prof_arena_log` and `__builtin_memory.arena_stats()`.
  - Typecheck under multi still uses merged program
  - Codegen fail = empty / `/* parse error` prefix only
  - CLink: find gcc/clang/tcc (`ZEN_CC` override); `-O2` default (`ZEN_OPT=0|1|2|3|s`); `-I runtime/` (no per-build copy); cache `output/selfhost_rt/bootstrap_runtime.o`; link out.c + that .o
  - `lsp` is not linked into zen-selfhost; hybrid `./bin/zen lsp` runs `tools/zenlsp.zl`
  - Interpreter: map env (`outer`); int literal coerce; return via module flags; `when x is [a,b]` / map / `Enum.Var(x)` binds; real `io.*`/`output.*` builtins dispatch; `eval_while` handles `K_DO_WHILE` (`AST.do_while_body`/`AST.do_while_cond`); `eval_expr` supports `K_BLOCK` and `K_WHEN` expressions.
  - Driver CLI: `interpret`/`eval`/`vm`/`test`/`--test` are tokens in `is_cli_token` (must not skip as argv0); native `zen-selfhost test` discovers/executes `test_*` functions; `vm` executes via bytecode compiler and stack VM engine without C compilation.
  - Bytecode VM & Parity: `Bytecode.zl` handles 4-boundary ranges (`..`, `..-`, `..=`, `...`, `..+`), exponentiation `**` (OP 61 `OP_POW`), underscore separators in number literals (`1_000_000`, `0xDEAD_BEEF`, `0b1010_0101`, `0o755`), type constructor calls (`Integer(val)` via `K_VARIABLE` and `K_LITERAL`), `Map.get`/`Map.at` with default value fallback, String-to-Decimal casting, and zero-allocation `OP_CALL` argument extraction (direct forward reading from evaluation stack without intermediate lists or reversal loops).
  - **A1 import graph:** `interpret_file` uses GraphBuilder compilation order; `import path as Alias` binds a map of exported free fns + module lets + classes/enums (skip `main`)
  - **A2:** `do for` / lists / maps / IndexAssign / `.length`; list append + index write-back for `-g`
  - **A3:** `__builtin_string` (and file/io stubs) so `import zen.text.string as Str` works; STRING literals are not coerced to ints
  - Parser: `let` is mutable, `set` is constant (`v == 'let'`); `let x :> expr` parses initializer; `Codegen` uses positional `AST.*` accessors for `K_ASSERT`, `K_ASSIGN`, `K_INDEX_ASSIGN`, `K_SET`, and `K_CHECK_STMT`.
  - **Check Statements & Pattern Matching:** `check` (`?`), `raise` (`^`), `assert` (`!`). `Parser.zl` parses `check expr { case ... } or (alias) { ... }`, `check expr or fallback`, `? expr or fallback`, `case is <Type>`, and `case in <coll>`. `AST.zl` encodes `check_stmt_alias` at slot 7. `Codegen.zl` wraps `expr` in `ZenExceptionContext` (`setjmp`/`longjmp`), binds `ZenException_last` to temporaries, matches cases, falls back to `or_block` binding `error` and optional alias to the subject/error value, and re-raises unhandled exceptions when no `or` block exists. Logical `or` coalesces `ZEN_ERROR` and `ZEN_NOTHING`. `Bytecode.zl` handles `K_IS` and `K_BINARY` (`in`) in `compile_pattern_case` with full scope and jump patching. `Interpreter.zl` provides dual-path parity in `eval_check_stmt` and `match_pattern_value`. Covered in `tests/language/check_match_test_01.zl`.
  - **Phase L:** `Default` sentinel materializes from a TypeAnn (`Integer`→0, `Boolean`→False, `String`→``, `List`→[]); `== Default` compares to that zero; `Nothing` is distinct. Lexer accepts lowercase aliases.
  - **Phase D:** classes/`extends`/`self`/`parent.meth`; closures by-value snapshot; enums + payload `is`; `with` + software MEM arena; `__builtin_memory` / real standard output. Guest `.length` must not hit `.has` on lists; never `Str.to_string` cyclic env maps (native overflow).
- **Interpreter.zl** — endgame Phase A+D+E AST walk; tests: `test_interpreter.zl` (22 dual-path)
- **Bytecode.zl & Standalone Packaging (.zbc):** `compile_program`, `serialize_chunk`, `deserialize_chunk`, `write_bytecode_file`, `read_bytecode_file`, `compile_file_to_bundle`, `eval_bytecode_file`, `invoke_callable`, `create_vm_prelude` — compiles AST to compact bytecode chunks for immediate VM evaluation without GCC. Supports cross-module imports, namespaced member resolution, standard library prelude capabilities (`io`, `IO`, `output`, `input`, `file`, `term`, `sys`, `time`, `Str`, `zd`), bounds-safe local registers (`OP_LOAD_LOCAL`, `OP_STORE_LOCAL`), loop constructs (`K_FOR`, `K_WHILE`), and `.zbc` standalone binary bytecode caching and packaging (`zen bundle <file.zl>`), allowing source-free execution (`zen <file.zbc>`). Tests: `test_vm.zl` (7 dual-path), `test_vm_multimodule.zl` (4 dual-path), `test_mixed_abi.zl` (6 dual-path), `test_bytecode_cache.zl` (3 dual-path).
- **Plugin.zl & Compiler Extension Subsystem:** `register_plugin`, `reset_plugins`, `dispatch_on_ast`, `dispatch_on_check`, `dispatch_on_codegen`, `dispatch_command`, `report_issue` — provides a modular extension ecosystem for developer tooling (linters, AST inspectors, comment/TODO trackers, custom CLI commands) keeping the compiler core lean and extensible. Default plugins: `TodoTracker`, `Linter`. Tests: `test_plugins.zl` (4 dual-path).
- **Extensions.zl & Baked-in Developer Tooling:** `compiler_info`, `disasm_file`, `disasm_chunk`, `ast_file`, `bash_completion_script`, `get_command_suggestion`, `style_*` ANSI helpers — baked into `bin/zen` as native modules for zero runtime overhead.
  - ANSI terminal styling functions respect `NO_COLOR` and `TERM=dumb`.
  - Bytecode disassembler (`zen disasm`) formats chunk headers, constant pools, opcodes, and operands.
  - AST inspector (`zen ast`) pretty-prints hierarchical AST structure with source line/column positions.
  - Bash completion generator (`zen completion bash`) provides comprehensive CLI flag, subcommand, and file (`*.zl`, `*.zbc`) tab completion.
  - Command typo suggestion engine matches prefix/substring/Levenshtein approximations ("Did you mean 'build'?"). Tests: `test_cli_modern.zl` (4 dual-path).
- **Daemon.zl & Resident Compiler Service:** `zen daemon start|stop|status|clear` manages background compilation service over Unix Domain Socket (`/tmp/zen_compiler.sock`) with descriptor multiplexing via `ZenNet_poll`.
  - Integrates Linux `inotify` kernel watchers with debouncing for sub-millisecond incremental cache invalidation (`GraphBuilder.invalidate_cache`).
  - CLI commands (`compile`, `build`, `check`) transparently proxy requests to the daemon when active, falling back seamlessly to in-process compilation if unreachable.
- **Stage 7:** Standalone Native Compiler + E2E + Self-Rebuild.
  - Standalone `bin/zen` is pure native selfhost compiler with zero Python fallback (`./scripts/zen install`). Python bootstrap compiler is retained only as an initial seed / emergency rollback (`./scripts/zen install-rollback`).
  - `selfhost-smoke` → 50/50 tests passed; self-rebuild of `selfhost/zen.zl` (`ZEN_SELFHOST_REBUILD=1`) is 100% green (native selfhost parses and emits selfhost compiler to C, gcc links secondary binary `zen_from_self`, which executes help, lists plugins, bundles bytecode, and compiles fixtures to working binaries with zero Python involvement).
  - Codegen file emit: `transpile_program_to_file` / `CG.out_path` buffers in-memory for single-pass file emission (`io.write_file`); `do`/`while` → `while (1)` + `break` so emit_expr temps stay in scope
  - **STRING/RUNE token_kind** stay C strings (`emit_literal_node`); `looks_int("0")` is true and would turn `` `0` `` into `ZenValue_make_integer(0LL)`
  - Driver merge uses in-place `StmtChunk` pointer linking (`AST.stmt_chunk` / `AST.set_stmt_chunk_next`) for $O(1)$ zero-copy module merging.
  - Bare `io.write` → `ZenIO_write_*` (`emit_builtin_call` includes `io`, not only `IO`)
  - Interpreter prelude binds `io` / `IO` / `output` (bootstrap injects these without import)
  - CLink `run_exe` reprints captured child stdout/stderr so `run` matches bootstrap `-g`
  - `selfhost/zen.zl` passes through integer CLI codes (not collapsed to 0/1)
  - E3 golden: `./scripts/zen test-golden`
  - Merge + interpret reuse GraphBuilder `parse_cached` (one parse per path after graph walk; keys strip `./`)
  - GraphBuilder `source_may_import`: skip graph when entry source has no `import ` / `use ` / `from `
  - Runtime maps are hashed (AST/`CG`/env lookups); insertion order kept
  - Short strings interned in `ZenValue_make_string` (len 1–32)
  - After editing `runtime/`, delete `output/selfhost_rt/` so CLink recompiles the cached `.o`
  - Lexer: `tok_push` rebinds `LEX.tokens`
  - Parser: `stmt_push`; enumerator payloads via `parse_enum_member_value`; `is List`/`raise` for stdlib (`json.zl`)
  - **Namespacing:** lib/zen + selfhost/compiler; fixtures bare
  - IndexAssign; escape_piece / real NL-TAB
- Output targets top-level `runtime/` for link.
- **User-program backend:** AST→ZenValue C. No MIR/SMIR mid-end (PARITY).
- **Version 1 Beta (`v1.0.0-beta.1`) Unified Toolchain & Closure:** Standalone native `bin/zen` operates as a self-contained single binary developer platform (akin to Cargo, Go, Zig) with Stage 2 self-compilation closure:
  - **Stage 2 Self-Hosting Closure:** `bin/zen` compiles `selfhost/zen.zl` natively without bootstrap Python dependency.
  - **Directional Comprehensions (`[for x in list -> expr]`, `{for k, v in map -> k: v}`):** List and map comprehensions with optional `when` filter clauses desugar into efficient accumulator loops across Bytecode VM, Native AOT, and Interpreter with `G_ALLOW_ASSIGN` precedence protection.
  - **Collection Spreads (`[...list]`, `{...map}`):** List concatenation and map merging via `...expr` spread elements supported with 100% parity across VM, C runtime (`ZenList_concat`, `ZenMap_merge`), and AOT.
  - **Manifest-Driven Workflows:** In project directories containing `zen.pkg.zd` (or `.zbuild`), `zen build`, `zen run`, `zen test`, and `zen clean` automatically bind to the project manifest with zero config.
  - **Interactive REPL:** Bare invocation (`zen`) on an interactive TTY directly launches the native terminal line-editor REPL (`zen repl`).
  - **Zero-Config Package Management (`zen pkg`):** Automatically discovers modules in `deps/<pkg>/lib/`, `deps/<pkg>/src/`, `deps/<pkg>/<pkg>.zl`, and `deps/<pkg>/main.zl`. Full lockfile management with `zen.lock.zd`.
  - **Code Formatter (`zen fmt`):** Built-in style guide enforcer with stdout, `-w` (in-place write), and `--check` modes.
  - **Terminal Man Pages & Symbol Lookups (`zen doc <query>` / `zen explain <query>`):** Built-in interactive manual pages for language keywords, operators, types, sentinels, I/O streams, and stdlib modules (`zen doc --topics`).
  - **Graceful Empty File Diagnostics:** When compiling empty or blank files, refuses to emit empty `out.c` or binaries, outputting an instructional minimum program template.
  - **Optional Incremental Multi-Unit Compilation (`--incremental` / `-i`):** In `compile_file_multi` and `builder.zl`, tracks unit modification signatures in `.cache.zd`, skipping transpilation and GCC compilation for unchanged modules.
  - **Static & Shared Linking:** `zen build` supports `--static` (fully self-contained static binary) and `--shared` (dynamic `.so` library).
  - **Release Packaging Pipeline (`./scripts/zen release`):** Standalone archive bundle generation packaging `bin/zen`, `lib/zen`, docs, examples, licenses, and SHA256 checksums (`zen-v1.0.0-beta.1-<os>-<arch>.tar.gz`).
  - **Extensible Tooling Plugin Subsystem:** `Plugin.make_tooling_plugin()` dynamically dispatches `new`, `init`, `pkg`, `repl`, `fmt`, `doc`, `explain`, `dash`, `watch`, `bench`, `clean`, `publish`, `bump`, `env`, `profile`, `graph`, `playground` via `Plugin.find_tool_path` and `vm_cli`.
  - **Global Path Resolution:** `Resolver.zl` automatically locates `<root>/lib`, `<root>/deps`, `<root>/selfhost`, and `ZEN_PATH` entries when executed from arbitrary working directories.
- **Three-Layer Architecture & Parity:** Implemented with 100% parity across interpreter, native `-g`, and standalone `bin/zen`:
  - **Layer 1 (ZenValue ABI & C VM):** Shared ABI across interpreted and native modes, opcode parity in C VM (`zen_vm.c`, `zen_vm.h`) matching `Bytecode.zl` (`OP_RANGE_*`, `OP_CONCAT_APPEND`, `OP_DROP`, `OP_CHECK_UNWRAP`, `OP_IN`, `OP_COALESCE`, `OP_SLICE`).
  - **Layer 2 (Compiler IR):** Positional AST list structs (`[kind, line, col, ...payload]`) with $O(1)$ in-memory caching in `GraphBuilder.parse_cached` and `Driver.parse_file_cached`.
  - **Layer 3 (Script VM Execution Bridge):** Running `.zbc` chunks natively in C VM via `__builtin_vm.run_file` / `vm_cli` and `ZenValue_run_bytecode_file`. Tests: `tests/self_hosting/test_three_layer.zl` (dual-path).
- Memory: default automatic via runtime; opt-in `with`/arena → Codegen push/pop; checker scopes with-alias (ownership rules later).
- Production install: standalone pure native compiler `bin/zen` (`./scripts/zen install`). Fast local smoke: `./scripts/zen ci`. Soak: `./scripts/zen ci-soak`. Emergency rollback: `./scripts/zen install-rollback`.

# Work Guidance

- Prefer free functions + maps under `-g`.
- Unique names across modules when co-linked (`cg_walk_stmts` vs TypeChecker `walk_stmts`).
- Mutators return updated maps; callers rebind.
- Capture lengths before `do for`; prefer index recursion for multi-pass.
- Codegen: stream to `out_path` when compiling to a file; in-memory join is pairwise (`join_parts_tree`); ints via `Str.to_string`. STRING/RUNE use `emit_literal_node` (never `looks_int` on backtick digits).
- **Always emit IndexAssign** (`obj[k] -> v` → `ZenValue_set_at`) — required for module maps.
- **Multi-file namespacing:** `Driver.module_fn_prefix` + `append_file_stmts` rewrite; Codegen `Module.fn` → `z_Module_fn`. Fixtures not namespaced.
- Lexer & Parser escapes: `escape_piece(esc)`; `_ch_nl`/`_ch_tab`/`_ch_esc` real chars (not `\n`/`\x1b` string literals); `unescape_string_literal` and Codegen `escape_rec` convert `\x1b`, `\e`, and `\033` into real ESC bytes.
- `file_stem` / path scans: recursive, no `do while` rebind under `-g`.
- Avoid reserved names (`object`, `parent`, `scope` as function prefix, alias `T`).
- CLI paths: branch to helpers instead of rebinding `let` under nested `when` (`-g`).
- Keep tests under `tests/self_hosting/` (fixtures: `stage7_add`, `stage5_for_sum`, `multi_lib`/`multi_main`, `class_counter`, `class_inherit`, `enum_color`, `closure_add`, `with_region`, `interp_import`/`interp_lib`, `interp_map`, `interp_str`, `nothing_default`, `pattern_bind`, `enum_payload`, `class_dispatch`, `closure_nested`).
- Multi-unit: free functions external; host owns `main`; shared protos + **extern module globals**; capture `.length` before `do while` in Codegen.
- Multi self-rebuild gate: `./scripts/zen multi-selfhost-smoke`
- Classes: never use bare identifier `parent` in selfhost sources; map key `base` for extends.
- Class methods: **last**-registered short name wins (`obj.meth`); emit base before derived for overrides. No vtables.
- `parent` only as receiver in methods (`parent.speak`); never bind bare `parent` as a local.

# Verification

```bash
export ZEN_PATH=$PWD:$PWD/selfhost:$PWD/lib
for t in test_lexer test_parser test_module test_checker test_codegen test_driver test_interpreter test_plugins test_bytecode_cache; do
  python3 bootstrap/Zen.py tests/self_hosting/${t}.zl
  python3 bootstrap/Zen.py -g tests/self_hosting/${t}.zl
done
python3 bootstrap/Zen.py selfhost/zen.zl help
python3 bootstrap/Zen.py selfhost/zen.zl interpret tests/self_hosting/fixtures/stage7_add.zl
./scripts/zen install-selfhost
./scripts/zen selfhost-smoke
./scripts/zen install
```

# Child DOX Index

- Token.zl, Lexer.zl — Stage 1 (integer TokenType ids on native; KW map)
- AST.zl — integer K_* node kinds
- Parser.zl, AST.zl — Stage 2 MVP
- Module/ — Stage 3 MVP
- TypeChecker.zl, Types.zl — Stage 4 MVP+
- Codegen.zl — Stage 5+; CTranspiler.zl legacy
- CLink.zl — Zen→C link/run (gcc/runtime)
- Interpreter.zl — endgame #5 AST interpret MVP
- Bytecode.zl — Three-Layer Phase 3 bytecode compiler, caching (`.zbc`), and VM chunk evaluator
- Plugin.zl — Compiler plugin & extension manager with lifecycle hooks
- Driver.zl, main.zl — Stage 6/7+ CLI; ../zen.zl entry
- Builder.zl, host_main.c — legacy
