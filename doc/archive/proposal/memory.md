## Zenlang Memory Architecture: Implementation Proposal

### 1. Architecture Objective
To implement a zero-pause, deterministic memory management system for Zenlang that prioritizes compile-time resource scheduling over runtime garbage collection. The system will bridge the high-level Abstract Syntax Tree (AST) and the low-level C/LLVM backend using a Two-Tier Intermediate Representation (S-MIR and L-MIR).

### 2. Phase 1: The Region Graph & Type System Upgrade
Before we can generate memory instructions, the compiler must understand the exact hierarchical lifetime of every scope and the ownership state of every variable.

* **Deliverable 1.1: The Region Tree Builder**
    * Implement the `RegionNode` class to track parent-child scope relationships.
    * Update the `TypeChecker` / `ScopeManager` to push and pop `RegionNode` instances as it traverses functions, blocks, and loops.
* **Deliverable 1.2: Symbol State Tracking**
    * Extend the `Symbol` class in the symbol table to include `memory_kind` (`unique`, `shared`, `region`, `stack`) and `state` (`valid`, `moved`).
    * Implement the `outlives(region_a, region_b)` algorithm to determine if an allocation in Region A can safely be referenced in Region B.

### 3. Phase 2: Semantic MIR (S-MIR) Generation
Translate the AST into a linear stream of high-level, intent-based instructions that include explicit control flow.

* **Deliverable 2.1: S-MIR Instruction Set**
    * Define Python dataclasses for S-MIR: `Alloc(target, region)`, `Move(dest, src)`, `Borrow(dest, src)`, `Promote(target, new_region)`, `RegionEnter(id)`, `RegionExit(id)`.
    * Define Control Flow S-MIR: `Label(name)`, `Jump(target)`, `Branch(cond, true_lbl, false_lbl)`.
* **Deliverable 2.2: AST to S-MIR Lowering**
    * Create an `SMIRGenerator` visitor pass. This pass walks the typed AST and emits the initial S-MIR instructions, assuming naive, localized allocations.

### 4. Phase 3: Static Analysis & Optimization Passes
This is where Zenlang performs its "magic," turning naive allocations into highly optimized, safe memory operations.

* **Deliverable 3.1: The Promotion & Escape Analysis Pass**
    * Walk the S-MIR. When a value is assigned to a target in a broader region (determined by the Region Graph), rewrite the original `Alloc` instruction to target the parent region.
    * Strip all `Promote` instructions out of the S-MIR.
* **Deliverable 3.2: Control-Flow Move Validation**
    * Implement a dataflow analysis pass over the S-MIR control flow graph.
    * If a symbol is marked as `moved` on a specific execution path, and a subsequent instruction attempts to read it, halt compilation and throw a `Use-After-Move` error.

### 5. Phase 4: Lowered MIR (L-MIR) & C Code Generation
Translate the optimized S-MIR into hardware-adjacent instructions, resolving all scope closures into explicit `reset` or `free` calls.

* **Deliverable 4.1: S-MIR to L-MIR Lowering**
    * Map `Alloc` -> `ArenaAlloc` or `HeapAlloc`.
    * Map `RegionEnter` -> `ArenaCreate`.
    * Split `RegionExit` -> `ArenaReset` (if loop scope) or `ArenaFree` (if function/block scope).
    * Map `Move(dest, src)` -> `PointerCopy(dest, src)` + `Nullify(src)`.
* **Deliverable 4.2: The C Backend Emitter**
    * Update the existing C string generator to consume L-MIR sequentially. 
    * Write the corresponding lightweight C runtime macros (`zen_arena_create`, `zen_arena_reset`, `zen_arena_free`) that the generated code will link against.

---

### Implementation Strategy & Timeline

I recommend building this **outside-in**. We should start by modifying your core data structures (The Symbol Table and TypeChecker) because everything downstream relies on accurate lifetime and state information. Once the compiler "knows" what a variable's lifetime is, emitting the MIR becomes a mechanical process.