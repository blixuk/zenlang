# Zenlang Tooling & Developer Ecosystem

Zenlang provides a unified, Unix-native developer ecosystem covering compilation, interpretation, automated testing, documentation generation, syntax formatting, and editor language servers.

---

## 1. The Zen Command-Line Interface (`zen`)

The `zen` command (`bin/zen` or `bin/zen-selfhost`) is the primary interface for running, compiling, testing, and checking Zenlang applications.

### Core CLI Commands

```bash
# 1. Compile to Native C
zen compile path/to/file.zl output/out.c
zen compile path/to/file.zl output/out.c --typecheck

# 2. Build Standalone Machine Binary (CLink)
zen build path/to/file.zl -o bin/app
zen build path/to/file.zl -o bin/app -O3

# 3. Direct Native Execution (Build + Link + Run)
zen run path/to/file.zl -- arg1 arg2

# 4. Instantaneous Script Interpretation
zen interpret path/to/file.zl
zen path/to/file.zl

# 5. Typecheck with Caret Diagnostics
zen check path/to/file.zl

# 6. Dependency Graph Inspection
zen deps path/to/file.zl

# 7. Automated Test Discovery & Execution
zen test path/to/file.zl
```

---

## 2. Compiler Diagnostics & Caret Reporting

Zenlang features Rust/Clang-style source-mapped diagnostic reporting built on zero-copy 7-tuple token spans (`[kind, start, length, line, col, end_line, end_col]`):

```
check failed:
error: Return type mismatch: expected Integer got String
  --> src/main.zl:14:5
  |
14 |     <- result
  |     ^
```

---

## 3. Tooling Ecosystem

### `zenmark` — Technical Document Compiler
Compiles Zen Mark (`.zm`) structured documents into native vector PDFs and interactive HTML previews:
```bash
zen tools/build_spec.zl
```

### `zendoc` — API Documentation Generator
Extracts doc-comments (`/! ... !/`) from `.zl` files and generates structured API reference manuals in markdown or Zen Mark:
```bash
zen tools/zendoc.zl lib/zen -o doc/api
```

### `zenfmt` — Automated Code Formatter
Enforces the canonical [Zenlang Style Guide](Style_Guide.md) across single files or whole projects:
```bash
zen tools/zenfmt.zl src/
```

### `zenlsp` — Language Server Protocol Daemon
Provides code completion, hover documentation, syntax highlighting, and live diagnostic squiggles for modern editors:
- **VS Code / Cursor:** Extensions under `editors/vscode/`
- **Zed:** Language configuration in `editors/zed/`
- **Sublime Text:** Package in `editors/sublime/`
- **Tree-sitter:** High-speed incremental parser grammar in `editors/tree-sitter/`

```bash
zen tools/zenlsp.zl --stdio
```

---

## 4. Repository Verification Ladder (`scripts/zen`)

For language contributors and local validation, `./scripts/zen` runs comprehensive verification suites without remote CI dependencies:

```bash
./scripts/zen install         # Builds and installs bin/zen router
./scripts/zen install-selfhost# Installs standalone native compiler
./scripts/zen test-core       # Runs core interpreter and compiler tests
./scripts/zen test-parity     # Verifies dual-execution interpreter ↔ native parity
./scripts/zen test-lib        # Runs full standard library test suite
./scripts/zen test-lib-native # Runs standard library under native AOT compilation
./scripts/zen selfhost-smoke  # 56-test native compiler self-rebuild smoke test
./scripts/zen ci              # Fast local smoke suite
./scripts/zen ci-soak         # Full local soak gate (smoke + hybrid + golden)
```
