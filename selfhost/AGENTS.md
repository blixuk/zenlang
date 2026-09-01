# Purpose

Self-hosted Zenlang compiler sources — long-term home of the compiler written in Zenlang (peer of `bootstrap/`). **Goal: parity with bootstrap**, then replace Python as the production host.

# Ownership

Owned by the self-hosting effort.

# Local Contracts

- **Bootstrap is authority** until a stage declares parity for that phase.
- Sources live only under `selfhost/` (never reintroduce `src/`).
- `selfhost/compiler/` holds ported components; `selfhost/zen.zl` is the future driver.
- `selfhost/stubs/` is legacy C glue for experimental linking.
- Imports: nested stdlib (`zen.text.string`, `zen.io.io`, …) and `compiler.*` with `ZEN_PATH` including `selfhost/`.
- Dual-path required for stage exit: interpret **and** `python3 bootstrap/Zen.py -g`.
- Full plan: [PARITY.md](PARITY.md). Post-MVP depth: [ENDGAME_PLAN.md](ENDGAME_PLAN.md) (phases A–E + **L required** Nothing/Default).
- **Language sentinels (required):** `Nothing` (absent), `Default` (type zero-state). Prefer capitalized specials (`Nothing`, `Default`, `True`, `False`) to match type naming.
- **Backend (three-layer):** language values = `ZenValue`; user programs AOT **AST → C**; compiler Token/AST **target native structs** (maps today, transitional); scripts **target a bytecode VM**. Full MIR/SMIR is **not** on the path. See [THREE_LAYER.md](THREE_LAYER.md) and PARITY *Backend & memory decision*.
- **Memory product:** automatic by default (runtime); opt-in regions/pointers via `zen.memory` + checker on those paths.

# Status

| Stage | Name | Status |
|-------|------|--------|
| 0 | Hygiene + plan | **Done** |
| 1 | Token + Lexer | **Done** — dual-path green (`tests/self_hosting/test_lexer.zl`) |
| 2 | Parser + AST | **Done (MVP)** — map AST + index-only RD parser dual-path green (`test_parser.zl`) |
| 3 | Module graph | **Done (MVP)** — Resolver + DependencyGraph + GraphBuilder dual-path green (`test_module.zl`) |
| 4 | Checker | **Done (MVP+)** — with/class/enum/lambda/is; dual-path green (`test_checker.zl` 11) |
| 5 | Transpiler / C | **Done + classes/enums/lambdas/with** — multi-unit; inheritance; enum; closures; region push/pop |
| 6 | Driver | **Done (MVP) + multi-file + multi-unit** — merge default; `--multi` one C TU/module + host; `build`/`run`/`bundle`/`plugin` |
| 7 | Native + E2E | **Done + Standalone Native Host** — self-compilation loop green; pure native `bin/zen`; `.zbc` packaging & caching; compiler plugins |

# Work Guidance

