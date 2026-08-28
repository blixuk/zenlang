# Purpose

The Zenlang developer tooling and project management subsystem. Provides pure Zenlang infrastructure for project scaffolding, relaxed ZON build manifests (`.zbuild`), reproducible lockfiles (`zen.lock`), incremental compilation and linkage, automated testing, benchmarking, comment auditing (`zen todo`), documentation generation, semantic version bumping, and flat package management.

# Ownership

Standard library and language tooling maintainers.

# Local Contracts

- **Pure Zenlang implementation**: All tooling modules are written in standard, idiomatic Zenlang without external runtime dependencies beyond GCC/Clang and standard OS utilities.
- **Manifest Format**: `.zbuild` files use Relaxed ZON (JSON with single-line `//` and multi-line `/* */` comments stripped before parsing).
- **Lockfile Contract**: `zen.lock` holds deterministic Git commit hashes and pinned dependency paths for reproducible builds.
- **Dependency Topology**: Dependencies are installed in a flat structure under `deps/` (`deps/<pkg_name>/`), preventing deep directory nesting and C symbol collisions in AOT native binaries.
- **App Templates**: Scaffolding templates for `cli` (with `cli.Parser`, flags, help, banner), `tui` (with canvas & layout), `lib` (exported classes and math routines), and `service` (HTTP request router and JSON endpoints).
- **Builder Integration**: Transpiles to intermediate C code using the Zenlang compiler pipeline, links against `libruntime.a` / C runtime objects with GCC or Clang, and supports `--release`, `--debug`, and `--dump` (compilation timing, dependencies, and file graph metadata).
- **Documentation Generation**: Generates comprehensive markdown API reference (`docs/API.md`) and interactive dark-mode HTML documentation (`docs/html/index.html`).
- **Interactive TUI Dashboard**: Live reactive terminal dashboard (`zen dash`) running on `zen.ui.canvas` and `zen.sys.term`, streaming live build output, displaying test status badges, and scanning codebase annotations.
- **Dependency Graph Visualizer**: Tree-based terminal visualizer (`zen pkg graph`) and interactive SVG/HTML dependency architecture visualizer (`zen pkg graph --html`).

# Work Guidance

- Follow Zenlang naming conventions: prefer full descriptive names (`format`, `benchmark`, `publish`, `manifest`, `make_dirs`).
- Keep modules modular and re-exported through `zen.tooling.tooling` (`lib/zen/tooling/tooling.zl`).
- Any new project tool command or manifest key must have corresponding unit tests in `tests/tools/test_tooling.zl`.

# Verification

- Automated test suite: `python3 bootstrap/Zen.py tests/tools/test_tooling.zl`
- End-to-end toolchain CLI: `python3 bootstrap/Zen.py tools/zenpm.zl <command>`
- Handoff binary verification: `./bin/zen new /tmp/test_app --template=cli && cd /tmp/test_app && ../../bin/zen build && ./build/test_app`

# Child DOX Index

- manifest.zl: Comment stripper, `.zbuild` parser/serializer, `zen.lock` lockfile manager
- templates.zl: Project scaffolding templates (`cli`, `tui`, `lib`, `service`), starter test suites, `.gitignore`, and `README.md`
- project.zl: Project root discovery (`find_root`, `load_project`), `init_project`, and `new_project`
- builder.zl: Compilation pipeline, C linkage, binary placement in `build/`, `--dump` profiling, `run_project`, and `clean_project`
- watcher.zl: Filesystem snapshotting, polling change detector, and auto-rebuild loop (`zen watch`, `zen run --watch`)
- tester.zl: Test runner discovering `tests/test_*.zl` and executing with full `ZEN_PATH` propagation
- bench.zl: Benchmark runner discovering `benches/bench_*.zl` and executing with iteration metrics
- todo.zl: Codebase annotation scanner for `TODO:`, `FIXME:`, `BUG:`, `NOTE:`, `HACK:`
- pkg.zl: Flat package manager with Git repository cloning, local path linking, lockfile synchronization, and removal
- publish.zl: Semantic version bumper (`patch`, `minor`, `major`), Git tagger, and release tar packager
- docgen.zl: Markdown API reference and interactive dark-mode HTML documentation generator
- graph.zl: Dependency tree resolver, Unicode terminal visualizer, and standalone dark-mode HTML/SVG interactive node-graph generator
- dash.zl: Live interactive multi-pane TUI dashboard with file tree, build stream, test runner badges, and hotkey control loop
- profiler.zl: Terminal hot spots table, flame tree visualizer, and interactive zoomable HTML flame graph report generator
- diagnostic.zl: Structured compiler diagnostics, ANSI source frame renderer with caret gutters, and native serialization to Zen Data (.zd) and Zen Mark (.zm) Callouts
- tooling.zl: Domain package entry and public re-exports
