# Purpose

Minimal C runtime support for native Zenlang executables. Provides the object model, memory management, primitive collections, I/O, system bindings, and task primitives that generated C code links against.

# Ownership

Owned by the runtime / native execution layer maintainers.

# Local Contracts

- The runtime is intentionally small. High-level semantics, collections logic, and application code belong in Zenlang stdlib (lib/zen/) or the compiler.
- Entry point: main_wrapper.c calls zen_entry() (provided by generated code).
- Default implementations live in *_default.c (io, sys, memory/allocator).
- Object model (zen_object, zen_value, variant, list/string) in object/.
- Task/fiber support foundations in concurrency/zen_task.* (enables the "Everything is a Task" model).
- Runtime is referenced by Makefile and copied into build/ and bootstrap/Transpiler/runtime/ for linking and bootstrap self-use.
- Public interface via zen_*.h headers.

# Work Guidance

- Use zen_ prefix for symbols.
- Keep changes minimal and ABI-stable where possible.
- When extending (e.g. more task primitives), coordinate with transpiler codegen and stdlib Task usage.
- Default impls can be swapped for platform-specific in the future.

# Verification

- Successful `make` linking and execution of generated binaries.
- tests/memory/* (manual arena, promotion, shared ref, etc.).
- native_compiler/ and runtime_contract tests.
- Feature parity and smoke tests that exercise native execution.

# Child DOX Index

- main_wrapper.c: Thin host main.
- io/: zen_io.h + io_default.c
- memory/: allocator_default.c
- object/: string.c, list.c, value.c + headers
- sys/: sys_default.c + zen_sys.h
- concurrency/: zen_task.* (task model primitives)
- Note: bootstrap_runtime.* and build/ copies are build artifacts / vendored snapshots.
