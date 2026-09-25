# Zenlang

Unix-native programming language for scripts, terminal apps, and networked services.

- Visual data flow: `->` (bind), `<-` (return), `|>` (pipeline), `??` (coalesce)
- Explicit over magic; terminal-first
- Modern ergonomics: directional comprehensions (`[for x in list -> x*2]`), collection spreads (`[...items]`), and direct C header imports (`extern use '<header.h>'`)
- Dual execution: **interpret** scripts or **AOT to C** binaries; mix on one value ABI ([three-layer](selfhost/THREE_LAYER.md))
- Stage 2 self-hosting closure in standalone `bin/zen` single-binary platform (`v1.0.0-beta.1`)

## Quick start

**The Language Specification (Single Source of Truth):** [doc/SPECIFICATION.md](doc/SPECIFICATION.md) — canonical specification for syntax, grammar, types, operators, and semantics.  
**Documentation Standards:** [doc/DOCUMENTATION_STANDARDS.md](doc/DOCUMENTATION_STANDARDS.md) — formatting rules and documentation governance.  
**Feature Proposals & RFCs:** [doc/proposals/README.md](doc/proposals/README.md) — formal review process for language evolution.  
**The Official Book:** [doc/book/README.md](doc/book/README.md) — *The Zen of Programming: A Practical Guide to Zenlang*.  
**Tutorial & On-Ramp:** [doc/Getting_Started.md](doc/Getting_Started.md) — hands-on language tour and patterns.  
**Standard Library Reference:** [doc/Standard_Library_Reference.md](doc/Standard_Library_Reference.md) — standard library package index.

```bash
# Host-1.0 daily CLI (selfhost primary, bootstrap fallback)
./scripts/zen install

# Hello (bare .zl → bootstrap interpret)
./bin/zen tests/hello.zl

# Native path: try selfhost, then bootstrap
./bin/zen -g tests/hello.zl

# Selfhost compiler
./bin/zen compile tests/hello.zl /tmp/hello.c
./bin/zen run tests/hello.zl

# Typecheck only
./bin/zen --check examples/zedit.zl

# Emergency: bin/zen → Python bootstrap
./scripts/zen install-rollback
```

### Interactive Stateful REPL (`zen repl`)

```bash
./scripts/zen repl
```

Interactive development shell with persistent session state, automatic `_` and `_N` result history, state snapshotting (`:save` / `:load` with Zen Data `.zd`), multi-line block entry, live syntax highlighting, and tab completion. Guide: [doc/REPL.zm](doc/REPL.zm).

### Interactive Playground & Code Lab

```bash
./scripts/zen playground
# or load an existing script:
./scripts/zen playground examples/getting_started/01_hello.zl
```

Keys: **Ctrl+R** run · **Ctrl+P** templates · **Ctrl+E** backend (interpret / native `-g` / selfhost) · **Ctrl+T** split · **Ctrl+S** save · **Ctrl+Q** quit. Guide: [doc/Playground.md](doc/Playground.md).

### Interactive Terminal File Manager (`zenfm`)

```bash
./scripts/zen fm [path]
```

Split-pane file navigation, icons, live syntax preview, and instant <kbd>P</kbd> launch into the Playground. Guide: [doc/FileManager.md](doc/FileManager.md).

### Code Formatter (`zenfmt`)

```bash
./scripts/zen fmt -w src/     # Format files in-place
./scripts/zen fmt --check src/  # Verify formatting in CI
```

Canonical style and indentation formatter. Guide: [doc/Formatter.md](doc/Formatter.md) · Style Guide: [doc/Style_Guide.md](doc/Style_Guide.md).

### Nano-like editor demo

```bash
./bin/zen examples/zedit.zl notes.txt
# or
./bin/zen -g examples/zedit.zl notes.txt
```

Keys: arrows · type · Enter · Backspace · **Ctrl+S** save · **Ctrl+Q** quit

### Getting started (tutorial programs)

```bash
./bin/zen examples/getting_started/01_hello.zl
./bin/zen examples/getting_started/10_count_lines.zl README.md
# Full ladder + notes: examples/getting_started/README.md
# Guide: doc/Getting_Started.md
```

### Unix cookbook (bash replacements + visual tools)

