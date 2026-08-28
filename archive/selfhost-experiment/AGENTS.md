# Purpose

In-progress modern, phase-separated Self-Hosted Zenlang compiler written in Zenlang (using current language idioms). Currently implements Lexer + partial Parser + skeletal Transpiler. Goal is to become the canonical self-hosted compiler and eventually replace `src/compiler/`.

# Ownership

Owned by the self-hosting effort.

# Local Contracts

- `main.zl` is the entry point driver (lex + parse + C generation via handlers).
- Modular handler split: `Parser/Handlers/` and `Transpiler/Handlers/` (StatementHandler + ExpressionHandler).
- Uses modern patterns: `check` / `or` for dispatch, `when`, dataflow where practical.
- Vendored copy of runtime/ for potential native builds of the compiler.
- Not yet wired into primary `make selfhost-regen` (which uses `src/compiler/` sources).

# Work Guidance

- Implement parser construction methods (let_declaration, function_declaration, etc.) and expression node building first.
- Port emission logic in Transpiler handlers to produce C compatible with runtime/ (study bootstrap/Transpiler/ and src/compiler/CTranspiler.zl for reference).
- Keep AST structures and TokenTypes in sync with bootstrap and src/ versions.
- Add Checker/ and Interpreter/ directories when those phases are ported.

# Verification

- `python3 bootstrap/Zen.py selfhost/main.zl <some.zl> out.c` loads without fatal type errors and produces plausible C for supported constructs.
- Generated C for simple programs compiles and runs (once transpiler is real).
- Later: full parity with src/ components and bootstrap.

# Child DOX Index

- Lexer.zl + Token.zl + AST.zl: Core data models (Lexer substantially complete; keyword classification improved).
- Parser/: Parser orchestrator + Handlers/ (dispatch + many declarations now implemented: let, function (with Parameter), imports, basic when/while/return; expression parsing implemented for literals/vars/calls/binary/grouping).
- Transpiler/: CodeGenerator + Handlers/ (basic emission for functions, blocks, lets, returns, expressions; still produces low-quality C due to node shape and runtime issues during interpreted execution).
- runtime/: Vendored C runtime snapshot (for future self-contained builds).
- Known limitation: interpreted driver read_file + lex of target sources currently produces unexpected token streams in some runs; parser/transpiler logic itself has been advanced.
