# Zenlang Language & Platform Roadmap

This document outlines the strategic roadmap for Zenlang's language evolution, compiler architecture, runtime systems, and developer tooling.

Zenlang's development follows three core design tenets:
1. **Directional Visual Flow**: Code reflects how data moves through assignments (`->`), returns (`<-`), pipelines (`|>`), and transformations.
2. **Explicitness over Magic**: Clear semantics, deterministic memory management, and transparent control flow without hidden control transfer.
3. **Unix-Native Power**: Native performance, first-class terminal interfaces, robust process orchestration, and seamless C interoperability.

---

## 1. Current Baseline (Completed Milestones)

| Area | Feature / Capability | Status |
| :--- | :--- | :--- |
| **Dual Execution Engine** | Seamless execution across interpreter VM and native `-g` C AOT compiler with 100% feature parity. | ✅ Shipped |
| **Directional Guards & Concise Syntax** | `function f(x) <- expr`, `task t(x) <- expr`, and guard returns `when cond <- expr` / `or <- expr`. | ✅ Shipped |
| **Extended Flow Operators** | `++` (append/prepend/concatenate) and `--` (drop end/start/decrement) across strings, lists, and numbers. | ✅ Shipped |
| **Document Publishing Engine** | Zen Mark (`zenmark`) vector PDF generator with TOC, Callouts, Flow Diagrams, Table Zebra Shading, and 6 Themes (including official Arctic Nord Dark). | ✅ Shipped |
| **Terminal & TUI Engine** | `zen.ui.canvas`, `zen.ui.table`, `zen.ui.spinner`, ANSI raw terminal control, and mouse/keyboard event loops. | ✅ Shipped |
| **Task Concurrency Model** | Fibers, channels, WaitGroups, mutexes, task pools, async combinators, and timeouts. | ✅ Shipped |
| **Reflection & Plugin System** | Dynamic reflection (`zen.reflect`), `is reflectable` types, method registration thunks, and runtime plugin loading. | ✅ Shipped |
| **Flow Operators & Slicing** | Null-coalescing (`??`), directional pipeline (`\|>`), negative indexing (`[-1]`), and interval slicing (`[start:end:step]`). | ✅ Shipped |
| **Directional Comprehensions & Spreads** | Directional comprehensions (`[for x in iter -> expr]`, `{for k, v in iter -> k: v}`) and collection spreads (`...list`, `...map`) with 100% execution parity. | ✅ Shipped |
| **Zero-Wrapper C Interop & FFI** | Direct C system header imports (`extern use`), dynamic library loader (`zen.sys.ffi`), and zero-glue system modules (`zen.sys.hardware`, `zen.sys.meminfo`, `zen.sys.termposix`). | ✅ Shipped |
| **Version 1 Beta (`v1.0.0-beta.1`) Platform** | Standalone single-binary `bin/zen` developer platform with Stage 2 native self-hosting closure and complete Python bootstrap retirement. | ✅ Shipped |

---

## 2. Milestone 1: Directional Ergonomics & String Systems

Focus: Eliminating boilerplate in string formatting, slicing, data pipelines, and text extraction.

### 1.1 Formatted F-Strings (`f`...``) & Template Strings (`t`...``)
- **Motivation**: Explicitness over magic. Unprefixed backtick strings (`` `...` ``) remain raw and literal, ensuring zero accidental interpolation in raw text, regexes, or Zen Mark markup (such as `{{code}}`).
- **Formatted F-Strings (`f`...``)**: Eagerly evaluates expressions inside `{expr}` and concatenates them:
  ```zen
  let user -> "Alice"
  let score -> 95
  let msg -> f`Player {user} scored {score} points (Grade: {calc_grade(score)})`
  ```
- **Template Strings (`t`...``)**: Produces a deferred, reusable `Template` object:
  ```zen
  let card_tpl -> t`Card for {name}: Status is {status}`
  let rendered -> card_tpl.render({ `name` -> `Alice`, `status` -> `Active` })
  ```

### 1.2 Python-Style Slicing for Strings & Lists (`[start:end:step]`)
- **Motivation**: Ergonomic, intuitive slicing for strings and lists with negative indexing and stepping.
- **Syntax**:
  ```zen
  let s -> `Zenlang`
  let items -> [10, 20, 30, 40, 50]

  // Substring & sublist slicing
  s[0:3]       // "Zen"
  items[1:4]   // [20, 30, 40]

  // Open-ended slices
  s[3:]        // "lang"
  s[:3]        // "Zen"
  items[:2]    // [10, 20]

  // Negative indexing (from end)
  s[-1]        // 'g'
  s[:-1]       // "Zenlan"
  items[-1]    // 50
  items[:-1]   // [10, 20, 30, 40]

  // Stepping & reversal
  s[::-1]      // "gnalneZ"
  items[::-1]  // [50, 40, 30, 20, 10]
  ```

