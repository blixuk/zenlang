
# Zenlang Code Processing Pipeline

Zenlang source code can be **interpreted** or **compiled**. Both modes share a common front-end and post-processing pipeline, diverging only at the final execution stage.

---

## 1. Preprocessing Phase

**Purpose:** Load source files, resolve dependencies, and construct a unified AST.

### 1.1 Loading

* Read the entry file into memory.
* Normalize line endings and encoding (e.g., UTF-8).
* Associate file metadata:

  * File ID
  * Absolute / canonical path
  * Source text

### 1.2 Include Resolution

* **Purpose:** Inject code from other files directly into the current file context (Code Composition).
* Includes are resolved in **FIFO order** (Order of Appearance).
* **Processing:**
  1. Parser encounters `include "file.zl"`.
  2. Compiler pauses current file.
  3. Loads, lexes, and parses the included file.
  4. Merges the included AST into the current stream.
  5. Resumes current file.
* **Cycle Detection:**
  * Track active include stack.
  * Error on recursion.

**Example internal structure:**

```text
IncludeNode {
    id
    parent_id
    file_path
    ast_fragment
}
```

### 1.3 Lexing

* Convert source text into a token stream.
* Each token includes:

  * Type
  * Value
  * Source location (file ID, line, column)
* Lexing is performed **per include file**, not globally.

### 1.4 Parsing

* Convert tokens into an **Abstract Syntax Tree (AST)**.
* Each include produces its own AST fragment.
* AST nodes retain:

  * Source span
  * Include/file ID
* **Result:** A cohesive, but unresolved, AST containing all included code. Note that `import` statements remain as `ImportNodes` for the next phase.

---

## 2. Postprocessing Phase

**Purpose:** Validate, analyze, and optimize the unified AST.

---

### 2.1 Dependency Resolution (Imports)

**Purpose:** Resolve logical dependencies and build the build graph.

* **Import Discovery:**
  * Scan AST for `ImportNode`.
  * Resolve module paths to file paths (using `modules.md` logic).
* **Tree Shaking & Graph Building:**
  * Build a **Dependency Graph** starting from `main`.
  * Determine which symbols (function, classes) are actually referenced.
  * Prune unused modules or symbols (if optimizing).

### 2.2 Checking

#### 2.1.1 Structural Validation

* Ensure AST invariants hold:

  * No malformed nodes
  * Correct parent/child relationships
  * Valid control flow constructs

#### 2.1.2 Semantic Analysis

* Name resolution

  * Variables
  * Functions
  * Classes
  * Modules
* Scope management

  * Global
  * Local
  * Class-level
* Detect semantic errors:

  * Undefined symbols
  * Duplicate definitions
  * Invalid access (private/protected rules if applicable)

#### 2.1.3 Type Checking

* Infer or verify types:

  * Static (for compiled mode)
  * Optional / deferred (for interpreted mode)
* Validate:

  * Function signatures
  * Operator compatibility
  * Assignments
  * Return types
* Annotate AST nodes with resolved types.

---

### 2.2 Optimization

Optimizations operate on the validated AST.

#### 2.2.1 Dead Code Elimination

* Remove:

  * Unreachable branches
  * Unused variables/constants
  * Functions/classes never referenced (configurable)

#### 2.2.2 Constant Folding

* Evaluate compile-time expressions:

```zenlang
const x = 2 + 3 * 4  // becomes 14
```

#### 2.2.3 Constant Propagation

* Replace variables with known constant values where safe:

```zenlang
const a = 10
b = a + 5  // becomes 15
```

---

### 2.3 Code Generation (Compiler Path Only)

* Transform optimized AST into a lower-level intermediate representation (IR) or target code.
* Possible targets:

  * C (Zen Runtime) (Current)
  * LLVM IR (Future)
  * Native assembly (Future)
  * Bytecode (VM-based execution) (Zen Virtual Machine) (Future)

* Preserve debug metadata if enabled.

### 2.4 Linking (Compiler Path)

**Purpose:** Combine generated artifacts into final output.

* **Symbol Resolution:** Connect references between different compilation units (if compiled separately).
* **Runtime Linking:** Link against the Zen Runtime (C standard library wrappers, GC, etc.).
* **Output:**
  * Final Executable / Binary.
  * Shared Library.

---

## 3. Execution Phase

### 3.1 Interpretation

* Walk the optimized AST directly.
* Use:

  * Runtime environment
  * Stack frames
  * Heap objects
* Type checks may occur at runtime depending on configuration.

### 3.2 Compilation

* Compile generated output into:

  * Executable
  * Library
  * Bytecode package
* Optional:

  * JIT compilation
  * Ahead-of-time (AOT) compilation

---

## Suggested Internal Architecture (High-Level)

```text
Source Files
    ↓
Preprocessor (Includes, Lexing, Parsing)
    ↓
Unified AST
    ↓
Semantic + Type Analysis
    ↓
AST Optimizer
    ↓
 ┌───────────────┬───────────────┐
 │ Interpreter   │ Compiler      │
 │ AST Executor  │ Code Generator│
 └───────────────┴───────────────┘
```

---

## Notes & Recommendations

* Keep **AST immutable** after validation; produce transformed copies during optimization.
* Maintain a clear separation between:

  * Front-end (parsing, semantics)
  * Middle-end (optimization)
  * Back-end (execution or codegen)
* Design the pipeline so the **interpreter and compiler share as much logic as possible**.

