
how Zenlang should handle errors, we need to decide if Zenlang views errors as **Bugs** (contract violations) or **Expected Failures** (recoverable conditions).

#### The Problem with standard `try/catch`

In a language focused on "clarity and rapid development", traditional `try/catch` often leads to "GOTO" style spaghetti code where the happy path is obscured.

#### A "Zen" Proposal: The Result/Option Pattern with `raise`

Instead of traditional heavy exceptions, Zenlang could treat recoverable errors as **values**. This fits your existing syntax for types and arrows perfectly.

**The Concept:**

1. **`raise`**: Used to return an error value immediately from a function.
2. 
**`check`**: Keyword to "unwrap" a result or handle it.


3. 
**Union Types**: Leveraging Zenlang's `Variant` or `Tagged Union` capabilities.


### 2. Detailed Example: The "Check/Raise" Model

Let’s look at how this would look in Zenlang code, assuming we want to avoid the "catch" syntax but keep the power of "raise."

#### Step 1: Defining a Function that "Fails"

Instead of throwing an exception that unwinds the stack invisibly, the function explicitly returns a `Variant` that might be an error.

```
// Zenlang Syntax
function divide(a: Decimal, b: Decimal) Decimal {
    when b == 0 {
        raise `DivisionByZeroError` // This immediately returns the error value
    }
    <- a / b
}

```

#### Step 2: Handling the Error with `check`

Rather than a big `try` block, you use `check` on the specific call. This keeps the "happy path" left-aligned and clear.

# Check

```
function calculate() {
    let result -> check divide(10, 0) or {
        write(`Something went wrong!`)
        <- 0 // Default value
    }
    
    write(`Result is: ` + result)
}
```

```
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

# Raise

```
raise `ErrorUnknown` // raise keyword

^ `ErrorUnknown` // raise symbol '^' 


// raise with value
raise `ErrorUnknown` with `Value`


// check conditions

check condition { cases } or { default }


check condition or default // check with default
? condition or default // inline check with check symbol '?'

check condition raise error // check with raise
? condition ^ error // inline check symbol '?' with raise symbol '^' 

```

# Assert

```
assert condition
assert condition raise error // assert with raise
assert condition ^ error // assert with raise symbol '^' 

! condition // assert symbol '!' 
! condition raise error // assert symbol '!' with raise
! condition ^ error // assert symbol '!' with raise symbol '^' 


```

# Result-based error model

treat errors as first-class citizens rather than invisible control-flow jumps.

## Updated Lexical Analysis

Symbol: ^, Keyword: raise, Purpose: Immediate return of an error value/variant.
Symbol: ?, Keyword: check, Purpose: Unwrapping a value or branching based on a condition.
Symbol: !, Keyword: assert, Purpose: Validation of assumptions; halts or raises on failure.

## Deep Dive into assert (!)

Zenlang's philosophy of being "beginner-friendly"  benefits from assert. Assert is essentially a check that defaults to a panic or a specific error.

### Semantic Comparison Table

Recovery: let x -> ? func() or 0
Propagation: ? condition ^ Error(`ErrorName`)
Validation: `! x > 0`
Matching: `check value { case ... }`

## Error ReturnType

```

// Multiple Return Types '[Decimal, Error]' Will return error if raise is called else return Decimal
// Base ReturnType should be either Variant or TypeUnion?
function divide : [Decimal, Error] (a: Decimal, b: Decimal) {
    when b == 0 {
        raise `DivisionByZeroError` // This immediately returns the error value
    }
    <- a / b
}
```