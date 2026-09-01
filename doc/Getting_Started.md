# Getting Started with Zenlang

A practical tutorial for writing Zenlang programs: how the language works, the features you will use day to day, how to run them, and design patterns that fit Zen’s philosophy.

| Document | Role |
|----------|------|
| **This guide** | Tutorial + patterns (start here) |
| [book/README.md](book/README.md) | **The Zen of Programming** (the complete official book) |
| [REPL.zm](REPL.zm) | **Interactive Stateful REPL** (`zen repl` live shell guide) |
| [Style_Guide.md](Style_Guide.md) | **Zenlang Style Guide** (syntax standards & conventions) |
| [Playground.md](Playground.md) | **Interactive Playground** (live code lab & dual runner) |
| [FileManager.md](FileManager.md) | **Terminal File Manager** (`zenfm` split-pane explorer) |
| [Formatter.md](Formatter.md) | **Code Formatter** (`zenfmt` automated style formatting) |
| [Language_Module_and_Reflect.md](Language_Module_and_Reflect.md) | **`module`, entry, `use`, reflect, plugins** (full language reference) |
| [README.md](../README.md) | Install, CLI, examples map |
| [Zen Manifesto.md](Zen%20Manifesto.md) | Why Zen exists |
| [Zenlang Explained.md](Zenlang%20Explained.md) | Deeper language reference |
| [Standard_Library_Reference.md](Standard_Library_Reference.md) | Import map + stdlib API |
| [Zenlang Tooling.md](Zenlang%20Tooling.md) | Compiler / tools |
| [editors/README.md](../editors/README.md) | VS Code / Cursor, Zed, Sublime |
| `doc/Specification/` | Formal Typst spec → PDF |

Examples in this guide match **Host-1.0**: `./scripts/zen install` then `./bin/zen`. Prefer nested imports (`use zen.io`, `use zen.text.string as Str`). Python `bootstrap/` is the in-tree **maintenance fallback**, not the daily front door.

### Runnable companion

Step-through programs live in **[`examples/getting_started/`](../examples/getting_started/)**:

```bash
./scripts/zen install
./bin/zen examples/getting_started/01_hello.zl
# … through 12_patterns.zl — see that directory’s README
```

| Files | Focus |
|-------|--------|
| `01`–`04` | Hello, variables, control flow, functions |
| `05`–`08` | Collections, strings, structures, closures |
| `09`–`11` | CLI args, file tool, process/shell |
| `12` | Design patterns (result maps, rebind, index loops) |

---

## 1. What Zenlang is

Zenlang is a **Unix-native** language for:

- Scripts and glue tools
- Terminal UIs and CLI apps
- Small networked services

It is designed around:

| Principle | In practice |
|-----------|-------------|
| **Visual data flow** | `->` binds values; `<-` returns them |
| **Explicit over magic** | Few hidden coercions; control flow is written out |
| **Terminal-first** | `zen.sys.term`, examples like `zedit`, `zcat`, `zless` |
| **Composition** | Small programs + stdlib + processes/pipes |
| **Dual execution** | Same source: **interpret** or **transpile to C** and run natively |

It is **not** trying to replace the shell or C wholesale. It extends Unix: write reliable tools in one language, call out to the OS when that is simpler.

---

## 2. Install and run (5 minutes)

### Requirements

- Linux or macOS-like environment
- `python3`
- A C compiler (`gcc` or `clang`) for the native (`-g`) path

### Install the daily CLI

From the repo root:

```bash
./scripts/zen install
export PATH="$PWD/bin:$PATH"   # optional
```

This is the **Host-1.0** install:

| Binary | Role |
|--------|------|
| `bin/zen` | Daily CLI: compile/build/run/interpret/test/check/deps/help → native selfhost; bare `.zl` and `--check` → bootstrap |
| `bin/zen-selfhost` | Native selfhost compiler only |
| `bin/zen-bootstrap` | Full Python language host (maintenance fallback) |

### Hello

