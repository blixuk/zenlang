# Zenlang Memory & Security Model

Zenlang eliminates traditional garbage collection (GC) pauses and unpredictable latency spikes by combining **automatic reference management**, **chunk-chained bump arenas**, and **snapshot-by-value concurrency**.

---

## 1. Zero-GC Memory Management Architecture

Zenlang does not rely on a stop-the-world tracing garbage collector. Instead, memory is governed by three complementary tiers:

```
+-------------------------------------------------------------------------+
|                       1. Automatic Reference Tier                       |
|   - Dynamic collections (List, Map, Set) use deterministic cleanup     |
|   - Out-of-scope entities are deallocated immediately upon scope exit   |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       2. Scoped Bump Arena Tier                         |
|   - High-throughput batch processing / compiler passes                  |
|   - Chunk-chained bump allocation (ZenMemory_allocate)                  |
|   - O(1) bulk reclamation upon block exit                               |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       3. Short-String Interning Tier                    |
|   - Strings of length 1 to 32 bytes are interned globally               |
|   - Zero-allocation string comparisons and instant map hashing          |
+-------------------------------------------------------------------------+
```

---

## 2. Scoped Bump Arenas (`with memory.create_arena`)

For intensive processing loops, compiler pipelines, or temporary batch transformations, Zenlang provides first-class memory arenas via `zen.memory`:

```zen
import zen.memory as memory
import zen.io.io as io

function process_telemetry(batches) {
    // 32MB arena created on entry, freed in O(1) on block exit
    with memory.create_arena(32 * 1024 * 1024) as arena {
        do for batch in batches {
            let transformed -> parse_and_filter(batch)
            emit_telemetry(transformed)
        }
    }
}
```

### Arena Lifecycle Rules
1. **Push on Entry:** Entering a `with arena` block pushes the arena onto the runtime thread's allocation stack.
2. **Bump Allocation:** All memory allocations (`ZenRuntime_allocate`) inside the block are satisfied by fast pointer bump increments.
3. **Pop and Free on Exit:** Exiting the block restores the previous memory frame and releases the entire arena memory in a single $O(1)$ operation without walking individual objects.

---

## 3. Short-String Interning (1–32 Bytes)

Zenlang automatically interns all short strings with lengths between 1 and 32 bytes in a global string table (`runtime/collections/zen_string_table.c`).
- **Pointer Equality:** Identical short strings share the same immutable character pointer, allowing string equality (`a == b`) to resolve in a single machine instruction.
- **Fast Hashing:** Map lookups with short string keys execute in sub-nanosecond time.

---

## 4. Snapshot-by-Value Concurrency

Zenlang ensures data-race-free multithreading through **snapshot-by-value semantics**:
- When an asynchronous task or closure captures outer variables, values are deeply copied or snapshotted by value at the point of task creation.
- Tasks execute in isolated memory states and communicate exclusively through CSP-style channels (`zen.sync.chan`).
- Eliminates mutex locks, deadlock vulnerabilities, and race conditions across worker threads.

---

## 5. Security & Safety Guarantees

1. **Zero Implicit Type Coercion:** Strings are never silently coerced to numbers, preventing injection flaws and boundary confusion.
2. **Bounds-Checked Collection Access:** Index operations (`list[i]`, `str[i]`) are bounds-checked at runtime, preventing buffer over-reads or under-reads.
3. **Deterministic Destruction:** Resource handles (files, sockets, database connections) are deterministically closed at block exit.
4. **Predictable Memory Footprint:** Applications run with compact, bounded memory footprints ideal for embedded Linux, containers, and edge microservices.
