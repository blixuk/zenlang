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
  | sys | `zen.sys.sys`, `zen.sys.process`, `zen.sys.term`, `zen.sys.readline`, `zen.sys.cli`, `zen.sys.env`, `zen.sys.ffi`, `zen.sys.hardware`, `zen.sys.meminfo`, `zen.sys.termposix` |
  | text | `zen.text.string`, `zen.text.text`, `zen.text.regex`, … |
  | math | `zen.math.math`, `zen.math.random`, `zen.math.range` |
  | collections | `zen.collections.list`, `.set`, `.stack`, `.queue`, `.trie`, `.collections` |
  | data | `zen.data.json`, `.csv`, `.xml`, … |
  | geometry | `zen.geometry.point`, …, `zen.geometry` |
  | ui | `zen.ui.canvas`, `.widgets`, `.term` |
  | net | `zen.net.http` (curl under `-g`), `.socket` (interpret) |
  | graphics | `zen.graphics.bmp`, `.ppm`, `.qrcode` (ISO/IEC 18004) |
  | patterns | `zen.patterns.ecs`, `.fsm` |
  | crypto | `zen.crypto.crypto` (`zen.crypto`), `.chacha20`, `.rc4`, `.xor_cipher`, `.crc32`, `.hash`, `.sha256`, `.sha512`, `.sha1`, `.md5`, `.fnv`, `.base16`, `.base32`, `.base58`, `.base64`, `.base85`, `.hex`, `.uuid`, `.hmac`, `.jwt`, `.pbkdf2`, `.poly1305`, `.aead`, `.xtea`, `.aes`, `.padding`, `.modes`, `.dh`, `.classical`, `.merkle`, `.blockchain` |
  | color | `zen.color` (`.color`, `zen.ui.color`) — RGB, Hex, HSL, 8/16/256 ANSI, TrueColor, WCAG contrast |
  | net | `zen.net.http` (curl under `-g`), `.socket` (interpret), `.url`, `.mime` |
  | text | `zen.text.string`, `zen.text.text`, `zen.text.lorem`, `zen.text.zenmark` (`.zenmark`, `zen.zenmark`), `zen.text.regex`, `.wrap`, `.template`, `.diff`, `.html`, … |
  | data | `zen.data.zendata` (`.zendata`, `zen.zendata`), `zen.data.json`, `.csv`, `.xml`, `.yaml`, `.toml`, `.dotenv`, `.ini`, `.deflate`, `.gzip`, `.zlib`, `.zip`, … |
  | tooling | `zen.tooling.zencode` (`.zencode`, `zen.zencode`), `zen.tooling.builder`, `zen.tooling.pkg` |