```bash
./bin/zen tests/hello.zl
```

Bare `.zl` files still interpret on the bootstrap host (full language). Compiler commands (`compile`, `run`, `interpret`, `-g`) prefer selfhost.

### Two ways to run any program

```bash
# Interpret (fast edit loop) — bare file uses bootstrap
./bin/zen path/to/program.zl [args...]

# Native: try selfhost, then bootstrap
./bin/zen -g path/to/program.zl [args...]

# Typecheck only (bootstrap --check)
./bin/zen --check path/to/program.zl

# Selfhost compiler CLI
./bin/zen compile path/to/program.zl out.c
./bin/zen run path/to/program.zl
```

| Mode | Use when |
|------|----------|
| **Interpret** (default bare `.zl`) | Learning, scripts, tests, quick iteration |
| **`-g` / `run` native** | Performance, shipping a tool, parity checks |
| **`--check`** | Typecheck without running |

**Rule of thumb:** develop with interpret; prove important tools with `-g` (`./scripts/zen test-parity` for core language). Local soak: `./scripts/zen ci-soak`.

### Emergency rollback (bootstrap as `bin/zen`)

`bootstrap/` stays in the tree. To put the Python host back on `bin/zen` without deleting selfhost:

```bash
./scripts/zen install-rollback
# or, with hybrid still installed:
ZEN_FORCE_BOOTSTRAP=1 ./bin/zen path/to/program.zl
```

Restore Host-1.0: `./scripts/zen install`.

### Your first file

Create `hello.zl`:

```zl
import zen.io.io as io

function main() {
    io.writeln(`Hello, Zenlang!`)
    <- 0
}
```

```bash
./bin/zen hello.zl
./bin/zen -g hello.zl
```

- Entry point is `function main()`.
- Exit code: return an integer from `main` (`<- 0` success, non-zero failure).
- Strings use **backticks**: `` `text` `` (not double quotes).

---

## 3. How Zen works (mental model)

```text
  your.zl
     │
     ▼
 ┌─────────┐   tokenize / parse / check
 │bootstrap│   (Python today; selfhost/ later)
 └────┬────┘
      │
      ├── interpret ──► run AST on host (Python)
      │
      └── -g ──► emit C ──► link runtime/ ──► native binary ──► run
```

- **Same syntax and stdlib** in both modes. Prefer writing code that stays dual-path green.
- **Runtime** (`runtime/`) backs native builds with boxed values, lists, maps, strings, IO, etc.
- **Stdlib** lives under `lib/zen/` as nested packages (`zen.io.file`, `zen.sys.process`, …).
- **`ZEN_PATH`** tells the resolver where to find modules (repo root, `selfhost/`, `lib/` — set by `scripts/zen`).

You rarely need to think about the C step unless you are debugging native failures: look under `output/build/` after a `-g` run.

---

## 4. Language tour

### 4.1 Visual data flow: `->` and `<-`

```zl
let name -> `Ada`          // bind
name -> `Grace`            // rebind mutable let

function double(x) {
    <- x * 2               // return (preferred style)
}
```

| Operator | Meaning |
|----------|---------|
| `->` | “Data flows into this name / field” (assignment / init) |
| `<-` | “Data flows out of this function” (return) |

Some older tests also use `return`; new code should prefer `<-`.

### 4.2 Variables: `let`, `set`, types

```zl
let x -> 10                    // mutable, type inferred
set PI : Decimal -> 3.14       // immutable constant
let name :> `Zen`              // infer and lock type (:>)

let count : Integer -> 0       // optional explicit type
let maybe -> nothing           // no value
```

- **`let`** — rebind with `name -> new_value`.
- **`set`** — constant; do not reassign.
- **`nothing`** — explicit empty (not silent null everywhere).

### 4.3 Literals and operators

