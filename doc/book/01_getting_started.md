# Chapter 1: Getting Started

Welcome to your journey with Zenlang! In this chapter, you will install the language tools, write and run your first Zenlang program, and learn how to use the built-in developer tools.

---

## 1. Installation

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

---

## 2. Your First Program: "Hello, Zen!"

Create a new file named `hello.zl`:

```zenlang
// hello.zl
use zen.io

function main() {
    io.writeln(`Hello, World from Zenlang!`)
    <- 0
}
```

### Running with the Interpreter

During development, run scripts instantly with the interpreter:

```bash
./bin/zen hello.zl
```

**Output:**
```
Hello, World from Zenlang!
```

### Compiling to Native C (`-g`)

Zenlang features **dual execution parity**. The exact same file can be compiled directly into a standalone, optimized native executable:

```bash
./bin/zen -g hello.zl
```

This generates C code, invokes the C compiler (`gcc` or `clang`), links the runtime, and executes the native binary in milliseconds.

---

## 3. The Interactive Playground

Zenlang includes an interactive terminal code lab with real-time syntax highlighting, templates, and live execution.

Launch it with:

```bash
./scripts/zen playground
```

### Playground Shortcuts:
- <kbd>Ctrl+R</kbd>: Run code immediately
- <kbd>Ctrl+P</kbd>: Load standard library template examples
- <kbd>Ctrl+E</kbd>: Switch execution engine (Interpreter / Native `-g`)
- <kbd>Ctrl+S</kbd>: Save file
- <kbd>Ctrl+Q</kbd>: Quit

---

## 4. The Terminal File Manager (`zenfm`)

To explore your project files, browse directories, and preview `.zl` source files with live syntax highlighting:

```bash
./scripts/zen fm .
```

Press <kbd>P</kbd> on any `.zl` file to open it directly in the Playground!

---

## 5. Formatting Code (`zenfmt`)

Zenlang includes an automated style formatter:

```bash
# Format in place
./scripts/zen fmt -w hello.zl
```

---

## 💡 Key Takeaways
1. Zenlang programs start at `function main()` and return with `<-`.
2. Code runs under both an interpreter (for rapid iteration) and a native C compiler (`-g`).
3. Built-in tools like `playground`, `zenfm`, and `zenfmt` make development fluid and self-contained.
