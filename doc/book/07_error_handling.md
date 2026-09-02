# Chapter 7: The Error Handling Triad & Resilience Model

Zenlang treats errors as values, rejecting hidden exceptions and convoluted `try/catch/finally` control flow. It provides a clean, visual triad: **`raise` (`^`)**, **`check` (`?`)**, and **`assert` (`!`)**.

---

## 1. The Error Triad

| Concept | Keyword | Symbol | Role | Example |
|:---|:---|:---|:---|:---|
| **Raise** | `raise` | `^` | Emit error / unwind stack | `raise `DivisionByZero` with b` |
| **Check** | `check` | `?` | Unwrap value or recover with fallback | `let val -> check divide(10, 0) or 0` |
| **Assert** | `assert` | `!` | Invariant precondition validation | `assert count >= 0 raise `InvalidCount`` |

---

## 2. Emitting Errors with `raise` (`^`)

Functions declare errors either as explicit error returns or via the `raise` (`^`) operator:

```zl
use zen.io
use zen.text.string as Str

// Multiple return type signature [Value, Error]:
function divide : [Decimal, Error] (a: Decimal, b: Decimal) {
    when b == 0.0 {
        // Keyword form:
        raise `DivisionByZero` with `Cannot divide by zero`
        
        // Or visual symbol form:
        // ^ `DivisionByZero`
    }
    <- a / b
}
```

---

## 3. Unwrapping & Recovery with `check` (`?`)

The `check` expression evaluates a fallible operation and provides a deterministic fallback:

### 3.1 Inline Unwrapping with Fallback
```zl
// Keyword form:
let result -> check divide(10.0, 0.0) or 0.0

// Visual symbol form:
let result -> ? divide(10.0, 0.0) or 0.0

io.writeln(`Result is: ` + Str.to_string(result)) // Prints: 0.0
```

### 3.2 Block Recovery
```zl
let user_data -> check {
    let raw -> file.read_all(`user.zd`)
    <- zd.parse(raw)
} or {
    io.warn(`Failed to read user data, returning default profile`)
    <- Default
}
```

### 3.3 Condition Validation (`check ... raise` / `? ... ^`)
Ensure conditions hold or raise immediately:

```zl
function process_age(age: Integer) {
    // Validate condition or raise error:
    check age >= 0 raise `InvalidAge` with age
    
    // Symbol form:
    // ? age >= 0 ^ `InvalidAge` with age

    io.info(`Age accepted: ` + Str.to_string(age))
}
```

---

## 4. Contract Assertions with `assert` (`!`)

Use `assert` (`!`) to enforce internal invariants and function preconditions:

```zl
function allocate_buffer(size: Integer) {
    // Assert invariant:
    assert size > 0 raise `InvalidBufferSize`

    // Symbol form:
    // ! size > 0 ^ `InvalidBufferSize`

    <- memory.alloc(size)
}
```

---

## 5. The Result Map Pattern

For predictable I/O operations (such as HTTP requests or database queries), standard libraries return a Result Map:

```zl
use zen.io.file as file

function load_config(path: String) : Map {
    when not file.exists(path) {
        <- { `ok` -> False, `error` -> `File not found: ` + path }
    }
    <- { `ok` -> True, `data` -> file.read_all(path) }
}

function main() {
    let res -> load_config(`app.zd`)
    when not res.ok {
        io.error(`Error: ` + res.error)
    } or {
        io.info(`Config loaded successfully`)
    }
    <- 0
}
```

---

## 💡 Chapter Exercises

1. Write a function `safe_sqrt(x: Decimal) : [Decimal, Error]` that raises `NegativeNumber` if $x < 0$.
2. Use `check ... or` to call `safe_sqrt(-4.0)` and provide a fallback value of `0.0`.
3. Write a function `parse_percentage(text: String)` that uses `assert` to ensure the parsed integer is between `0` and `100`.

