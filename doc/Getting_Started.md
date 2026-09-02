# Getting Started with Zenlang

| Attribute | Value |
|:---|:---|
| **Role** | Practical Learner Tutorial & Language Tour |
| **Authority** | Derived On-Ramp Guide (Canonical Truth in [doc/SPECIFICATION.md](SPECIFICATION.md)) |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Welcome to Zenlang

Zenlang is a modern, Unix-native programming language designed for clarity, visual ergonomics, and high performance. It uses visual data flow (`->` for assignment, `<-` for return) and supports both rapid scripting via a fast Bytecode VM and high-performance Ahead-of-Time (AOT) C compilation.

---

## 2. Installation & Quick Start

```bash
# 1. Install the standalone compiler and toolchain
./scripts/zen install

# 2. Run a script via the Bytecode VM
./bin/zen examples/getting_started/01_hello.zl

# 3. Compile and execute natively (AOT)
./bin/zen run examples/getting_started/01_hello.zl

# 4. Launch the interactive REPL
./bin/zen repl
```

---

## 3. Ten-Minute Language Tour

### 3.1 Hello World
```zl
use zen.io

function main() {
    io.writeln(`Hello, Zenlang!`)
}
```

### 3.2 Variables, Constants & Sentinels
```zl
use zen.io
use zen.text.string as Str

// Mutable variable (let)
let count -> 10
count -> count + 5

// Immutable constant (set)
set APP_NAME : String -> `ZenTutorial`

// Inferred type lock (:>)
let status :> `Active` // Locked to String

// Standard Sentinels: Nothing (absent) & Default (zero-state)
let avatar : String -> Nothing
let items  : List   -> Default // Evaluates to []
let flags  : Map    -> Default // Evaluates to {}

io.writeln(APP_NAME + `: Count is ` + Str.to_string(count))
```

### 3.3 Numeric Prefixes & Byte Scalars
```zl
let hex_val -> 0x7B             // Hexadecimal
let oct_val -> 0o173            // Octal
let bin_val -> 0b0111_1011      // Binary
let big_num -> 1_000_000        // Underscore separator

let a : Byte -> 0x41            // 8-bit unsigned scalar
let char_code -> a <: Integer   // 65
let hex_str   -> a <: String    // `0x41`
```

### 3.4 Control Flow (`when ... or` and `check`)
```zl
use zen.io

let score -> 85

// 1. Conditional Branching (when ... or)
when score >= 90 {
    io.info(`Grade A`)
} or when score >= 80 {
    io.info(`Grade B`)
} or {
    io.info(`Grade C`)
}

// 2. Inline Ternary Expression
let status -> `Pass` when score >= 80 or `Fail`

// 3. Multi-Way Switch & Match (check)
let command -> `start`
let exit_code -> check command {
    case `start`   <- 0,
    case `stop`    <- 1,
    case `restart` <- 2
} or <- -1
```

### 3.5 Looping Constructs (`do`)
```zl
use zen.io
use zen.text.string as Str

// 1. Full inclusive range loop (1 to 5)
do for i in 1...5 {
    io.writeln(`Step: ` + Str.to_string(i))
}

// 2. While loop with zero-execution fallback
do while has_tasks() {
    process_task()
} or {
    io.writeln(`Queue was empty.`)
}
```

### 3.6 The 5 Core Collections
```zl
use zen.io

// 1. List: Ordered, Dynamic, Mutable
let fruits -> [`apple`, `banana`]
fruits++ `cherry` // Stepped append operator

// 2. Map: Key-Value Dictionary
let user -> {
    `name` -> `Alice`,
    `role` -> `Developer`
}

// 3. Vector: Fixed-size, Immutable
let coords -> Vector{ 10, 20, 30 }

// 4. Set: Unique Elements
let tags -> Set{ `web`, `systems`, `terminal` }

// 5. Tuple: Heterogeneous Fixed Record
let entry -> Tuple{ `Attack`, 100, True }
```

### 3.7 Functions & Arrow Bodies
```zl
use zen.io

// 1. Standard Function
function add : Integer (a: Integer, b: Integer) {
    <- a + b
}

// 2. Single-Expression Arrow Function
function greet : String (name: String) -> `Hello, ` + name

// 3. Anonymous Function (Lambda)
let square -> function(x) -> x * x
```

### 3.8 The Three Container Tiers: Struct, Object & Class
```zl
use zen.io
use zen.text.string as Str

// 1. Low Tier: Structure (fast C ABI value record)
structure Vector2 { x: Integer -> 0, y: Integer -> 0 }
let pt -> Vector2{ x -> 10, y -> 20 }

// 2. Middle Tier: Fluid Object (dynamic fields & Zen Data .zd interop)
let player -> object {
    name   : String  -> `Player`,
    health : Integer -> 100
}
player.weapon -> `Sword` // Dynamic field addition

// 3. High Tier: Class (nominal OOP with single inheritance)
class Entity {
    let id: Integer
    function init(id: Integer) {
        self.id -> id
    }
}

class Monster extends Entity {
    let power: Integer
    function init(id: Integer, power: Integer) {
        parent.init(id)
        self.power -> power
    }
}
```

