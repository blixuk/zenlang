# Chapter 5: Functions, Arrow Bodies & Closures

Functions are the primary procedural building blocks in Zenlang. They feature visual return flow (`<-`), parameterless signatures, arrow function bodies, and snapshot-by-value closures.

---

## 1. Defining Functions

### 1.1 Standard Block Functions
Functions are declared using the `function` keyword. Return values emit outward using the return arrow (`<-`):

```zl
use zen.io
use zen.text.string as Str

// Parameterless function (empty parentheses omitted):
function say_hello {
    <- `Hello, World!`
}

// Function with return type annotation:
function get_number : Integer {
    <- 42
}

// Typed function with parameters:
function add : Integer (a: Integer, b: Integer) {
    <- a + b
}
```

### 1.2 Single-Expression Arrow Bodies (`->`)
For concise functions, Zenlang allows arrow bodies (`->`), omitting braces and the `<-` keyword:

```zl
// Parameterless arrow function:
function get_status -> `System Operational`

// Typed parameterless arrow function:
function get_code : Integer -> 200

// Typed arrow function with parameters:
function greet : String (name: String) -> `Hello, ` + name

// Mathematical computation:
function multiply : Integer (a: Integer, b: Integer) -> a * b
```

---

## 2. Anonymous Functions & Lambdas

Functions are first-class values that can be assigned to variables, passed into algorithms, or stored in collections:

### 2.1 Arrow Lambdas
```zl
// Parameterless inline lambda:
let get_greeting -> function <- `Welcome!`

// Typed inline lambda:
let get_magic : Function<Integer> -> function <- 42

// Parameterized arrow lambda:
let square -> function(x: Integer) -> x * x
let is_even -> function(x: Integer) -> (x % 2) == 0
```

### 2.2 Higher-Order Functions
A higher-order function is a function that accepts another function as an argument:

```zl
function apply_twice(fn, value) {
    let first -> fn(value)
    <- fn(first)
}

function increment(x: Integer) : Integer -> x + 1

let val -> apply_twice(increment, 5) // Evaluates to 7
```

---

## 3. Closures & Snapshot-By-Value Capture

When an anonymous function references variables from its surrounding scope, it forms a **closure**. In Zenlang, outer local variables are captured **by value (snapshot)**:

```zl
function make_adder(offset: Integer) {
    let adder -> function(x: Integer) {
        <- x + offset // offset is captured by value snapshot
    }
    <- adder
}

let add_10 -> make_adder(10)
let add_50 -> make_adder(50)

io.writeln(Str.to_string(add_10(5)))  // Prints: 15
io.writeln(Str.to_string(add_50(5)))  // Prints: 55
```

### Why Snapshot-By-Value?
- **Concurrency Safety:** Concurrent tasks and closures cannot inadvertently mutate each other's outer stack frames.
- **Deterministic Lifetimes:** The captured state remains immutable and valid even after the enclosing scope terminates.

---

## 💡 Chapter Exercises

1. Write a single-line arrow function `celsius_to_fahrenheit(c: Decimal) : Decimal -> ...`.
2. Write a higher-order function `filter_list(items, predicate_fn)` using `do for` and an arrow lambda.
3. Create a function generator `make_multiplier(factor)` that returns a closure multiplying any input by `factor`.

