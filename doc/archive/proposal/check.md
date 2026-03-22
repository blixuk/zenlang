```
// check takes an identifer's value and checks if it matches a case if it does then does that case
// check can also return value and that value can be assigned to a variable

// Value-match mode
check <identifer> {
    case <value> { .... },
    case <value> { .... }
}
// optinal `or` for else cases
check <identifer> {
    case <value> { .... },
    case <value> { .... }
} or { .... }

// Pattern Matching
check <identifer> {
    case in [1,2,3] { ... }
    case > 10 { ... }
    case String { ... }
    case is SomeType { ... }
}

// Expression-returning:
let result -> check x {
    case 1 <- `one`,
    case 2 { <- result * 2 }
}

// if no identifer is provided check can check conditions instead
// Condition-mode (no identifier)
check {
    case <condition> { .... },
    case <condition> { .... }
} or { .... }
```

# Semantics
Value-match mode:
- check <identifier> looks at the value of the identifier
- each case <value> compares with ==
- first match wins
- optional or { } acts as else

Condition-mode:
- If no identifier is provided, case <condition> is evaluated as a boolean expression
- first truthy case executes
