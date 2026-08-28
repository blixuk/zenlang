# Chapter 7: Error Handling

In Zenlang, error handling is explicit, ergonomic, and structured. There are no silent crashes or untyped surprises.

---

## 1. Catching Errors with `check`

The `check` expression executes a block of code and catches any errors raised during execution:

```zenlang
use zen.io
use zen.text.string as Str

function safe_division(a, b) {
    let result -> check {
        when b == 0 { raise `DivisionByZero` }
        <- a / b
    } or {
        io.writeln(`Caught an error during division!`)
        <- 0
    }
    <- result
}

function main() {
    let res -> safe_division(10, 0)
    io.writeln(`Result: ` + Str.to_string(res)) // 0
    <- 0
}
```

---

## 2. Raising Errors with `raise`

Use `raise` to signal an exceptional condition:

```zenlang
function parse_port(s) {
    let port -> Str.to_integer(s)
    when port < 1 or port > 65535 {
        raise `InvalidPortNumber`
    }
    <- port
}
```

---

## 3. The Result Map Pattern

For operations that frequently encounter predictable errors (such as file I/O or network requests), the standard library idiom is the *Result Map*:

```zenlang
function read_user_file(filepath) {
    when not file.exists(filepath) {
        <- { `ok` -> False, `error` -> `File not found: ` + filepath }
    }
    let content -> file.read(filepath)
    <- { `ok` -> True, `data` -> content }
}

function main() {
    let res -> read_user_file(`config.json`)
    when res.ok {
        io.writeln(`File content: ` + res.data)
    } or {
        io.writeln(`Error: ` + res.error)
    }
    <- 0
}
```

---

## 💡 Chapter Exercises

1. Write a function `safe_json_parse(text)` that attempts to parse a string, returning `{ \`ok\` -> True, \`value\` -> ... }` on success or `{ \`ok\` -> False, \`error\` -> ... }` on invalid syntax.
2. Implement a retry loop with `check` that attempts a network operation up to 3 times before returning an error.
