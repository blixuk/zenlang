# Zenlang Documentation Suite

Welcome to the official documentation for **Zenlang**, a modern, Unix-native programming language designed for simplicity, composition, and developer control.

---

## 1. Introduction & Overview

### What is Zenlang?
Zenlang is a high-level, optionally typed language built for the modern Unix environment. It is designed to bridge the gap between rapid shell scripting and robust systems programming, providing a single coherent model for building CLI tools, terminal applications (TUIs), and networked services.

### Core Philosophy
Zenlang is guided by the **Zen Manifesto**:
*   **Simplicity over cleverness**: Code should be obvious and readable.
*   **Composition over frameworks**: Power is built by connecting small, well-defined tools.
*   **Explicitness over magic**: Visual data flow makes state changes and returns unmistakable.
*   **Terminal-first**: The terminal is a primary UI surface, not a legacy afterthought.

### Why Zenlang?
*   **Visual Data Flow**: Uses `->` for assignment and `<-` for return, making data movement visually distinct.
*   **Unified Concurrency**: "Everything is a Task." Zenlang uses fiber-based tasks that suspend naturally, eliminating the complexity of `async`/`await` virality.
*   **Semantic Text**: Text is treated as more than just byte arrays; it supports semantic structures like `Word`, `Sentence`, and `Paragraph`.
*   **Boxed Runtime**: A unified memory model that balances the safety of a managed language with the control of manual arenas.

---

## 2. Getting Started

### Installation
Zenlang is currently in a developer-preview bootstrap phase. To set up the environment on Linux or macOS:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/zenlang.git
    cd zenlang
    ```
2.  **Dependencies**: Ensure you have `python3` and a C compiler (`gcc` or `clang`) installed.
3.  **Build the Host Compiler**:
    ```bash
    make
    ```
    This builds the Zenlang driver in `bin/zen`.

### Hello, World!
Create a file named `hello.zl`:

```zenlang
import zen.io

function main {
    io.write(`Hello, Zenlang!`)
}
```

### Basic CLI Usage
You can run Zenlang code in two modes:

*   **Interpreted (Default)**: Ideal for scripts and quick iteration.
    ```bash
    python3 bootstrap/Zen.py hello.zl
    ```
*   **Ahead-of-Time Compiled**: Generates a fast, native binary via C.
    ```bash
    python3 bootstrap/Zen.py hello.zl --generate
    ./output/build/out
    ```

---

## 3. Language Reference (Core Features)

### Variables & Data Types
Zenlang uses explicit operators to distinguish between mutable and immutable state.

*   **`let`**: Defines a mutable variable.
*   **`set`**: Defines a constant (immutable).

```zenlang
let score : Integer -> 100    // Mutable integer
set PI -> 3.14159             // Inferred decimal constant
let name :> `Alice`           // Type-locked (String) but value can change
```

**Base Types**:
*   `Integer`, `Decimal`, `Boolean` (`True`/`False`)
*   `String` (UTF-32 default), `Rune` (Single glyph)
*   `Variant` (Dynamic type), `Void` (No return)

### Control Flow
Zenlang uses familiar but refined control flow structures.

**`when` (Conditionals)**:
```zenlang
when x > 10 {
    io.write(`Large`)
} or when x > 5 {
    io.write(`Medium`)
} or {
    io.write(`Small`)
}
```

**`do` (Loops)**:
```zenlang
// While loop
do while x < 10 { x++ }

// For-in loop
do for item in [1, 2, 3] {
    io.write(item)
}
```

### Functions
Functions are declared using the `function` keyword and return values using the `<-` operator.

```zenlang
function add(a: Integer, b: Integer) : Integer {
    <- a + b
}

// Anonymous function / Closure
let multiply -> function(x, y) { <- x * y }
```

### Data Structures
*   **Lists**: Dynamic arrays `[1, 2, 3]`
*   **Maps**: Key-value pairs `{ `key` -> `value` }`
*   **Structures**: Lightweight value types `structure Point { x, y }`
*   **Classes**: Full OOP support with inheritance.

```zenlang
class Person {
    let name : String
    function init(name) { self.name -> name }
    function greet { io.write(`Hi, I'm ` + self.name) }
}
```

### Error Handling
Zenlang uses the **Error Triad** for explicit and predictable failure management.

*   **`raise` / `^`**: Returns an error object.
*   **`check` / `?`**: Unwraps a value or handles an error fallback via an `or` block.
*   **`!` (Assert)**: Halts execution if a condition is met.

```zenlang
function riskyDiv(a, b) {
    when b == 0 { raise `DivideByZero` }
    <- a / b
}

