#import "template.typ": *

= Error Handling & Resilience

Zenlang provides two complementary error management models: *Result Maps* for predictable, explicit function returns, and *`check` / `raise` / `assert`* for structured exceptions.

== Result Maps (Idiomatic Zen Flow)

The primary and recommended approach for recoverable errors in Zenlang is returning explicit result maps:

#feature(
    "Result Map Pattern",
    "<- { `ok` -> True, `value` -> val, `error` -> `` }\n<- { `ok` -> False, `value` -> Nothing, `error` -> `reason` }",
    "function read_config(path: String) {\n    when not file.exists(path) {\n        <- { `ok` -> False, `value` -> Nothing, `error` -> `file_not_found` }\n    }\n    <- { `ok` -> True, `value` -> file.read_all(path), `error` -> `` }\n}\n\nlet res -> read_config(`settings.json`)\nwhen not res.ok {\n    io.writeln(`Error: ` + res.error)\n} or {\n    process_config(res.value)\n}"
)

== Structured Exception Handling (`check` / `raise`)

When an unrecoverable failure occurs deep in a call stack, `raise` immediately unwinds execution:

```zl
function divide(a: Decimal, b: Decimal) : Decimal {
    when b == 0.0 {
        raise `DivisionByZeroError`
    }
    <- a / b
}
```

=== Recovering with `check ... or`

The `check` construct catches errors raised within a block and executes an alternative recovery block:

#feature(
    "Check Recovery Block",
    "check {\n    ...\n} or {\n    ...\n}",
    "let result -> check {\n    <- divide(10.0, 0.0)\n} or {\n    io.writeln(`Caught division error, falling back to 0.0`)\n    <- 0.0\n}"
)

== Validation Asserts (`assert`)

The `assert` keyword validates invariants. If the condition is false, execution terminates or raises an assertion failure:

```zl
assert user_age >= 0
assert buffer.length > 0
```