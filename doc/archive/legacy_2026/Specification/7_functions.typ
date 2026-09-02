#import "template.typ": *

= Functions & Closures

Functions in Zenlang are declared using the `function` keyword. Data returning from a function uses the outward return arrow `<-`.

== Function Declarations

#feature(
    "Standard Function Declaration",
    "function Identifier(Parameters) : ReturnType {\n    ...\n    <- ReturnValue\n}",
    "function calculate_area(width: Decimal, height: Decimal) : Decimal {\n    let area -> width * height\n    <- area\n}"
)

=== Inline Functions

Functions consisting of a single return expression can be written concisely inline:

#feature(
    "Inline Function Definition",
    "function Identifier(Parameters) <- Expression",
    "function add(a: Integer, b: Integer) : Integer <- a + b\nfunction square(n: Decimal) <- n * n"
)

== Anonymous Functions & Closures

Anonymous functions are first-class values that can be assigned to variables, passed into higher-order functions, or returned from other functions.

#feature(
    "Anonymous Function Binding",
    "let Identifier -> function(Parameters) { ... }",
    "let multiply -> function(x, y) {\n    <- x * y\n}\n\nlet result -> multiply(6, 7) // 42"
)

=== Snapshot-by-Value Closure Capture

When an anonymous function references variables from its enclosing lexical scope, the values are *captured by value* (snapshotted) at the moment the closure is created.

#tip[
  *By-Value Isolation Guarantee:* Capturing outer variables by value prevents concurrent data corruption and race conditions across tasks. In the shared C runtime, closures support up to 8 captured values efficiently.
]

```zl
function make_adder(offset: Integer) {
    // offset is snapshotted into the returned closure
    let adder -> function(x: Integer) {
        <- x + offset
    }
    <- adder
}

let add_10 -> make_adder(10)
let add_50 -> make_adder(50)

io.writeln(Str.to_string(add_10(5))) // 15
io.writeln(Str.to_string(add_50(5))) // 55
```

== Parameter Defaults & Variadics

Parameters can specify default values or accept variadic argument lists:

```zl
// Default parameter values
function greet(name: String, greeting: String -> `Hello`) {
    io.writeln(greeting + `, ` + name + `!`)
}

greet(`Alice`)               // Prints: Hello, Alice!
greet(`Bob`, `Welcome back`) // Prints: Welcome back, Bob!
```
