#import "template.typ": *

= Control Flow & Branching

Zenlang provides clean, keyword-driven control flow structures that replace traditional C-style constructs with expressive `when` branching and `do` loops.

== Conditional Branching (`when`)

Conditionals use `when` and `or`:

#feature(
    "When Conditional Statement",
    "when condition {\n    ...\n} or when condition {\n    ...\n} or {\n    ...\n}",
    "when score >= 90 {\n    grade -> `A`\n} or when score >= 80 {\n    grade -> `B`\n} or {\n    grade -> `C`\n}"
)

=== Inline Ternary Expressions (`when ... or`)

Expressions can branch inline for concise value selection:

#feature(
    "Inline When Expression",
    "result -> value when condition or default_value",
    "let status -> `Online` when is_connected or `Offline`\nlet discount -> 0.20 when is_vip or 0.0"
)

== Loop Constructs (`do`)

All looping constructs in Zenlang begin with the `do` keyword:

=== 1. `do while` (Pre-Condition Loop)
Executes repeatedly as long as the condition evaluates to `True`:

```zl
let i -> 0
do while i < 5 {
    io.writeln(`Step: ` + Str.to_string(i))
    i -> i + 1
}
```

=== 2. `do until` (Inverse Pre-Condition Loop)
Executes repeatedly until the condition evaluates to `True` (while `False`):

```zl
let ready -> False
do until ready {
    ready -> check_system_ready()
}
```

=== 3. `do for` (Collection & Range Iteration)
Iterates over elements in a `List`, `Map`, or range:

```zl
// Range iteration
do for i in 0..10 {
    io.writeln(`Index: ` + Str.to_string(i))
}

// Collection iteration
let items -> [`alpha`, `beta`, `gamma`]
do for item in items {
    io.writeln(`Item: ` + item)
}
```

=== 4. `do { ... } while` (Post-Condition Loop)
Executes at least once, evaluating the loop condition at the end of each iteration:

```zl
let attempts -> 0
do {
    attempts -> attempts + 1
    let success -> try_network_ping()
} while not success and attempts < 3
```

== Loop Control (`break`, `continue`)

- `break`: Immediately exits the innermost enclosing loop.
- `continue`: Skips the remaining statements in the current iteration and begins the next iteration.

== Deferred Execution (`defer`)

The `defer` statement schedules an expression or block to execute when the enclosing function returns, regardless of whether return occurs normally or via early exit:

#feature(
    "Deferred Cleanup",
    "defer cleanup_expression\ndefer { ... }",
    "function process_file(path) {\n    let f -> file.open(path)\n    defer file.close(f) // Guaranteed to run upon return\n\n    let content -> file.read_all(f)\n    <- content\n}"
)
