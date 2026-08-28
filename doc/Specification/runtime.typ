#import "template.typ": *

= Runtime & Memory Architecture

The Zenlang execution environment consists of the shared C runtime (`runtime/`), the dual execution pipeline, and the standard library (`lib/zen/`).

== Dual Execution Pipeline

Zenlang executes in two complementary modes:

=== 1. Interpreter Pipeline
- AST / Bytecode evaluation
- Instant startup for scripts and interactive terminal tools
- Zero compilation overhead

=== 2. Native C Pipeline (`-g`)
- AST analysis and type propagation
- Translation into structured C code linking `runtime/zen_runtime.h`
- Direct C compiler invocation (`gcc` or `clang` with `-O3`)
- Output: standalone, zero-dependency native executable

== Memory Management Model

1. *Automatic Managed Lifetime (Default)*: Values in Zenlang are automatically managed by the runtime environment.
2. *Opt-in Memory Regions*: Sensitive systems paths can allocate within scoped memory arenas (`with zen.memory.Region`) for deterministic bulk allocation and deallocation without GC pauses.
3. *Snapshot-by-Value Isolation*: Variable state transferred across concurrent tasks is snapshotted by value, ensuring memory safety.

== Standard Library Hierarchy (`lib/zen/`)

The standard library is organized into nested functional namespaces:

#table(
  columns: (1.5fr, 3fr),
  [Package], [Domain & Capabilities],
  [`zen.io`], [Console I/O, formatted output, stream readers],
  [`zen.io.file`], [File system operations, read/write utilities],
  [`zen.text.string`], [UTF-8 string manipulation, splitting, pattern searches],
  [`zen.math.math`], [Mathematical functions, trigonometric, statistical],
  [`zen.sys.term`], [Terminal raw mode, ANSI canvas, cursor positioning],
  [`zen.sys.process`], [Process pipelines, shell execution, subprocess streams],
  [`zen.ui.table`], [Unicode border tables, column formatting],
  [`zen.ui.spinner`], [Terminal loading animations, spinner widgets],
  [`zen.reflect`], [Runtime introspection, type discovery],
  [`zen.test`], [Unit testing framework, assertion suites]
)