```zl
// Booleans
let ok -> True
let no -> False
! not no                    // assert in tests; also logical not

// Numbers and compare
let n -> 42
let d -> 3.14
let eq -> n == 42
let lt -> n < 100

// Logic (words, not && / ||)
when ok and n > 0 {
    // ...
}
when no or n == 0 {
    // ...
}

// Strings (backticks) and concatenation
let msg -> `count=` + /* string of n via stdlib */ `42`
```

Prefer **`and` / `or` / `not`** over C-style `&&` / `||`.

### 4.4 Strings and text

```zl
import zen.text.string as Str
import zen.io.io as io

function main() {
    let s -> `  hello, world  `
    io.writeln(Str.trim(s))
    io.writeln(Str.to_string(123))
    let parts -> Str.split(`a,b,c`, `,`)
    io.writeln(Str.join(parts, ` | `))
    <- 0
}
```

- Use **`Str.*` free functions** from `zen.text.string` for dual-path reliability.
- Semantic text types (Word, Sentence, …) exist in the design; day-to-day tools mostly use `String` + `Str`.

### 4.5 Collections

```zl
// Lists
let xs -> [1, 2, 3]
let n -> xs.length
let first -> xs[0]

// Maps (records / dicts)
let person -> {
    `name` -> `Ada`,
    `year` -> 1815
}
let name -> person[`name`]
person[`year`] -> 1816
```

Maps double as **lightweight records** (very common in tools and in the selfhost compiler).

Ranges build lists of integers or characters:

```zl
let a -> 0..5       // [0,1,2,3,4]  half-open
let b -> 0..=5      // [0..5] inclusive
let letters -> `a`..=`c`   // [`a`,`b`,`c`]
```

### 4.6 Control flow: `when` and loops

There is no C-style `if`. Use **`when` / `or when` / `or`**:

```zl
function grade(score) {
    when score >= 90 {
        <- `A`
    } or when score >= 80 {
        <- `B`
    } or {
        <- `C`
    }
}

// Loops
let i -> 0
let sum -> 0
do while i < 5 {
    sum -> sum + i
    i -> i + 1
}

do for x in [10, 20, 30] {
    // use x
}
```

Also supported: `do { ... } while condition`.

**Dual-path tip:** under native (`-g`), `for-in` can **consume** a list. If you need the list again, capture `.length` and index, or rebuild. Prefer:

```zl
let n -> xs.length
let i -> 0
do while i < n {
    let x -> xs[i]
    // ...
    i -> i + 1
}
```

### 4.7 Functions and closures

```zl
function add(a, b) {
    <- a + b
}

// Optional types on params / return (when you want them)
function fib(n: Integer) : Integer {
    when n <= 1 {
        <- n
    }
    <- fib(n - 1) + fib(n - 2)
}

// Anonymous functions (lambdas)
let double -> function(x) { <- x * 2 }
let y -> double(21)    // 42
```

**Closures capture outer locals by value** (snapshot at creation):

```zl
let n -> 10
let add_n -> function(x) { <- x + n }
n -> 99
// add_n(5) is still 15 — capture does not see later rebinds
```

### 4.8 Structures

```zl
structure Point {
    x: Integer
    y: Integer
}

function main() {
    let p -> Point { x -> 10, y -> 20 }
    p.x -> 30
    <- 0
}
```

Use structures when the shape is stable and shared. Use **maps** for ad-hoc JSON-like data and internal compiler/tool state.

### 4.8b Built-in `module` context

Every file has a map-like **`module`** binding (no import needed):

| Field | Meaning |
|-------|---------|
| `module.name` | Short name (file stem or last import segment) |
| `module.path` | Logical path (import path or entry name) |
| `module.file` | Absolute source path |
| `module.dir` | Directory of that file |
| `module.is_entry` | `True` only for the process entry file |

```zl
use zen.io

when module.is_entry {
    io.writeln(`running ` + module.file)
}

function main() {
    io.writeln(module.name)
    <- 0
}
```

Libraries keep helpers at top level; wrap script-only work in `when module.is_entry { … }` or use `main()`.

**Custom entry (no decorators):** set `module.entry` to a function name or function value to bypass `main` (useful for tests/alternate CLI):

