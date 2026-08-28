#import "template.typ": *

= Introduction & Language Philosophy

Zenlang is a modern, optionally typed, Unix-native programming language designed for clarity, visual simplicity, and high-performance execution across scripts, terminal user interfaces, and networked backend services.

== Core Guiding Principles

1. *Visual Data Flow*: Data movement is explicit in the code syntax. Variable binding and assignment use `->` (moving left-to-right into the target), while function returns, yields, and emissions use `<-` (returning outward to the caller).
2. *Explicitness Over Magic*: No hidden type coercions, no implicit variable captures, and no silent conversions. Absence is represented by `Nothing`, and type zero-states are represented by `Default`.
3. *Dual Execution Parity*: Every valid Zenlang program (`.zl`) executes identically in two complementary modes without code changes:
   - *Interpreted Mode*: Direct AST/bytecode execution for instantaneous feedback, debugging, and rapid iteration.
   - *Native Compiled Mode (`-g`)*: Ahead-Of-Time (AOT) transpilation to optimized C and native machine code, linking with the shared C runtime in `runtime/`.
4. *Terminal as a First-Class Citizen*: Sub-millisecond ANSI canvas rendering, 60 FPS redraw capabilities, interactive keyboard polling, and declarative table formatting are standard library primitives.
5. *Snapshot-by-Value Concurrency & Closures*: Captured outer variables are snapshotted by value at instantiation time, eliminating data races without heavy runtime synchronization.
6. *Self-Hosting Architecture*: The language compiler is designed for full self-hosting (`selfhost/`), bootstrapping from a Python reference implementation (`bootstrap/`) toward a native self-hosted toolchain.

== Language File Format

All Zenlang source files use the `.zl` extension and are UTF-8 encoded text files.

#note[
  Zenlang maintains a single unified `.zl` file extension across both interpreted and native execution modes. The previous legacy `.zs` distinction has been superseded by universal `.zl` dual execution.
]
