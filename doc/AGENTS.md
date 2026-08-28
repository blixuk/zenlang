# Purpose

All project documentation, language specification, design documents, roadmaps, plans, manifestos, examples, and reference material for Zenlang.

# Ownership

Owned by documentation maintainers. This is the source of truth for "what the project is" and "how it works."

# Local Contracts

- Durable written material belongs under doc/ (or root files like Testing.md and AGENTS.md themselves).
- Specification/ holds the formal language definition (`Zenlang.zm` built to `Zenlang.pdf` using the native Zen Mark Vector PDF generator). Chapters cover syntax, types, control flow, data structures, OOP, concurrency, error handling, modules, runtime, organization.
- Top-level files: Getting_Started.md (tutorial + patterns — preferred on-ramp), Language_Module_and_Reflect.md (module/entry/reflect/plugins language reference), Zen Manifesto.md (core philosophy), Zenlang Explained.md, Zenlang.md, Zenlang Tooling.md, Zenlang_Documentation_Suite.md, Roadmap.md, plan.md, Standard_Library_Reference.md, ideas.md, design_module_reflect.md.
- Human front door for the repo is root `README.md` (quick start + layout); longer tutorial is `doc/Getting_Started.md`. Daily install is Host-1.0 hybrid (`./scripts/zen install`); bootstrap is documented as maintenance fallback.
- archive/ contains historical drafts and proposals. Treat as read-only context, not current spec.
- Memory/MIR: active decision is in `selfhost/PARITY.md` (*Backend & memory decision*) — AST→C for user programs, auto default + opt-in regions; `doc/archive/proposal/memory.md` is historical only.
- Execution product: three-layer (ZenValue + compiler native IR + script VM, AOT remains C) — [selfhost/THREE_LAYER.md](../selfhost/THREE_LAYER.md).
- Documentation that defines process or contracts (Testing.md, roadmaps) is binding in conjunction with AGENTS.md files.
- When implementation or ownership changes, corresponding docs + nearest AGENTS.md must be updated.

# Work Guidance

- Keep prose, spec, and examples in sync with actual language features and stdlib.
- Use examples that can be executed.
- For language surface changes, update both Specification/ chapters and high-level docs.
- Anonymous functions / closures: Zenlang Explained §3.5, Zenlang.md, Specification/7_functions.typ. Outer locals captured **by value**; tests/language/closure_01.zl.
- Ranges: `..` / `..=` in Zenlang Explained §3.4, Zenlang.md, Specification/5_operators_logic.typ + 6_control_flow.typ, Standard_Library_Reference (`zen.math.range`); do not use `...` (rest/spread).
- Module context / entry / reflect / plugins: **Language_Module_and_Reflect.md** (user-facing); keep Getting_Started §4.8b–4.9 and Explained §7 in sync; no `@entry`/`@reflectable` — use `module.entry` and `is reflectable`.
- Prefer direct, operational writing per the Style section in root AGENTS.md.
- Stdlib docs must use nested imports (`use zen.io`, `zen.sys.term`, …); keep the import map in Standard_Library_Reference.md current with `lib/zen/`.
- Run doc/Specification/build.sh when regenerating the PDF.

# Verification

- Consistency checks: docs match code/tests (e.g. feature lists, syntax examples).
- Build of the spec PDF succeeds.
- Review of Roadmap.md / plan.md against actual status in bootstrap/, src/, tests/.
- No stale claims about "implemented" features that are still in roadmap.

# Child DOX Index

- Getting_Started.md — tutorial, language tour, dual execution, design patterns (start here for learners)
- Language_Module_and_Reflect.md — **canonical language docs** for `module`, entry, `use`, reflect, plugins
- Companion programs: `examples/getting_started/` (01–12 + README); `examples/plugins_demo.zl`
- Compiler_Architecture.md / Compiler_Architecture.zm — Three-Layer execution engine (ZenValue ABI, native positional IR structs, VM, AOT C)
- Memory_Model.md / Memory_Model.zm — Automatic reference management, chunk-chained arenas, string interning, snapshot concurrency
- Cookbook.md / Cookbook.zm — Practical recipes for CLI tools, TUI canvas, JSON/ZenData, arenas, mixed ABI
- Style_Guide.md / Style_Guide.zm — Canonical syntax standards and formatting guidelines
- Zenlang Tooling.md / Zenlang_Tooling.zm — Compiler CLI, zendoc, zenmark, zenfmt, and zenlsp
- Zen Manifesto.md, Zenlang Explained.md (§7 modules/reflect), Zenlang.md — philosophy and deeper reference
- Standard_Library_Reference.md (includes `zen.reflect`, `zen.plugins`, `zen.ui.table`, `zen.ui.spinner`, built-in `module`), Playground.md, FileManager.md, Formatter.md, Zenlang_Documentation_Suite.md
- book/: *The Zen of Programming* official book — `doc/book/README.md` & `doc/book/AGENTS.md`
- Roadmap.md, plan.md, ideas.md
- Specification/: Formal spec sources (*.zm), build.sh (`tools/build_spec.zl`), generated Zenlang.pdf & Zenlang.html, ZSP.md, Zen_Data.md, and Zen_Mark.md.
- archive/: Historical proposals (AST, concurrency, memory, modules, error, types, etc.), old drafts, and ideas. Not current.