let result -> check riskyDiv(10, 0) or {
    io.warn(`Division failed, using default`)
    0
}
```

---

## 4. Advanced Features

### Structured Memory Management
Zenlang provides high-performance memory management without a traditional garbage collector, focusing on **Bounded Arenas**.

*   **`with` statement**: Creates a lexically bounded memory region that is automatically reclaimed when the block exits.
*   **`in` keyword**: Directs an allocation into a specific named arena.
*   **`defer`**: Schedules code to run at the end of the current scope.

```zenlang
import zen.memory

function process {
    with memory.Region() as scene {
        let p in scene -> Person(`Zen`)
        // 'p' is allocated inside 'scene'
    } // 'scene' and all objects inside it are reclaimed here
}
```

### Unified Concurrency (Tasks)
Concurrency is a first-class citizen. Any function or block can be spawned as a **Task**.

```zenlang
task background_work {
    time.sleep(1.second)
    <- `Done`
}

function main {
    let t -> background_work().spawn
    io.write(t.wait)
}
```

---

## 5. Standard Library Overview

| Module | Description | Key Functions |
| :--- | :--- | :--- |
| **`zen.io`** | Basic Input/Output & Logging | `write()`, `read()`, `info()`, `warn()`, `error()`, `debug()` |
| **`zen.string`**| String Manipulation | `split()`, `join()`, `trim()`, `substring()`, `to_string()` |
| **`zen.list`** | Functional List Utilities | `map()`, `filter()`, `reduce()`, `each()`, `find()`, `contains()` |
| **`zen.collections`**| Map/Set Utilities | `Map.keys()`, `Map.values()`, `Set.from_list()`, `Set.to_list()` |
| **`zen.time`** | Time & Delays | `now()`, `sleep()`, `monotonic()`, `wallclock()`, `500.ms`, `2.seconds` |
| **`zen.process`**| Process Management | `run()`, `get_id()` |
| **`zen.test`** | Unit Testing | `assert_equal()`, `run_unit()`, `run_suite()` |
| **`zen.collections`**| Data Structures | `Map`, `Set`, `Stack`, `Queue` |
| **`zen.error`**| Error Creation | `new()`, `literal()` |
| **`zen.math`** | Mathematical Utilities | `abs()`, `sqrt()`, `pow()`, `sin()`, `cos()`, `pi`, `e` |
| **`zen.sys`** | System Environment | `get_args()`, `get_env()`, `get_cwd()`, `platform()`, `version()` |
| **`zen.file`** | File System Ops | `read()`, `write()`, `append()`, `exists()`, `remove()` |
| **`zen.path`** | Path Manipulation | `join()`, `basename()`, `dirname()`, `extname()` |
| **`zen.json`** | JSON Serialization | `parse()`, `stringify()` |
| **`zen.memory`**| Arena Management | `Region()`, `Arena()`, `push_arena()`, `pop_arena()` |
| **`zen.term`** | Terminal UI | `clear()`, `move()`, `color()`, `reset()`, `alt_screen()`, `get_size()` |
| **`zen.random`** | Randomness | `seed()`, `integer()`, `decimal()`, `range()` |
| **`zen.geometry`** | Geometry | `Point`, `Rect`, `Size`, `point()`, `rectangle()`, `size()` |
| **`zen.text`** | Semantic Text | `Word`, `Sentence`, `Paragraph`, `capitalize()`, `to_words()`, `wrap()` |

### Logging

Zenlang provides standardized, color-coded logging via the `zen.io` module:

- `io.info(msg)`: Blue prefix `[INFO]`
- `io.warn(msg)`: Yellow prefix `[WARN]`
- `io.error(msg)`: Red prefix `[ERROR]` (outputs to `stderr`)
- `io.debug(msg)`: Cyan prefix `[DEBUG]`

---

## 6. Best Practices & Idiomatic Zenlang

1.  **Visual Data Flow**: Use the `->` and `<-` operators consistently to make the data flow obvious to the reader.
2.  **Explicit Memory**: Prefer `with` blocks for large object graphs or temporary data structures to keep the program footprint small.
3.  **Semantic Text**: Don't just use `String`. Use `Word` or `Sentence` when processing natural language to leverage built-in linguistic logic.
4.  **Avoid Global State**: Use the `in` keyword to pass context and dependencies into functions rather than relying on global variables.

---

*Zenlang is calm. Zenlang is deliberate. Zenlang is Unix.*
