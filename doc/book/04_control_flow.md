# Chapter 4: Control Flow, Ranges & Pattern Matching

Zenlang replaces traditional C-style constructs with expressive `when` branching, mathematical 4-boundary ranges, structured `do` loops with fallback branches, and dual-layer pattern matching.

---

## 1. Branching with `when ... or`

Instead of `if`/`elif`/`else`, Zenlang uses `when` and `or`:

```zl
use zen.io
use zen.text.string as Str

function check_status(code: Integer) {
    when code == 200 {
        io.info(`OK: Success`)
    } or when code == 404 {
        io.warn(`Not Found: Resource missing`)
    } or when code == 500 {
        io.error(`Error: Server failure`)
    } or {
        io.writeln(`Unknown status code: ` + Str.to_string(code))
    }
}
```

### 1.1 Inline Ternary Expressions
Zenlang provides a natural inline expression syntax for conditional assignment and returns:

```zl
// Variable assignment:
let label -> `Active` when is_online or `Offline`
let discount -> 0.15 when is_member or 0.0

// Early return:
<- result when is_valid or Default
```

---

## 2. The 4-Boundary Range System

Zenlang eliminates off-by-one errors with four distinct mathematical range operators:

| Range Operator | Name | Interval | Ascending (`0` to `5`) | Descending (`5` to `0`) |
|:---|:---|:---|:---|:---|
| **`..`** | Range Between | $(start, end)$ | `[1, 2, 3, 4]` | `[4, 3, 2, 1]` |
| **`..+`** | Inclusive End | $(start, end]$ | `[1, 2, 3, 4, 5]` | `[4, 3, 2, 1, 0]` |
| **`..-`** | Exclusive End | $[start, end)$ | `[0, 1, 2, 3, 4]` | `[5, 4, 3, 2, 1]` |
| **`...`** | Full Inclusive | $[start, end]$ | `[0, 1, 2, 3, 4, 5]` | `[5, 4, 3, 2, 1, 0]` |

```zl
// Character rune ranges:
let letters -> `a`...`e` // [`a`, `b`, `c`, `d`, `e`]
```

---

## 3. Looping with `do`

All iteration in Zenlang begins with the `do` keyword:

### 3.1 `do for` Collection & Range Iteration
```zl
use zen.io
use zen.text.string as Str

// Full inclusive range:
do for i in 1...5 {
    io.writeln(`Step: ` + Str.to_string(i))
}

// Collection iteration:
do for fruit in [`Apple`, `Banana`, `Cherry`] {
    io.writeln(`Fruit: ` + fruit)
}
```

### 3.2 Loop-Or (`or { ... }` Empty Fallback)
The `or` block executes if the loop executed zero times (e.g. empty collection or initial false condition):

```zl
do for user in active_users {
    render_user(user)
} or {
    io.writeln(`No active users found.`) // Runs if active_users is empty
}
```

### 3.3 Iteration Hooks (`before` and `after`)
Execute pre-frame and post-frame logic around the main iteration body:

```zl
do while is_running {
    process_game_frame()
} before {
    clear_screen()
} after {
    render_screen()
}
```

---

## 4. Multi-Way Matching with `check`

`check` serves as Zenlang's pattern-matching and multi-way switch table:

### 4.1 Value-Match Mode
```zl
check status_code {
    case 200 { io.info(`Success`) },
    case 404 { io.warn(`Resource missing`) },
    case 500 { io.error(`Internal server error`) }
} or {
    io.error(`Unhandled status code`)
}
```

### 4.2 Condition Mode (No Target Identifier)
```zl
check {
    case score >= 90 { grade -> `A` },
    case score >= 80 { grade -> `B` },
    case score >= 70 { grade -> `C` }
} or {
    grade -> `F`
}
```

### 4.3 Expression-Returning Match
```zl
let exit_code -> check command {
    case `start`   <- 0,
    case `stop`    <- 1,
    case `restart` <- 2
} or <- -1
```

---

## 5. Dual Pattern Matching

Zenlang supports both single-pattern destructuring (`when ... is`) and multi-pattern tables (`check`):

### 5.1 Single-Pattern Extraction (`when <target> is <pattern>`)
```zl
// List Head and Tail:
let payload -> [10, 20, 30, 40]
when payload is [head, ...tail] {
    io.info(`Head: ` + Str.to_string(head)) // 10
    io.info(`Tail items: ` + Str.to_string(tail.length))
}

// Map Destructuring:
let user -> { `name` -> `Bob`, `role` -> `Admin` }
when user is { name, role } {
    io.info(name + ` has role ` + role)
}
```

### 5.2 Multi-Pattern Table (`check`)
```zl
check response {
    case { `ok` -> True, `data` -> d }   { handle_data(d) },
    case { `ok` -> False, `error` -> e } { handle_error(e) },
    case in 1...100                      { handle_range(response) }
} or {
    io.error(`Unrecognized response shape`)
}
```

---

## 💡 Chapter Exercises

1. Write a `fizzbuzz` loop using `do for i in 1...30` and `check` condition mode.
2. Given a list of users, write a `do for ... or` loop that renders each user, or prints an empty notice if none are present.
3. Write a function that accepts a tuple `(width, height)` and destructures it using `when dims is (w, h)`.

