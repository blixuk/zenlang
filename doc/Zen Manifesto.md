# The Zenlang Manifesto

| Attribute | Value |
|:---|:---|
| **Role** | Core Philosophical Bedrock & Guiding Principles |
| **Authority** | Foundational Document for Language Intent & Design Decisions |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Purpose & Mission

Zenlang exists to be a modern, Unix-native programming language for building scripts, terminal applications, system utilities, and networked services using a single, coherent execution model.

Zenlang is designed for developers who value:
- **Simplicity over cleverness**
- **Composition over frameworks**
- **Explicitness over magic**
- **Tools that work with Unix, not against it**

Zenlang is not intended to replace Unix. Zenlang is intended to extend Unix.

---

## 2. Core Philosophy

### 2.1 The Unix Philosophy
Zenlang embraces foundational Unix principles:
- **Do one thing well:** Tools and functions have focused, well-defined responsibilities.
- **Compose through interfaces:** Programs communicate cleanly through standard input, output, streams, and pipes.
- **Prefer text and structured streams:** Universal data flow enables rapid automation.
- **Keep the core small; grow power through libraries:** Minimal language grammar, maximum modular expressiveness.

### 2.2 Terminal-First Execution
The terminal is not a legacy interface; it is a primary execution surface. Zenlang treats the terminal as:
- A structured, environment-aware output surface
- A stateful, real-time input device
- A first-class canvas for rich terminal user interfaces (TUIs)

### 2.3 Dual Execution on a Single Value ABI
Zenlang provides both fast interactive execution via Bytecode VM and high-performance Ahead-of-Time (AOT) C compilation. Both execution modes share:
- The exact same syntax and grammar
- The exact same semantics
- The exact same standard library
- The shared `ZenValue` universal tagged-union ABI

---

## 3. Language Design Directives

### 3.1 Visual Data Flow
- Assignment binds value into target (`->`): `total -> 100 + 50`
- Function return emits outward (`<-`): `<- total`

### 3.2 Explicitness Over Implicit Magic
Zenlang avoids:
- Hidden control flow
- Silent type coercions
- Implicit variable capture

What a program does is immediately obvious from reading the source code.

### 3.3 Practical Optional Typing
Zenlang supports optional static typing. Types exist to improve correctness, documentation, and tooling without hindering rapid scripting or prototyping.

### 3.4 Structured Concurrency
Zenlang favors structured concurrency (tasks, channels, fibers, synchronization primitives) over unconstrained threading, avoiding shared mutable state by default.

---

## 4. Closing Principle

Zenlang exists to help developers build reliable, useful tools simply, using abstractions that respect both the machine and the human.

*Zenlang is calm.*  
*Zenlang is deliberate.*  
*Zenlang is Unix.*