# Three-layer Zen (product)

**Status: accepted** (2026-08-24)  
**Companion:** [PARITY.md](PARITY.md) (memory + no MIR half-port), [ENDGAME_PLAN.md](ENDGAME_PLAN.md) (Host-1.0 / E4)

Zen is the middle of **Python** (change it, run it) and **C** (build it, ship it). One language, three gears that share values.

## Gears

| Gear | User feel | Mechanism |
|------|-----------|-----------|
| **Script** | Edit and run | Bytecode VM (not today’s AST walk in Zen) |
| **Program** | Ship a fast Unix binary | AOT → C (`compile` / `-g`) — keep this |
| **Mix** | Binary + live Zen, or script + native modules | Shared `ZenValue` ABI |

Not VM-only (loses real executables unless we write a JIT). Not C-only (loses fast iterate). Not a bootstrap MIR port.

## Layers

1. **Language values — `ZenValue`**  
   Maps, lists, variants, closures, Nothing/Default. Compiled and interpreted code pass the same values. Runtime stays `runtime/`.

2. **Compiler IR — native structs**  
   Tokens and AST are C structs (integer kinds, arena nodes, `switch` on kind), **not** hash maps. Makes `zen-selfhost` usable. Does **not** by itself speed user binaries (those already run as C).

   Today’s map AST in `selfhost/compiler/` is transitional. Target: Token + Node as typed structs (prefer Zen `class` with typed fields so bootstrap `-g` emits C structs; or a small `runtime/` node API). Dual-path until native IR matches map interpret.

3. **Script VM — bytecode**  
   `zen file.zl` → bytecode → tight C loop in `runtime/`. Fast start, no gcc. Same language as AOT.

## Mix (required)

- Interpreted script **calls compiled modules** (`.so` / linked `z_*` that take `ZenValue`).
- Compiled program **loads interpreted Zen** (plugin, config, REPL) via an embed API.
- One runtime, one value ABI. No second object model.

## Order of work (do not skip)

| Phase | Work | Done when |
|-------|------|-----------|
| **0** | Stage timers (`ZEN_PROFILE=1`) + `scripts/profile_selfhost.py` | **Done** — `stage7_add.zl` (~5.5s `-O0` host): graph 6ms, **lex ~1.9s**, **parse ~3.2s**, codegen ~0.37s. Map-walk lexer/parser profile mapped. |
| **1** | Compiler IR: Token structs, then AST nodes; Parser walks structs | **Done** — Zero-copy 7-tuple tokens + positional AST list nodes with arena allocation. |
| **2** | Incremental `--multi` / `-O0` rebuild of `zen.zl` (edit loop) | **Done** — `install-selfhost-fast` and resident background daemon (`zen daemon`). |
| **3** | Bytecode VM for interpret; Codegen can still AOT AST→C | **Done** — `Bytecode.zl` + `runtime/core/zen_vm.c` stack VM; `.zbc` binary caching & standalone packaging (`zen bundle`); source-free bytecode execution. |
| **4** | Embed + import of compiled modules from VM; Compiler Plugins | **Done** — Mixed ABI (`test_mixed_abi.zl`); `Plugin.zl` lifecycle hooks (`on_ast`, `on_check`, `on_codegen`, `commands`) for modular compiler tooling. |
| **E4** | Standalone Selfhost Compiler / Drop Python Fallback | **Done** — Selfhost compiles itself cleanly; `bin/zen` is pure native selfhost compiler with zero Python fallback. |

## Verification

- Dual-path: `tests/self_hosting/test_lexer.zl`, `test_parser.zl`, `test_plugins.zl`, `test_bytecode_cache.zl`
- Golden: `./scripts/zen test-golden`
- Smoke: `./scripts/zen selfhost-smoke` (50 passed, 0 failed)
- Fast CI: `./scripts/zen ci`
- Standalone Install: `./scripts/zen install` (pure native `bin/zen`)
