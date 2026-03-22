# ZenLang’s Core Identity

ZenLang is:
- Compiled and interpreted (same language, same semantics)
- Unix-native first, not cross-platform-first
- Terminal-centric, not GUI-centric
- Compositional, not monolithic
- Minimal core, powerful standard libraries
- Text, streams, and processes are first-class

Think:
“A modern systems scripting language for Unix environments, with batteries included for TUI and web.”

# Execution Model: Compiler + VM

Three execution modes

| Mode                | Description           | Use Case                    |
| ------------------- | --------------------- | --------------------------- |
| **Interpreter**     | Fast startup, dynamic | Scripts, REPL, admin tasks  |
| **Bytecode VM**     | Portable, optimized   | TUI apps, services          |
| **Native Compiler** | Ahead-of-time to ELF  | Long-running tools, daemons |

Single frontend, multiple backends

Lexer → Parser → AST → SymanticChecker → TypeChecker

```
AST
 ├─ Interpreter backend
 ├─ Bytecode compiler → ZenVM
 └─ Native compiler → C / LLVM / WASM
```

Important:
Do not fork the language semantics between interpreted and compiled modes.
If something works in the interpreter, it must work identically when compiled.

# Unix Philosophy Applied to ZenLang

Core principles to encode into the language

- Everything streams
	- stdin/stdout/stderr are first-class
	- Pipes are language primitives, not shell hacks
- Programs are composable
	- Zen programs should replace Bash scripts, not fight them
- Text is the universal interface
	- Structured text, not just strings
- Explicit is better than implicit
	- No hidden magic runtimes

# Zen vs Bash

- Zen becomes the preferred scripting language

How this works in practice
```
zen run script.zen
zen build tool.zen
zen repl
```
Inside Zen:
```
process("ls -la") | grep("zen") | sort()
```

This avoids:
- Reimplementing job control
- Reimplementing terminal quirks
- Reimplementing POSIX shells

Zen will ship a ZenShell later

# Terminal Programming as a First-Class Domain

This is where Zen will be genuinely unique.

Terminal is not “just output”
Treat it as a stateful device.

Core Terminal Module (zen.term)
- Raw mode
- Alternate buffer
- Cursor control
- Color & style abstraction
- Window resize events
- Input decoding (keys, mouse)

# TUI + HTML Unification

Unifying abstraction: ZenUI

Instead of:
- TUI library
- Web UI library

You define:
```
ZenUI → Renderer
        ├─ TerminalRenderer
        └─ HTMLRenderer
```

Declarative UI Model
```
view App {
    Column {
        Text(`Zen Dashboard`)
        Button(`Refresh`, on_click: refresh)
        List(items)
    }
}

```

Then:
```
zen run app.zen          # Terminal UI
zen serve app.zen        # Web UI

```

Rendering rules
- Layout is shared
- Styling maps to:
	- ANSI + terminal layout
	- CSS + HTML

This eliminates duplication and makes Zen immediately compelling.

# Web Stack: Zen as Full-Stack Language

Server-side
- HTTP server
- Routing
- Middleware
- Streaming responses
- WebSockets

```
route GET `/users/:id` {
    return json(db.users.get(id))
}
```

Client-side (No JavaScript required initially)

Two viable models:
Option A: Zen → WASM
- Zen compiles to WASM
- Browser runtime handles DOM

Option B (simpler, first iteration):
- Server renders HTML
- Client interactions handled via:
	- Form submits
	- WebSocket messages
	- Minimal JS runtime shipped by Zen

Recommendation:
Start with Option B, add WASM later.

# Database Philosophy: Embedded First

Do not chase PostgreSQL/MySQL initially.

ZenDB (Embedded, Script-Friendly)

Features:
- Key-value store
- Structured documents
- Indexed fields
- ACID-ish guarantees
- File-backed
- JSON

Think:
- TinyDB philosophy
- But idiomatic to Zen

```
db = open("app.db")

db.users.insert({
    id: 1,
    name: `Alex`,
    role: `admin`
})

users = db.users.where(role == `admin`)
```

# Standard Library Modules (Proposed)

Core
- zen.fs – files, paths, permissions
- zen.io – streams, pipes
- zen.proc – processes, signals
- zen.net – sockets, DNS
- zen.time – timers, schedulers

Terminal / UI
- zen.term
- zen.tui
- zen.ui (shared abstraction)
- zen.style

Web
- zen.http
- zen.router
- zen.html
- zen.css
- zen.websocket

Data
- zen.db
- zen.json
- zen.yaml
- zen.csv

System
- zen.os
- zen.env
- zen.user

# Language-Level Features Worth Adding

1. Structured Concurrency

Not threads everywhere.

```
task fetch_user()
task fetch_orders()

await all(fetch_user, fetch_orders)
```

2. Algebraic Data Types (Eventually)

Perfect for CLI tools.

```
Result<T> = Ok(T) | Error(String)
```

3. Pattern Matching

Extremely useful for text tools.

```
match input {
    `quit` -> exit(),
    _ -> process(input)
}

```

4. First-Class Pipelines

```
read(`file.txt`)
| lines()
| filter(|l| l.contains(`error`))
| write(`errors.log`)
```
functions with added input and output for piping, different from parameters and returns.

```
// [ in : out] is named function input and ouput for the function.
// [:] - this would use the defualt names `input` and `ouput`
// [in:] - just input
// [:out] - just output
// [::error] - could add error? optinal idea. then you could do something like [in:out:err]

function test_1 [ in : out] {
	let a -> in
	a.append(`Hello`)
	out -> a
}

let a -> `world` | test_1() // this wont work as the function is not defined to return a string
write(`world` | test_1()) // this will work as the function is not defined to return a string

function test_2 (word : String -> `Hello`) : String [ in : out] {
	let a -> in
	a.append(word)
	out -> a
	<- a
}

let b -> `world` | test_2(`Hello`) // this will work as the function is defined to return a string
write(`world` | test_2(`Hello`)) // this will work as the function is defined to return a string
`world` | test_2(`Hello`) | write() // this will work as the `write` function is defined to accept input

function solve [in : out] {
	let result -> eval(in)
	out -> result
}

`1 + 1` | solve() | write() // this will work as the `solve` function is defined to accept input
```

# Packaging & Ecosystem

Packages -> Modules -> Classes -> Functions

Packages can contain multiple Modules and Modules can contain multiple Classes and Classes can contain multiple Functions.


Zen Package Manager (zenpkg)
- Git-based
- Semantic versioning
- Minimal metadata

```
zenpkg add zen/http
```

Distribution
- Single binary runtime
- Optional standard library bundles
- No “npm-scale” dependency hell

Zen project tools for setting up new projects with the defualts from project templates

```
zen create `new project`
zen create `new project` -t terminal
```

