# Selfhost endgame implementation plan

**Status:** active (post MVP #1–#5)  
**Authority:** bootstrap remains language host until Product gates say otherwise  
**Backend:** three-layer — ZenValue ABI + compiler native IR + script VM; user AOT stays AST→C; MIR/SMIR **not** on path  
**Companion:** [PARITY.md](PARITY.md), [THREE_LAYER.md](THREE_LAYER.md)

## Goal

Ship a **fully Zen production host**: compile, recompile, link, run, and interpret without Python for the language surface used by the compiler, stdlib, tests, and typical apps. Hybrid handoff is the bridge; bootstrap drop is the exit.

```
Today                          Target
-----                          ------
bin/zen-bootstrap  (full host) → retired or emergency fallback only
bin/zen-selfhost   (compiler)  → full host (compile + interpret + run)
bin/zen handoff    (router)    → pure selfhost bin/zen
```

## Baseline (done)

| Track | MVP delivered |
|-------|----------------|
| Codegen/Driver | multi-unit C, classes+extends, enums, lambdas/`is`, `with`/arena emit, CLink `build`/`run` |
| Checker | names, redecl, structs, with-alias, class `self`, enum/`is`/lambda |
| Interpret | pure arithmetic/control, functions, `when`, int coerce, CLI `interpret` |
| Product | hybrid `install-handoff` + `handoff-soak`; self-rebuild smoke |

## Principles

1. **Bootstrap is authority** until a feature is dual-path green in selfhost *and* fixture-parity with bootstrap behavior.
2. **Dual-path for selfhost sources:** interpret + `-g` on stage tests; never ship a stage that only works under one host.
3. **Thin vertical slices:** each phase ends with a fixture + CLI path, not a partial API.
4. **Shared AST contract:** interpret and Codegen consume the same Stage-2 map AST; fix Parser once.
5. **Memory product unchanged:** auto default; opt-in arenas/ownership; no MIR mid-end.
6. **Do not rebind `parent` / reserved soft names** in selfhost code; env maps use `outer`.
7. **Product routing expands only when soak green** — never route bare `.zl` interpret to selfhost until gate says so.
8. **Capitalized special values & types (required):** language sentinels and type names use **PascalCase** like other types — canonical forms are `Nothing`, `Default`, `True`, `False`, `Integer`, `String`, … Lowercase `nothing` is legacy; endgame standard is capitalized only (see Phase L).

## Required language surface — `Nothing` and `Default`

**Status: required for host-1.0** (not optional polish). Design source: [doc/Zenlang Explained.md](../doc/Zenlang%20Explained.md) §2.3, archive Type Rules.

| Sentinel | Meaning | Assign | Compare |
|----------|---------|--------|---------|
| **`Nothing`** | No value / absent | `let x -> Nothing` | `when x == Nothing` |
| **`Default`** | Type’s zero / empty state | `let x : Integer -> Default` → `0` | `when x == Default` (true if value equals type zero) |

### Zero table for `Default` (required)

| Type context | `Default` materializes as |
|--------------|---------------------------|
| `Integer` / numeric ints | `0` |
| `Decimal` | `0.0` (or type-width zero) |
| `Boolean` | `False` |
| `String` / `Rune` | `` (empty) |
| `List` / dynamic sequence | `[]` |
| `Map` | `{}` |
| Structure / class | each field Default, or empty map instance per class rules |
| `Variant` / unknown | soft: `Nothing` or reject without type context — document choice |
| No type context | **error** (Default needs a type; Nothing does not) |

### Capitalization policy (required)

| Form | Role |
|------|------|
| `Nothing`, `Default` | **Canonical** literals / keywords |
| `True`, `False` | Already canonical booleans |
| `nothing`, `default` | **Legacy** — accept during transition if needed; **deprecate**; new code and selfhost sources use capitalized forms only |
| Spec / docs / editor snippets | Prefer `Nothing` / `Default` only |

`default` in prose like `check … or default` means “fallback branch,” not the `Default` sentinel — keep wording distinct in docs.

### Semantic rules

1. `x == Nothing` ⇔ value is absent (current Nothing semantics).
2. `x == Default` ⇔ value **equals** the zero-value of **x’s static/inferred type** (not “is the Default token”).
3. `Nothing` and `Default` are **not** the same (`0 != Nothing`, `[] != Nothing`).
4. `is Nothing` / `is Default` may alias equality for patterns once `is` bind work lands.
5. Checker: materialize `Default` using declared type of binding or expected type of expression.

---

## Recommended sequence (why this order)

```
Phase A  Interpret core (imports + for + maps/lists)
    ↓ enables running more of selfhost tests under interpret CLI
Phase L  Nothing/Default sentinels + capitalization (REQUIRED)
    ↓ language truth for empty/absent; both hosts
Phase B  Codegen language gaps (patterns, enum payload, class dispatch polish)
    ↓ same AST; compile path catches up to parse surface
Phase C  Checker ownership + method resolution
    ↓ safety before widening product routing
Phase D  Interpret host depth (classes, closures, with, builtins)
    ↓ selfhost can run real scripts
Phase E  Product handoff → bootstrap drop
```

**Rationale:** interpret *imports* unblock dogfooding; **L is required language surface** (docs already promise Default; Nothing capitalization matches type style) and should land before claiming product completeness; codegen gaps are compile-path blockers; checker ownership is smaller/opt-in; product moves last so soak never regresses CI.

Parallelism allowed:

- **A ‖ L** after Lexer/Parser tokens exist for `Default` (L can start immediately).
- **A ‖ B** after Parser fixtures are shared (patterns need Parser work first if incomplete).
- **C** can start after with/class declare is stable (already is); **C** should understand Default materialization types.
- **D** depends on A (modules) before class/closure interpret; D must honor Nothing/Default once L lands.
- **E** depends on D + B + **L** for any host we claim is complete.

---

## Phase A — Interpreter core (modules + data + loops)

**Owner files:** `compiler/Interpreter.zl`, `Driver.zl`, `tests/self_hosting/test_interpreter.zl`, new fixtures  
**Depends on:** Stage 3 Resolver/GraphBuilder (already MVP)

### A1. Import graph under interpret

| Item | Detail |
|------|--------|
| Work | Resolve `import` / `from … import` via existing `Module.Resolver` + `GraphBuilder`; load deps in order; define alias as module map of exports |
| Scope | Free functions + module-level lets only first; skip classes in imported modules until D |
| API | `interpret_file` loads graph; entry `main` only |
| Fixture | `fixtures/interp_import.zl` + tiny lib module; exit 0 |
| Exit | dual-path tests; `selfhost/zen.zl interpret` on fixture |

### A2. Lists, maps, index, for-in

| Item | Detail |
|------|--------|
| Work | List/map literals already partial; complete `IndexAssign`, `.length`, `for x in iter`, string index if needed |
| Fixture | list sum / map get-set roundtrip |
| Exit | parity with stage5_for_sum semantics under interpret |

### A3. Builtins minimum for scripts

| Item | Detail |
|------|--------|
| Work | Map `__builtin_*` / common free names used by fixtures: file read (already), `io.writeln` soft, `Str.*` via imported `zen.text.string` once A1 works |
| Exit | interpret a file that `import zen.text.string as Str` and uses `Str.to_string` |

### A exit criteria

- [x] `interpret` runs all pure fixtures that do not need classes/closures: `stage7_add`, for-sum, import graph
- [x] `test_interpreter.zl` ≥ 12 cases, dual-path green
- [x] No Driver import in unit tests that would force full CLink graph under `-g`

**Status: Done** (A1–A3). Fixtures: `interp_import.zl` + `interp_lib.zl`, `stage5_for_sum.zl`, `interp_map.zl`, `interp_str.zl`.

---

## Phase L — `Nothing` / `Default` sentinels (**required**)

**Owner files (both hosts):**  
- Bootstrap: `Lexer/Token.py`, Parser AST + primary expr, Interpreter literals, Codegen/C if needed, TypeChecker  
- Selfhost: `compiler/Token.zl`, `Lexer.zl`, `Parser.zl`, `AST.zl`, `TypeChecker.zl`, `Codegen.zl`, `Interpreter.zl`  
- Docs: `doc/Zenlang Explained.md` (already sketches Default), formal spec `3_types_literals.typ`, editor snippets  
- Tests: `tests/self_hosting/fixtures/nothing_default.zl`, language suite cases  

**Priority:** required before **E** / host-1.0; preferred early (can run ‖ A).

### L1. Canonical `Nothing`

| Item | Detail |
|------|--------|
| Work | Treat **`Nothing`** as the only documented form; lexer keyword already mostly present — ensure Parser/Checker/Interpreter/Codegen accept `Nothing` everywhere lowercase `nothing` works today |
| Migration | During transition, accept `nothing` as alias → same literal; selfhost + new examples use `Nothing` only |
| End state | Spec + snippets + core docs show `Nothing`; optional lint/warn on lowercase later |
| Exit | Fixture: assign + `== Nothing` + `is Nothing` dual-path bootstrap + selfhost interpret/run |

### L2. Implement `Default` end-to-end

| Item | Detail |
|------|--------|
| Work | Token `DEFAULT` / keyword `Default`; AST literal `DefaultLiteral` (or shared special lit with kind); type-driven materialize using zero table above |
| Checker | `Default` in typed `let x : T -> Default` OK; bare `Default` without expected type → error; `x == Default` uses type of `x` |
| Interpret | Evaluate Default → zero of expected type; `==` compares values after materialize |
| Codegen | Emit zero C/`ZenValue` for type (int 0, empty list/map/string, False, …) |
| Fixture | `nothing_default.zl`: Integer/String/List/Boolean assign Default; equality true; Nothing ≠ 0 / ≠ [] |
| Exit | bootstrap interpret + `-g` + selfhost `run` + selfhost `interpret` all exit 0 |

### L3. Capitalization consistency pass

| Item | Detail |
|------|--------|
| Work | Prefer `Nothing`/`Default`/`True`/`False` in selfhost compiler sources, new tests, Getting Started / Explained / formal Nothing section |
| Editors | VSCode/Sublime/Zed snippets and syntax: highlight `Nothing`/`Default` as constants (alongside `True`/`False`) |
| Stdlib | Gradual: new APIs and docs use capitalized forms; mass-rewrite of all `nothing` in lib is allowed but can be staged |

### L exit criteria

- [x] `Default` assign + compare works for Integer, Boolean, String, List at minimum (Map recommended)
- [x] `Nothing` is canonical in new fixtures/selfhost sources; lowercase still accepted
- [x] Zero table documented in formal spec §literals (not only Explained)
- [x] Fixture `nothing_default.zl` on interpreter suite + bootstrap interpret/`-g` + selfhost `interpret`
- [x] PARITY / this plan mark Phase L **Done**
- [x] **Required** for host-1.0 — E3 drop criteria include L

**Status: Done.** Formal spec §literals zero table and editor highlight of `Default` landed.

---

## Phase B — Codegen language depth

**Owner files:** `compiler/Codegen.zl`, `Parser.zl` (if bind patterns incomplete), fixtures, `test_codegen.zl`  
**Depends on:** #2 MVP (enums/lambdas/`is`)

### B1. Pattern bind unpack & Advanced Pattern Matching

| Item | Detail |
|------|--------|
| Work | `when x is [a, b, c]` / map field binds (`{ x -> px }` or `{ x, y }`); list spreads `[first, ...rest]`; structure destructuring `Point { x, y }`; pattern guards (`when cond when guard`); `check <expr> { case <pat> [when <guard>] { ... } } [or { ... }]` |
| Parser | `RestPattern`, `CheckStatement`, `case_clause_guard`, list ellipsis `...`, struct shorthand field matching |
| Interpreter | `match_struct_pattern`, `match_enum_payload`, `slice_list_rec`, `eval_check_stmt`, `eval_check_cases_rec` |
| Codegen | `ZenList_slice_from`, structure field destructuring, case guard conditions, `emit_check_stmt`, `emit_check_cases` |
| TypeChecker | `check_check`, `check_pattern_binds` with scoped bindings |
| Fixtures | `tests/self_hosting/fixtures/pattern_bind.zl`, `tests/language/pattern_matching_02.zl` |
| Exit | dual-path green across interpret and native `-g` |

### B2. Enum payload variants

| Item | Detail |
|------|--------|
| Work | `Some(value)` style members; emit make_variant with payload; `is` + extract or match bind |
| Fixture | option-like enum roundtrip under `run` |

### B3. Class dispatch polish

| Item | Detail |
|------|--------|
| Work | Prefer `__type` (or registered type tag) for `obj.meth` when multiple classes share short names; keep last-wins as fallback |
| Optional | multi-level `parent` chain sugar (document if deferred) |
| Fixture | two unrelated classes same method name; correct dispatch |

### B4. Nested / edge closures

| Item | Detail |
|------|--------|
| Work | nested lambdas, capture of outer lets, call via `ZenValue_apply` already present — fix edge failures |
| Fixture | extend `closure_add.zl` or new nested capture fixture |

### B exit criteria

- [x] PARITY #2 “still open” items closed or explicitly deferred with reason
- [x] selfhost_smoke includes pattern + payload enum fixtures (`pattern_bind`, `enum_payload`, `class_dispatch`, `closure_nested`)
- [x] Advanced pattern matching verified: list spreads `[head, ...tail]`, struct destructuring, pattern guards, and `check` statements
- [x] No MIR reintroduction

**Status: Done.** Multi-level `parent` chain sugar deferred (existing `parent.meth` → base free fn remains). Advanced pattern matching fully landed in both AST interpreter and C codegen.

---

## Phase C — Checker depth (ownership + resolution)

**Owner files:** `TypeChecker.zl`, `Types.zl`, `test_checker.zl`  
**Product rule:** light default; **strict only on opt-in** `owned` / `borrowed` / region escape

### C1. Method / call resolution

| Item | Detail |
|------|--------|
| Work | Resolve `obj.meth` against class method table; arity soft-check; `Module.fn` after import alias |
| Exit | tests for wrong arity optional; unknown method diagnostic |

### C2. Typed `with` / arena resource

| Item | Detail |
|------|--------|
| Work | When resource type is arena/region (named or structure tag), allow alias type; warn if non-resource used with push semantics (soft) |
| Exit | checker test that with-alias is scoped (already); optional type tag on alias |

### C3. Opt-in ownership rules

| Item | Detail |
|------|--------|
| Work | Track `owned` / `borrowed` annotations if present in AST; reject obvious escape of borrowed out of `with`; use-after-move on `owned` where AST marks move |
| Non-goal | prove UAF on default automatic values |
| Exit | small suite of intentional error programs |

### C exit criteria

- [x] `test_checker.zl` dual-path; ownership tests isolated
- [x] `compile --typecheck` on selfhost sources does not explode (may still be soft)
- [x] Documented in PARITY #4 still-open → done/deferred

**Status: Done.** Full inference/generics still out of scope. Untyped (`Variant`) `with` aliases are not borrowed; Integer/arena aliases are.

---

## Phase D — Interpreter host depth

**Owner files:** `Interpreter.zl`, builtins table, fixtures  
**Depends on:** Phase A; Codegen class/closure semantics as behavioral reference

### D1. Classes + inheritance under interpret

| Item | Detail |
|------|--------|
| Work | Map instances + method table like Codegen (`Class_new`, `self`, `parent.meth`); `extends` field chain |
| Fixture | interpret `class_counter.zl` / `class_inherit.zl` exit 0 |

### D2. Closures + `is` + enums

| Item | Detail |
|------|--------|
| Work | FunctionExpression with capture env; enumerator tags; `is` equality |
| Fixture | interpret `closure_add.zl`, `enum_color.zl` |

### D3. `with` + memory builtins

| Item | Detail |
|------|--------|
| Work | Call into runtime-like hooks if available under host, or soft stack of arenas in interpret state matching Codegen push/pop semantics |
| Fixture | interpret `with_region.zl` exit 0 (may require builtin memory shim) |

### D4. Stdlib surface for dogfood

| Item | Detail |
|------|--------|
| Work | Enough of `zen.text.string`, `zen.io.io`, `zen.test` to run `tests/self_hosting/test_*.zl` under `selfhost interpret` **or** document residual bootstrap-only APIs |
| Stretch | interpret `selfhost/zen.zl help` without Python (native selfhost binary already can for compile path) |

### D exit criteria

- [x] All current selfhost fixtures pass under both `run` (AOT) and `interpret` where language-complete
- [x] `test_interpreter` dual-path; optional native selfhost binary `interpret` smoke
- [x] Written matrix: fixture × interpret × run

**Status: Done.** `test_interpreter.zl` 22/22 interpret + 22/22 `-g`. CLI `selfhost/zen.zl interpret` on class/enum/closure/with fixtures exit 0. Matrix: `tests/self_hosting/fixtures/MATRIX.md`. Residual bootstrap-only: real stdout (`__builtin_output` no-op), host `zen.test` runner, interpreting `selfhost/zen.zl` itself.

---

## Phase E — Product: handoff → bootstrap drop

**Owner files:** `scripts/zen`, `scripts/zen_bin_handoff.sh`, `scripts/handoff_soak.sh`, `scripts/selfhost_smoke.sh`, CI  
**Depends on:** A–D for any path we re-route

### E1. Expand hybrid routing (incremental)

| Step | Route to selfhost when | Gate |
|------|------------------------|------|
| E1a | `interpret` / bare script subset | **Done** — `interpret`/`eval` → selfhost; bare `.zl` via `ZEN_INTERPRET=selfhost` |
| E1b | `-g` / generate via selfhost first, bootstrap fallback | **Done** — default try-selfhost; `ZEN_GENERATE=bootstrap` skips |
| E1c | `--test` / test runner via selfhost | **Done** — `bin/zen test` / `--test` dispatches to native selfhost test runner; real `io.*`/`output.*` builtins connected |

Keep `ZEN_FORCE_BOOTSTRAP=1` forever as escape hatch until drop.

### E2. Soak and CI

| Item | Detail |
|------|--------|
| Work | **Done** — `handoff-soak` interpret matrix (11 fixtures) + `ZEN_INTERPRET` + `run` + generate opt-out; threshold ≥ 20 PASS |
| CI | Local only (no GitHub Actions). Fast: `./scripts/zen ci`. Soak: `./scripts/zen ci-soak` → handoff-soak. Self-rebuild of `zen.zl` still opt-in |
| Multi | keep `multi-selfhost-smoke` as heavy optional gate |

### E3. Bootstrap drop criteria (all required)

1. **Compile path:** selfhost compiles `selfhost/zen.zl` and core `lib/zen` used by compiler; self-rebuild + multi-unit green  
2. **Run path:** selfhost `run`/`-g` matches bootstrap on a fixed golden set (language + selected lib tests)  
3. **Interpret path:** selfhost `interpret` runs the same golden set (or policy: interpret only for `.zs`/scripts; AOT for apps — document)  
4. **Language sentinels (Phase L):** `Nothing` + `Default` (assign + compare) on both hosts; capitalized specials are the documented standard  
5. **Handoff soak** — local gate `./scripts/zen ci-soak` (this repo has no remote CI)  
6. **Docs:** Getting Started / Tooling point at Host-1.0 selfhost-primary install; PARITY marks bootstrap “maintenance fallback” — **done**  
7. **Rollback:** in-tree `bootstrap/` + `./scripts/zen install-rollback` / `ZEN_FORCE_BOOTSTRAP=1` (local project; no release tags) — **done**  

### E4. Post-drop cleanup

- Archive or freeze Python bootstrap evolution (bugfix only)
- Remove hybrid router complexity if pure selfhost `bin/zen`
- Script bytecode VM is **layer 3** of the product ([THREE_LAYER.md](THREE_LAYER.md)), not optional polish — required before E4 routes bare `.zl` to selfhost

**Status: Host-1.0 complete (E1–E3).** Product target is **three-layer Zen** ([THREE_LAYER.md](THREE_LAYER.md)). Working toward E4 without expanding routing yet.

Remaining before drop:

1. Soak stays green (`./scripts/zen ci-soak`).
2. **Layer 2:** compiler Token/AST as native structs (maps transitional) so `zen-selfhost` is usable.
3. **Layer 3:** bytecode VM for scripts; AOT stays C.
4. Mix: VM ↔ compiled modules on `ZenValue`.
5. Edit-loop rebuild: `ZEN_OPT=0 ./scripts/zen install-selfhost-fast`; cached runtime `.o`. Self-rebuild of `zen.zl` still `ZEN_SELFHOST_REBUILD=1`.
6. Bare `.zl` stays bootstrap until layers 2+3 are what you’d actually use.
7. Then E4: freeze Python as emergency-only.

Golden `./scripts/zen test-golden`. Soak: `./scripts/zen ci-soak`. Rollback: `./scripts/zen install-rollback`.

Hybrid `bin/zen` (default install):

- `compile` / `build` / `run` / `interpret` / `eval` / `test` / `--test` / `check` / `deps` / `help` → selfhost
- Bare `.zl`, `--check`, `--repl` → bootstrap
- `-g` / `--generate` → try selfhost compile+link+run, then bootstrap (`ZEN_GENERATE=bootstrap` skips)
- `ZEN_INTERPRET=selfhost` → bare `.zl` via selfhost interpret
- `ZEN_FORCE_BOOTSTRAP=1` → always bootstrap

Soak: `handoff_soak.sh` interpret matrix via native `zen-selfhost interpret` (Driver `interpret`/`eval` are CLI tokens; argv0 skip no longer swallows the command).

### E exit criteria

- [x] Hybrid routes `interpret` (and `run`/`build`) to selfhost; soak expanded (endgame-E)
- [x] Default `./scripts/zen install` produces selfhost-primary `bin/zen` (E3 / host-1.0)
- [x] CI green without requiring Python for user-facing compile/run/interpret
- [x] PARITY endgame table: all rows **Done** (depth, not just MVP)

---

## Cross-cutting work

| Item | When | Notes |
|------|------|-------|
| Parser bind patterns | before B1 | share AST with interpret D2 |
| Exact `is_kind` (no contains) in Checker | C anytime | align with Parser contract |
| Codegen `queue_lambda` / list append under `-g` | if blocks dual-path of large graphs | known native method-call quirks |
| Runtime memory quality | with D3 / C3 | dual arena stacks already; keep API stable |
| Fixture matrix doc | start of A | `tests/self_hosting/fixtures/MATRIX.md` or section in this file |
| DOX | every phase | update `selfhost/AGENTS.md`, `compiler/AGENTS.md`, PARITY status tables |

---

## Verification ladders (every phase)

```bash
export ZEN_PATH=$PWD:$PWD/selfhost:$PWD/lib

# Stage unit dual-path
for t in test_lexer test_parser test_module test_checker test_codegen test_driver test_interpreter; do
  python3 bootstrap/Zen.py tests/self_hosting/${t}.zl
  python3 bootstrap/Zen.py -g tests/self_hosting/${t}.zl
done

# Feature fixtures (expand as phases land)
python3 bootstrap/Zen.py selfhost/zen.zl interpret tests/self_hosting/fixtures/stage7_add.zl
python3 bootstrap/Zen.py selfhost/zen.zl run tests/self_hosting/fixtures/with_region.zl

# Product gates
./scripts/zen install-selfhost
./scripts/zen selfhost-smoke
./scripts/zen install-handoff
./scripts/zen handoff-soak
```

Phase-specific: add fixture to smoke before claiming phase done.

---

## Suggested milestone tags

| Tag | Meaning |
|-----|---------|
| `endgame-A` | interpret imports + for/list/map + Str import |
| `endgame-L` | `Nothing`/`Default` sentinels + capitalization (**required**) |
| `endgame-B` | patterns + enum payload + dispatch polish in Codegen |
| `endgame-C` | ownership checker MVP |
| `endgame-D` | interpret classes/closures/with; fixture matrix AOT‖interp |
| `endgame-E` | hybrid routes interpret; soak expanded |
| `host-1.0` | bootstrap drop criteria met (includes L) |

---

## Explicit non-goals (this plan)

- Full MIR/SMIR port into selfhost  
- Proving UAF on automatic (non-owned) values  
- Package manager / LSP / net.http (see `doc/plan.md` product roadmap — separate)  
- Replacing C runtime with pure Zen  
- Bit-identical C output vs bootstrap (behavioral parity only)

---

## First concrete sprint (start here)

1. **A1** import graph interpret + fixture  
2. **A2** for-in + index assign under interpret  
3. **A3** `import zen.text.string` works under interpret  
4. **L1–L2** Lexer/Parser `Default` + zero materialize (bootstrap + selfhost); canonical `Nothing`; fixture `nothing_default.zl`  
5. Track B1 only if Parser already has bind nodes; else Parser spike then B1  
6. Do **not** expand handoff routing until A fixtures soak under hybrid manually  

**Note:** Phase L is **required**, not optional. Prefer landing L early so new tests/docs never teach lowercase-only `nothing` or omit `Default`.

---

## Tracking

Update this file’s checkboxes and PARITY status tables when a phase exits.  
Child detail lives in `compiler/AGENTS.md` Work Guidance; do not duplicate long history — link here.
