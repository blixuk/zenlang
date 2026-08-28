# Purpose

Self-hosted compiler components ported from `bootstrap/`.

# Ownership

Part of `selfhost/` parity effort.

# Local Contracts

- Map 1:1 to bootstrap packages where possible (Token/Lexer ↔ `bootstrap/Lexer/`).
- **Stage 1:** `Token.zl`, `Lexer.zl` — dual-path.
  - Tokens are flat positional tuples `[kind, start, length, line, column, end_line, end_column]` via `Tok.token` (Phase 5.1 zero-copy token spans). Accessor helpers `tok_kind`, `tok_start`, `tok_length`, `tok_lexeme(src, t)`, `tok_line`, `tok_column`, `tok_end_line`, `tok_end_column` index `t[0..6]`.
  - State `LEX` is a flat positional list `[src, pos, len, line, col, tokens]` indexed via `LEX_SRC..LEX_TOKENS` integer constants (Phase 5.2 state de-indirection).
  - `ZEN_PROFILE=1` on parse/compile/interpret prints stage ms (`profile lex` … `profile total`).
  - Native host: bootstrap emits `TokenType.X` as integer ids 0–114; Parser `is_kind` is `k == name`.
  - Interpret host: `kind` stays the TokenType variant; same `k == name` (no `kind_id` on the lex/parse hot path).
  - Lexer identifier lookup uses zero-allocation length-switch character matcher `match_keyword(src, start, len)`.
  - API: `Lexer.tokenize_source(src)`.
- **Stage 2:** `AST.zl`, `Parser.zl` — dual-path MVP. AST nodes are flat positional list structs `[kind, line, column, ...payload]` created via constructors in `AST.zl` and accessed via `AST.*` accessors (`stmt_kind`, `fn_name`, `expr_left`, `prog_stmts`, etc., migrated from string-keyed maps). Parser result helpers are `parser_ok` / `parser_ok_list` (not `ok`) so native C does not collide with `zen.sys.process.ok`. Statement lists via `stmt_push`; enumerator `->` payloads via `parse_enum_member_value` (nested `j` rebind hangs Token.zl under `-g`).
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
- **Stage 2.x / 7.x parser:** exact `is_kind`; map literals; `export`/`from import`; soft-keyword names (`scope`/`self`); kind-only operators; `with` / enum / lambda / `is`.
- **Stage 5 / 5.x / 7.x:** `Codegen.zl` — functions, module lets→globals+init, lists/maps, for-in, builtins→ZenIO_*.
  - API: `transpile_source` / `transpile_program` (single unit + host main)
  - Multi-unit: `transpile_unit` / `transpile_unit_ex`; `proto_block_for_program`; `emit_multi_host_main`; register `z_*` protos as free fns (direct C call, not `ZenValue_apply`)
  - **Classes MVP + inheritance:** map instance + `z_Class_method`; `extends` / `base`; field chain; init from base; `parent.meth` → base free fn
  - **with/region:** `emit_with_statement` — `ZenMemory_push_arena`/`pop` when `ZEN_ARENA`; memory builtins mapped
  - CG: `classes`, `methods` (last-wins override), `class_info`, `current_class`/`current_base`
  - Parser: `EXTENDS` token kind (not only KEYWORD extends); `parse_let` marks `AST.let_mut(node) = true` on `set` statements so Codegen emits mutation assignments (`x = val;`) rather than variable re-declarations (`ZenValue x = val;`)
  - Codegen statements: `break;` and `continue;` emit genuine C loop jump statements; `emit_when_cases` uses nested `else { if (...) }` blocks ensuring condition temporaries are evaluated in-scope; `.kind` property maps to `ZenValue_get_kind(obj)`
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
  - Typecheck under multi still uses merged program
  - Codegen fail = empty / `/* parse error` prefix only
  - CLink: find gcc/clang/tcc (`ZEN_CC` override); `-O2` default (`ZEN_OPT=0|1|2|3|s`); `-I runtime/` (no per-build copy); cache `output/selfhost_rt/bootstrap_runtime.o`; link out.c + that .o
  - `lsp` is not linked into zen-selfhost; hybrid `./bin/zen lsp` runs `tools/zenlsp.zl`
  - Interpreter: map env (`outer`); int literal coerce; return via module flags; `when x is [a,b]` / map / `Enum.Var(x)` binds; real `io.*`/`output.*` builtins dispatch; `eval_while` handles `K_DO_WHILE` (`AST.do_while_body`/`AST.do_while_cond`); `eval_expr` supports `K_BLOCK` and `K_WHEN` expressions.
  - Driver CLI: `interpret`/`eval`/`vm`/`test`/`--test` are tokens in `is_cli_token` (must not skip as argv0); native `zen-selfhost test` discovers/executes `test_*` functions; `vm` executes via bytecode compiler and stack VM engine without C compilation.
  - **A1 import graph:** `interpret_file` uses GraphBuilder compilation order; `import path as Alias` binds a map of exported free fns + module lets + classes/enums (skip `main`)
  - **A2:** `do for` / lists / maps / IndexAssign / `.length`; list append + index write-back for `-g`
  - **A3:** `__builtin_string` (and file/io stubs) so `import zen.text.string as Str` works; STRING literals are not coerced to ints
  - Parser: `let` is mutable, `set` is constant (`v == 'let'`); `let x :> expr` parses initializer; `Codegen` uses positional `AST.*` accessors for `K_ASSERT`, `K_ASSIGN`, `K_INDEX_ASSIGN`, `K_SET`, and `K_CHECK_STMT`.
  - **Phase L:** `Default` sentinel materializes from a TypeAnn (`Integer`→0, `Boolean`→False, `String`→``, `List`→[]); `== Default` compares to that zero; `Nothing` is distinct. Lexer accepts lowercase aliases.
  - **Phase D:** classes/`extends`/`self`/`parent.meth`; closures by-value snapshot; enums + payload `is`; `with` + software MEM arena; `__builtin_memory` / real standard output. Guest `.length` must not hit `.has` on lists; never `Str.to_string` cyclic env maps (native overflow).