### 1.3 Nullish / Sentinel Coalescing Operator (`??`)
- **Motivation**: Simplify accessing optional fields in dynamic maps and sentinel fallbacks.
- **Syntax**:
  ```zen
  let title -> opts.title ?? `Untitled`
  let timeout -> config.timeout ?? 30
  ```
- **Semantics**: Evaluates the left operand; if it is `Nothing`, evaluates and returns the right operand.

### 1.4 Directional Pipeline Operator (`|>`)
- **Motivation**: Complete Zen's visual directional flow for multi-step data transformations without deeply nested function calls.
- **Syntax**:
  ```zen
  let clean_output -> raw_text
      |> Str.trim
      |> Str.to_lower
      |> Str.replace(`\r\n`, `\n`)
  ```
- **Semantics**: `x |> f` evaluates to `f(x)`, and `x |> f(y)` evaluates to `f(x, y)`.

---

## 3. Milestone 2: The Zen Trinity & `zen.text` Ecosystem Integration

Focus: Unifying computation (**Zen Code**), structured data (**Zen Data**), and rich communication (**Zen Mark**).

```
                 ┌──────────────────────────────────────┐
                 │       The Zen Ecosystem Trinity      │
                 └──────────────────┬───────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
 ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
 │   Zen Code    │           │   Zen Data    │           │   Zen Mark    │
 │    (.zl)      │           │    (.zd)      │           │    (.zm)      │
 ├───────────────┤           ├───────────────┤           ├───────────────┤
 │  Computation  │           │   Structure   │           │ Communication │
 │ - 3-Layer VM  │           │ - AST Caching │           │ - Doc Comments│
 │ - Native AOT  │           │ - Config/IPC  │           │ - zendoc / Man│
 │ - Tooling/LSP │           │ - Package ZD  │           │ - Vector PDF  │
 └───────────────┘           └───────────────┘           └───────────────┘
```

### 2.1 Zen Data (`.zd`) in the Compiler & Runtime
- **AST Caching (Incremental Selfhost Rebuilds)**: Serializing parsed ASTs into `.zd` caches so untouched modules deserialize instantly during `--multi` builds.
- **Project & Package Manifests (`zen.zd` / `pkg.zd`)**: Native Zen data configuration replacing JSON/TOML/YAML.
- **IPC & Task Message Passing**: Serializing `ZenValue` state across fiber channels, processes, and Unix sockets.

### 2.2 Zen Mark (`.zm`) & Compiler Tooling (`zendoc`)
- **Doc-Comment API Extraction (`zendoc`)**: Extracting `/! ... !/` doc comments from `.zl` sources to compile interactive terminal man-pages (`zen doc <mod>`), HTML references, and PDF monographs.
- **Compiler Diagnostic Callouts**: Formatting compiler errors with Zen Mark callout badges (`Note`, `Warning`, `Caution`) and source frames.
- **`zen.text` Linguistic Bridge**:
  - `zm.Document.from_book(book, opts)`: 1-line conversion of `Book` / `Chapter` / `Paragraph` structures directly to vector PDF/HTML.
  - `zm.Document.to_book(doc)`: Extracts pure semantic text for word counts and readability analysis.
  - `Str.dedent(text)`: Strips baseline indentation from embedded Zen Mark and multiline code strings.
  - `Str.slugify(text)`: Generates clean anchor IDs for headings and internal PDF links.

### 2.3 Zen Code (`zencode` / `zen.tooling`)
- **Canonical Code Formatter (`zen fmt`)**: Standardizes `->` assignments, `<-` returns, and block indentations.
- **Syntax Highlighter & REPL**: Colorizes stack traces, diagnostics, and interactive terminal sessions.
- **LSP Daemon**: Language server backend powering hover docs, autocomplete, and diagnostics in VS Code, Zed, and Sublime.

---

## 4. Milestone 3: Type System & Required Surface (Host 1.0 / Phase L)

Focus: Formalizing sentinels and type zero-states before self-host compiler graduation.

### 3.1 `Default` Sentinel Materialization
- **Motivation**: Distinguish absent values (`Nothing`) from type zero-states (`Default`).
- **Materialization Table**:
  - `Integer` $\rightarrow$ `0`
  - `Decimal` $\rightarrow$ `0.0`
  - `Boolean` $\rightarrow$ `False`
  - `String` / `Rune` $\rightarrow$ `""`
  - `List` $\rightarrow$ `[]`
  - `Map` $\rightarrow$ `{}`
  - Structure / Class $\rightarrow$ Zero-initialized field instance.
