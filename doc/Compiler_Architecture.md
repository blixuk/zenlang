# Zenlang Compiler & Execution Architecture

| Attribute | Value |
|:---|:---|
| **Role** | Technical Systems Architecture & Runtime Specification |
| **Authority** | Definitive Guide to the Three-Layer Execution Engine |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Executive Summary

Zenlang employs a **Three-Layer Execution Architecture** engineered to combine the instantaneous feedback of a scripting language with the raw execution speed and standalone deployability of an ahead-of-time compiled systems language.

```
┌─────────────────────────────────────────────────────────────┐
│                       Zenlang Source                        │
│                     (*.zl, *.zd, *.zm)                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌──────────────────────────┐  ┌──────────────────────────┐
   │    Bytecode Script VM    │  │     AOT C Transpiler     │
   │  (Instant execution,     │  │   (Optimized binaries,   │
   │   REPL, dynamic scripts) │  │    zero-dep deployment)  │
   └────────────┬─────────────┘  └────────────┬─────────────┘
                │                             │
                └──────────────┬──────────────┘
                               ▼
            ┌────────────────────────────────────┐
            │          Universal Runtime         │
            │           `ZenValue` ABI           │
            └────────────────────────────────────┘
```

---

## 2. The Three Layers

### Layer 1: Universal `ZenValue` ABI Layer
At the runtime core is `ZenValue`, a 128-bit tagged union that serves as the universal value representation across all execution paths.

- **Data Representation:** Integers, IEEE 754 floats, booleans, strings, lists, maps, structures, functions, and sentinels (`Nothing`, `Default`).
- **Seamless Interop:** Scripts running on the Bytecode VM can directly call AOT-compiled C functions and vice-versa with zero data serialization or marshaling overhead.

### Layer 2: Positional AST Compiler IR
The self-hosted compiler avoids heavy tree structures with dispersed heap allocations in favor of flat, positional token and AST lists.

- **High Cache Locality:** AST nodes are stored in contiguous memory arrays (`[kind, line, col, ...]`).
- **Rapid Compilation:** Parsing and semantic passes traverse flat buffers with minimal pointer chasing.
- **Instant Teardown:** Entire compiler ASTs are allocated inside dedicated memory arenas that are reclaimed in $O(1)$ time.

### Layer 3: Dual Execution Engine
1. **Bytecode Virtual Machine (`zen <file.zl>`):**
   - Compiles AST directly into compact stack-based bytecode instructions.
   - Powers the interactive REPL (`zen repl`), live test runners, and quick scripting.
2. **Ahead-of-Time C Transpiler (`zen build <file.zl>`):**
   - Transpiles AST into clean, standard ISO C99 code.
   - Compiles via GCC/Clang with full `-O3` optimizations into standalone native executables.

---

## 3. Compiler Pipeline Stages

1. **Lexical Analysis (`Lexer.zl`):** Scans UTF-8 source text into token arrays.
2. **Syntactic Parsing (`Parser.zl`):** Constructs positional AST nodes.
3. **Semantic Analysis & Type Checking (`TypeChecker.zl`):** Validates type constraints, struct definitions, and variable scopes.
4. **Code Generation:**
   - **Bytecode Emitter (`Bytecode.zl`):** Generates bytecode chunks with constant pools.
   - **C Codegen (`Codegen.zl`):** Emits optimized C source code with forward declarations and multi-unit support (`--multi`).
5. **Execution / Linking:**
   - VM executes bytecode directly.
   - Native builds link against the shared C runtime (`runtime/libzen_runtime.a`).