- **Interpreter.zl** — endgame Phase A+D+E AST walk; tests: `test_interpreter.zl` (22 dual-path)
- **Bytecode.zl & Mixed ABI:** `compile_program`, `eval_chunk`, `eval_chunk_fn`, `invoke_callable` — compiles AST directly to compact bytecode chunks for fast evaluation without GCC. `OP_CALL` dispatches seamlessly between bytecode chunks, native Zen functions, closures with captured environments, and host APIs. Tests: `test_vm.zl` (7 dual-path), `test_mixed_abi.zl` (6 dual-path).
- **Stage 7:** Native + E2E + namespaced self-rebuild.
  - `selfhost-smoke` → fixtures + class + enum/closure/with + native interpret + multi-unit; self-rebuild of `selfhost/zen.zl` (`ZEN_SELFHOST_REBUILD=1`) is 100% green (native selfhost parses and emits selfhost compiler to C, gcc links secondary binary `zen_from_self`, which executes help and compiles fixtures to working binaries with zero Python involvement).
  - Codegen file emit: `transpile_program_to_file` / `CG.out_path` streams chunks; `do`/`while` → `while (1)` + `break` so emit_expr temps stay in scope
  - **STRING/RUNE token_kind** stay C strings (`emit_literal_node`); `looks_int("0")` is true and would turn `` `0` `` into `ZenValue_make_integer(0LL)`
  - Lexer `_is_digit` uses `Str.contains(`0123456789`)` (not `` `0` ``/`` `9` `` range) so the self-built lexer still tokenizes integers
  - Driver merge uses `drv_list_push` (capture `.append` return)
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
- **Compiler IR:** Token and AST representations are native positional structs `[kind, ...]` with zero string dictionary overhead ([THREE_LAYER.md](../THREE_LAYER.md) Phase 1 Steps 1 & 2 complete).
- **Bytecode Compiler & Evaluator:** `Bytecode.zl` — Three-Layer Phase 3 bytecode emitter (`compile_program`, `eval_chunk`, `eval_chunk_fn`). Compiles positional AST structs to bytecode chunks targeting the C runtime VM (`zen_vm.c`) or in-memory evaluator; tested in `tests/self_hosting/test_vm.zl` under dual execution (interpreter & native `-g`).
- Memory: default automatic via runtime; opt-in `with`/arena → Codegen push/pop; checker scopes with-alias (ownership rules later).
- Production handoff: hybrid via `install` (selfhost compile/run/interpret/test; bare `.zl` still bootstrap). Soak: `./scripts/zen ci-soak`. Emergency: `./scripts/zen install-rollback`.

# Work Guidance

- Prefer free functions + maps under `-g`.
- Unique names across modules when co-linked (`cg_walk_stmts` vs TypeChecker `walk_stmts`).
- Mutators return updated maps; callers rebind.
- Capture lengths before `do for`; prefer index recursion for multi-pass.
- Codegen: stream to `out_path` when compiling to a file; in-memory join is pairwise (`join_parts_tree`); ints via `Str.to_string`. STRING/RUNE use `emit_literal_node` (never `looks_int` on backtick digits).
- **Always emit IndexAssign** (`obj[k] -> v` → `ZenValue_set_at`) — required for module maps.
- **Multi-file namespacing:** `Driver.module_fn_prefix` + `append_file_stmts` rewrite; Codegen `Module.fn` → `z_Module_fn`. Fixtures not namespaced.
- Lexer escapes: `escape_piece(esc)`; `_ch_nl`/`_ch_tab` real chars (not `\n` string literals).
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
for t in test_lexer test_parser test_module test_checker test_codegen test_driver test_interpreter; do
  python3 bootstrap/Zen.py tests/self_hosting/${t}.zl
  python3 bootstrap/Zen.py -g tests/self_hosting/${t}.zl
done
python3 bootstrap/Zen.py selfhost/zen.zl help
python3 bootstrap/Zen.py selfhost/zen.zl interpret tests/self_hosting/fixtures/stage7_add.zl
./scripts/zen install-selfhost
./scripts/zen selfhost-smoke
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
- Bytecode.zl — Three-Layer Phase 3 bytecode compiler & VM chunk evaluator
- Driver.zl, main.zl — Stage 6/7+ CLI; ../zen.zl entry
- Builder.zl, host_main.c — legacy
