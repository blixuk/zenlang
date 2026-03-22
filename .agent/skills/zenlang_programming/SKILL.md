---
name: zenlang programming
description: A guide to programming in Zenlang, a Unix-native, terminal-first language designed for simplicity and composability.
---

# Zenlang Programming Skill

Zenlang is a modern, optionally typed programming language designed for clarity, flexibility, and rapid development. It uses visual data flow (`->`, `<-`) and a unified execution model.

## 1. Environment & Tools

- **Compiler/Interpreter**: `python3 bootstrap/Zen.py [source.zl]`
- **Native Generation**: `python3 bootstrap/Zen.py [source.zl] --generate`
- **REPL**: `python3 bootstrap/Zen.py --repl`

## 2. Variables, Values & Assignment

Zenlang strictly separates mutable from immutable state.

### 2.1 Mutability
- **`let`**: Defines a **mutable** variable.
- **`set`**: Defines a **constant** (immutable).

### 2.2 Assignment Syntax
Assignment uses the `->` operator.
```zl
let count : Integer -> 10     // Explicit typing
set PI : Decimal -> 3.14159   // Explicit constant
let name :> `Alice`           // Locked to inferred type
let health -> 100             // Variant inferred as Integer
```

### 2.3 Reassignment
Reassignment of mutable variables **does not** use `let` or `set`.
```zl
let status -> 0  // Declaration
status -> 1      // Reassignment
```

## 3. The Type System & Literals

### 3.1 Base Types
- **Primitives**: `Void`, `Variant`, `Boolean` (`True`/`False`)
- **Numbers**: `Integer`, `Decimal`, `Number` (Abstract)
- **Text**: `String`, `Rune`, `Text` (Abstract)

### 3.2 Collection Literals
Collections use explicit bracketed prefixes for clarity.
```zl
let v :> [V]{1, 2, 3}        // Vector
let l :> [L]{1, `a`, True}   // List
let s :> [S]{1, 2, 3}        // Set
let t :> [T]{ x -> 10, y -> 20 } // Named Tuple
let m :> [M]{ `k` -> `v` }   // Map
```

## 4. Control Flow

### 4.1 Conditionals (`when`)
```zl
when x == 10 {
    out.write(`Ten`)
} or {
    out.write(`Other`)
}
```

### 4.2 Loops (`do`)
```zl
do while i < 10 {
    i -> i + 1
}

do for item in list {
    out.write(item)
}
```

## 5. Unified Concurrency: The Task

ZenLang uses a single fiber-based model: **The Task**.

```zl
task fetch_data(id) {
    <- net.get(id)
}

function main {
    let data -> fetch_data(1).wait
}
```

## 6. Input/Output System

ZenLang uses environment-aware streams (`out` and `in`) instead of `print`.

```zl
out.write(`Hello`)
out.info(`System Ready`)
out.error(`Failure`)

let input -> in.read.line()
```

## 7. Error Handling (`^`, `?`, `!`)

- **`^` (Raise)**: Immediately returns an Error variant.
- **`?` (Check)**: Unwraps a value or handles an error.
- **`!` (Assert)**: Halts if a condition is false.

```zl
let result -> ? divide(10, 0) or 0
```

## 8. Best Practices

1. **Explicit Constants**: Use `set` for all values that shouldn't change.
2. **Visual Flow**: Use `->` for assignment and `<-` for return.
3. **Structured IO**: Prefer `out.write` and semantic variants (`info`, `error`) over generic output.
4. **Task-Based**: Design long-running or external operations as `task` rather than `function`.
