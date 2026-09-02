# Purpose

All project documentation, language specification, design documents, roadmaps, plans, manifestos, examples, and reference material for Zenlang.

# Ownership

Owned by documentation maintainers. This is the source of truth for "what the project is" and "how it works."

# Local Contracts

- Durable written material belongs under doc/ (or root files like Testing.md and AGENTS.md themselves).
- **Single Source of Truth:** `doc/SPECIFICATION.md` is the sole immutable ground truth for Zenlang grammar, syntax, types, and execution semantics.
- **Documentation Standards:** All documents must strictly adhere to `doc/DOCUMENTATION_STANDARDS.md`.
- **RFC Proposals Framework:** Proposed language syntax and semantic modifications must undergo the formal RFC review process in `doc/proposals/` using `TEMPLATE.md`.
- Top-level files: SPECIFICATION.md (single source of truth), DOCUMENTATION_STANDARDS.md (style & rules), Zen Manifesto.md (core philosophy), Getting_Started.md (tutorial on-ramp), Standard_Library_Reference.md, Compiler_Architecture.md, Memory_Model.md, Style_Guide.md.
- Human front door for the repo is root `README.md` (quick start + layout); tutorial is `doc/Getting_Started.md`. Daily install is Host-1.0 hybrid (`./scripts/zen install`).
- archive/ contains historical drafts, legacy proposals, and archived material (`doc/archive/legacy_2026/`). Treat as read-only context, not current spec.
- Execution product: three-layer (ZenValue + compiler native IR + script VM, AOT remains C) — [selfhost/THREE_LAYER.md](../selfhost/THREE_LAYER.md).
- When implementation or ownership changes, corresponding docs + nearest AGENTS.md must be updated.

# Work Guidance

- Every syntax example in docs must be 100% valid, runnable Zenlang conforming to `doc/SPECIFICATION.md`.
- Sentinels must always be capitalized: `Nothing` and `Default`.
- Visual data flow must be used consistently: `->` (assignment), `<-` (return).
- Collections must use clean syntax: `[1, 2, 3]` (List), `{ key -> value }` (Map).
- Module context / entry / reflect / plugins: no `@entry`/`@reflectable` — use `module.entry` and `is reflectable`.
- Stdlib docs must use nested imports (`use zen.io`, `zen.sys.term`, …); keep the import map in Standard_Library_Reference.md current with `lib/zen/`.
- Prefer direct, operational writing per the Style section in root AGENTS.md.

# Verification

- Consistency checks: docs match code/tests (e.g. feature lists, syntax examples against `SPECIFICATION.md`).
- Review of RFC proposals in `doc/proposals/`.
- Zero broken links across all documentation files.

# Child DOX Index

- SPECIFICATION.md — **the single source of truth** for Zenlang syntax, types, grammar, and semantics
- DOCUMENTATION_STANDARDS.md — universal documentation rules, typography, and code style
- Zen Manifesto.md — core philosophy and design directives
- Getting_Started.md — hands-on learner tutorial and tour
- Zen_Data.md — Zen Data (`.zd`) declarative data serialization specification
- Zen_Mark.md — Zen Mark (`.zm`) document markup and terminal UI specification
- Concurrency.md — The Unified Task Concurrency Substrate architecture & programming guide
- Cookbook.md — Practical recipes, pipelines, and integration patterns
- Standard_Library_Reference.md — standard library API catalog
- Compiler_Architecture.md / Compiler_Architecture.zm — Three-Layer execution engine (ZenValue ABI, native positional IR structs, VM, AOT C)
- Memory_Model.md / Memory_Model.zm — Automatic reference management, scoped arenas, and resource lifetimes
- Style_Guide.md / Style_Guide.zm — Canonical syntax standards and formatting guidelines
- proposals/ — formal RFC proposal process (`doc/proposals/README.md` and `doc/proposals/TEMPLATE.md`)
- book/: *The Zen of Programming* official book — `doc/book/README.md` & `doc/book/AGENTS.md`
- Playground.md, FileManager.md, Formatter.md, REPL.zm / REPL.md
- archive/: Historical proposals, legacy drafts (`doc/archive/legacy_2026/`). Not current.