### 3.9 Error Handling: `raise` (`^`), `check` (`?`), and `assert` (`!`)
```zl
use zen.io

function divide : [Decimal, Error] (a: Decimal, b: Decimal) {
    when b == 0 {
        ^ `DivisionByZeroError` // Immediate error return via symbol
    }
    <- a / b
}

// Recover with fallback value:
let safe -> check divide(10.0, 0.0) or 0.0

// Invariant assertion:
assert safe >= 0.0 raise `NegativeResult`
```

### 3.10 Concurrency: The Unified `task` Substrate
```zl
use zen.io
use zen.text.string as Str

// Tasks are implicitly suspendable; no viral async/await!
task fetch_data : String (endpoint: String) {
    <- `Data from ` + endpoint
}

function run_concurrent() {
    // 1. Dispatch background execution
    let handle -> fetch_data(`/api/metrics`).spawn

    // 2. Wait without blocking the OS thread
    let result -> handle.wait
    io.writeln(result)
}
```

---

## 4. Rosetta Stone: Zenlang for Python, JavaScript & Rust Developers

| Concept | Python | JavaScript / TypeScript | Rust | Zenlang |
|:---|:---|:---|:---|:---|
| **Assignment** | `x = 10` | `let x = 10;` | `let x = 10;` | `let x -> 10` |
| **Return** | `return 42` | `return 42;` | `return 42;` / `42` | `<- 42` |
| **String Literal** | `"hello"` / `'hello'` | `"hello"` / `'hello'` | `"hello"` | `` `hello` `` strictly |
| **Branching** | `if / elif / else` | `if / else if / else` | `if / else if / else` | `when / or when / or` |
| **Ternary** | `val if cond else alt` | `cond ? val : alt` | `if cond { val } else { alt }` | `val when cond or alt` |
| **Null/None** | `None` | `null` / `undefined` | `None` | `Nothing` (capitalized) |
| **Zero-State** | `0`, `""`, `[]` manual | `0`, `""`, `[]` manual | `Default::default()` | `Default` (capitalized) |
| **Type Cast** | `int(x)` | `Number(x)` / `x as number` | `x as i64` | `x <: Integer` / `Integer(x)` |
| **Ranges** | `range(0, 5)` | `[...Array(5).keys()]` | `0..5` / `0..=5` | `0...5` (inclusive), `0..-5` (exclusive) |
| **Loops** | `for x in list:` | `for (const x of list)` | `for x in list` | `do for x in list` |
| **Switch/Match** | `match x:` | `switch (x)` | `match x` | `check x { case ... }` |
| **Concurrency** | `async def` / `await` | `async` / `await` | `async fn` / `.await` | `task` / `.spawn` / `.wait` |
| **Error Raise** | `raise ValueError()` | `throw new Error()` | `Err(...)` | `raise \`Error\` with val` / `^` |
| **Error Catch** | `try / except` | `try / catch` | `match res` / `?` | `check expr or fallback` / `?` |

---

## 5. Hands-On Mini-Project: Building `zen-count`

Let's build a real Unix utility that reads a file and outputs line, word, and character counts:

```zl
use zen.sys.sys as sys
use zen.io.file as file
use zen.text.string as Str
use zen.color.color as color
use zen.io

function count_file(filepath: String) : [Map, Error] {
    // Invariant check:
    assert filepath.length > 0 raise `EmptyPathError`

    when not file.exists(filepath) {
        ^ `FileNotFoundError` with filepath
    }

    let text  -> file.read_all(filepath)
    let lines -> Str.split(text, `\n`)
    let words -> Str.split(text, ` `)

    <- {
        `lines` -> lines.length,
        `words` -> words.length,
        `chars` -> Str.length(text)
    }
}

function main() {
    let args -> sys.get_args()
    when args.length < 2 {
        let help -> color.format(`Usage: zen-count <filepath>`, color.YELLOW, Default)
        io.writeln(help)
        <- 1
    }

    let target_path -> args[1]
    
    // Evaluate safely with fallback:
    let stats -> check count_file(target_path) or {
        let err_msg -> color.format(`Error: Could not read file ` + target_path, color.RED, Default)
        io.writeln(err_msg)
        <- 1
    }

    // Display formatted results:
    let header -> color.format(`=== File Statistics for ` + target_path + ` ===`, color.CYAN, Default)
    io.writeln(header)
    io.writeln(`  Lines:      ` + Str.to_string(stats.lines))
    io.writeln(`  Words:      ` + Str.to_string(stats.words))
    io.writeln(`  Characters: ` + Str.to_string(stats.chars))
    <- 0
}
```

---

## 6. Next Steps & References

- **The Official Book:** [*The Zen of Programming*](book/README.md)
- **Full Language Specification:** [doc/SPECIFICATION.md](SPECIFICATION.md)
- **Standard Library API Catalog:** [doc/Standard_Library_Reference.md](Standard_Library_Reference.md)
- **Coding Style Guide:** [doc/Style_Guide.md](Style_Guide.md)
- **Executable Recipes & Integrations:** [doc/Cookbook.md](Cookbook.md)
- **Zen Data (`.zd`) Guide:** [doc/Zen_Data.md](Zen_Data.md)
- **Unified Task Concurrency Guide:** [doc/Concurrency.md](Concurrency.md)

