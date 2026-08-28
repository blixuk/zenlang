# Chapter 4: Control Flow

Zenlang provides clean, structured control flow statements: `when` for branching and `do` for looping.

---

## 1. Branching with `when`

Instead of `if`/`elif`/`else`, Zenlang uses `when`, `or when`, and `or`:

```zenlang
use zen.io
use zen.text.string as Str

function check_status(code) {
    when code == 200 {
        io.writeln(`OK: Success`)
    } or when code == 404 {
        io.writeln(`Not Found: Resource missing`)
    } or when code == 500 {
        io.writeln(`Error: Server failure`)
    } or {
        io.writeln(`Unknown status code: ` + Str.to_string(code))
    }
}
```

### Single-Line `when` Guards
For compact checks and early returns:

```zenlang
function divide(a, b) {
    when b == 0 { <- Nothing }
    <- a / b
}
```

---

## 2. Looping with `do while` and `do until`

Zenlang provides explicit loop constructs:

### `do while` (Runs while condition is True)
```zenlang
let count -> 5
do while count > 0 {
    io.writeln(`Countdown: ` + Str.to_string(count))
    count -> count - 1
}
io.writeln(`Blast off!`)
```

### `do until` (Runs until condition becomes True)
```zenlang
let buffer -> []
do until buffer.length >= 3 {
    buffer.append(`item`)
}
```

### Loop Control: `break` and `continue`
- `break`: Exits the loop immediately.
- `continue`: Skips to the next iteration.

```zenlang
let i -> 0
do while i < 10 {
    i -> 0 + i + 1
    when i == 5 { continue } // Skip 5
    when i > 8 { break }     // Stop after 8
    io.writeln(`Value: ` + Str.to_string(i))
}
```

---

## 3. Pattern Matching & Destructuring

Zenlang supports expressive structural pattern matching:

### Matching Lists & Spreads
```zenlang
let values -> [1, 2, 3]

check values {
    case [first, ..rest] {
        io.writeln(`First: ` + Str.to_string(first))
    }
}
```

### Matching Maps & Guards
```zenlang
let point -> { `x` -> 10, `y` -> 20 }

check point {
    case { `x` -> x, `y` -> y } when x > 0 {
        io.writeln(`Positive X coordinate: ` + Str.to_string(x))
    }
}
```

---

## 💡 Chapter Exercises

1. Write a function `fizzbuzz(n)` that prints numbers from 1 to `n`, substituting multiples of 3 with `"Fizz"`, multiples of 5 with `"Buzz"`, and multiples of both with `"FizzBuzz"`.
2. Write a loop using `do while` that finds the first power of 2 greater than 1000.