```zl
function run() {
    io.writeln(`custom entry`)
    <- 0
}
function main() {
    io.writeln(`default entry`)
    <- 0
}
module.entry -> `run`    // or: module.entry -> run
```

### 4.8c Reflection (`zen.reflect`)

```zl
use zen.reflect as reflect

let m -> { `a` -> 1 }
reflect.is_map(m)           // true
reflect.type_name(1)        // Integer
reflect.fields(m)           // list of keys
reflect.field(m, `a`)       // 1
m -> reflect.set_field(m, `b`, 2)
m.keys()                    // also m.values(), m.items() → {key,value} pairs

// Dynamic call (plugin maps)
let cmds -> { `hi` -> function(n) { <- n } }
reflect.call(cmds, `hi`, [`zen`])
```

Plugins helper: `use zen.plugins as P` — `P.create()`, `P.add`, `P.dispatch` (see `examples/plugins_demo.zl`).

Opt-in rich metadata:

```zl
structure Point is reflectable {
    x: Integer
    y: Integer
}
class Counter is reflectable {
    let n: Integer
    function bump() { self.n -> self.n + 1 }
}
```

Then `reflect.fields(p)`, `reflect.methods(c)`, `reflect.is_reflectable(x)`. Maps are always field-introspectable without the marker.

### 4.9 Modules and imports

`use` is an **alias for `import`** (preferred for new code; `import` still works until a full migration).

```zl
use zen.io                         // package entry lib/zen/io/io.zl → binds `io`
use zen.io.file                    // binds `file` (optional `as`)
use zen.text.string as Str         // rename when you want a shorter name
from zen.io use writeln            // selective
from zen.io use writeln as wl
```

| Style | Example |
|-------|---------|
| **Preferred** | `use zen.io` / `use zen.io.file` |
| Still valid | `import zen.io as io` |
| Package short | `use zen.time` → `lib/zen/time/time.zl` |
| Avoid for new code | `import zen.io.io as io` (redundant double name) |
| Avoid | Flat legacy paths like `` import `lib/zen/io` `` |

Default binding without `as` is the **last path segment** (`zen.io` → `io`).

See [Standard_Library_Reference.md](Standard_Library_Reference.md) for the full import map.

**Full write-up** of `module`, entry points, reflection, and plugins:  
→ **[Language_Module_and_Reflect.md](Language_Module_and_Reflect.md)**

### 4.10 Errors

Prefer **explicit checks** and `when` over hidden exceptions. One available pattern:

```zl
import zen.io.io as io

function divide(a, b) {
    when b == 0 {
        <- __builtin.error(`Division by zero`)
    }
    <- a / b
}

function main() {
    let r -> check divide(10, 0) or {
        io.writeln(`handled divide-by-zero`)
        0
    }
    io.writeln(`result=` /* ... */)
    <- 0
}
```

For CLI tools, returning non-zero from `main` and printing to stderr is often enough:

```zl
when not file.exists(path) {
    io.writeln(`not found: ` + path)
    <- 1
}
```

### 4.11 Assertions and tests

In language tests, **`! condition`** asserts (fails the run if false):

```zl
function test_math() {
    ! 2 + 2 == 4
}

function main() {
    test_math()
}
```

Stdlib-style suites use `zen.test`:

```zl
import zen.test as test

function test_add() {
    <- test.assert_equal(1 + 1, 2, `one plus one`)
}

function main() {
    // or: zen --test file.zl for test_* discovery where supported
    when test_add() { <- 0 } or { <- 1 }
}
```

Run core language checks:

```bash
./scripts/zen test-core
./scripts/zen test-lib
```

### 4.12 Processes and the shell (composition)

Zen is happy to call Unix:

```zl
import zen.sys.process as process
import zen.io.io as io
import zen.text.string as Str

function main() {
    let listing -> process.shell(`ls -la | head -5`)
    io.write(listing)

    when process.ok(`test -d lib/zen`) {
        io.writeln(`lib/zen exists`)
    }

    let uname -> Str.trim(process.require(`uname -s`))
    io.writeln(`os: ` + uname)
    <- 0
}
```

