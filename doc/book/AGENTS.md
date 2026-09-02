# Purpose

*The Zen of Programming: The Zenlang Book* — The definitive, end-to-end tutorial and reference book for learning and mastering the Zenlang programming language.

# Ownership

Owned by Zenlang documentation authors and educators.

# Local Contracts

- Every code example in the book must be syntactically valid and runnable under the authoritative compiler (`bootstrap/Zen.py`).
- All code follows [doc/Style_Guide.md](../Style_Guide.md) standards: 4-space indentation, single spaces around `->` and `<-`, capitalized `Nothing` and `Default`.
- Chapters are organized progressively: from zero-knowledge fundamentals to advanced terminal systems and dual-path native compilation.

# Child DOX Index

- README.md: Table of contents, foreword, and learning path
- 01_getting_started.md: Introduction, installation, and first steps
- 02_visual_data_flow.md: The visual data flow philosophy (`->` and `<-`)
- 03_types_and_sentinels.md: Primitive types, collections, and `Nothing`/`Default`
- 04_control_flow.md: Conditionals, loops, and pattern matching
- 05_functions_and_closures.md: Functions, closures, and value capture
- 06_structures_and_oop.md: Structs, classes, methods, and ADTs
- 07_error_handling.md: Safe error recovery with `check` and `raise`
- 08_modules_and_reflection.md: Packages, imports, `module`, and `zen.reflect`
- 09_terminal_mastery.md: Terminal graphics, canvas, widgets, and TUI design
- 10_dual_execution_and_c.md: Dual execution (interpreter vs `-g` native)
- 11_practical_projects.md: Complete capstone projects (CLI tools, TUI apps)
- 12_concurrency_and_tasks.md: The Unified Task Substrate, structured concurrency, and channels
- build.sh: Compilation script for generating `Zen_Book.pdf` via native Zen Mark
- tools/build_book.zl: Pure-Zenlang vector PDF & HTML book generator


