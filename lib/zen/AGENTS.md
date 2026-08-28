# Purpose

The Zenlang standard library. Composable modules in pure (or near-pure) Zenlang for I/O, data, text, UI, system interaction, collections, networking, and more.

# Ownership

Standard library maintainers. This is the batteries layer — power without bloating the language core.

# Local Contracts

- **Nested layout only.** Modules live under domain packages:
  - `lib/zen/<domain>/<module>.zl`
  - Package entry: `lib/zen/<domain>/<domain>.zl` for short imports (`zen.core` → `core/core.zl`)
- **Canonical imports** (prefer these in new code):

  | Domain | Examples |
  |--------|----------|
  | core | `zen.core` |
  | error | `zen.error` |
  | test | `zen.test` |
  | log | `zen.log` |
  | memory | `zen.memory` — auto default; opt-in arenas (`create_arena`/`push`/`pop`/`free`, `region_run`, `using_arena`) |
  | time | `zen.time` |
  | io | `zen.io.io`, `zen.io.file`, `zen.io.path` |
  | sys | `zen.sys.sys`, `zen.sys.process`, `zen.sys.term`, `zen.sys.cli`, `zen.sys.env` |
  | text | `zen.text.string`, `zen.text.text`, `zen.text.regex`, … |
  | math | `zen.math.math`, `zen.math.random`, `zen.math.range` |
  | collections | `zen.collections.list`, `.set`, `.stack`, `.queue`, `.collections` |
  | data | `zen.data.json`, `.csv`, `.xml`, … |
  | geometry | `zen.geometry.point`, …, `zen.geometry` |
  | ui | `zen.ui.canvas`, `.widgets`, `.term` |
  | net | `zen.net.http` (curl under `-g`), `.socket` (interpret) |
  | graphics | `zen.graphics.bmp`, `.ppm` |
  | patterns | `zen.patterns.ecs`, `.fsm` |
  | crypto | `zen.crypto.hash`, `.base64`, `.hex`, `.uuid` |
  | color | `zen.color` (`.color`, `zen.ui.color`) — RGB, Hex, HSL, 8/16/256 ANSI, TrueColor, WCAG contrast |
  | net | `zen.net.http` (curl under `-g`), `.socket` (interpret), `.url`, `.mime` |
  | text | `zen.text.string`, `zen.text.text`, `zen.text.lorem`, `zen.text.zenmark` (`.zenmark`, `zen.zenmark`), `zen.text.regex`, `.wrap`, `.template`, `.diff`, `.html`, … |
  | data | `zen.data.zendata` (`.zendata`, `zen.zendata`), `zen.data.json`, `.csv`, `.xml`, `.yaml`, `.toml`, `.dotenv`, `.ini`, … |
  | tooling | `zen.tooling.zencode` (`.zencode`, `zen.zencode`), `zen.tooling.builder`, `zen.tooling.pkg` |

- Short aliases (`zen.string`, `zen.file`, `zen.term`, `zen.list`, `zen.json`, `zen.random`, `zen.io`, `zen.process`, `zen.zendata`, `zen.zencode`, `zen.zenmark`) resolve via `bootstrap/Module/Resolver.py` for compatibility; **prefer nested forms** in new code.
- No flat `lib/zen/*.zl` modules.
- Public APIs use `/! … !/` documentation comments.
- Prefer pure Zenlang; bridge to C builtins only for OS/primitives.
- Follow project philosophy: visual data flow, explicitness, streams, semantic text, tasks.
- Geometry (and similar class APIs used under native `-g`): annotate object params and class-returning methods (`p: Point`, `translate(v: Vector2) : Point`, `center() : Point`) so field access emits struct loads, not map `get_field`. Use logical `and`/`or`, not C-style `&&`/`||`.
- Semantic text (`zen.text.text`): hierarchy Word → Sentence → Paragraph → Chapter → Book with `scope` helpers; Chapter holds a list of Paragraphs, Book a list of Chapters; annotate structure params/returns for clarity; native instances are map-backed so dynamic field access works.
- Dual-path stdlib patterns (interpret + `-g`):
  - Prefer `Str.*` free functions over bare string methods (`index_of`, `substring`, `length`, `at`).
  - Prefer map index `m[k]` / `m.has(k)` over two-arg `m.get(k, default)` (native map get is single-key only).
  - Prefer map-based APIs for buffers/records when class methods that call other methods fail to mutate under `-g` (e.g. `zen.ui.canvas` map surface).
  - Avoid mutable index `while` loops that trigger SMIR use-after-move hangs; use recursive rest-string parsers or `for` ranges when possible (`zen.data.sexp`).
  - Logfmt/XML: POSIX ERE `re.find_all` with capturing groups (no non-capturing `(?:…)`).
  - **Name collisions across modules under `-g`:** bare `read` / `write` / `exists` inside `zen.io.file` can mangle to `zen.io` (`io_read` = stdin) when both are linked. Prefer `__builtin_file.*` for OS file ops inside stdlib bodies.