- Short aliases (`zen.string`, `zen.file`, `zen.term`, `zen.list`, `zen.json`, `zen.random`, `zen.io`, `zen.process`, `zen.zendata`, `zen.zencode`, `zen.zenmark`, `zen.qrcode`, `zen.data.qrcode`) resolve via `bootstrap/Module/Resolver.py` for compatibility; **prefer nested forms** in new code.
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
- time/: clocks, Duration (arithmetic, constructors, formatting), Timer, cron, timestamp formatting (to_utc, format_iso, format_date, format_time), measure
- io/: io (console I/O, write/write_line/writeln, read/read_line/readln, flush, info/warn/error/debug), file (`list_dir`, `walk`, `walk_depth`, `list_files`, `find_files`, `mkdir`/`mkdir_p`, `copy`, `copy_tree`, `remove_tree`, `lines`, `size`, `touch`), path
- sys/: sys, process (`which`, `run`, `run_result`, `run_ok`, `run_require`, `exec`, `output`, `capture`, `pid`, `sleep`, pipelines, `shell_env`), term (`is_tty`/style/mouse/`spinner_frame`/`readline`), readline (zero-dependency in-line editor, rainbow brackets, matching pair standout, unmatched delimiter alerts, unclosed depth tracking, history, and autocompletion), cli (`--opt=val`, `_rest`, `parse_args`), env, ffi (dynamic shared library loader, dlopen, dlsym, call, close, error, resolve), hardware (cpu_count, available_cpu_count, page_size, physical_pages, available_pages, clock_ticks, hardware_summary), meminfo (total/available/used RAM bytes, MB, GB, percentage, memory_summary), termposix (POSIX TTY detection, stream flushes)
- net/: http (`get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `post_json`, `put_json`, `patch_json`, `get_json`, `json_body`, `status_text`, `is_success`, `is_redirect`, `is_client_error`, `is_server_error`, `bearer_auth`, `basic_auth`, case-insensitive `header`), socket, url (`parse`, `build`, `encode_component`, `decode_component`, `encode_query`, `decode_query`, `join_path`, `resolve`, `get_query_param`, `set_query_param`, `remove_query_param`), mime (lookup/extension), ip (v4/v6 parsing, CIDR, private detection), server (router, request dispatch, text/json response builders)
- text/: string (pad_left/pad_right), text, lorem (classical Latin words, sentences, paragraphs, titles, seedable generation), regex, markdown, columns, zenmark, wrap (wrap/fill/indent/dedent/shorten), template ({{ var }}, #if, #each), diff (diff_lines, unified_diff), html (escape/unescape, builders, parse_attributes, find_tags), fuzzy (Levenshtein, search, rank), inflect (camel, snake, kebab, Pascal, title, slugify, pluralize)
- math/: math, random, range, stats (sum, mean, median, variance, stdev, percentiles, summary)
- collections/: list (`sort`, `sort_by`, `map`, `filter`, `reduce`), set, stack, queue, collections (map/set helpers; Map.items), priority_queue (min/max heap queue), lru (fixed-capacity cache), ring_buffer (circular sliding buffer), trie (Prefix tree, autocomplete, longest prefix matching)
- reflect/: type_name, is_*, fields/call/apply, keys/values/items
- plugins/: create, add, has, list, dispatch, merge
- data/: json (parse, stringify, stringify_pretty, load, dump, dump_pretty), csv (parse, parse_with_headers, stringify, stringify_with_headers, load, load_with_headers, dump, dump_with_headers), xml, yaml, toml, bytes, serialize, sexp, logfmt, database, dotenv (parse/stringify), ini (parse/stringify/get), schema (declarative validation, type/range/enum checks), tar (USTAR format archive creator & parser), deflate (RFC 1951 Deflate/Inflate compression engine with LZ77 32KB window & canonical fixed Huffman trees), gzip (RFC 1952 .gz archive container with header, filename/timestamp preservation, and CRC-32 verification), zlib (RFC 1950 zlib stream container with Adler-32 verification), zip (PKZIP format archive creator & extractor with Deflate/Stored modes, Central Directory parsing, per-file CRC-32 integrity validation, and direct disk archive operations)
- geometry/: point, vectors, shapes, geometry package entry
- ui/: app shell (Bubble Tea–style), canvas, map layout (dual-path); term; prompt (confirm, text, password, select, multiselect), tree (ASCII/Unicode hierarchy formatting), chart (sparkline, bar charts), color bridge
- color/: Color (RGB, RGBA, Hex, HSL, named 8/16 ANSI palette, TrueColor SGR escapes, 256-color, blend, luminance, contrast_ratio)
- graphics/: bmp, ppm, qrcode (pure ISO/IEC 18004 QR code matrix generation & decoding across Numeric, Alphanumeric, and Byte modes with RS error correction, terminal half-blocks, ASCII, SVG, and 24-bit uncompressed BMP render targets)
- patterns/: ecs, fsm
- crypto/: base16 (RFC 4648 §8), base32 (RFC 4648 §6, §7 Base32Hex, Crockford), base58 (Bitcoin/IPFS Base58, Base58Check), base64 (standard & URL-safe), base85 (Ascii85 Adobe, ZeroMQ Z85), hash (unified facade for SHA-256, SHA-224, SHA-512, SHA-384, SHA-1, MD5, FNV-1a), sha256 (SHA-256/224), sha512 (SHA-512/384 32-bit limb core), sha1 (SHA-1), md5 (MD5), fnv (FNV-1a 32/64-bit), hmac (RFC 2104 HMAC-SHA256, verify), jwt (HS256 sign, decode, verify), hex (encode/decode/hexdump/decode_bytes), uuid (uuid_v4), chacha20 (RFC 8439 256-bit symmetric stream cipher), rc4 (ARC4 stream cipher), xor_cipher (repeating-key XOR & OTP), crc32 (IEEE 802.3 CRC-32 & Adler-32 checksums), pbkdf2 (PBKDF2-HMAC-SHA256 key derivation), poly1305 (RFC 8439 128-bit MAC), aead (ChaCha20-Poly1305 authenticated encryption), aes (AES-128 block cipher), xtea (64-bit Feistel cipher), modes (CBC/CTR modes), padding (PKCS#7), dh (Diffie-Hellman key exchange), classical (Caesar, ROT13, Vigenere, Atbash, Rail Fence), crypto (unified package entry point) — lib/zen/crypto/AGENTS.md
- util/: awk, table, bench (micro-benchmarking & throughput), inspect (type inspection & formatting), profile (function/block profiling, self/total time, call tree)
- tooling/: Developer toolchain & project manager (.zbuild, zen.lock, templates, builder, watcher, docgen, pkg, publish, todo, tester, bench, profiler) — lib/zen/tooling/AGENTS.md
- concurrency/: Channels, Tasks, WaitGroup, Mutex, Atomic, Barrier, Semaphore, Once, and Fibers — lib/zen/concurrency/AGENTS.md
- async/: Promises, Futures, Deferred, and async workflow combinators (parallel, series, retry, poll) — lib/zen/async/AGENTS.md
