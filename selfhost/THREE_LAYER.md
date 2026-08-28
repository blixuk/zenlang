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
| **0** | Stage timers (`ZEN_PROFILE=1`) + `scripts/profile_selfhost.py` | **Done** — `stage7_add.zl` (~5.5s `-O0` host): graph 6ms, **lex ~1.9s**, **parse ~3.2s**, codegen ~0.37s. Merge ≈ lex+parse. Interpret load ≈ lex+parse. Map-walk lexer/parser dominate. |
| **1** | Compiler IR: Token structs, then AST nodes; Parser walks structs | `test_lexer` / `test_parser` dual-path; tiny compile/interpret clearly faster |
| **2** | Incremental `--multi` / `-O0` rebuild of `zen.zl` (edit loop) | `install-selfhost-fast` comfortable; dirty rebuild minutes not ~15 |
| **3** | Bytecode VM for interpret; Codegen can still AOT AST→C | Golden interpret via VM; scripts start fast |
| **4** | Embed + import of compiled modules from VM | Mix fixtures green |
| **E4** | Drop hybrid router / freeze Python | Phases 1+3 good enough that bare `.zl` on selfhost is what you’d actually use |

Cheap C `int` compares for known kinds (today’s Codegen) may land inside phase 1 as a stepping stone. Do **not** spend another week on token-table micro-opts unless phase 0 shows they dominate.

**Phase 1 Token note:** a Zen `class Token` with `init` field writes failed dual-path `-g` (`t[`value`]` → Nothing). Next Token struct needs `Tok.tok_kind` / `tok_value` (already started in Parser helpers) and integer `kind` always — not class index on untyped fields.

## Non-goals

- Half-port bootstrap MIR/SMIR into selfhost
- VM as the only backend
- Expanding bare-`.zl` routing before phase 1+3
- Replacing `runtime/` ZenValue as the language ABI

## Verification

- Dual-path: `tests/self_hosting/test_lexer.zl`, `test_parser.zl`, then interpreter/codegen as IR lands
- Golden: `./scripts/zen test-golden`
- Soak: `./scripts/zen ci-soak` (self-rebuild still `ZEN_SELFHOST_REBUILD=1`)
- Mix: new fixtures when phase 4 starts (compiled host + script, script + compiled lib)
