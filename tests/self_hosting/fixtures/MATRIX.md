# Selfhost fixture matrix (Phase D)

Language-complete fixtures should pass **interpret** (`selfhost/zen.zl interpret` / `Interpreter.interpret_file`) and **run** (AST→C→gcc).

| Fixture | interpret | run (`selfhost_smoke` / gcc) |
|---------|-----------|------------------------------|
| `stage7_add.zl` | yes | yes |
| `stage5_for_sum.zl` | yes | yes |
| `interp_import.zl` | yes | n/a (interpret-graph) |
| `interp_map.zl` | yes | n/a |
| `interp_str.zl` | yes | n/a |
| `nothing_default.zl` | yes | yes (bootstrap `-g` too) |
| `pattern_bind.zl` | yes (list/map) | yes |
| `enum_color.zl` | yes | yes |
| `enum_payload.zl` | yes | yes |
| `closure_add.zl` | yes | yes |
| `closure_nested.zl` | yes | yes |
| `class_counter.zl` | yes | yes |
| `class_inherit.zl` | yes | yes |
| `class_dispatch.zl` | yes | yes |
| `with_region.zl` | yes (software arena depth) | yes (runtime arenas) |
| `multi_main.zl` | n/a (merge/codegen) | yes |

Residual bootstrap-only under selfhost interpret: real stdout (`__builtin_output` is a no-op), host `zen.test` runner, interpreting `selfhost/zen.zl` itself.

`test_interpreter.zl`: 22/22 interpret + 22/22 `-g` (Phase D).

Phase E: hybrid `bin/zen interpret` **execs native** `zen-selfhost interpret` (MATRIX yes-interpret rows exit 0). Bare `bin/zen file.zl` stays bootstrap unless `ZEN_INTERPRET=selfhost`. `--test` remains bootstrap.

E3 golden (bootstrap vs selfhost, not MATRIX-only): [GOLDEN.md](GOLDEN.md) / `./scripts/zen test-golden`.
