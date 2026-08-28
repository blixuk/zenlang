= Getting Started

Welcome to your journey with Zenlang! In this chapter, you will install the language tools, write and run your first Zenlang program, and learn how to use the built-in developer tools.

== Installation

Zenlang uses a centralized driver script located at `./scripts/zen`.

To install the `zen` executable into your local `./bin` directory:

```bash
git clone https://github.com/zenlang/zen.git
cd zen
./scripts/zen install
```

Verify that Zenlang is installed:

```bash
./bin/zen --help
```

== Your First Program: "Hello, Zen!"

Create a new file named `hello.zl`:

```zl
// hello.zl
use zen.io

function main() {
    io.writeln(`Hello, World from Zenlang!`)
    <- 0
}
```

=== Running with the Interpreter

During development, run scripts instantly with the interpreter:

```bash
./bin/zen hello.zl
```

=== Compiling to Native C (`-g`)

Zenlang features *dual execution parity*. The exact same file can be compiled directly into a standalone, optimized native executable:

```bash
./bin/zen -g hello.zl
```

This generates C code, invokes the C compiler (`gcc` or `clang`), links the runtime, and executes the native binary in milliseconds.

== The Interactive Playground

Zenlang includes an interactive terminal code lab with real-time syntax highlighting, templates, and live execution:

```bash
./scripts/zen playground
```

*Playground Shortcuts:*
- *Ctrl+R*: Run code immediately
- *Ctrl+P*: Load standard library template examples
- *Ctrl+E*: Switch execution engine (Interpreter / Native `-g`)
- *Ctrl+S*: Save file
- *Ctrl+Q*: Quit

== The Terminal File Manager (`zenfm`)

To explore your project files, browse directories, and preview `.zl` source files with live syntax highlighting:

```bash
./scripts/zen fm .
```

Press *P* on any `.zl` file to open it directly in the Playground!

== Formatting Code (`zenfmt`)

Zenlang includes an automated style formatter:

```bash
./scripts/zen fmt -w hello.zl
```
