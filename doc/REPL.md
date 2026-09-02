# Zenlang Interactive Stateful REPL Guide

| Attribute | Value |
|:---|:---|
| **Role** | Interactive REPL User Guide |
| **Authority** | Tooling Manual |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

The Zenlang REPL provides an interactive development shell featuring persistent session state, automatic `_` and `_N` result history, state snapshotting (`:save` / `:load` with Zen Data `.zd`), multi-line block entry, live syntax highlighting, and tab autocompletion.

## Starting the REPL

Launch the REPL with:
```bash
./scripts/zen repl
```
or via the installed binary:
```bash
zen repl
```

---

## Key Features & Testing Workflows

### 1. Persistent Session State
Variables, constants, functions, classes, and imported modules persist throughout the session:
```zl
zen> let radius: Integer -> 5
zen> function circle_area(r) { <- 3.14159 * r * r }
zen> circle_area(radius)
78.53975
```

### 2. Automatic Result Sentinels (`_` and `_N`)
- `_` stores the result of the most recent evaluation.
- `_1`, `_2`, `_3`... provide indexed access to past evaluation outputs.
```zl
zen> 100 / 4
25
zen> _ + 10
35
zen> _1 * 2
50
```

### 3. State Snapshotting (`:save` and `:load`)
Serialize active session variables and imports into a structured **Zen Data (`.zd`)** file:
```zl
zen> let api_key -> "secret_12345"
zen> :save my_session.zd
[STATE] Saved active variables to my_session.zd

zen> :reset
[STATE] Session environment reset.

zen> :load my_session.zd
[STATE] Restored variables from my_session.zd
```

### 4. Multi-Line Continuation
Blocks with open delimiters (`{`, `(`, `[`) automatically switch to the continuation prompt (`... `):
```zl
zen> function fib(n) {
...      when n <= 1 { <- n }
...      <- fib(n - 1) + fib(n - 2)
...  }
zen> fib(7)
13
```

### 5. Execution Profiling
Toggle millisecond timing for every evaluated statement:
```zl
zen> :time on
Execution timing: ON

zen> "12345" <: Integer
12345 (0.04 ms)
```

---

## Command Reference

| Command | Description |
|:---|:---|
| `:help`, `:h` | Show interactive command manual |
| `:vars`, `:state` | List active variables and values |
| `:save <file.zd>` | Save session snapshot to a Zen Data file |
| `:load <file.zd>` | Restore session snapshot from a Zen Data file |
| `:time [on\|off]` | Toggle millisecond execution timing |
| `:mode [vm\|interp]` | Set execution engine (`vm` or `interp`) |
| `:reset` | Reset session state to empty |
| `:clear`, `:cls` | Clear screen |
| `:quit`, `:exit` | Exit REPL (or press `Ctrl+D`) |
