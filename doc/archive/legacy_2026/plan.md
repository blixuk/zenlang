# Zenlang: Road to 0.2.0 (Updated Plan)

This plan has been refined after a direct audit of the `lib/` and `bootstrap/` directories. It shifts focus from basic utilities (which are largely complete) to core architectural integration.

## Phase 1: Core Compiler Integration
*Goal: Bring the compiler in line with the language's high-level specifications.*

1.  **Concurrency: The `task` Keyword**
    *   **Lexer/Parser**: Add `task` keyword support to `bootstrap/Lexer/Token.py` and `bootstrap/Parser/StatementHandler.py`.
    *   **Runtime**: Implement the Fiber-based runtime in the C backend to allow non-blocking execution.
2.  **Formalizing `Result` and `Option`** [COMPLETED]
    *   Migrated `Option` and `Result` from user-land `core.zl` to compiler-recognized types.
    *   Implemented `?` (Check) syntactic sugar for unwrapping and propagation.
3.  **Structural Pattern Matching**
    *   Enhance the `when` statement to support destructuring of the already-implemented `Map` and `Structure` types.

## Phase 2: Advanced Standard Library
*Goal: Build high-level "Killer Features" on top of the new Task model.*

1.  **`zen.net.http`: Server Implementation**
    *   Build a non-blocking HTTP server using the new `task` primitives.
2.  **`zen.fs.ext`: Recursive Operations**
    *   Implement `file.walk(path, callback)` for recursive directory processing.
    *   Add cross-platform `file.watch()` support.
3.  **Declarative TUI Layout**
    *   Create a layout engine for the terminal that handles auto-sizing and positioning of widgets from `zen.ui.widgets`.

## Phase 3: Ecosystem & Tooling
*Goal: Provide a professional developer experience.*

1.  **`zen pkg`: The Package Manager**
    *   Implement the fetching and versioning logic for external modules.
2.  **LSP (Language Server Protocol)**
    *   Expose the `Checker/TypeChecker.py` logic via an LSP server for IDE support.
3.  **API Doc Generator**
    *   Build a tool to parse `doc comments` (`/! ... !/`) and generate the "Standard Library Reference" automatically.

---

## The "Self-Hosting" Milestone
Once Phase 1 and the Package Manager are stable, we will begin the transition of the Python bootstrap to a **Native Zenlang Compiler**.

---


### 1. Formalizing `Result` and `Option` (Phase 1, Step 2)
Currently, `Option` and `Result` are defined in user-land (`lib/zen/core.zl`). Moving them into the compiler as first-class types would allow us to:
*   Add **safety checks**: Prevent `unwrap()` on a value that hasn't been checked.
*   Optimize the C backend for these types (e.g., using tagged unions or niche optimizations).
*   Add syntactic sugar (like a `?` operator for optional chaining or `!` for result propagation).

### 2. Advanced Pattern Matching (Phase 1, Step 3)
We saw that basic structural matching works, but we could make it a "WOW" feature by adding:
*   **Spread patterns**: `is [first, ...rest]` for lists.
*   **Destructuring Bindings**: Allowing `is Point { x, y }` where `x` and `y` are automatically bound to the structure's fields.
*   **Guard clauses**: `is Message.Move(x, y) when x > 0 { ... }`.

### 3. "Semantic Text" Power (`zen.text.text`)
The roadmap mentions treating text as high-level structures (`Word`, `Sentence`, `Paragraph`). We could expand the existing `lib/zen/text/text.zl` to include:
*   Recursive directory walking (e.g., `file.walk`).
*   Text flow and alignment for terminal UIs.
*   Linguistic boundaries (proper sentence detection beyond just splitting at dots).