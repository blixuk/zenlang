# Conditional Branching (when ... or)

```
when <condition> { 
  .... 
}

when <condition> { 
  .... 
} or { 
  .... 
}

when <condition> {
  ....
} or when <condition> {
  ....
} or {
  ....
}

// Inline versions

when <condition> { <statement> }

when <condition> { <statement> } or { <statement> }

// variable assignment
let result -> <value1> when <condition> or <value2>

// function return  
<- <value1> when <condition> or <value2>

```

# Looping Constructs (do)

Do Loop
```
do {
  <statement>
}
```

Do When Loop
```
do when <condition> {
  <statement>
}

do when <condition> {
  <statement>
} or {
  <statement>
}
```

Do While Loop
```
// pre check
do while <condition> {
  <statement>
}

// post check
do {
  <statement>
} while <condition>

// or only with pre check
do while <condition> {
  <statement>
} or {
  <statement>
}
```

Do Until Loop
```
// pre check
do until <condition> {
  <statement>
}

// post check
do {
  <statement>
} until <condition>
```

Do For Loop
```
do for <identifier> in <collection> | <range> {
  <statement>
}

do for <identifier> in <collection> | <range> {
  <statement>
} or {
  <statement>
}
```

Do While (Before / After)
```
do while <condition> {
    <statement>
} before <function> after <function>

do while <condition> {
    <statement>
} before { <statement> } after { <statement> }

// Before is run every loop before the main body
// After is run every loop after the main body

```


Break / Continue
```
break       // Immediately exit innermost loop
continue    // Skip to next iteration
```

# Pattern Matching & Destructuring (when <target> is <pattern>)

Pattern matching is expressed cleanly using when ... is:
```
when <...> is <...> {}

// 1. List Spread & Slicing:
let payload -> [10, 20, 30, 40]
when payload is [head, ...tail] {
    io.info(`Head: ` + Str.to_string(head)) // 10
    io.info(`Tail: ` + Str.to_string(tail)) // [20, 30, 40]
}

// 2. Map Destructuring:
let user -> { `name` -> `Bob`, `role` -> `Admin` }
when user is { name, role } {
    io.info(name + ` has role ` + role)
}

// 3. Tuple Destructuring:
let pair -> (`Attack`, 100)
when pair is (stat, value) {
    io.info(stat + `: ` + Str.to_string(value))
}

// 4. Guards & Wildcards (_):
let val -> 150
when val is Integer and val > 100 {
    io.info(`Large Integer: ` + Str.to_string(val))
}

let coords -> [1, 999, 3]
when coords is [1, _, 3] {
    io.info(`Matched wildcard pattern`)
}
```

Resource Scoping & Deferred Cleanup (with & defer)
```
with <...> as <...> {}

// 1. Scoped Resource Management:
with Arena.create(1024 * 1024) as arena {
    let temp_buf -> Memory.alloc_in(arena, 512)
} // Arena memory is freed immediately upon block exit

// 2. Guaranteed Cleanup on Return (defer / ~):
function read_file_safe(path: String) {
    let f -> file.open(path)
    defer file.close(f) // Guaranteed to execute when function exits
    
    <- file.read_all(f)
}
```

Check
```
// check takes an identifer's value and checks if it matches a case if it does then does that case
// check can also return value and that value can be assigned to a variable

// Value-match mode
check <identifer> {
    case <value> { <statement> },
    case <value> { <statement> }
}
// optinal `or` for else cases
check <identifer> {
    case <value> { <statement> },
    case <value> { <statement> }
} or { <statement> }

// Pattern Matching
check <identifer> {
    case <condition> { <statement> },
    case in [1,2,3] { <statement> },
    case > 10 { <statement> },
    case is String { <statement> },
    case is Integer and val > 100 { <statement> },
    case has value { <statement> }
}

// Expression-returning:
let result -> check <identifer> {
    case <condition> <- <statement>,
    case <condition> { <statement> }
}

// if no identifer is provided check can check conditions instead
// Condition-mode (no identifier)
check {
    case <condition> { <statement> },
    case <condition> { <statement> }
} or { <statement> }
```

Value-match mode:
- check <identifier> looks at the value of the identifier
- each case <value> compares with ==
- first match wins
- optional or { } acts as else

Condition-mode:
- If no identifier is provided, case <condition> is evaluated as a boolean expression
- first truthy case executes
