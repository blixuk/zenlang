# Chapter 2: Visual Data Flow

At the core of Zenlang is the philosophy of **Visual Data Flow**. In most languages, assignment uses `=` and returning uses `return`. In Zenlang, data movement is explicitly visible through arrows:
- `->` represents **assignment, binding, and data flow forward**.
- `<-` represents **returning, yielding, and data flow outward**.

---

## 1. The Assignment Arrow (`->`)

To declare a new variable or rebind an existing one, use `let` with `->`:

```zenlang
use zen.io
use zen.text.string as Str

function main() {
    let name -> `Alice`
    let age -> 30
    let is_member -> True

    io.writeln(`Name: ` + name)
    io.writeln(`Age: ` + Str.to_string(age))
    <- 0
}
```

### Why Arrows Instead of `=`?

1. **Reads Left-to-Right**: `let value -> compute()` explicitly visualizes the output of `compute()` flowing into `value`.
2. **Distinguishes Assignment from Equality**: In Zenlang, `==` tests equality and `->` assigns. There is no confusing `=` assignment with comparison.

---

## 2. The Return Arrow (`<-`)

To return a value from a function, use `<-`:

```zenlang
function add(a, b) {
    <- a + b
}

function multiply(a, b) {
    let product -> a * b
    <- product
}
```

A function can return early at any point:

```zenlang
function clamp(val, min_val, max_val) {
    when val < min_val { <- min_val }
    when val > max_val { <- max_val }
    <- val
}
```

---

## 3. Rebinding & Mutation

Variables in Zenlang can be rebound:

```zenlang
let score -> 100
score -> score + 50
score -> score * 2
```

### Loop Index Rebinding Pattern

When updating loop counters across iterations, compute indices with clean arithmetic expressions:

```zenlang
let i -> 0
do while i < 5 {
    io.writeln(`Step: ` + Str.to_string(i))
    i -> 0 + i + 1
}
```

---

## 💡 Chapter Exercises

1. Write a function `celsius_to_fahrenheit(c)` that takes a temperature in Celsius and returns Fahrenheit (`(c * 9 / 5) + 32`).
2. Write a function `greet(name)` that returns `"Greetings, " + name + "!"`. Test both in `./scripts/zen playground`.
