# Zenlang Tooling

## zen

- Compiler
- REPL
- Interpreter
- Virtual Machine?
- Package Manager
- Build System (Implemented)
    - `.zbuild` project files
    - `zen --build` command
- Source Mapping (Implemented)
    - `#line` directive support for C debugging
    - `zen --source-map` flag

## Test Runner

The Zenlang Test Runner discovery and execution system.

### Usage

To run tests in a source file:
```bash
zen <source_file> --test
```

### Test Discovery

The runner discovers tests in two ways:

1.  **Test Functions**: Any function starting with `test_` (e.g., `function test_addition()`).
2.  **Doctests**: Any code block within a documentation comment (`/! ... !/`) that starts with `@example`.

### Assertion Syntax

While you can use the `zen.test` library, Zenlang also supports native assertions using the `!` operator:

```zenlang
function test_math() {
    ! 1 + 1 == 2
}
```

```zenlang
/!
 Adds two values.
 @example
   ! add(1, 2) == 3
 !/
function add(a, b) { <- a + b }
```

## Source Mapping

The Zenlang compiler supports C source mapping via `#line` directives. This allows C debuggers (like GDB) and C compiler error reports to point directly back to the original Zenlang source files.

### Usage

Source mapping is enabled by default. To explicitly control it:

```bash
zen <source_file> --generate --source-map    # Enable (default)
zen <source_file> --generate --no-source-map # Disable
```

## Build System

The Build System allows managing Zenlang projects via a `.zbuild` configuration file.

### .zbuild File Format

Create a `.zbuild` file in your project root:

```zenlang
name: "MyProject"
entry: "src/main.zl"
output: "bin/main"
source_map: "true"
```

### Usage

To build a project:

```bash
zen --build
```

The build system will automatically find the `.zbuild` file in the current directory, resolve the entry point, and generate/compile the C output.

## Core

- Runtime
- Standard Library

## Standard Library (nested packages)

See [Standard_Library_Reference.md](Standard_Library_Reference.md) for the full import map.

- **zen.io.io** — write/read, info/warn/error/debug  
- **zen.io.file** / **zen.io.path** — files, `walk` / `list_files`, path join  
- **zen.sys.sys** / **zen.sys.process** / **zen.sys.term** / **zen.sys.cli** — system, shell, TUI keys  
- **zen.text.string** / **zen.text.text** — strings and semantic text  
- **zen.math.math** / **zen.math.random** / **zen.math.range**  
- **zen.collections.list** (and set/stack/queue)  
- **zen.data.json** (and csv, xml, …)  
- **zen.test**, **zen.time**, **zen.log**, **zen.memory**, **zen.error**  
- **zen.ui.***, **zen.geometry.***, **zen.net.***, **zen.graphics.***

## Extended

- GUI
