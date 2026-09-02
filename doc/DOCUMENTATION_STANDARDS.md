# Zenlang Documentation Standards & Style Guide

**Status:** Canonical Standard  
**Authority:** All documentation under `doc/` and throughout the Zenlang repository must adhere strictly to this standard.

---

## 1. Core Principles

The Zenlang documentation suite must reflect the same values as the language itself: **clarity, precision, visual ergonomics, and explicitness**. Documentation is not an informal scratchpad; it is the official record of the language contracts.

### Rule 1: Single Source of Truth (`doc/SPECIFICATION.md`)
- `doc/SPECIFICATION.md` is the **sole immutable source of truth** for Zenlang syntax, grammar, types, execution semantics, and memory models.
- Tutorial guides (`Getting_Started.md`), reference manuals, standard library docs, book chapters, and tooling guides **must derive directly from and link to `SPECIFICATION.md`**.
- No document may introduce, invent, or describe syntax, operators, or keywords that have not been formally accepted and documented in `SPECIFICATION.md`.

### Rule 2: Gated Syntax Changes via RFCs (`doc/proposals/`)
- Any proposed modification, enhancement, or addition to the Zenlang language syntax, operators, type system, or core semantics **must** be proposed as an RFC under `doc/proposals/` using `TEMPLATE.md`.
- No experimental syntax may be documented as "canonical" until the RFC has reached the **Accepted & Canonized** state.

### Rule 3: 100% Valid & Runnable Examples
- Every code snippet in documentation must be syntactically valid, idiomatic Zenlang.
- Snippets must use the canonical visual data flow (`->` for assignment, `<-` for return/emit).
- Standard sentinels must always be written in canonical capitalized form: **`Nothing`** and **`Default`** (never lowercase `nothing` or `default`).
- Collections must use standard syntax: `[1, 2, 3]` for Lists and `{ key -> value }` for Maps. Never use deprecated bracket prefixes like `[List]{...}` or `{ 1, 2, 3 }` for lists.

---

## 2. Document Structure & Metadata Header

Every top-level markdown document in `doc/` must begin with a standardized metadata block:

```markdown
# Document Title

| Attribute | Value |
|:---|:---|
| **Role** | [e.g. Formal Language Specification / Practical Tutorial / Architecture Guide] |
| **Authority** | [e.g. Canonical Source of Truth / Derived Tutorial / Proposal] |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Target Execution** | Dual-Path (Bytecode Script VM & Native C AOT via `ZenValue` ABI) |
```

---

## 3. Formatting & Typography Standards

### 3.1 Code Blocks
- Always specify the `zl` language identifier for Zenlang syntax blocks:
  ````markdown
  ```zl
  let message : String -> `Hello, Zenlang!`
  io.writeln(message)
  ```
  ````
- Use `bash` for shell commands and CLI examples.
- Use `c` for runtime C code or transpiled output.

### 3.2 GitHub Flavored Markdown Alerts
Use alerts to emphasize critical context. Never nest alerts inside tables or other quotes:

> [!NOTE]
> Explains background context, historical decisions, or implementation notes.

> [!TIP]
> Best practices, performance optimizations, or idiomatic patterns.

> [!IMPORTANT]
> Essential language contracts, mandatory rules, or critical requirements.

> [!WARNING]
> Prohibited behaviors, breaking changes, or invalid syntax.

### 3.3 Tables for Comparative & Structured Data
Use standard markdown tables with aligned headers for:
- Type cast matrices
- Operator precedence tables
- CLI command references
- Standard library package indexes

---

## 4. Canonical Terminology Canon

To eliminate confusion across documentation, use the exact canonical terms:

| Canonical Term | Prohibited / Deprecated Term | Reason |
|:---|:---|:---|
| **`Zenlang`** (or **`Zen`**) | *ZenScript*, *ZenLang* (mixed case), *ZS* | The language is officially named Zenlang (or Zen). |
| **`.zl`** | *.zs* (ZenScript file) | Single unified `.zl` extension for all scripts, libraries, and applications. |
| **`Nothing`** | *nothing*, *null*, *nil*, *None* | `Nothing` is the canonical capitalized sentinel for absent values. |
| **`Default`** | *default* (lowercase), *zero* | `Default` is the canonical capitalized sentinel for type zero-states. |
| **`->` (bind / assign)** | *assignment equals*, *=* | Zenlang uses visual data flow `->` for binding. |
| **`<-` (return / emit)** | *return keyword* | Zenlang uses visual return arrow `<-`. |
| **`when ... or`** | *if / else if / else* | Zenlang's conditional construct is `when`. |
| **`check ... or`** | *try / catch*, *except* | Structured recovery uses `check`. |
| **`Three-Layer Architecture`** | *MIR half-port*, *VM-only* | (1) `ZenValue` ABI, (2) Positional AST IR, (3) Script VM + C AOT. |
| **`[1, 2, 3]`** | *`[List]{1, 2, 3}`*, *`{ 1, 2, 3 }`* | Lists are cleanly delimited with square brackets. |
| **`{ key -> value }`** | *`[Map]{...}`* | Maps are delimited with curly braces and arrow bindings. |

---

## 5. Maintenance Checklist for Document Updates

When creating or modifying any document:
1. Verify all syntax examples against `doc/SPECIFICATION.md`.
2. Confirm all links use relative paths with `.md` extension.
3. Check that the document is indexed in `doc/AGENTS.md` (Child DOX Index).
4. Run `./scripts/zen test` and `./scripts/zen ci` to verify that doc changes haven't broken any tests.