# Work Guidance

- Keep modules small and focused.
- Add tests under `tests/lib/` when modifying.
- Do not reintroduce flat duplicates at `lib/zen/*.zl`.
- Update `doc/Standard_Library_Reference.md` as the surface grows.

# Verification

- `./scripts/zen test-lib` → `tests/lib/run_all.sh` (interpreter)
- `./scripts/zen test-lib-native` → `scripts/run_lib_smoke_native.sh` (full `tests/lib/test_*.zl` under `-g`, currently all 41 modules)
- Prefer modules that stay green under `-g` when expanding demos
- Individual: `python3 bootstrap/Zen.py tests/lib/test_<mod>.zl` / `-g`

# Child DOX Index

- core/: Option, Result, Ordering, combinators, unwrap, conversions
- error/: error constructors
- test/: unit test framework, mock (spies, stubs, call tracking)
- log/: structured logging
- memory/: arena / memory primitives
- time/: clocks, Duration, Timer, cron (5-field schedule parsing & matching)
- io/: io, file (`list_dir`, `walk`, `walk_depth`, `list_files`, `find_files`, `mkdir`/`mkdir_p`, `copy`, `remove_tree`), path
- sys/: sys, process (`which`/`run_result`/pipelines/shell_env), term (`is_tty`/style/mouse/`spinner_frame`), cli (`--opt=val`, `_rest`, `parse_args`), env
- net/: http (dual-path GET/POST via urllib / curl), socket, url (parse/build/query/encode/decode), mime (lookup/extension), ip (v4/v6 parsing, CIDR, private detection), server (router, request dispatch, text/json response builders)
- text/: string (pad_left/pad_right), text, lorem (classical Latin words, sentences, paragraphs, titles, seedable generation), regex, markdown, columns, zenmark, wrap (wrap/fill/indent/dedent/shorten), template ({{ var }}, #if, #each), diff (diff_lines, unified_diff), html (escape/unescape, builders, parse_attributes, find_tags), fuzzy (Levenshtein, search, rank), inflect (camel, snake, kebab, Pascal, title, slugify, pluralize)
- math/: math, random, range, stats (sum, mean, median, variance, stdev, percentiles, summary)
- collections/: list, set, stack, queue, collections (map/set helpers; Map.items), priority_queue (min/max heap queue), lru (fixed-capacity cache), ring_buffer (circular sliding buffer)
- reflect/: type_name, is_*, fields/call/apply, keys/values/items
- plugins/: create, add, has, list, dispatch, merge
- data/: json, csv, xml, yaml, toml, bytes, serialize, sexp, logfmt, database, dotenv (parse/stringify), ini (parse/stringify/get), schema (declarative validation, type/range/enum checks), tar (USTAR format archive creator & parser)
- geometry/: point, vectors, shapes, geometry package entry
- ui/: app shell (Bubble Tea–style), canvas, map layout (dual-path); term; prompt (confirm, text, password, select, multiselect), tree (ASCII/Unicode hierarchy formatting), chart (sparkline, bar charts), color bridge
- color/: Color (RGB, RGBA, Hex, HSL, named 8/16 ANSI palette, TrueColor SGR escapes, 256-color, blend, luminance, contrast_ratio)
- graphics/: bmp, ppm
- patterns/: ecs, fsm
- crypto/: base64 (standard & URL-safe), hash (SHA-256, FNV-1a), hmac (RFC 2104 HMAC-SHA256, verify), jwt (HS256 sign, decode, verify), hex (encode/decode/hexdump), uuid (uuid_v4)
- util/: awk, table, bench (micro-benchmarking & throughput), inspect (type inspection & formatting), profile (function/block profiling, self/total time, call tree)
- tooling/: Developer toolchain & project manager (.zbuild, zen.lock, templates, builder, watcher, docgen, pkg, publish, todo, tester, bench, profiler) — lib/zen/tooling/AGENTS.md
- concurrency/: Channels, Tasks, WaitGroup, Mutex, Atomic, Barrier, Semaphore, Once, and Fibers — lib/zen/concurrency/AGENTS.md
- async/: Promises, Futures, Deferred, and async workflow combinators (parallel, series, retry, poll) — lib/zen/async/AGENTS.md
