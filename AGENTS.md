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
- tools/: Extra tools (zendoc, …)
- zenshell/: Standalone modern shell unifying the Zen Trinity (.zl, .zd, .zm) — zenshell/AGENTS.md

Transient: `build/`, `bin/`, `output/`, `tmp/`, logs — never hand-edited.
