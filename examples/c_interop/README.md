# Zero-Wrapper C Interoperability & `.zbuild` Example (`c_interop`)

This example demonstrates how to build a high-performance Zenlang application that directly calls C standard library and POSIX system functions using `extern use`, packaged and built via a `.zbuild` manifest.

---

## Features

- **Direct C Header Imports (`extern use`)**:
  - `<unistd.h>`: Process ID (`getpid`), Parent Process ID (`getppid`), User ID (`getuid`), POSIX configuration (`sysconf`).
  - `<sys/sysinfo.h>` (`sys.sysinfo`): Number of configured and online CPU cores (`get_nprocs`, `get_nprocs_conf`).
  - `<math.h>`: Floating-point routines (`sqrt`, `hypot`, `pow`, `sin`, `cos`).
- **Zero-Glue Interoperability**:
  - No hand-written C wrappers or binding layers needed.
  - Return types are automatically boxed into `ZenValue` via C11 `_Generic` (`ZenValue_from_c`), and primitive arguments are unboxed natively.
- **Manifest-Driven Builds (`.zbuild`)**:
  - Scaffolds a standalone project using the `.zbuild` specification.
  - Automatically compiles directly to a native ELF binary using `zen build`.

---

## Directory Structure

```
examples/c_interop/
├── .zbuild             # Manifest configuration (name, entry, target, c_flags)
├── zen.pkg.zd          # Modern Zen Data package manifest
├── AGENTS.md           # DOX framework contract for this subtree
├── README.md           # Project documentation and guide
├── src/
│   └── main.zl         # Application source with C extern declarations
└── tests/
    └── test_main.zl    # Automated verification test suite
```

---

## Building and Running

### 1. Build the Project via `.zbuild`
From inside this directory:
```bash
# Compile to a native binary using .zbuild
../../bin/zen build
```
This produces the native binary in `build/c_interop`.

### 2. Run the Application
```bash
# Run the built binary
./build/c_interop

# Or run directly via project manager
../../bin/zen run
```

### 3. Command Options
```bash
# Show only system & POSIX telemetry
./build/c_interop info

# Show only C math calculations
./build/c_interop math

# Run native tight-loop benchmark (100k C function calls)
./build/c_interop bench
```

### 4. Run Automated Tests
```bash
../../bin/zen tests/test_main.zl
```
