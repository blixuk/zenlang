# Testing Zenlang

## Primary ladder

Post-reorg status: `./scripts/zen test` is the full ladder and is expected to stay green.

```bash
./scripts/zen install          # Host-1.0 hybrid bin/zen (selfhost primary)
./scripts/zen test-core        # interpret core set
./scripts/zen test-parity      # interpret vs native (-g)
./scripts/zen test-lib         # stdlib (interpreter)
./scripts/zen test-lib-native  # native stdlib smoke
./scripts/zen test             # all of the above
./scripts/zen ci               # faster local smoke (install + core + parity + lib-native)
./scripts/zen ci-soak          # local soak: handoff-soak (selfhost-smoke + hybrid + golden)
```

Direct equivalents:

```bash
python3 bootstrap/Zen.py tests/hello.zl
python3 bootstrap/Zen.py -g tests/01_primitives.zl
bash scripts/run_core_tests.sh
bash scripts/run_core_parity.sh
bash tests/lib/run_all.sh
bash scripts/run_lib_smoke_native.sh
```

Deep tracing (optional): `ZEN_TRACE=1`. Verbose compiler: `-d` / `--verbose`.

## What each target covers

| Command | Scope |
|---------|--------|
| test-core | `tests/01`–`06`, hello, smoke, suite, error/pattern/ownership/range/closures samples |
| test-parity | Same core files under interpret and `-g`; exit + stdout match |
| test-lib | `tests/lib/run_all.sh` (stdlib modules, interpreter) |
| test-lib-native | Subset under `-g` (core, string, math, list, collections, range, error, test, sys, cli, io, file, path, csv, json, log, time, term, process) |

## Dual-layer strategy

1. **Host / bootstrap** — Python pipeline correctness (lexer, parser, checker, transpiler).
2. **Native** — generated C + `runtime/` behavior and interpret/`-g` parity.

Assertions: Zen `!` conditions, `zen --test` / `test_*` functions, and suite runners under `tests/lib` and `tests/suite`.

## Notes

- Prefer `./scripts/zen` over Make. Legacy Make rules: `archive/Makefile.legacy`.
- Interactive demos (e.g. `examples/zedit.zl`) are not part of the automated ladder.
- Historical testing essay material was trimmed; strategy above is the operational contract.
