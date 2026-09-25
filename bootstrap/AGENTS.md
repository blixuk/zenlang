# Purpose

The Python bootstrap compiler that implements the full Zenlang pipeline: lexing, parsing, semantic and type checking, interpretation, and transpilation to C. It is the current development host and reference implementation for all language features while self-hosting in Zenlang matures.

# Ownership

Owned by the bootstrap layer maintainers. Contains the complete working implementation of the compiler and tooling.

# Local Contracts

- bootstrap/Zen.py is the main orchestrator (load, lex, parse modules with dependency resolution, type/semantic check, interpret or transpile+compile).
- All major phases (Lexer, Parser, Checker, Interpreter, Transpiler) live here as the authoritative logic.
- Transpiler/runtime is a **symlink** to the project-root `runtime/` (canonical shared C runtime). Edit `runtime/` only; do not maintain a second private tree.
- Debug stdout prints must stay gated (`debug`/`debugging` flags). File tracing via `Logging/Trace.zen_trace` only when `ZEN_TRACE=1`.
- Typecheck is fail-closed: diagnostics print and process exits non-zero; no silent success after type errors.
- Deferred function bodies: `TypeChecker.defer_function_bodies` is on; `check_program` flushes deferred bodies after the declare pass so later siblings (e.g. Lexer `_read_doc`, `scope Sentence { to_words; count_words }`) resolve. Fail-closed: logged type errors still exit non-zero.
- Module-level rebind of `__builtin` / `__builtin_*` is allowed (stdlib aliases).
- `sys.get_args` / `__builtin_sys.get_args` reflects interpreter argv (script path + user args).
- Native `-g` runs `zen_program` with the same user/script argv extras as interpret mode (`CCompile.compile(..., run_args=)`).
- Integer/bool `main` results become process exit codes.
- Move checking is opt-in (`MemoryKind.UNIQUE`); structures share by default so compiler sources can rebind AST nodes.
- Native error constructors: `__builtin.error` raises (`ZenValue_make_error_message` + `ZenException_raise`); `error_literal` returns Error value only.
- Check expressions use Try/setjmp so raised errors are catchable (`check expr or { … }`), matching the interpreter.
- Import aliases must install a fresh MODULE symbol — never mutate an existing function symbol in place (collision: `import zen.error as error` vs `io.error`).
- `use` is a keyword alias for `import`; `from path use name` aliases `from path import name` (prefer `use` in new code; AST remains ImportStatement).
- Built-in `module` map (name, path, file, dir, is_entry): interpreter injects per Environment; native `ZenModule_initialize` + global `module` in `runtime/core/zen_sys.c`.
- `structure/class/object … is reflectable`: AST flag; native `ZenReflect_register_type` in `init_singletons`; class instances `ZenReflect_tag_object`; stdlib `zen.reflect` + `__builtin_reflect`.
- `module.entry -> \`name\`` or function value selects process entry (interpret + native `-g`); no `@entry` decorator.
- Native host: user `main` emits as `zen_user_main`; C `main` runs init_singletons + entry-file top-level (incl. `module.entry`) then dispatches string/function entry or `zen_user_main`.
- `reflect.call` / `ZenReflect_call`: map-of-functions (plugins); class methods via `ZenReflect_register_method` thunks for `is reflectable` classes under `-g`.
- Top-level init only runs statements from the entry file (skip merged deps without filename / other files).
- Mangle: do not map local VARIABLE names (`out`, `in`, `file`, …) to `__builtin_*` — only bare global/capability identifiers.
- Module-qualified calls: `alias.fn` / `alias.Type()` → `<module>_<fn>` / `<module>_<Type>_new`; path imports (`lib/zen/io`) use basename only.
- Native `TokenType` enumerator globals (`ZenVariant_TokenType_X`) are initialized as integer ids 0–114 (`TOKEN_TYPE_IDS`) matching `selfhost/compiler/Token.zl` `kind_id`. Parser hot path is int equality on those singletons.
- CCompile honors `ZEN_OPT` (`0|1|2|3|s|g`, default `2`) and `ZEN_CC` (gcc/clang/tcc). Edit-loop: `ZEN_OPT=0 ./scripts/zen install-selfhost-fast`.
- CCompile links `out.c` + cached `output/selfhost_rt/bootstrap_runtime.o` with `-I runtime/` (no per-build copy of `runtime/`). Delete that `.o` after editing `runtime/`.
- Native builtins: `__builtin_time` → `ZenTime_*`; `__builtin_term` → `ZenTerm_*` (ANSI + `raw_enter`/`raw_exit`, `read_key`/`poll_key`, `paint_canvas` bulk TUI paint, cursor/write/flush, `mouse_enable`/`mouse_disable`, `is_tty`); `__builtin_process` → `ZenProcess_*` (+ handle wait/stdout/code/kill; `shell` / `shell_result` via `/bin/sh -c`); `__builtin_net.http_request` → `ZenNet_http_request` (curl); file IO extended (`append`, `remove`, `is_file`, `is_dir`, `write_bytes`, `open`, `list_dir`, `mkdir`, `mkdir_p` + handle read/write/close). Same-module calls that share names with `zen.io` (`read`/`write`) must use `__builtin_file.*` under `-g` to avoid `io_read` mangling.
- Interpreter map/record access: `.kind` is type introspection unless the value is a map/object that already has a `kind` field (term key maps, etc.).
- `ZenSystem_chdir` for `sys.chdir` (bash `cd`).
- Map/record field access (`size.width`): `ZenValue_get_field` when type is Map/unknown (not only C struct fields).
- Native class param/return field access: annotate method params and returns with class types (`v: Vector2`, `center() : Point`) so MIR uses struct fields instead of `ZenValue_get_field` (maps only). PointerCopy / call_return_types preserve class types through SSA.
- Native structures are map-backed (`Type_new` → `ZenMap_make_from_arguments`) so `.field` works without static types via `ZenValue_get_field`. Classes remain C structs.
- SMIRGenerator inherits `current_scope` so named-scope sibling calls (`to_words` inside `scope Sentence`) mangle to `text_Sentence_to_words`. Only FUNCTION symbols take the `current_scope` prefix (not Structure/Class type names).
- Qualified structure literals `text.Word { … }` parse as name `"text.Word"` (not `str(MemberExpression)`); scope statics `text.Word.capitalize` → `text_Word_capitalize`. Prefer inlining cross-scope static calls inside other scopes when native mangling is incomplete.
- One-arg `s.substring(start)` / `s.slice(start)` supply end=`length` for `ZenString_get_substring`; `slice` aliases substring.
- Map/list `.get(key)` on ZenValue receivers maps to `ZenValue_get_at` (not class methods).
- Native memory: `__builtin_memory.*` → `ZenMemory_*` (do not alias through a local `__builtin` binding).
- Native regex: `__builtin_regex.*` → `ZenRegex_*` (POSIX ERE in `runtime/core/zen_regex.c`; `\s`/`\d`/`\w` expanded; `find_all` returns group lists when captures exist).
- Native `.kind` → `ZenValue_get_kind` (primitives + Map; Map field `kind` overrides).
- Structure `Type_new` map-backed instances include `"kind" → "TypeName"` for ECS/type checks.
- Bytes: `ZenBytes_*` in `runtime/core/zen_bytes.c`; map `.remove(key)` via `ZenMap_remove_key`.
- Native `&&`/`||` map to `ZenValue_and`/`ZenValue_or` (logical); prefer `and`/`or` keywords in stdlib.
- Native method dispatch: list/map/string ops on `ZenValue` receivers (including closure captures) use `ZenValue_*` / `ZenString_*` — never `(ZenValue*)x.as.object` class-method form.
- `IO.writeln` / `io.writeln` map to `ZenIO_write_line` (not `ZenIO_writeln`); module aliases participate in MIR import dispatch.
- Native string `<>`/`<=`/`>=` use `strcmp` (not numeric cast of string bits) — required for JSON digit parsing and similar.
- Module constants (`log.LEVEL_WARN`) resolve via `_module_key_for_attr` even when the alias is mangled as `log_log`.
- Shell scripting stdlib: `zen.sys.process` — shell string APIs, cwd/env overlays, fluent `Pipeline` (real `pipe(2)` argv stages), `each_line` streaming.
- Native: `ZenProcess_pipeline_run(stages, cwd, env)`; `ZenProcess_shell_each_line*` applies fn per line via `ZenValue_apply`.
- Native shell env: child `setenv` from Map overlay; parent process env untouched.
- Class method returns of `self` box via `ZenValue_from_object`; method receivers cast `((Class*)v.as.object)`; bare `self` args stay raw pointers.
- Native math: `__builtin_math.*` / bare sin/cos/… → `ZenMath_*` (never raw libm).
- Native first-class functions: `ZenValue_apply` / `ZenValue_from_function` / `ZenValue_from_closure` (`ZenClosureData` in as.object); captures prepended as leading params; lambda flush after main so lambdas in `main` emit.
- Closures: free outer locals snapshotted by value at creation (interpreter Environment shadow + native caps); max 8 captures.
- Function merge key is `(filename, name)` so same-named helpers in different modules both emit.
- Structure/class definitions and type names are module-prefixed from source filename (`time_Duration`, `time_Timer_*`).
- List equality is deep (element-wise), not pointer identity.
- Pattern matching (native): RestPattern / DestructurePattern / guards; pattern binds copy (Borrow) not Move; `Result.Ok(x)` → `ZenValue_make_variant`.
- Ranges: lexer `..` / `..=` (not `...`); interpreter + `ZenValue_range` / `ZenValue_range_inclusive`; result is List.
- Extended `++` and `--` operators: `++` appends/prepends/concatenates strings and lists (or adds numbers); `--` drops $N$ characters/items from end (`target -- N`) or from start (`N -- target`) (or subtracts numbers). Statement-level updates (`bar ++ "░"`, `test -- 4`, `1 -- test`) lower directly to reassignment.
- Binary `in` Membership Operator: first-class binary comparison operator `in` evaluates containment across lists, sets, maps (keys), strings (substrings), and ranges (`val in container`). Evaluates in bootstrap Interpreter (`ExpressionHandler`), Checker (returns `TypeBoolean`), and lowers to `ZenValue_in` in MIR transpiler.
- Type Introspection (`type(x)`): universal built-in prelude `type(x)` (returns type string name) registered in global `Environment` and `TypeChecker`, lowering to direct C calls `ZenValue_get_kind` in `MIRHandler`. All math operations reside in standard library `zen.math` with full descriptive names as primary functions and short aliases.
- Abstract & Union Types (`Number`, `Text`, `Collection`, `Container`): `Number` encompasses `Integer`, `Byte`, `Decimal`, and sized variations; `Text` encompasses `String`, `Rune`, and sized `String[SIZE]`; `Collection` encompasses `List`, `Vector`, `Set`, `Tuple`, and `Map`; `Container` encompasses `Structure`, `Object`, `Class`, and `Enumerator`. Supported across pattern matching (`val is Type`, `when val is Type`), type casting (`val <: Type`, `Type(val)`), and type annotations with 100% parity across bootstrap Interpreter, TypeChecker, and C transpiler.
- Parameterized Generic Type Annotations (`List<T>`, `Map<K, V>`, `Set<T>`, `Vector[N]<T>`, `Tuple<...>`): Parameterized type syntax using canonical `<...>` parsed in `Patterns.py`, `Primary.py`, and `ParsingHelpers.py`. TypeChecker enforces structural collection unification and compile-time rejection of mismatched element assignments without lenient variant fallback on explicit annotations. Interpreter and Transpiler support generic type prefixes in `is` matching, casting (`<:`, constructor calls), and Default materialization.
- User-Defined Generic Types & Functions (`function f<T>`, `structure Box<T>`, `class Storage<T>`): Support for generic function, structure, and class declarations (`type_params`), explicit type argument calls (`f<Integer>(x)`), generic constructor calls (`Box<Integer>{ ... }`, `Storage<String>(...)`), pattern matching (`val is Box`, `val is Storage`), and type introspection (`type(box)`). Strict canonical type enforcement treats single-letter uppercase names (`T`, `A`, `B`, etc.) as type parameters only within their defining generic scopes while rejecting forbidden informal collection aliases elsewhere. Full parity across Interpreter and Transpiler (`-g`).
- Directional Guard Returns & Concise Functions: `function f(x) <- expr` and `task t(x) <- expr` declare single-expression functions/tasks lowering to `BlockStatement([ReturnStatement(expr)])`. `when cond <- expr` and chained `or when cond <- expr` / `or <- expr` guard returns lower directly to block returns.
- Modern Error Diagnostics & Source Frames: `Logging/Diagnostic.py` provides `SourceCache`, `Span`, `Diagnostic`, and `DiagnosticRenderer` rendering ANSI-colored source frames with `--> file:line:col`, context lines, line numbering gutters (` 14 | `), colored caret underlines (`^^^^`), and notes/hints. Diagnostics support export to Zen Data (`.zd`) and Zen Mark (`.zm`) Callouts. `LexerLogger`, `ParserLogger`, `TypeCheckerLogger`, `Logger`, and `Errors` format through `DiagnosticRenderer`.
- Native `do` loops: `while` / `until` pre-test; `while_post` / `until_post` body-first (`do {…} until cond` stops when cond is true).
- Module resolution searches selfhost/ and lib/ (see ZEN_PATH).
- Stdlib is nested-only under `lib/zen/<domain>/`; short aliases (`zen.string`→`zen.text.string`, `zen.term`→`zen.sys.term`, …) live in `Module/Resolver._IMPORT_ALIASES`.
- `-g` copies project-root `runtime/` into `output/build/` (via CCompile); extend `runtime/` for native lib support.