```bash
# Visual cat (line numbers + gutter)
./bin/zen examples/zcat.zl README.md

# Colorful directory tree
./bin/zen examples/ztree.zl lib/zen

# Find files by name (like find … -name '*pat*')
./bin/zen examples/zfind.zl lib/zen term

# Recursive content search (like grep -rn)
./bin/zen examples/zgrep.zl walk lib/zen/io

# Visual word/line/byte counts
./bin/zen examples/zwc.zl README.md tests/hello.zl

# Full-screen pager (q to quit)
./bin/zen examples/zless.zl README.md

# Tiny nano-like editor
./bin/zen examples/zedit.zl notes.txt

# Shell-scripting patterns (process/pipelines)
./bin/zen examples/shell_script.zl
```

| Example | Replaces / similar to |
|---------|------------------------|
| `zcat.zl` | `cat -n` with color |
| `ztree.zl` | `tree` |
| `zfind.zl` | `find` (name substring) |
| `zgrep.zl` | `grep -rn` (literal) |
| `zwc.zl` | `wc` with relative bars |
| `zless.zl` | `less` (pager keys) |
| `zedit.zl` | tiny `nano` |
| `shell_script.zl` | bash pipelines / `$?` / env |

## Project layout

| Path | Role |
|------|------|
| **`bootstrap/`** | Authoritative compiler today (Python): lex → parse → check → interpret / C transpile |
| **`selfhost/`** | Self-hosted compiler sources (Zenlang) — long-term replacement for bootstrap |
| **`runtime/`** | Shared C runtime for native binaries (used by `-g` and self-host) |
| **`lib/zen/`** | Standard library (**nested packages only**, e.g. `zen.sys.term`, `zen.io.file`) — [import map](doc/Standard_Library_Reference.md) |
| **`tests/`** | Language, stdlib, compiler, memory, parity tests |
| **`examples/`** | Demos (zedit, shell scripts, dashboards, …) |
| **`doc/`** | Manifesto, Explained, formal Typst spec, references |
| **`scripts/`** | Host tooling (`scripts/zen`, test runners) |
| **`editors/`** | VS Code / Cursor, Zed, Sublime, Tree-sitter — see [editors/README.md](editors/README.md) |
| **`tools/`** | Extra tools (e.g. zendoc) |
| **`archive/`** | Historical / experimental material (not daily path) |

Generated / local only (gitignored): `bin/`, `build/`, `output/`, `tmp/`, `*.log`.

## Developer CLI

Make is **not** the long-term build system. Use:

```bash
./scripts/zen help
./scripts/zen repl        # interactive stateful REPL
./scripts/zen install     # hybrid bin/zen (selfhost primary)
./scripts/zen test-core   # core language ladder
./scripts/zen test-parity # interpret vs -g
./scripts/zen test-lib    # stdlib (interpreter)
./scripts/zen test        # all of the above + native lib smoke
./scripts/zen ci          # faster local smoke
./scripts/zen ci-soak     # local handoff-soak + golden
./scripts/zen clean
```

A thin `Makefile` still forwards to `scripts/zen` for muscle memory. Historical rules live in `archive/Makefile.legacy`.

## Ecosystem direction

Zen is growing its own toolchain (not a Make/Cargo clone forever):

- **Build** — `.zbuild` + future self-hosted builder
- **Test runner** — `zen --test` / `test_*` (bootstrap already supports this)
- **Package manager** — planned
- **Docs** — `tools/zendoc.zl` and Spec sources under `doc/Specification/`

Until those land, **`bootstrap/Zen.py`** is the source of truth.

## Documentation

| Doc | Contents |
|-----|----------|
| [doc/Zen Manifesto.md](doc/Zen%20Manifesto.md) | Philosophy |
| [doc/Zenlang Explained.md](doc/Zenlang%20Explained.md) | Language tour |
| [doc/Standard_Library_Reference.md](doc/Standard_Library_Reference.md) | Stdlib API |
| [doc/Specification/](doc/Specification/) | Formal Typst spec |
| [Testing.md](Testing.md) | Test ladder |
| [AGENTS.md](AGENTS.md) | Project contracts (for humans and agents) |

## Status

- **Daily path:** `./scripts/zen install` installs hybrid `bin/zen` (selfhost compiler CLI + bootstrap for bare `.zl`). Stdlib and examples (including zedit) work.
- **Self-host:** `selfhost/` compiler CLI. Local gate: `./scripts/zen handoff-soak` / `./scripts/zen ci-soak`. Self-rebuild of `zen.zl` stays `ZEN_SELFHOST_REBUILD=1`.
- **Runtime:** one tree at `runtime/`; `bootstrap/Transpiler/runtime` links there.

## License / contributing

See repository policy and `AGENTS.md` for contribution contracts. Prefer small, tested changes; run `./scripts/zen test-core` before larger work.
