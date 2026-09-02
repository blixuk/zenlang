# Zenlang Memory Model & Scoped Resource Management

| Attribute | Value |
|:---|:---|
| **Role** | Memory Architecture & Systems Resource Specification |
| **Authority** | Definitive Reference for Memory Management and Arenas |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

Zenlang combines automatic memory management for daily scripting with zero-overhead **Scoped Memory Arenas** (`with Arena.create()`) for high-throughput systems programming and deterministic resource cleanups.

---

## 2. Resource Management Modes

### 2.1 Automatic Reference Tracking
By default, all heap objects (strings, lists, maps, structures, objects, and classes) allocated in standard scopes are automatically tracked and safely reclaimed by the runtime when their bindings exit scope.

### 2.2 Scoped Memory Arenas (`with`)
For high-performance algorithms, batch compilers, or game loops, Zenlang provides scoped memory arenas via the `with` statement.

```zl
use zen.memory as Memory

with Memory.Arena.create(1024 * 1024) as arena {
    // All allocations within this block are drawn from the arena's contiguous memory pool
    let buffer -> Memory.alloc_in(arena, 4096)
    
    // Perform intensive, temporary heap operations...
}
// Upon block exit, the entire arena is reset in O(1) time with zero fragmentation
```

### 2.3 Scoped I/O & File Handles
The `with` statement guarantees deterministic cleanup for operating system resources:

```zl
use zen.io.file as file

with file.open(`data.zd`) as f {
    let content -> file.read_all(f)
    process(content)
} // File descriptor is guaranteed to close immediately upon block exit
```

---

## 3. Container Memory Tiers

Zenlang defines three distinct memory layouts for data structures:

| Container Tier | Memory Layout | Allocation | Semantics |
|:---|:---|:---|:---|
| **`structure`** | Contiguous flat memory matching C ABI | Stack / Arena / Flat Heap | Value semantics, no pointer indirection |
| **`object`** | Dynamic hash map with shape transition table | Heap / Managed | Identity semantics, dynamic field addition |
| **`class`** | Vtable pointer + instance field array | Heap / Managed | Nominal reference semantics, single inheritance |

---

## 4. String Interning & Immutability

1. **UTF-8 Buffers:** Strings in Zenlang are UTF-8 byte buffers.
2. **String Deduplication:** String literals and identifier symbols are interned in a global symbol table to enable fast $O(1)$ pointer comparison.
3. **Immutable Semantics:** Strings are immutable; modifying operations (such as `++` and `--`) produce new strings or mutate explicitly allocated mutable buffers.

---

## 5. Task Fibers & Channel Memory

Zenlang's concurrency substrate avoids expensive 2MB OS thread stacks by using lightweight runtime fibers:
- **Fiber Stacks:** Allocated in small, dynamically growing chunks (starting at 4KB).
- **Channels:** Pre-allocated circular ring buffers with zero lock contention on M:N fiber handoffs.
- **Task Groups (`with task_group`):** Child task fiber allocations are anchored to the parent task group and deterministically freed upon group exit.

---

## 6. Systems Pointers & Buffers (`zen.memory`)

For low-level C interop, hardware interfacing, or custom memory structures, `zen.memory` provides safe pointer wrappers:

| Primitive | Description |
|:---|:---|
| **`Arena`** | Contiguous memory chunk chain with bulk allocation and $O(1)$ reset |
| **`Buffer`** | Fixed-capacity byte slice with direct read/write primitives |
| **`Pointer`** | Foreign memory address wrapper with bounds-checked access |