See `examples/shell_script.zl` for pipelines, env, and `process.result`.

### 4.13 Terminal UI (taste)

```zl
import zen.sys.term as term
import zen.io.io as io

function main() {
    term.color(`black`, `cyan`)
    term.write(` title `)
    term.reset()
    io.writeln(``)
    <- 0
}
```

Full demos: `examples/zedit.zl`, `examples/zcat.zl`, `examples/zless.zl`.

---

## 5. A small complete program

Word-count style tool (illustrative — compare `examples/zwc.zl`):

```zl
/!
  count_lines.zl — count lines in a file.
  Usage: ./bin/zen count_lines.zl path/to/file
!/

import zen.sys.sys as Sys
import zen.io.io as io
import zen.io.file as file
import zen.text.string as Str

function count_lines(text) {
    when text == `` {
        <- 0
    }
    let lines -> Str.split(text, `\n`)
    <- lines.length
}

function main() {
    let args -> Sys.get_args()
    // args[0] is the script/binary; need at least one path
    when args.length < 2 {
        io.writeln(`usage: count_lines <file>`)
        <- 1
    }
    let path -> Str.to_string(args[1])
    when not file.exists(path) {
        io.writeln(`not found: ` + path)
        <- 1
    }
    let text -> file.read(path)
    let n -> count_lines(text)
    io.writeln(path + `: ` + Str.to_string(n) + ` lines`)
    <- 0
}
```

Patterns used: docstring, nested imports, argv, early `<- 1`, pure helper + `main` orchestration.

---

## 6. Design patterns in Zenlang

These fit the manifesto (small tools, explicit flow, Unix composition).

### 6.1 Pipeline of pure steps

Keep I/O at the edges; pure functions in the middle.

```zl
function parse(line) { /* -> structure or map */ }
function transform(item) { /* -> item */ }
function format(item) { /* -> string */ }

function main() {
    let raw -> file.read(path)
    let lines -> Str.split(raw, `\n`)
    // map/filter via loops or zen.collections.list helpers
    // write once at the end
}
```

Data flow reads left-to-right with `->` rebinds:

```zl
let text -> file.read(path)
text -> Str.trim(text)
let n -> Str.length(text)
```

### 6.2 Map as a result / options bag

Return a map instead of many out-params:

```zl
function compile_string(src) {
    // ...
    <- {
        `ok` -> True,
        `c_code` -> code,
        `errors` -> []
    }
}

let r -> compile_string(src)
when r[`ok`] == True {
    file.write(out, r[`c_code`])
} or {
    // show r[`errors`]
}
```

Used heavily in the selfhost driver and process APIs (`process.result` → `code` / `stdout` / `stderr`).

### 6.3 Early return for CLI errors

```zl
function main() {
    when args.length < 2 {
        usage()
        <- 1
    }
    // happy path only below
    <- 0
}
```

Avoid deep nesting; each failure is a branch that returns.

### 6.4 Rebind-friendly mutators (native-safe)

Under `-g`, **mutating a map/list in place and ignoring the result can go wrong**. Prefer **return the updated value** and rebind:

```zl
function add_edge(g, a, b) {
    // update g...
    <- g
}

let g -> empty_graph()
g -> add_edge(g, `a`, `b`)
g -> add_edge(g, `b`, `c`)
```

Same idea for string builders: build a new string or buffer, rebind `acc -> acc + piece`.

### 6.5 Index loops over for-in (when dual-path matters)

```zl
// Prefer when you need the list twice or under -g:
let n -> items.length
let i -> 0
do while i < n {
    process(items[i])
    i -> i + 1
}
```

### 6.6 Free functions + modules over deep class hierarchies

Zen has classes/structures, but **Unix tools and the dual-path compiler** stay happiest with:

```zl
// module: zen.text.string
function trim(s) { <- __builtin_string.trim(s) }

// call site
import zen.text.string as Str
Str.trim(s)
```

