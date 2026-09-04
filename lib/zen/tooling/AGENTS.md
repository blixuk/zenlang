# Purpose

The Zenlang developer tooling and project management subsystem. Provides pure Zenlang infrastructure for project scaffolding, declarative Zen Data package manifests (`zen.pkg.zd`), reproducible lockfiles (`zen.lock.zd`), incremental compilation and linkage, automated testing, benchmarking, interactive stateful REPL (`zen repl`), comment auditing (`zen todo`), documentation generation in Zen Mark (`docs/API.zm`), semantic version bumping, and flat package management.

# Ownership

Standard library and language tooling maintainers.

# Local Contracts

- **Pure Zenlang implementation**: All tooling modules are written in standard, idiomatic Zenlang without external runtime dependencies beyond GCC/Clang and standard OS utilities.
- **Manifest Format**: `zen.pkg.zd` files use native Zen Data format (tagged `Package { ... }` structs with visual `->` flow maps), with backward compatibility for legacy `.zbuild` JSON.
- **Lockfile Contract**: `zen.lock.zd` holds deterministic Git commit hashes and pinned dependency paths in Zen Data format.
- **Documentation & Scaffolding**: Scaffolding generates `README.zm` (Zen Mark format readable in terminal via `zen view README.zm`). Doc generation produces `docs/API.zm` and interactive dark-mode HTML (`docs/html/index.html`). `docgen.zl` also provides built-in terminal manual pages and symbol lookups (`zen doc <symbol|keyword>`, `zen explain <topic>`, and `zen doc --topics`).
- **Interactive Stateful REPL (`zen repl`)**: Provides persistent session state (`env`), automatic `_` and `_N` variables, Zen Data state snapshotting (`:save` / `:load` with `.zd`), multi-line block entry, tab autocompletion, live syntax highlighting, and execution timing (`:time`).
- **Dependency Topology**: Dependencies are installed in a flat structure under `deps/` (`deps/<pkg_name>/`), preventing deep directory nesting and C symbol collisions in AOT native binaries.
- **App Templates**: Scaffolding templates for `cli` (with `cli.Parser`, flags, help, banner), `tui` (with canvas & layout), `lib` (exported classes and math routines), and `service` (HTTP request router and JSON endpoints).
- **Builder Integration**: Transpiles to intermediate C code using the Zenlang compiler pipeline, links against `libruntime.a` / C runtime objects with GCC or Clang, and supports `--release`, `--debug`, `--dump`, `--incremental` (multi-unit change caching via `.cache.zd`), `--static` (fully static native binary), and `--shared` (dynamic library `.so`).
- **Interactive TUI Dashboard**: Live reactive terminal dashboard (`zen dash`) running on `zen.ui.canvas` and `zen.sys.term`, streaming live build output, displaying test status badges, and scanning codebase annotations.
- **Dependency Graph Visualizer**: Tree-based terminal visualizer (`zen pkg graph`) and interactive SVG/HTML dependency architecture visualizer (`zen pkg graph --html`).

# Work Guidance

- Follow Zenlang naming conventions: prefer full descriptive names (`format`, `benchmark`, `publish`, `manifest`, `make_dirs`).
- Keep modules modular and re-exported through `zen.tooling.tooling` (`lib/zen/tooling/tooling.zl`).
- Any new project tool command or manifest key must have corresponding unit tests in `tests/tools/test_tooling.zl` or `tests/tools/test_repl.zl`.

# Verification

- Automated test suite: `python3 bootstrap/Zen.py tests/tools/test_tooling.zl` and `python3 bootstrap/Zen.py tests/tools/test_repl.zl`
- End-to-end toolchain CLI: `python3 bootstrap/Zen.py tools/zenpm.zl <command>` and `python3 bootstrap/Zen.py tools/zenrepl.zl`
- Handoff binary verification: `./bin/zen new /tmp/test_app --template=cli && cd /tmp/test_app && ../../bin/zen build && ./build/test_app`

# Child DOX Index

- repl.zl: Interactive stateful REPL shell with `_`/`_N` tracking, `:save`/`:load` snapshots (.zd), tab completion, and multi-line blocks
- manifest.zl: Comment stripper, `zen.pkg.zd` parser/serializer, `zen.lock.zd` lockfile manager (with `.zbuild` fallback)
- templates.zl: Project scaffolding templates (`cli`, `tui`, `lib`, `service`), starter test suites, `.gitignore`, and `README.zm`
- project.zl: Project root discovery (`find_root`, `load_project`), `init_project`, and `new_project`
- builder.zl: Compilation pipeline, C linkage, binary placement in `build/`, `--dump` profiling, `run_project`, and `clean_project`
- watcher.zl: Filesystem snapshotting, polling change detector, and auto-rebuild loop (`zen watch`, `zen run --watch`)
- tester.zl: Test runner discovering `tests/test_*.zl` and executing with full `ZEN_PATH` propagation
- bench.zl: Benchmark runner discovering `benches/bench_*.zl` and executing with iteration metrics
- todo.zl: Codebase annotation scanner for `TODO:`, `FIXME:`, `BUG:`, `NOTE:`, `HACK:`
- pkg.zl: Flat package manager with Git repository cloning, local path linking, lockfile synchronization, and removal
- publish.zl: Semantic version bumper (`patch`, `minor`, `major`), Git tagger, and release tar packager
- docgen.zl: Zen Mark API reference (`docs/API.zm`) and interactive dark-mode HTML documentation generator
- graph.zl: Dependency tree resolver, Unicode terminal visualizer, and standalone dark-mode HTML/SVG interactive node-graph generator
- dash.zl: Live interactive multi-pane TUI dashboard with file tree, build stream, test runner badges, and hotkey control loop
- profiler.zl: Terminal hot spots table, flame tree visualizer, and interactive zoomable HTML flame graph report generator
- diagnostic.zl: Structured compiler diagnostics, ANSI source frame renderer with caret gutters, and native serialization to Zen Data (.zd) and Zen Mark (.zm) Callouts
- tooling.zl: Domain package entry and public re-exports
