= Dual Execution & The C Runtime

Zenlang is built upon an architecture of *Dual Execution Parity*. Every Zenlang program can run in two complementary modes without changing a single line of code.

== The Two Execution Modes

=== 1. The Interpreter Path
- *Command*: `./bin/zen script.zl`
- *Use Case*: Rapid local development, debugging, interactive scripts, and REPL exploration.

=== 2. The Native AOT Path (`-g`)
- *Command*: `./bin/zen -g script.zl`
- *Use Case*: Production deployments, high-performance CLI tools, standalone binary distribution.

== Under the Hood: C Transpilation & SMIR

When compiling with `-g`, the compiler performs:
1. *Lexical & Parsing*: Builds the Abstract Syntax Tree (AST).
2. *Type Checking & Inference*: Validates variable scopes and type annotations.
3. *SMIR Analyzer*: Converts AST into Structured Machine Intermediate Representation (SMIR), tracking variable lifetimes and move semantics.
4. *C Codegen*: Emits clean, optimized C code linking to the shared C runtime in `runtime/`.
5. *Native Linking*: Invokes `gcc` or `clang` with `-O3` optimizations.

== The Shared C Runtime (`runtime/`)

The C runtime provides:
- *`ZenValue`*: A tagged union representation of all Zenlang types (Integers, Decimals, Strings, Lists, Maps, Functions, Objects).
- *Automated Memory Safety*: Structured reference tracking without pause-the-world garbage collection overhead.
- *Platform Abstraction*: POSIX and Windows terminal abstractions for raw keyboard polling and alt-screen switching.

== The Road to Self-Hosting (`selfhost/`)

The ultimate milestone for Zenlang is full self-hosting:
- Phase 1: Porting Tokenizer & Lexer to Zenlang (`selfhost/compiler/lexer.zl`)
- Phase 2: Porting Parser & AST nodes (`selfhost/compiler/parser.zl`)
- Phase 3: Self-compilation where `selfhost/zen.zl` compiles itself!
