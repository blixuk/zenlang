# Purpose

Demonstration project showcasing zero-wrapper C header interoperability (`extern use`), POSIX system telemetry, `<math.h>` floating-point operations, and manifest-driven compilation via `.zbuild` (and `zen.pkg.zd`).

# Ownership

Standard library, documentation, and example maintainers.

# Local Contracts

- Manifest: `.zbuild` defines `name`, `entry`, `target`, and `c_flags`. Compatible with `zen.pkg.zd`.
- Zero-wrapper C interop: Directly imports system headers (`<math.h>`, `<unistd.h>`, `sys.sysinfo`) without manual C wrapper glue.
- Visual flow syntax: `->` for assignment, `<-` for return.
- Universal preludes: `writeln` and `write` for terminal console output; backtick strings only.
- Output artifacts: Built native binary outputs to `build/c_interop`.

# Work Guidance

- Keep C header imports standard and portable across POSIX Linux environments.
- Verify tests in `tests/test_main.zl` remain passing after any changes.
- Ensure the application runs cleanly under both bytecode interpretation (`zen run src/main.zl`) and native compilation (`zen build`).

# Verification

From `examples/c_interop/`:
```bash
# Build binary via .zbuild
../../bin/zen build

# Run application binary
./build/c_interop

# Run test suite
../../bin/zen tests/test_main.zl
```

# Child DOX Index

- `.zbuild` — project build manifest
- `zen.pkg.zd` — Zen Data project manifest
- `src/main.zl` — main program entry importing C headers and executing benchmarks
- `tests/test_main.zl` — automated test suite
- `README.md` — project guide and CLI usage