Classes shine for long-lived UI/process objects; do not force OOP for scripts.

### 6.7 Compose with the OS

Do not reimplement `grep` poorly if a process pipeline is clearer — or do implement `zgrep` when you want structured output and a single binary (`examples/zgrep.zl`).

```zl
// Shell when it is the right tool
let out -> process.shell(`git rev-parse --short HEAD`)

// Pure Zen when you need portability / control
// (walk files, parse, format)
```

### 6.8 Feature flags via `when` chains

```zl
function dispatch(cmd) {
    when cmd == `help` { <- do_help() }
    or when cmd == `run` { <- do_run() }
    or when cmd == `build` { <- do_build() }
    or {
        io.writeln(`unknown: ` + cmd)
        <- 1
    }
}
```

Clearer than large switch tables for CLI routers.

### 6.9 Doc comments for tools

```zl
/!
  zcat — visual cat with line numbers.
  Run: ./bin/zen examples/zcat.zl README.md
!/
```

Readers and future you will thank you; demos in `examples/` use this heavily.

### 6.10 Dual-path check before you ship

```bash
./bin/zen mytool.zl -- args
./bin/zen -g mytool.zl -- args
```

If interpret works and `-g` fails, you usually hit ownership/for-in/rebind or a codegen gap — fix with the patterns above, not with “only interpret.”

---

## 7. Project layout (for contributors)

| Path | Role |
|------|------|
| `bootstrap/` | Authoritative compiler (Python) |
| `selfhost/` | Compiler written in Zen (parity in progress) |
| `runtime/` | C runtime for `-g` |
| `lib/zen/` | Standard library |
| `tests/` | Language + lib + compiler tests |
| `examples/` | Runnable demos (zedit, zcat, shell_script, …) |
| `doc/` | This guide, manifesto, spec, references |
| `scripts/zen` | Developer CLI |

Daily confidence:

```bash
./scripts/zen test-core
./scripts/zen test-parity
./scripts/zen test-lib
```

---

## 8. Style checklist (idiomatic Zen)

1. **Backtick strings**; concatenate with `+` or `Str.join`.
2. **`->` / `<-`** for data flow; avoid burying returns.
3. **`when` / `or`**, not `if`.
4. **`and` / `or` / `not`**, not `&&` / `||`.
5. **Nested imports** (`zen.io.file`, not flat legacy paths).
6. **`Str.*` and free functions** for text and dual-path safety.
7. **Early `<- 1`** in CLI `main` on usage errors.
8. **Rebind** updates under `-g` (`x -> f(x)`).
9. **Small pure helpers** + thin `main`.
10. **Document run lines** in `/! ... !/` at the top of tools.

---

## 9. Where to go next

| Goal | Open |
|------|------|
| More language depth | [Zenlang Explained.md](Zenlang%20Explained.md) |
| Philosophy | [Zen Manifesto.md](Zen%20Manifesto.md) |
| Stdlib modules | [Standard_Library_Reference.md](Standard_Library_Reference.md) |
| Formal rules | `doc/Specification/Zenlang.pdf` (build via `doc/Specification/build.sh`) |
| Learn by reading | `examples/zcat.zl`, `zedit.zl`, `shell_script.zl` |
| Language tests as examples | `tests/01_primitives.zl` … `tests/06_structs.zl` |
| Tooling | [Zenlang Tooling.md](Zenlang%20Tooling.md), [README.md](../README.md) |

### Try this path

1. Work through `examples/getting_started/01_hello.zl` … `12_patterns.zl` (see that folder’s README).
2. Run `examples/zcat.zl` on a file, then open `examples/zedit.zl`.
3. Re-run a few getting-started files with `-g` (e.g. `04_functions.zl`, `10_count_lines.zl`).
4. Skim `examples/shell_script.zl` and replace one `bash` one-liner you use.

Welcome to Zen — keep tools small, data flow visible, and the terminal first-class.
