= Functions & Closures

Functions are the primary building blocks of Zenlang programs. They support first-class treatment, higher-order compositions, and safe snapshot-by-value closures.

== Defining Functions

Functions are defined with the `function` keyword:

```zl
use zen.io
use zen.text.string as Str

function greet(name) {
    io.writeln(`Hello, ` + name + `!`)
}

function add(a, b) {
    <- a + b
}

function main() {
    greet(`Zen Programmer`)
    let sum -> add(10, 20)
    io.writeln(`Sum: ` + Str.to_string(sum))
    <- 0
}
```

== First-Class & Anonymous Functions

In Zenlang, functions are first-class values: you can assign them to variables, pass them to other functions, and return them:

```zl
// Anonymous function / Lambda
let double -> function(x) {
    <- x * 2
}

let result -> double(21) // 42
```

=== Higher-Order Functions

A higher-order function is a function that accepts another function as an argument:

```zl
function apply_twice(fn, value) {
    let first -> fn(value)
    <- fn(first)
}

function increment(x) {
    <- x + 1
}

let val -> apply_twice(increment, 5) // 7
```

== Closures & Snapshot-By-Value Capture

When an anonymous function references variables from its surrounding scope, it forms a *closure*.

In Zenlang, outer local variables are captured *by value (snapshot)*:

```zl
function make_adder(offset) {
    let adder -> function(x) {
        <- x + offset // offset is captured by value
    }
    <- adder
}

let add_10 -> make_adder(10)
let add_50 -> make_adder(50)

io.writeln(Str.to_string(add_10(5)))  // Prints: 15
io.writeln(Str.to_string(add_50(5)))  // Prints: 55
```

=== Why Snapshot-By-Value?
- *Concurrency Safety*: Tasks and closures cannot inadvertently mutate each other's outer stack variables.
- *Predictable Behavior*: The captured value remains constant even if the outer scope changes later.