- **Comparison Semantics**:
  ```zen
  let count : Integer -> Default   // Initialized to 0
  when count == Default {
      // True when count equals its type zero-value (0)
  }
  ```

### 3.2 Canonical PascalCase Sentinels
- Enforce `Nothing`, `Default`, `True`, `False` across all language specifications and stdlib sources, deprecating legacy lowercase variants.

---

## 5. Milestone 4: Pattern Matching & Structured Data

Focus: Expressive destructuring and type-safe tagged union handling.

### 4.1 Tagged Union / Enum Payload Binding (`is`)
- **Syntax**:
  ```zen
  when response {
      is Result.Ok(data) <- process_payload(data)
      is Result.Err(err_msg) {
          io.error(f`Request failed: {err_msg}`)
          <- -1
      }
  }
  ```

### 4.2 Tuple & Multi-Return Destructuring
- **Syntax**:
  ```zen
  function divmod(a, b) <- (a / b, a % b)

  let (quotient, remainder) -> divmod(10, 3)
  ```

### 4.3 Struct & Map Pattern Destructuring
- **Syntax**:
  ```zen
  let Point { x, y } -> get_cursor_position()
  let { title, author, ...extra } -> metadata_map
  ```

---

## 6. Milestone 5: Collections & Metaprogramming (✅ Shipped in `v1.0.0-beta.1`)

### 5.1 Directional List & Map Comprehensions
- **Status**: ✅ Shipped with 100% parity across C runtime, selfhost C Codegen, Bytecode VM, and Interpreter.
- **Syntax**:
  ```zen
  // List comprehension
  let squares -> [for x in 1...10 when x % 2 == 0 -> x * x]

  // Map comprehension
  let id_map -> {for u in users -> u.id: u.name}
  ```

### 5.2 Collection Spread & Deep Merge
- **Status**: ✅ Shipped across lists and maps.
- **Syntax**:
  ```zen
  let base_config -> { `timeout` -> 30, `retries` -> 3, `debug` -> False }
  let user_config -> { ...base_config, `debug` -> True, `host` -> `localhost` }
  ```

---

## 7. Milestone 6: Three-Layer Self-Hosting Architecture

Tracked in detail under [selfhost/ENDGAME_PLAN.md](file:///home/blix/.grok/worktrees/2025-zen/zen/selfhost/ENDGAME_PLAN.md) and [selfhost/THREE_LAYER.md](file:///home/blix/.grok/worktrees/2025-zen/zen/selfhost/THREE_LAYER.md):

1. **Layer 1: Universal ZenValue ABI**: Language values and inter-module calling conventions shared between compiled C binaries and interpreted scripts.
2. **Layer 2: Native Compiler AST/IR**: High-speed native structs in self-hosted compiler sources (`selfhost/compiler/`) replacing Python bootstrap dictionary nodes.
3. **Layer 3: Bytecode Script VM**: Instant startup script execution VM without dependency on Python or external toolchains.
4. **Bootstrap Retirement**: Full transition of `bin/zen` router to the standalone self-hosted compiler binary.

---

## 8. Priority & Implementation Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ Immediate Priority: Milestone 1 & 2                         │
│  ├─ 1.1 Formatted F-Strings (`f`...``) & Templates (`t`...``)│
│  ├─ 1.2 Python-Style Slicing (`s[start:end:step]`)          │
│  ├─ 1.3 Nullish Coalescing (`??`)                           │
│  ├─ 1.4 Pipeline Operator (`|>`)                            │
│  └─ 2.1 Zen Text & Zen Mark Bridge (`from_book`, `dedent`)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Near-Term Priority: Milestone 3 (Required Surface)          │
│  ├─ 3.1 Default Zero-State Materialization (Phase L)        │
│  └─ 3.2 PascalCase Sentinels (Nothing, Default)             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Medium-Term Priority: Milestone 4 & 5 (Patterns & Collects) │
│  ├─ 4.1 Enum Payload Pattern Matching: `is Ok(val)`         │
│  ├─ 4.2 Tuple & Struct Destructuring: `let (a, b)`          │
│  └─ 5.1 Directional Comprehensions: `[for x in list -> x*2]`│
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Long-Term Priority: Milestone 6 (Self-Host Stage Graduation)│
│  └─ Pure Self-Hosted Three-Layer Compiler & VM Distribution  │
└─────────────────────────────────────────────────────────────┘
```