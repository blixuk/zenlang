# Defer

defer is a keyword that schedules a function call to run only after the surrounding function has finished executing, acting as a reliable cleanup mechanism for resources like files, network connections, or locks, ensuring they're closed regardless of errors or early returns. Multiple deferred calls run in reverse order (LIFO), and their arguments are evaluated immediately when defer is called, not when the function executes, making it great for pairing setup and teardown code. 

Key Characteristics
- Execution: Runs when the enclosing function returns, even if it panics or returns early.
- Order (Multiple Deferrals): Last-In, First-Out (LIFO) – the last defer statement executes first.
- Argument Evaluation: Arguments are evaluated when defer is encountered, but the function call itself is delayed.
- Purpose: Simplifies resource management (files, DBs, mutexes) by keeping setup/cleanup close together. 

```zl
function test {
    defer write(`Defer`)
    write(`Hello`)
}
```