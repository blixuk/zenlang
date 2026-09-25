# Purpose

Automation and helper scripts supporting development, build, testing, refactoring, and experimentation for the Zenlang project.

# Ownership

Owned by tooling / developer experience maintainers.

# Local Contracts

- `scripts/zen` is the preferred developer CLI (install, test, run, clean, tools). Tool subcommands (`view`/`zenview`, `fm`, `fmt`, `playground`, `zenpm`) dispatch through `$ROOT/bin/zen` / native selfhost executables. Makefile is a thin shim only.
- Scripts augment bootstrap. They must remain functional or be removed when obsolete.
- Complex logic belongs in Python; thin wrappers or orchestration in shell.
- Refactoring scripts (refactor_*.py) are for periodic maintenance and should not be relied upon as part of normal builds.
- Check and test scripts (check_*, test_*) provide targeted verification.
- No new external dependencies without corresponding doc updates and justification.

# Work Guidance

- Make scripts executable when intended for direct use.
- Document usage at the top of the file or in Testing.md / relevant docs.
- Prefer idempotent or safe operations.
- After running refactor or experiment scripts, re-verify with the test suites.

# Verification

- Core language (Makefile wrappers):
  - scripts/run_core_tests.sh — interpret core set
  - scripts/run_core_parity.sh — interpret vs native (`-g`) core set
  - scripts/run_lib_smoke_native.sh — full lib suite under `-g` (via `make test-lib-native` / `./scripts/zen test-lib-native`)
  - tests/lib/run_all.sh — via `make test-lib`
- Selfhost Stage 7 + handoff (Host-1.0):
  - `./scripts/zen install` → default install: hybrid `bin/zen` + `zen-bootstrap` + `zen-selfhost`
  - `./scripts/zen install-selfhost` → `bin/zen-selfhost` (`-O2`)
  - `./scripts/zen install-selfhost-fast` → same with `ZEN_OPT=0` (edit-loop)
  - C compile env: `ZEN_OPT=0|1|2|3|s`, `ZEN_CC=gcc|clang|tcc`
  - `./scripts/zen install-bootstrap` → `bin/zen-bootstrap` (maintenance)
  - `./scripts/zen install-rollback` → emergency `bin/zen` → bootstrap; restore with `install`
  - `./scripts/zen selfhost-smoke` / `scripts/selfhost_smoke.sh` — native compile → gcc/runtime → run (reuses `bin/zen-selfhost` unless `ZEN_SMOKE_REBUILD=1`)
  - Hybrid routes: compile/build/run/interpret/check/deps/help → `zen-selfhost` (native interpret); bare `.zl`/`--test` → bootstrap; `-g` try-selfhost then bootstrap
  - `./scripts/zen test-golden` / `scripts/run_golden.sh` — bootstrap vs selfhost interpret + AOT on GOLDEN.txt
  - `./scripts/zen handoff-soak` / `scripts/handoff_soak.sh` — smoke + hybrid checks + golden
  - `./scripts/zen ci` / `scripts/ci_smoke.sh` — fast local smoke (install + core + parity + lib-native)
  - `./scripts/zen ci-soak` / `scripts/ci_soak.sh` — local soak (`handoff-soak`; `ZEN_SELFHOST_REBUILD=0`; no remote CI)
  - `./scripts/zen multi-selfhost-smoke` — multi-unit full selfhost compile+link (long)
  - Wrapper source: `scripts/zen_bin_handoff.sh` (copied to `bin/zen` on install)
- Other scripts as part of dev loops:
  - scripts/profile_selfhost.py — selfhost vs bootstrap bench; `ZEN_PROFILE=1` prints Driver/Parser stages
  - scripts/check_lexer.py
  - scripts/test_memory_safety.py
  - scripts/test_smir.py
  - scripts/refactor_*.py (when performing refactors)
  - scripts/zen-build-runtime.sh
  - scripts/run_experiments.py
- Confirm no breakage in `make test`, bootstrap runs, and broader test batches after changes.

# Child DOX Index

- zen — primary host CLI (install, install-rollback, install-handoff, handoff-soak, install-selfhost, install-selfhost-fast, selfhost-smoke, test-golden, test-*, ci, ci-soak, run, doc-pdf, shell/zsh, clean)
- zen_bin_handoff.sh — hybrid bin/zen template (selfhost compiler CLI + interpret; bootstrap language host)
- handoff_soak.sh — production handoff gate (interpret matrix + -g try-selfhost + golden)
- run_golden.sh — E3 golden: bootstrap vs selfhost exit+stdout (`tests/self_hosting/fixtures/GOLDEN.txt`)
- multi_selfhost_smoke.sh — multi-unit selfhost→C×N→link→help/fixture
- selfhost_smoke.sh — Stage 7 E2E (native driver + fixtures + class_counter + multi-unit --multi; self-rebuild of zen.zl still `ZEN_SELFHOST_REBUILD=1`; that path gcc+help+fixture is green)
- setup_zed_extension.sh — generate tree-sitter-zen nested git rev + writers editors/zed/extension.toml
- setup_vscode_extension.sh — symlink editors/vscode into VS Code / Cursor / Antigravity extension dirs
- ci_smoke.sh — fast local smoke (core + parity + lib-native)
- ci_soak.sh — local soak wrapper for handoff-soak (self-rebuild stays 0)
- run_core_tests.sh, run_core_parity.sh — language core verification
- run_lib_smoke_native.sh — native `-g` for lib smoke tests (include new `tests/lib/test_*.zl` when adding stdlib coverage; includes test_reflect)
- activate_venv.sh, check_executable.sh, check_lexer.py
- refactor_imports.py, refactor_tests.py
- run_experiments.py, test_memory_safety.py, test_smir.py
- zen-build-runtime.sh