# Work Guidance

- Preserve the phase-oriented package layout (Lexer/, Parser/, Checker/, Interpreter/, Transpiler/, Logging/, Module/, Build/, REPL/, Test/).
- Use handler mixins and delegation for Parser and Transpiler extensibility (see Transpiler/Handlers/ and Parser/ handlers).
- Add or extend diagnostics via Logging/ (loggers, dumper for AST/JSON, Trace, Diagnostic engine).
- Prefer explicit code; keep debug paths gated.
- When a feature is added or changed here, consider the corresponding port impact on selfhost/compiler/.
- Scope/namespace constants must initialize their mangled globals (`ZenVariant_*`) in `init_singletons` for native parity.

# Verification

- `python3 bootstrap/Zen.py <source.zl>` (interpret, default)
- `python3 bootstrap/Zen.py -g <source.zl>` (transpile → C → run `output/build/zen_program`)
- `python3 bootstrap/Zen.py --check <source.zl>` / `--test <source.zl>`
- `make test-core` and `make test-parity` (core language ladder)
- Self-host verification under tests/self_hosting/ and tests/native_compiler/ (advanced)
- REPL and individual phase tests

# Child DOX Index

- Lexer/: Core lexer + Rules/ (numbers, strings, identifiers, operators, symbols, comments). Token.py.
- Parser/: Parser.py, AST.py + AST/ (node definitions), handlers (StatementHandler, ExpressionHandler, TokenHandler), Scope.py, ParseContext.py, Rules/ (Statements/, Expressions/).
- Checker/: SemanticChecker.py, TypeChecker.py, Type.py, Scope.py, Handlers/ (for statements, expressions, literals, patterns).
- Interpreter/: Interpreter.py, Runtime.py, Exceptions.py, Handlers/ (Builtin, Statement, Expression, Literal, Pattern).
- Transpiler/: CodeGenerator.py (multi-inheritance handlers), BaseGenerator.py, CCompile.py, MIR.py, SMIR*, Handlers/ (Expression, Statement, Structural, Functional, Type, Mangle, Pattern, MIR). Also contains vendored runtime/.
- Logging/: Diagnostic.py (SourceCache, Span, Diagnostic, DiagnosticRenderer), Dumper.py (AST), Errors, various *Logger.py, Printer.py, Trace.py.
- Module/: Resolver.py, DependencyGraph.py.
- Build/: BuildSystem.py.
- REPL/: REPL.py.
- Test/: TestRunner.py.
- Note: __pycache__/ is transient.

## bootstrap/Transpiler/runtime/
Symlink → `../../runtime`. Canonical sources and AGENTS live under top-level `runtime/`.
