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
- **Type Casting (`<:` and `Type(val)`):** Dual syntax: visual operator `<:` (`val <: Integer`) and constructor syntax `Type(val)` (`Integer(val)`). Supported across base types (`Integer`, `Decimal`, `String`, `Boolean`), aliases (`Int`, `Str`, `Float`, `Bool`), character/binary types (`Rune`/`Char`, `Bytes`/`Buffer`), collections (`List`, `Set`, `Map`), and `Nothing`. Implemented with full parity across runtime (`ZenValue_cast`), AST/Parser, C Codegen, Bytecode VM (`OP_CAST`), and Interpreter.
- **Native Console I/O & Ambient Streams:** Native built-in console I/O replaces imported wrappers. `stdout`, `stderr`, `stdin` are ambient stream instances with member methods (`write`, `writeln`, `flush`, `read`, `readln`, `lines`). Universal built-in preludes `write(...)`, `writeln(...)`, `read(...)`, `readln(...)` are available without import. Replaces `print`/`println`.
- **Dynamic Program Arguments:** Dynamic arity binding allows entry functions to declare `function main(args)` to receive CLI arguments directly, while preserving `function main()` for zero-parameter entry points. Top-level scripts also have ambient access to `args` (list of strings) and `env` (map of environment variables). Full parity across C runtime (`z_stdout`, `z_stderr`, `z_stdin`, `z_args`, `z_env`), selfhost C Codegen, selfhost Bytecode VM, selfhost Interpreter, and Python bootstrap.
- **Binary in Membership Operator:** First-class binary operator `in` evaluates containment across collections and sequences (`val in list`, `key in map`, `item in set`, `needle in string`, `x in range`). Implemented with full parity across C runtime (`ZenValue_in`), selfhost Parser/Codegen, Bytecode VM (`OP_IN`), selfhost Interpreter, and Python bootstrap.

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
- doc/: Documentation and specification — doc/AGENTS.md
- tests/: Test suite — tests/AGENTS.md
- scripts/: Host scripts including `scripts/zen` — scripts/AGENTS.md
- editors/: Editor integrations (VS Code/Cursor, Zed, Sublime, Tree-sitter) — editors/AGENTS.md
- archive/: Historical reference only — archive/README.md (no full DOX tree required)
- examples/: Illustrative demos (owned at root until independent contracts appear); learner ladder in examples/getting_started/ (see doc/Getting_Started.md)
- tools/: Extra tools (zendoc, …)

Transient: `build/`, `bin/`, `output/`, `tmp/`, logs — never hand-edited.
