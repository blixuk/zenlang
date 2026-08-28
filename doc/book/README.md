# The Zen of Programming: A Practical Guide to Zenlang

Welcome to **The Zen of Programming**, the official book for learning **Zenlang** — a modern, Unix-native programming language designed for scripts, terminal applications, and networked services.

---

## 🌟 Foreword: Why Zenlang?

Most programming languages force you into a compromise:
- High-level scripting languages (Python, Ruby, JavaScript) offer rapid development and rich developer ergonomics, but often struggle with terminal latency, distribution overhead, and single-binary packaging.
- Systems languages (C, C++, Rust, Zig) deliver blisteringly fast, sub-millisecond execution and tiny native binaries, but require extensive boilerplate for daily scripts and UI layout.

**Zenlang bridges this divide.** It combines:
1. **Visual Data Flow**: Code reads the way data moves: `->` assigns and binds; `<-` returns and yields.
2. **Terminal as a First-Class Citizen**: ANSI canvas, 60 FPS sub-millisecond redraws, table formats, and built-in widget layouts.
3. **Dual Execution Parity**: Write once — run instantly with the interpreter during development, or compile directly to standalone native C binaries (`-g`) for production.
4. **Explicit Over Magic**: No hidden coercions, no unexpected type mutations, and explicit snapshot-by-value capture.

---

## 📖 Table of Contents

### Part I: Fundamentals
- **[Chapter 1: Getting Started](01_getting_started.md)** — Installation, the daily CLI, your first program, and interactive tools (`playground`, `zenfm`).
- **[Chapter 2: Visual Data Flow](02_visual_data_flow.md)** — Understanding `->` and `<-`, variables, mutability, and flow thinking.
- **[Chapter 3: Types, Collections & Sentinels](03_types_and_sentinels.md)** — Primitives, Strings, Lists, Maps, and the power of `Nothing` & `Default`.
- **[Chapter 4: Control Flow](04_control_flow.md)** — Expressive branching with `when` / `or when` / `or`, and loop iteration with `do while` / `do until`.

### Part II: Abstractions & Architecture
- **[Chapter 5: Functions & Closures](05_functions_and_closures.md)** — Function signatures, recursion, higher-order functions, and snapshot-by-value closures.
- **[Chapter 6: Structures, Classes & OOP](06_structures_and_oop.md)** — Structs, object-oriented classes, methods, and Algebraic Data Types (ADTs).
- **[Chapter 7: Error Handling](07_error_handling.md)** — Reliable error management with `check`, `assert`, `raise`, and result maps.
- **[Chapter 8: Modules, Packages & Reflection](08_modules_and_reflection.md)** — Code organization, `import`/`use`, built-in `module`, and runtime introspection with `zen.reflect`.

### Part III: Terminal Systems & Advanced Topics
- **[Chapter 9: Terminal Mastery & UI](09_terminal_mastery.md)** — Direct terminal control, ANSI buffers, declarative tables (`zen.ui.table`), spinners (`zen.ui.spinner`), and live interactive apps.
- **[Chapter 10: Dual Execution & The C Runtime](10_dual_execution_and_c.md)** — How Zenlang interprets and compiles to C, memory management, and self-hosting.
- **[Chapter 11: Practical Projects](11_practical_projects.md)** — Step-by-step capstones: building a Unix log analyzer CLI, an interactive dashboard, and a terminal mini-game.

---

## 🚀 How to Read This Book

- **Exercises**: Hands-on challenges to test your understanding.

---

## 📕 Compiling to PDF

You can compile the entire book into a formatted PDF document ([Zen_Book.pdf](Zen_Book.pdf)) with full syntax highlighting using the Typst build script:

```bash
bash doc/book/build.sh
```
