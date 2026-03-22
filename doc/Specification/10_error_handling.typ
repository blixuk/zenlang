= Error Handling

Zenlang uses `check`, `assert` and `raise` to manage exceptions.

== Check

```zl
check {
  ....
} or {
  write(error)
}
```

```zl
function calculate() {
    let result -> check divide(10, 0) or {
        write(`Something went wrong!`)
        <- 0 // Default value
    }
    
    write(`Result is: ` + result)
}
```

```zl
let file -> open(`config.zl`)

check file {
    case is Error { 
        write(`Failed to open file`) 
    },
    case is String { 
        write(`File content: ` + file) 
    }
}
```

```zl
check condition { 
    cases 
} or { default }                    // check conditions

check condition or default          // check with default
? condition or default              // inline check with check symbol '?'

check condition raise error         // check with raise
? condition ^ error                 // inline check symbol '?' with raise symbol '^' 

```

== Raise

```zl
raise `ErrorUnknown`                // raise keyword

^ `ErrorUnknown`                    // raise symbol '^' 

raise `ErrorUnknown` with `Value`   // raise with value
```

```zl
function divide(a: Decimal, b: Decimal) Decimal {
    when b == 0 {
        raise `DivisionByZeroError` // This immediately returns the error value
    }
    <- a / b
}
```

== Assert

```zl
assert condition                // assert keyword
assert condition raise error    // assert keyword with raise keyword

! condition                     // assert symbol '!'
! condition ^ error             // assert symbol '!' with raise symbol '^' 
```

- Symbol: ^, Keyword: raise, Purpose: Immediate return of an error value/variant.
- Symbol: ?, Keyword: check, Purpose: Unwrapping a value or branching based on a condition.
- Symbol: !, Keyword: assert, Purpose: Validation of assumptions; halts or raises on failure.

=== Semantic Comparison Table

Recovery: let x -> ? func() or 0
Propagation: ? condition ^ Error(`ErrorName`)
Validation: `! x > 0`
Matching: `check value { case ... }`

== Error ReturnType

```zl
// Multiple Return Types '[Decimal, Error]'
// Will return error if raise is called else return Decimal
// Base ReturnType should be either Variant or TypeUnion?

function divide : [Decimal, Error] (a: Decimal, b: Decimal) {
    when b == 0 {
        raise `DivisionByZeroError` // This immediately returns the error value
    }
    <- a / b
}
```