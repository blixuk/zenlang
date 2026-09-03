# Purpose

Comprehensive test suites for Zenlang covering language features, stdlib, compiler pipeline (lexer/parser/typechecker/transpiler), memory model, modules, self-hosting, graphics, OOP, error handling, and execution parity between interpreter and native.

# Ownership

Owned by the testing / QA effort.

# Local Contracts

- Dual-layer testing is mandatory:
  - Host layer: testing Python bootstrap internals (lexer, parser, checker, generator) — see guidance in Testing.md.
  - Native layer: .zl programs executed via `zen` or bootstrap (primary mechanism uses `function test_* {...}` + `! condition` assertions).
- tests/ is organized by concern: language/ (feature area tests), lib/ + stdlib/ (stdlib coverage), native_compiler/ (compiler passes and transpiler output), memory/, self_hosting/, syntax/, modules/, classes/, graphics/, framework/, suite/ (integration), serialize/.
- feature_parity*.zl and smoke_* ensure interpreter and compiled modes behave identically.
- framework/ provides reusable test runner support.
- suite/ contains higher-level runnable suites.

# Work Guidance

- Add a test for every new or changed language/stdlib feature.
- Place tests in the most specific category.
- Use the test runner conventions (test_ prefix, `!`, doctests in /! @example).
- For compiler changes, add both a host-level consideration and a native test in native_compiler/ or self_hosting/.
- Keep smoke tests quick; use run_all scripts for batches.
- Update Testing.md when the dual-harness strategy evolves.

# Verification

Core ladder (must stay green for “language works”):
- `./scripts/zen test-core` → `scripts/run_core_tests.sh` (interpret: `tests/01`–`06`, hello, smoke, suite/run_all, error + pattern samples)
- `./scripts/zen test-parity` → `scripts/run_core_parity.sh` (interpret vs `-g`)
- `./scripts/zen test-lib` → `tests/lib/run_all.sh` (stdlib, interpreter only)
- `./scripts/zen test-lib-native` → `scripts/run_lib_smoke_native.sh` (native `-g` for all `tests/lib/test_*.zl`, currently 41 modules including logfmt/sexp/serialize/canvas/zenmark)
- Term raw/keys: `tests/lib/test_term.zl`; editor demo `examples/zedit.zl`
- Range operators: `tests/language/range_syntax_01.zl` (core + parity)
- Closures (by-value capture): `tests/language/closure_01.zl` (core + parity)
- Extended operators (`++` / `--`): `tests/language/test_extended_operators.zl` (core + parity)
- Binary membership operator (`in`): `tests/language/test_in_operator.zl` (core + parity)
- Frontend syntax parity (bases, strings, arrow bodies, 4-boundary ranges): `tests/language/test_frontend_parity_01.zl`
- Sentinels & type casting (`Nothing`, `Default`, `<:`, `Type(val)`): `tests/language/test_nothing_default_01.zl`
- Directional guard returns & concise functions: `tests/core/test_guard_concise_syntax.zl` (core + parity)
- Diagnostic source frames, Zen Data & Zen Mark Callouts: `tests/core/test_diagnostics.zl` (core + parity)
- Individual: `python3 bootstrap/Zen.py path/to/test.zl` or `./bin/zen` after `./scripts/zen install`

Broader:
- Batch: tests/lib/run_all.zl, tests/suite/run_all.zl
- Targeted: tests/native_compiler/, tests/memory/, tests/language/
- feature_parity*.zl and self_hosting/verify* (advanced)
- Stage 7 selfhost E2E: `./scripts/zen selfhost-smoke` (fixture `tests/self_hosting/fixtures/stage7_add.zl`)
- E3 golden: `./scripts/zen test-golden` — bootstrap vs selfhost on `tests/self_hosting/fixtures/GOLDEN.txt` (see GOLDEN.md)
- E3 local soak: `./scripts/zen ci-soak` (handoff-soak + golden; no remote CI)
- Archived legacy suites: archive/tests-stdlib/, archive/tests-orphans/

# Child DOX Index

- language/: Per-area language feature tests (basics, control_flow, data_structures, oop, adt, pattern, error, concurrency, memory_model, etc.).
- lib/ + stdlib/: Stdlib module tests (test_*.zl mirroring lib/zen/ modules).
- native_compiler/: Lexer, parser, c_transpiler, typechecker, and smoke tests for the compiler itself.
- memory/: Low-level memory, ownership, arena, promotion tests.
- self_hosting/: Validation that self-hosted sources work.
- suite/: Integration suite driven by run_all.zl (part of test-core).
- syntax/, modules/, classes/, graphics/, framework/, serialize/: Cross-cutting or specialized.
- Top-level core ladder: 01_primitives.zl … 06_structs.zl, hello.zl, smoke_test.zl, feature_parity*.
- No per-subdir AGENTS.md at this time. Add when a test category acquires separate ownership or special contracts.