- Port one bootstrap module at a time; prove with `tests/self_hosting/`.
- Prefer free functions + maps under `-g` when class field mutation hangs or misreads.
- Prefer `Str.*`, `==`, `and`/`or`, recursive rest-string over mutable index `while`.
- After TokenType renames, update Parser consumers in Stage 2 (do not block Stage 1).
- Stage 7: no rebind of CLI paths under `-g`; use `compile_cli` / fresh bindings.
- Codegen numeric emit: use `Str.to_string(n)` — native `/` is float when not exact.
- Multi-file: free-fn calls after merge (strip imports); entry keeps `main`, deps drop theirs.
- Multi-unit (`--multi`): one `.c` per module + `zen_host_main.c`; shared protos; `zen_mod_init_<stem>`; merge remains default.
- Classes: map instances + `Class_method`; `extends` (EXTENDS token); inheritance fields/init/`parent.meth`; never bind bare `parent` local.
- **with/region:** parse `WithStatement`; Codegen push/pop `ZenMemory_*` when resource is `ZEN_ARENA`; fixture `with_region.zl`.
- Checker: with alias scope; class `self`; enumerator + `is`; lambdas — not full ownership yet.
- Do not port bootstrap MIR/SMIR into selfhost unless PARITY reopens that track; grow Codegen + runtime instead.
- **Endgame:** fully Zen host — **#1–#5 MVP done**; **Phases A, L, B, C, D, E1–E3 done (Host-1.0)**; **Standalone Pure Native Host (E4)** achieved. Golden: `./scripts/zen test-golden`. Soak: `./scripts/zen ci-soak`. Self-rebuild of `zen.zl` stays `ZEN_SELFHOST_REBUILD=1`. Edit-loop: `ZEN_OPT=0 ./scripts/zen install-selfhost-fast`. Smoke reuses `bin/zen-selfhost` unless `ZEN_SMOKE_REBUILD=1`. Bootstrap `-g` links cached runtime `.o` + `-I runtime/`.
- **Modern CLI UX & Extensions:** Modernized CLI with ANSI colors, contextual help (`zen <cmd> --help`), fuzzy typo suggestions ("Did you mean 'build'?"), bash tab-completion generator (`zen completion bash`), AST hierarchy visualizer (`zen ast`), and bytecode disassembler (`zen disasm`). Architectural split between baked-in native extensions (`compiler/Extensions.zl`) and dynamic script plugins (`compiler/Plugin.zl`).
- Production today: `./scripts/zen install` installs standalone native `bin/zen`; CLI: `build` / `bundle` / `run` / `compile` / `check` / `deps` / `disasm` / `ast` / `info` / `completion` / `test` / `plugin` / `todo` / `lint` / `daemon`. `lsp` is `tools/zenlsp.zl` (hybrid `./bin/zen lsp`).
- Edit-loop native rebuild: `ZEN_OPT=0 ./scripts/zen install-selfhost-fast` (or `ZEN_CC=tcc`). Release install stays `-O2`.
- Parser: **exact** token `is_kind` (`TokenType.NAME` only); never ends_with/contains (NOT vs NOTHING).
- Parser ops: match operator **kinds**, not `is_val(\`-\`)` (STRING `"-"` false-matched unary minus).
- Soft keywords as names: `scope`, `self`, `parent`; map lit `{ k -> v }`; `export` / `from … import`.
- GraphBuilder: exact AST kinds when walking (StructureMember ≠ Structure).
- Historical experiments: `archive/selfhost-experiment/`.

# Verification

```bash
export ZEN_PATH=$PWD:$PWD/selfhost:$PWD/lib
for t in test_lexer test_parser test_module test_checker test_codegen test_driver test_interpreter test_plugins test_bytecode_cache; do
  python3 bootstrap/Zen.py tests/self_hosting/${t}.zl
  python3 bootstrap/Zen.py -g tests/self_hosting/${t}.zl
done
# CLI (bootstrap host):
python3 bootstrap/Zen.py selfhost/zen.zl help
python3 bootstrap/Zen.py selfhost/zen.zl interpret tests/self_hosting/fixtures/stage7_add.zl
python3 bootstrap/Zen.py selfhost/zen.zl compile path/to/file.zl out.c --typecheck
python3 bootstrap/Zen.py selfhost/zen.zl compile path/to/file.zl output/multi_c --multi
# Stage 7 native standalone install:
./scripts/zen install-selfhost   # → bin/zen-selfhost
./scripts/zen selfhost-smoke     # compile fixture → gcc/runtime → run
./scripts/zen install            # standalone native bin/zen
./scripts/zen test-golden        # bootstrap vs selfhost interpret + AOT
./scripts/zen ci                 # fast full CI smoke
```
- Primary test ladder: `./scripts/zen test` (test-core, test-parity, test-lib, test-lib-native)
- Default install: `./scripts/zen install` → standalone native `bin/zen` (pure native selfhost execution with zero Python fallback)
- Rollback tool: `./scripts/zen install-rollback` → restores `bin/zen` to Python bootstrap if needed
- `bin/zen-bootstrap` = seed host; `bin/zen` / `bin/zen-selfhost` = native selfhost compiler & runtime host

# Child DOX Index

- PARITY.md — staged roadmap to bootstrap parity
- THREE_LAYER.md — product: ZenValue + compiler structs + script VM + C AOT
- ENDGAME_PLAN.md — Host-1.0 / path to E4
- compiler/ — components (see compiler/AGENTS.md)
- lsp/ — Language Server Protocol daemon (see lsp/AGENTS.md)
- zen.zl — driver CLI entry (Stage 6/7)
- stubs/ — C interface leftovers
