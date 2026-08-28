# Self-host ↔ Bootstrap Parity Plan

**Goal:** `selfhost/` implements the same compiler pipeline as `bootstrap/`, eventually replacing Python as the production host.

**Production host (Host-1.0):** `./scripts/zen install` — hybrid `bin/zen` (selfhost-primary).  
**Maintenance fallback:** `bootstrap/` stays in-tree. Dual-path stage tests still prove ports against bootstrap. Emergency: `./scripts/zen install-rollback` or `ZEN_FORCE_BOOTSTRAP=1`.

## Principles

1. **Stage by pipeline phase** — Token → Lexer → Parser/AST → Checker → Module → **AST→C Codegen** → Driver. Do not skip ahead for a “whole compiler” demo.
2. **Dual-path green** — Every selfhost component must pass under interpret *and* `python3 bootstrap/Zen.py -g` when exercised by its stage tests.
3. **Behavioral parity** — Same tokens, AST shape, diagnostics, and C output for a growing golden corpus (start with `tests/hello.zl` and the core ladder).
4. **Idiomatic Zen** — Nested stdlib imports (`zen.text.string`, `zen.io.io`), `==` / `and` / `or`, `do while`, `Str.*` free functions; no stale `lib/zen/*` flat paths.
5. **No `src/`** — Sources live only under `selfhost/`. Tests must not reference `src/compiler`.
6. **No half-port of MIR/SMIR** — Selfhost backend is AST→ZenValue C until a future, explicit project (see [Backend & memory decision](#backend--memory-decision)).

## Stage map

| Stage | Scope | Bootstrap map | Exit criteria |
|-------|--------|---------------|---------------|
| **0** | Hygiene | — | Imports, paths, AGENTS, tests point at `selfhost/`; plan documented |
| **1** | Token + Lexer | `Lexer/Token.py`, `Lexer/` | TokenType set matches bootstrap; lexer dual-path; golden token streams for core fixtures |
| **2** | Parser + AST | `Parser/`, `Parser/AST/` | Parse core ladder + stdlib samples; AST kinds aligned |
| **3** | Module graph | `Module/` | Resolve nested `zen.*` + multi-file; dependency order |
| **4** | Checker | `Checker/` | Type/semantic check parity on core set (`--check` equivalent) |
| **5** | Transpiler / C | `Transpiler/` C path (not full MIR port) | Emit ZenValue C that links with `runtime/`; dual-path fixtures + selfhost-smoke |
| **6** | Driver + install | `Zen.py` | `selfhost/zen.zl` CLI: interpret subset optional; compile path primary; `install-driver` works |
| **7** | Native selfhost + E2E | entire bootstrap (MVP) | Native `bin/zen-selfhost`; selfhost compile → gcc/runtime → run; full self-rebuild = 7.x |

## Stage 1 detail — **done**

- TokenType + functional lexer dual-path; `tests/self_hosting/test_lexer.zl`

## Stage 2 detail — **MVP done**

**In scope delivered**

- `AST.zl` — map factories + integer `K_*` kind ids
- `Parser.zl` — recursive descent, index-only over `G` token map
- `tests/self_hosting/test_parser.zl` — functions, when, do-while, structure, assert, 01-shape

**Dual-path lessons**

- Do not pass token lists as recursive args under `-g` (ownership move).
- Prefer map field mutation (`G[`tokens`]`) over rebinding bare module lists.
- Avoid name collisions with stdlib methods (`at` → `tok_at`).

**Still open for Stage 2.x / later**

- Full class/enumerator bodies, pattern matching, typed literals, complete type grammar
- Golden AST compare against bootstrap for entire core ladder files on disk
- Wire `main.zl` / driver to Stage 2 parse only

## Stage 3 detail — **MVP done**

**Delivered**

- `Module/Resolver.zl` — alias table, package entry (`zen.io.io`), `configure_search` + `resolve`
- `Module/DependencyGraph.zl` — map graph; mutators **return** graph (rebind under `-g`)
- `Module/GraphBuilder.zl` — parse entry → collect imports → resolve → topo order
- Fixtures `tests/self_hosting/fixtures/mod_{a,b,c}.zl`
- `tests/self_hosting/test_module.zl` — 5/5 interpret + 5/5 `-g`

**Dual-path lessons (Stage 3)**

- Mutators on maps/lists must **return** the structure; callers rebind (`g -> add_edge(g, …)`).
- List args are moved under `-g`; use module maps for accumulators (`IMPS`).
- Capture `list.length` **before** `do for` (for-in consumes the list under `-g`).
- Avoid `<- other_fn(...)` / list-copy loops in some helpers (void+`__ret_val` codegen bugs).
- AST node kinds are integer `AST.K_*` constants; compare with `==` (not substring).

**Still open**

- Full ZEN_PATH env merge; unlimited root list copy; cycle detection; from-import name lists

## Stage 4 detail — **MVP done**

**Delivered**

- `Types.zl` — map types, `sc_create` / `sc_define` / `sc_lookup` (avoid keyword `scope`)
- `TypeChecker.zl` — `check_source` / `check_program` → `{ok, errors, program}`
- Checks: undefined vars, redeclare, structure fields, returns, when/loops/calls (light)
- `tests/self_hosting/test_checker.zl` — 11/11 interpret + 11/11 `-g`

**Dual-path lessons**

- Do not `do for` twice over the same list under `-g` (for-in moves); use index recursion `walk_stmts`.
- Import aliases cannot be single-letter type abbreviations (`T` → `Ty`).
- Function names must not start with keywords (`scope_create` → `sc_create`).

**Still open vs bootstrap**

- Full inference, method resolution, generics, strict arithmetic, multi-file symbols from imports

## Stage 5 detail — **MVP done** / **5.x in progress**

**Delivered (MVP)**

- `Codegen.zl` — `transpile_source` / `transpile_program` → C string (`ZenValue_*`, `bootstrap_runtime.h`)
- Subset: functions, let, return, ops, when, while/do-while, calls, assert, host `main` / `zen_main`
- `tests/self_hosting/test_codegen.zl` — C shape checks (interpret + `-g`)

**Delivered (5.x)**

- **List literals** → `ZenList_make_from_arguments`
- **Index get** → `ZenValue_get_at`
- **for-in over lists** → C `for` + `ZenList_get_value_at_index`
- **for-in over ranges** `a..b` / `a..=b` → integer C for-loop
- **Map field get** → `ZenValue_get_field`
- **Structure init** (map-backed + `kind`) — basic emit
- **Parser fix**: `xs { body }` is not struct-init when `xs` is lowercase (unblocks `do for i in xs { … }`)
- **Kind match exact only** — `cg_is_kind` no longer uses `Str.contains` (avoided `ListLiteral` ⊃ `Literal`)
- Fixture `tests/self_hosting/fixtures/stage5_for_sum.zl` (sum list → exit 0)
- Tests: 9/9 interpret + 9/9 `-g` on `test_codegen.zl`
- **int_to_str** via `Str.to_string` (native `/` is float when not exact — recursive `%10`/`/10` peel was broken under `-g`)

**Dual-path lessons**

- Emit into a **string buffer** (`CG.buf`), not a long line list under `-g`
- Join with `acc == ```, not `i == 0` (int compare flaky in recursion under `-g`)
- Do not `let next -> acc` then reuse `acc` (UAM)
- Module state name `CG` (not `G`; clashes with Parser)
- Exact AST kind equality; never substring match kind names
- Struct-init vs for-body brace: type-name capitalization heuristic
- **Never peel digits with `/` under native** — `4/10` → `0.4` (exact-only integer divide in runtime); use `Str.to_string(n)` for C numeric literals / temp ids

**Still open (non-MIR)**

- Richer multi-file (from-import polish, cycle detection); class inheritance; region enter/exit emit
- Full MIR/SMIR **not** required for selfhost (see Backend & memory decision)

## Stage 6 detail — **MVP done** + multi-file merge

**Delivered**

- `compiler/Driver.zl` — pipeline API:
  - `compile_string(src, do_check)` / `compile_file(path, out, do_check)`
  - `check_string(src)` / `dep_order(...)` / `run_args(args)`
  - **Multi-file:** `dep_order` → `merge_program_files` (strip imports; drop non-entry `main`) → one Program → Codegen one C unit
- `selfhost/zen.zl` — CLI entry (`compile`, `check`, `deps`, `help`)
- `compiler/main.zl` — thin compile-one-file CLI
- Fixtures: `fixtures/multi_lib.zl` + `fixtures/multi_main.zl` (free-fn merge, exit 0 iff 3+4==7)
- `tests/self_hosting/test_driver.zl` — 8/8 interpret + 8/8 `-g` (includes multi + stage5_for_sum file)

**Dual-path lessons**

- When linking multiple selfhost modules, **unique function names** across modules (`walk_stmts`/`is_kind`/`emit`/`reset` collided Codegen↔TypeChecker under `-g`).
- Prefer `cg_*` / `checker_*` prefixes for shared helper names.
- Multi-file merge: call free functions by bare name after strip; do not rely on alias maps in MVP C unit.

## Stage 7 detail — **MVP done** + stage5/multi smoke

**Delivered**

- Native driver: bootstrap `-g selfhost/zen.zl` → `bin/zen-selfhost` via `./scripts/zen install-selfhost`
- E2E smoke: `./scripts/zen selfhost-smoke` / `scripts/selfhost_smoke.sh` (**12/12**)
  - native CLI help + compile `stage7_add` → gcc/runtime → exit 0
  - interpret host compile parity
  - **stage5_for_sum** native compile → gcc → run exit 0 (list + for-in)
  - **multi_main** dep merge → gcc → run exit 0 (lib free-fns in same unit)
- Driver CLI fixes for native argv:
  - skip binary/script path without treating bare commands as paths
  - no rebind of `src_path` under `-g` (`compile_cli` helper)
- Makefile: `install-selfhost`, `selfhost-smoke` (replaces stub `selfhost-regen`)

**Self-rebuild progress (Stage 7.x)**

- **Full loop green (smoke 18/18):** selfhost → C (~470KB namespaced) → gcc → `help` **and** self-built compile fixture → gcc → run exit 0.
- **IndexAssign:** `obj[key] -> val` → `ZenValue_set_at` (was noop; broke `B[`graph`]` / `CG[`buf`]`).
- **Free-fn namespacing:** `lib/zen/*` + `selfhost/compiler/*` → `Prefix_name` + same-file bare-call rewrite; import-alias → `z_Prefix_fn`. Fixtures stay bare.
- **String escapes under -g:** `escape_piece()`; real NL/TAB helpers; no multi-branch UAM on escape char.
- Bootstrap remains the daily `bin/zen` (`./scripts/zen install`).

## Backend & memory decision

**Status: accepted** (aligned with Zen product model).

### Compiler backend (selfhost)

| Choice | Decision |
|--------|----------|
| **User programs (AOT)** | **AST → ZenValue C** (`Codegen.zl` + `Driver.zl`) — keep |
| **Language values / mix ABI** | **`ZenValue`** — compiled and interpreted share this |
| **Compiler pipeline IR** | **Native Token/AST structs** (maps today are transitional) |
| **Scripts** | **Bytecode VM** in `runtime/` (today: AST walk — transitional) |
| **Not on critical path** | Full **MIR / SMIR** port from bootstrap; VM-only (no C AOT) |
| **Rule** | Do **not** half-port MIR dataclasses + partial generators while C still walks AST |

Product write-up and phase order: [THREE_LAYER.md](THREE_LAYER.md).

Bootstrap may keep SMIR for its own analysis (UAM warnings under `-g`). Selfhost does **not** need SMIR to ship or to implement managed memory.

### Language memory model (product)

| Mode | Who manages | Mechanism |
|------|-------------|-----------|
| **Default** | Runtime / compiler | Automatic lifetime for ordinary values (`ZenValue` heap, retain/release or equivalent hybrid over time) |
| **Opt-in** | Programmer | `zen.memory` regions/arenas (`with`, allocate-into), pointers (`source`/`&`, `target`/`*`), `owned` / `borrowed` |

Users never see MIR. They write normal code, or drop into regions/pointers for memory-sensitive work.

### Implementation stack (preferred)

```
Source → Checker (light default; stricter on opt-in ownership)
      → Compiler IR (native Token/AST structs — maps transitional)
      → Script: bytecode VM  |  Program: Codegen AST→C
      → runtime/ (ZenValue ABI + arenas + future VM)
```

| Layer | Responsibility |
|-------|----------------|
| **runtime/** | ZenValue ABI; automatic reclaim; arenas; script VM when phase 3 lands |
| **lib/zen/memory** | User-facing Region/Arena APIs |
| **Checker** | Opt-in rules (borrow escape, use-after-move on `owned`) — grow as needed |
| **Codegen** | User AOT AST→C; region enter/exit hooks; no bootstrap MIR port |

### When to reopen full SMIR (future only)

Only if real apps force one of:

1. RC/automatic path cost dominates and **region-default** is required system-wide  
2. Compile-time UAF proof is required for **default** code, not just opt-in  
3. Hard realtime / no-RC targets need static scheduling  

Until then: improve **runtime + opt-in checker + codegen hooks**. Historical design notes: `doc/archive/proposal/memory.md` (context only, not active plan).

### Full selfhost endgame (product goal)

**Target:** drop Python bootstrap as the production host. Zen is **fully Zen**:

| Capability | Goal |
|------------|------|
| Compile / recompile | Selfhost only |
| Link + run native | Selfhost owns gcc/runtime pipeline |
| All language features | Parser + checker + Codegen parity with bootstrap language surface |
| Interpret without Python | Zen bytecode/AST interpreter in selfhost (after AOT host works) |

**Ordered work (active):**

| # | Work | Status |
|---|------|--------|
| 1 | **CCompile-equivalent** — `build` / `run`/`-g` (Zen→C→gcc→run) | **Done MVP** (`CLink.zl` + Driver) |
| 2 | **Closures + patterns + enums** in Parser/Codegen | **Done MVP** (see below) |
| 3 | **`with`/region emit** in Codegen | **Done MVP** (see below) |
| 4 | **Checker depth** | **Done MVP** (with/class/enum/lambda/is) |
| 5 | **Interpret in Zen** (no Python) | **Done MVP** (AST walk; see below) |
| — | **MIR/SMIR port** | **Not** on path |

#### #2 language surface (MVP)

| Feature | Support |
|---------|---------|
| **enumerator** | Parse members; emit `z_Enum_Variant` via `ZenValue_make_variant`; `Color.Red` get |
| **lambdas** | `function(x) { … }`; free-var capture → `ZenValue_from_closure`; call via `ZenValue_apply` |
| **`is` patterns** | Parse `value is Pattern`; list/map bind unpack in `when`; enum payload `is Enum.Var(x)` |
| **Fixtures** | `enum_color.zl`, `closure_add.zl`, `pattern_bind.zl`, `enum_payload.zl`, `class_dispatch.zl`, `closure_nested.zl` |

Phase B: list/map bind, payload variants, `__type` method dispatch, nested closures — **Done**.

#### #3 `with` / region emit (MVP)

| Feature | Support |
|---------|---------|
| **Parse** | `with expr [as name] { body }` → `WithStatement` |
| **Emit** | If resource is `ZEN_ARENA`: `ZenMemory_push_arena` + `__with_pushed`; body; pop on exit |
| **Memory builtins** | `memory.*` / `__builtin_memory.*` → `ZenMemory_*` / free wrappers |
| **Fixture** | `with_region.zl` — depth +1 inside, restore after; anonymous `with` too (selfhost `run` exit 0) |

#### #4 Checker depth (MVP)

| Feature | Support |
|---------|---------|
| **with** | Resource expr checked; `as` alias bound in body only; typed alias; soft non-arena note |
| **class** | Class type + method table; ctor/`obj.meth` resolution; arity + unknown-method |
| **enumerator** | Declare enum type + member tags |
| **lambda / is** | `FunctionExpression` scoped params; `IsExpression` → Boolean |
| **owned/borrowed** | Opt-in: use-after-move on `owned`; borrowed escape from `with` |
| **Tests** | `test_checker.zl` 16 cases (interpret + `-g`) |

Phase C: method resolution, typed with, opt-in ownership — **Done**. Inference/generics still open.

#### #5 Interpret in Zen (MVP)

| Feature | Support |
|---------|---------|
| **Engine** | `compiler/Interpreter.zl` — map env (`outer`/`values`), free-fn walker |
| **Surface** | lets, when, functions/calls, return, arithmetic, compare, blocks, literals (int coerce; STRING not coerced) |
| **CLI** | `interpret` / `eval` `<file.zl>` — exit code from integer `main` |
| **Tests** | `test_interpreter.zl` 22/22 interpret + 22/22 `-g` |
| **Phase A** | **Done** — import graph (`interp_import`), for-in + IndexAssign + maps, `import zen.text.string as Str` |
| **Phase D** | **Done** — classes/`extends`/`parent.meth`, closures (by-value), enums/`is` (incl. payload), `with` + software arena, Default TypeAnn zeros |

Residual: real stdout (`__builtin_output` no-op), host `zen.test` runner, interpreting `selfhost/zen.zl` itself. Fixture matrix: `tests/self_hosting/fixtures/MATRIX.md`.

**Next implementation plan (phased A–E + L):** [ENDGAME_PLAN.md](ENDGAME_PLAN.md) — Interpreter core → **L Nothing/Default (required)** → Codegen → Checker → Interpret host depth → Product handoff/bootstrap drop.

### Required: `Nothing` / `Default` (Phase L)

| Form | Meaning | Status |
|------|---------|--------|
| **`Nothing`** | Absent / no value; compare with `== Nothing` | **Done** — canonical capitalized; lowercase alias still lexed |
| **`Default`** | Type zero-state (`0`, `[]`, ``, `False`, …); assign + `== Default` | **Done MVP** — Integer/Boolean/String/List; fixture `nothing_default.zl` |

See ENDGAME_PLAN *Required language surface* and Phase L. Blocks host-1.0.

Host-1.0 daily install is hybrid `./scripts/zen install` (selfhost compiler CLI + bootstrap language host). Bootstrap is the **maintenance fallback** for missing language features and emergency rollback — not the documented front door.

### Critical path (historical milestones)

1. Production handoff hybrid — **done**  
2. Memory auto + opt-in arenas — **done**  
3. Classes + inheritance — **done**  
4. Multi-unit self-rebuild — **done**  
5. Selfhost `build`/`run` — **done MVP**  
6. Full language + interpret — **#1–#5 MVP done**; deepen interpret/host toward bootstrap drop

### Production handoff (hybrid)

Selfhost is a **compiler CLI** (`compile` / `build` / `run` / `interpret` / `check` / `deps` / `help`). Interpret MVP covers pure arithmetic/control; bootstrap remains full language host. Handoff is therefore hybrid:

| Binary | Role |
|--------|------|
| `bin/zen-bootstrap` | Full language host (interpret, `-g`, `--check`, `--test`) |
| `bin/zen-selfhost` | Native selfhost compiler |
| `bin/zen` (handoff) | Routes `compile`/`build`/`run`/`interpret`/`test`/`check`/`deps`/`help` → selfhost; bare `.zl` / `--check` → bootstrap; `-g` tries selfhost then bootstrap |

```bash
./scripts/zen install              # Host-1.0: hybrid bin/zen (selfhost primary)
./scripts/zen install-bootstrap    # zen-bootstrap only (maintenance)
./scripts/zen install-rollback     # emergency: bin/zen → bootstrap
./scripts/zen ci-soak              # local gate: smoke + hybrid + golden
```

Overrides: `ZEN_FORCE_BOOTSTRAP=1`, `ZEN_INTERPRET=selfhost` (bare `.zl` via selfhost interpret), `ZEN_GENERATE=bootstrap` (skip selfhost `-g` attempt). Default hybrid `-g` tries selfhost first.

**Status: hybrid Host-1.0 + native interpret + native test runner.** Native fixture compile streams C to disk. Native `compile selfhost/zen.zl` **emits** (~15 min, ~1MB C); gcc+help of that unit are green; the rebuilt binary compiles `stage7_add` to `z_add`. Golden: `./scripts/zen test-golden`. Local soak: `./scripts/zen ci-soak`. Self-rebuild stays opt-in (`ZEN_SELFHOST_REBUILD=1`) for duration.

## Roadmap beyond 7.x (long-term compiler)

| Track | Goal | Notes |
|-------|------|--------|
| **Multi-unit C** | One C TU per `.zl` + host main, linked | **MVP done** — see below |
| **Classes / methods** | Class bodies, methods, `self` | **MVP done** — map-backed + `Type_method` |
| **Backend / memory** | AST→C + auto default + opt-in regions | **Decided** — see above; MIR deferred |
| **Production handoff** | Hybrid `bin/zen` + bootstrap language host | **Done** — `install-handoff` + `handoff-soak` green |
| **Name stability** | Freeze `module_fn_prefix` table | Or supersede with multi-unit exports |

### Multi-unit C (MVP)

Default `compile` still dep-merges into **one** C unit (self-rebuild path).

`--multi` / `-m` path:

- `Driver.compile_file_multi(entry, out_dir, do_check)` → one `.c` per dep + `zen_host_main.c`
- Per unit: `Codegen.transpile_unit_ex(prog, with_main=false, init_name, shared_protos)`
- Shared free-fn prototypes at top of every unit (external linkage)
- Unique non-static inits: `zen_mod_init_<stem>()`; host calls them in dep order then `zen_main`
- Namespacing rules unchanged (`should_namespace_path` / fixtures bare)
- CLI: `compile file.zl outdir --multi`
- Smoke: `selfhost_smoke` §5d multi_main --multi → gcc multi TU → exit 0
- **Cross-TU globals:** shared `extern ZenValue z_*` for module lets (`AST.K_*`, …)
- **Multi self-rebuild:** `compile selfhost/zen.zl outdir --multi` → gcc all TUs → help + fixture
  - Gate: `./scripts/zen multi-selfhost-smoke` (heavier than default selfhost-smoke)
- Limits: module-global name collisions if two units define the same bare let name

### Classes / methods (MVP + inheritance)

- **Parser:** `class Name [extends Base] { … }` → `ClassStatement` (`base` key; lexer `EXTENDS` token)
- **Codegen:** map instance (`ZenMap` + `__type` + optional `__base`)
  - `Class_new` → field defaults along base chain; init from nearest owner with `init`
  - Methods → `z_Class_method(z_self, …)`; overrides = last registration wins (emit base then derived)
  - `parent.meth(args)` → `z_Base_meth(z_self, args)` inside method bodies
  - `Class(args)` → `Class_new`; `obj.meth` → registered owner
- **Fixtures:** `class_counter.zl`, `class_inherit.zl` (override + parent.speak + inherited fields)
- **Not yet:** vtables/dynamic `__type` dispatch, multi-level parent chain sugar, typed C structs, reflect.call

**Limits:** two unrelated classes with the same method short-name: last emitted wins for `obj.meth`.

**Dual-path lessons (Stage 7)**

- Under `-g`, rebinding `let` inside nested `when` does not stick — branch helpers / recursion.
- `is_kind` exact only; operator layers kind-only; IndexAssign required for module maps.
- Multi-branch reuse of string locals (esc) → UAM under `-g`; factor helpers (`escape_piece`).
- Smoke must rebuild `bin/zen-selfhost` after Driver/Codegen changes.

## Workflow per stage

1. Diff bootstrap module(s) → list missing constructs
2. Port / rewrite selfhost component in dual-path Zen
3. Add/extend tests under `tests/self_hosting/` (and native_compiler if useful)
4. Run interpret + `-g` for those tests
5. Update `selfhost/AGENTS.md` status line for the stage
6. Only then open the next stage

## Tracking

- Status lines live in `selfhost/AGENTS.md`
- Historical experiments: `archive/selfhost-experiment/`
