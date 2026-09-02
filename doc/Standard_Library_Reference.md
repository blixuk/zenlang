# Zenlang Standard Library API Reference

| Attribute | Value |
|:---|:---|
| **Role** | Standard Library Package Catalog & API Reference |
| **Authority** | Derived API Reference |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

Nested package layout under `lib/zen/<domain>/`. Prefer fully qualified imports using `use`. Default binding without `as` is the last path segment (e.g. `use zen.io` → binds `io` → `lib/zen/io/io.zl`).

## Import map (canonical)

| Package | Import examples |
|---------|-----------------|
| **core** | `import zen.core as core` |
| **error** | `import zen.error as error` |
| **test** | `import zen.test as test` |
| **log** | `import zen.log as log` |
| **memory** | `import zen.memory as memory` |
| **time** | `import zen.time as time` |
| **io** | `zen.io.io`, `zen.io.file`, `zen.io.path` |
| **sys** | `zen.sys.sys`, `zen.sys.process`, `zen.sys.term`, `zen.sys.cli`, `zen.sys.env` |
| **text** | `zen.text.string`, `zen.text.text`, `zen.text.regex`, `zen.text.markdown`, … |
| **math** | `zen.math.math`, `zen.math.random`, `zen.math.range` |
| **collections** | `zen.collections.list`, `.set`, `.stack`, `.queue` |
| **data** | `zen.data.json`, `.csv`, `.xml`, `.yaml`, `.toml`, `.bytes`, … |
| **geometry** | `zen.geometry.point`, `.rectangle`, … |
| **ui** | `zen.ui.canvas`, `.layout` (map flex), `.term`; widgets/geometry (legacy classes) |
| **net** | `zen.net.http`, `zen.net.socket` |
| **graphics** | `zen.graphics.bmp`, `.ppm` |
| **patterns** | `zen.patterns.ecs`, `.fsm` |
| **crypto** | `zen.crypto.hash`, `.base64` |
| **color** | `zen.color` (`.color`, `zen.ui.color`) |
| **util** | `zen.util.awk` |
| **reflect** | `zen.reflect` — `type_name`, `is_*`, `fields`/`call`/`apply`, map helpers |
| **plugins** | `zen.plugins` — map plugin tables: `create`, `add`, `dispatch`, `merge` |

**Compatibility aliases** (resolver only; prefer nested forms):  
`zen.string`→`zen.text.string`, `zen.file`→`zen.io.file`, `zen.term`→`zen.sys.term`, `zen.process`→`zen.sys.process`, `zen.io`→`zen.io.io`, `zen.list`→`zen.collections.list`, `zen.json`→`zen.data.json`, `zen.random`→`zen.math.random`, `zen.path`→`zen.io.path`.

Package short form: `import zen.time` / `use zen.time` resolves to `lib/zen/time/time.zl` (and similarly for `core`, `test`, `error`, `log`, `memory`, `math`, `sys`, `reflect`, `plugins`, …).

**Language features** (built-in `module`, `module.entry`, `is reflectable`, design notes):  
[Language_Module_and_Reflect.md](Language_Module_and_Reflect.md).

See also: [README.md](../README.md), [lib/zen/AGENTS.md](../lib/zen/AGENTS.md), examples `zedit.zl`, `shell_script.zl`, `plugins_demo.zl`.

---

# Built-in: `module` (no import)

| Field | Meaning |
|-------|---------|
| `name`, `path`, `file`, `dir` | Module identity and location |
| `is_entry` | `True` only for the process entry file |
| `entry` | Optional start function: `module.entry -> \`run\`` or `module.entry -> run` |

Default process entry is `function main()`. Setting `module.entry` bypasses `main` (interpret and native `-g`). See [Language_Module_and_Reflect.md](Language_Module_and_Reflect.md).

---

# Module: zen.reflect

> Value introspection and dynamic call. Import: `use zen.reflect as reflect`.

| API | Description |
|-----|-------------|
| `type_name(x)` / `kind(x)` | Type tag string (`Integer`, `Map`, `Function`, `Point`, …) |
| `is_nothing` / `is_boolean` / `is_integer` / `is_decimal` / `is_string` | Predicates |
| `is_list` / `is_map` / `is_set` / `is_function` | Predicates |
| `is_structure` / `is_object` / `is_reflectable` | Structure/object / registered types |
| `fields(x)` / `has_field` / `field` / `set_field` | Field access (maps always; reflectable structures) |
| `methods(x)` / `has_method` / `method` | Method names (reflectable classes) |
| `keys` / `values` / `items` | Map-oriented helpers |
| `call(recv, name, args)` | Dynamic invoke; **args is a list** |
| `apply(fn, args)` | Apply function value to arg list |

**Maps:** also `m.keys()`, `m.values()`, `m.items()` (items → `{key, value}` maps).

**Reflectable types:**

```zl
structure Point is reflectable { x: Integer y: Integer }
class Counter is reflectable { /* fields + methods */ }
```

**Call (plugins):**

```zl
reflect.call({ `hi` -> function(n) { <- n } }, `hi`, [`zen`])
```

Dual-path: map `call` works interpret + `-g`. Class method `call` is interpreter-first.

Tests: `tests/lib/test_reflect.zl`, `test_reflectable.zl`, `test_reflect_call.zl`.

---

# Module: zen.plugins

> Map-based command tables. Import: `use zen.plugins as P`.

| API | Description |
|-----|-------------|
| `create()` | Empty plugin map |
| `add(table, name, fn)` | Register handler; **returns** table (rebind under `-g`) |
| `register_cmd` | Alias of `add` |
| `has(table, name)` | Whether command exists |
| `list(table)` | Command name list |
| `dispatch(table, name, args)` | `reflect.call` wrapper; `args` is a list |
| `merge(base, overlay)` | Overlay wins on conflicts |

Example: `examples/plugins_demo.zl`.

```zl
let cmds -> P.create()
cmds -> P.add(cmds, `hello`, hello_fn)
<- P.dispatch(cmds, `hello`, [`world`])
```

---

# Module: zen.collections.collections (Map helpers)

Under `scope Map`:

| API | Description |
|-----|-------------|
| `Map.keys(d)` | List of keys |
| `Map.values(d)` | List of values |
| `Map.items(d)` | List of `{key, value}` |
| `Map.has(d, k)` | Key present? |

Also available as methods on map values: `d.keys()`, `d.values()`, `d.items()`, `d.has(k)`.

---

# Module: zen.util.awk

> AWK-like Utility Module.

---

## Function: `process`

Processes text line by line, splitting each line into fields.

**Parameters:**
- `text`: The text to process.
- `callback`: A function(fields) to call for each line.

---

## Function: `column`

Simple column extractor (like awk '{print $1}').

**Parameters:**
- `text`: The text to process.
- `index`: The field index (0-based).

**Returns:** A list of values from that column.

---

# Module: zen.sys.process

> Process control module. Provides functions for running external commands and environment management.

---

## Class: `Process`

Represents a system process.

---

## Method: `Process.init`

Initializes a process with a command and arguments.

**Parameters:**
- `cmd`: The executable name or path.
- `args`: A list of string arguments.

#### Example
let p -> Process(`ls`, [`-l`, `/tmp`])


---

## Method: `Process.start`

Spawns the process.

---

## Method: `Process.wait`

Waits for the process to complete and returns the exit code.

**Returns:** The integer exit code.

---

## Method: `Process.stdout`

Returns the standard output of the process.

**Returns:** A string containing the captured stdout.

---

## Method: `Process.code`

Returns the exit code of the process.

---

## Method: `Process.kill`

Kills the process.

---

## Function: `run` / `run_result` / `run_ok` / `run_require`

Argv form (no shell metacharacters in the command name):

| API | Returns |
|-----|---------|
| `run(cmd, args)` | stdout string |
| `run_result(cmd, args)` | `{stdout, stderr, code}` |
| `run_ok(cmd, args)` | boolean exit 0 |
| `run_require(cmd, args)` | stdout or raise |

## Function: `which` / `available`

- `which(name)` → absolute path or `` (`command -v`)
- `available(name)` → true when on PATH

---

## Function: `shell`

Run a command string via `/bin/sh -c` (pipes, globs, redirects like bash).

**Parameters:**
- `command`: Full shell command (e.g. `ls -la | head`).

**Returns:** Captured stdout (stderr merged for convenience).

---

## Function: `result`

Run a shell command; return map `{stdout, stderr, code}`.

---

## Function: `ok`

True when the shell command exits 0.

---

## Function: `require`

Run a shell command; raise on non-zero exit (fail-fast). Returns stdout on success.

---

## Function: `lines` / `pipeline`

`lines` splits shell stdout into a list; `pipeline` is an alias of `shell` for pipe-heavy strings.

---

## Function: `shell_env` / `result_env` / `shell_in_env`

Per-command environment overlay (bash `FOO=bar cmd`). Parent process env is not modified.

**Parameters:**
- `env`: Map of string keys to string values.
- `command`: Shell command string.
- `cwd` (for `shell_in_env` / `result_in_env`): directory for child only.

---

## Class: `Pipeline`

Fluent argv pipeline: stages stored as argv lists and executed with real OS `pipe(2)` (no shell).  
`script()` still returns the equivalent shell form for debugging.

Methods: `pipe`, `in_dir`, `with_env`, `script`, `run`, `result`, `ok`, `require`.

Factory: `process.cmd(command, arguments)` → `Pipeline`.

---

## Function: `each_line` / `each_line_in` / `each_line_env`

Stream shell stdout one line at a time, calling `fn(line)`. Returns line count. Prefer this over `lines` for large output.

---

## Method: `Process.get_id`

Returns the process ID of the current process.

**Returns:** The PID.

---

# Module: zen.sys.cli

> CLI parsing for Unix-style tools (dual-path).

**Class API:** `Parser(name, description)` → `flag` / `option` / `argument` / `parse` / `help`.

**Parse features:** `-v`, `--verbose`, `--name=value`, `-o val`, positionals, leftover tokens under `_rest`.

**Helpers:** `get(values, key, default)`, `flag_set(values, key)`, free-function `parse_args(args, flags, options, positionals)`.

---

## Class: `ArgSpec`

Internal representation of a CLI option (flag or valued option).

---

## Class: `Parser`

Main CLI Parser class.

---

## Method: `Parser.flag`

Adds a boolean flag to the parser.

**Parameters:**
- `short`: The short name (e.g., 'v').
- `long`: The long name (e.g., 'verbose').
- `help`: The help description.

---

## Method: `Parser.option`

Adds an option that takes a value.

**Parameters:**
- `short`: The short name (e.g., 'o').
- `long`: The long name (e.g., 'output').
- `help`: The help description.
- `default`: The default value if not provided.

---

## Method: `Parser.argument`

Adds a positional argument.

**Parameters:**
- `name`: The name of the argument.
- `help`: The help description.

---

## Method: `Parser.help`

Prints the help message for the parser.

---

## Method: `Parser.parse`

Parses the provided list of arguments.

**Parameters:**
- `args`: The list of arguments (usually from sys.get_args()).

**Returns:** A map of parsed values.

---

# Module: zen.sys.sys

> System interface module. Provides access to command line arguments, environment variables, and process control.

---

## Function: `get_args`

Returns the command line arguments passed to the process.

**Returns:** A list of strings representing the arguments.

---

## Function: `exit`

Exits the current process with the specified exit code.

**Parameters:**
- `code`: The exit code (0 for success).

---

## Function: `get_env`

Returns the value of an environment variable.

**Parameters:**
- `key`: The name of the environment variable.

**Returns:** The value of the environment variable as a string.

---

## Function: `get_cwd`

Returns the current working directory.

**Returns:** The current working directory string.

---

## Function: `platform`

Returns the operating system platform name.

**Returns:** The platform name string (e.g., 'linux', 'darwin', 'win32').

---

## Function: `version`

Returns the Zenlang version string.

**Returns:** The version string.

---

## Function: `exec`

Executes a shell command using the system shell.

**Parameters:**
- `cmd`: The command to execute.

**Returns:** The exit code of the command.

---

# Module: zen.sys.env

> Environment Variable Access Module. Makes interacting with the shell environment feel like a native dictionary.

---

## Function: `get`

Gets an environment variable.

**Parameters:**
- `name`: The name of the variable.
- `default`: The default value if not found.

**Returns:** The value of the variable.

---

## Function: `set`

Sets an environment variable.

**Parameters:**
- `name`: The name of the variable.
- `value`: The value to set.

---

## Function: `keys`

Lists all environment variables.

**Returns:** A list of variable names.

---

## Function: `has`

Checks if an environment variable exists.

**Parameters:**
- `name`: The name of the variable.

**Returns:** True if it exists.

---

# Module: zen.sys.term

> Terminal UI utility module. Display control, alternate screen, raw input, and key events for TUI apps and editors (see `examples/zedit.zl`).

**Also:** `is_tty()`, `enable_mouse` / `disable_mouse`, `style` / `style_line` / `success` / `warn` / `error`, `spinner_frame(i)`. Key map: `{kind, name, ch, ctrl, code}`.

---

## Function: `clear`

Clears the terminal screen and home the cursor.

---

## Function: `move`

Moves the cursor to the specified coordinates.

**Parameters:**
- `x`: The column index (1-based).
- `y`: The row index (1-based).

---

## Function: `color`

Sets the foreground and background colors of the terminal.

**Parameters:**
- `fg`: The foreground color name (e.g. `green`).
- `bg`: The background color name (e.g. `black`).

---

## Function: `reset`

Resets all terminal attributes (colors, styles).

---

## Function: `get_size`

Returns the current terminal size.

**Returns:** A record with `width` and `height`.

---

## Function: `alt_screen`

Executes a block of code within the alternate screen buffer. Ensures the terminal returns to the original state even if an error occurs.

**Parameters:**
- `fn`: A closure to execute.

---

## Function: `raw_enter` / `raw_exit` / `with_raw`

Enable raw/cbreak-like input (no echo, no line buffering). Always pair enter with exit; `with_raw(fn)` restores even if `fn` raises.

**Returns (`raw_enter`):** Boolean — `true` if switched successfully (false on non-TTY).

---

## Function: `read_key` / `poll_key`

`read_key()` blocks until a key/event; `poll_key(timeout_ms)` waits up to the timeout.

**Returns:** Map with:
- `kind`: `char` | `special` | `resize` | `none`
- `name`: e.g. `left`, `enter`, `backspace`, `ctrl_s` (empty for plain chars)
- `ch`: printable character string
- `ctrl`: boolean
- `code`: integer (raw byte when relevant)

---

## Function: `write` / `flush` / `write_at` / `hide_cursor` / `show_cursor` / `clear_eol`

Low-level draw helpers for editors (no trailing newline on `write`; call `flush` after a frame).

---

# Module: zen.log

> Structured Logging module. Provides log levels and configurable output formats (text, json, logfmt).

---

## Function: `set_level`

Sets the global log level.

**Parameters:**
- `level`: The log level (e.g. log.LEVEL_DEBUG).

---

## Function: `set_format`

Sets the global log format.

**Parameters:**
- `format`: The format (`text`, `json`, or `logfmt`).

---

## Function: `debug`

Logs a debug message using the global logger.

---

## Function: `info`

Logs an info message using the global logger.

---

## Function: `warn`

Logs a warning message using the global logger.

---

## Function: `error`

Logs an error message using the global logger.

---

## Function: `fatal`

Logs a fatal message using the global logger.

---

# Module: zen.ui.widgets

## Class: `Widget`

Base UI Widget.

---

## Method: `Widget.draw`

Draws the widget to a canvas.

**Parameters:**
- `canvas`: The Canvas to draw on.

---

## Class: `Label extends Widget`

Simple Text Label.

---

## Class: `ProgressBar extends Widget`

Visual Progress Bar.

---

## Class: `Button extends Widget`

Interactive Button.

---

## Class: `Panel extends Widget`

Widget Container / Panel.

---

# Module: zen.ui.geometry

## Class: `UIPoint`

Geometry library for UI layout.

---

# Module: zen.ui.widget

> Dual-path **map widgets** drawn onto `zen.ui.canvas` within layout bounds `{x,y,w,h}`.

| Constructor | Kind |
|-------------|------|
| `label(text)` | text line |
| `panel(title)` | bordered box |
| `progress(value, max)` | bar |
| `list_view(items, selected)` | selectable list (`list_move`) |
| `status(left, right)` | status line |

`draw(canvas, bounds, widget)` / `draw_full(canvas, widget)` / `with_colors(w, fg, bg)`.

# Module: zen.ui.app

> Bubble Tea–style TUI loop (dual-path). **Model / update / view** with map messages.

| API | Role |
|-----|------|
| `run(init, update, view, opts)` | Interactive alt-screen loop |
| `step` / `run_msgs` | Headless simulation (tests) |
| `msg_char` / `msg_key` / `msg_tick` / `msg_resize` / `msg_quit` | Events |
| `key_char` / `key_name` / `is_default_quit_key` | Predicates |

Model convention: set `` `quit` -> true `` to exit.  
Example: `examples/tui_counter.zl`. Headless: `ZEN_TUI_HEADLESS=1`.

# Module: zen.ui.canvas

> Dual-path **map** canvas (not a class). Keys: `width`, `height`, `buffer`, `fg_buffer`, `bg_buffer`.

| Function | Role |
|----------|------|
| `create(w, h)` | New blank canvas |
| `set_cell` / `get_cell` | Cell access |
| `clear` / `fill_rect` / `draw_rect` / `draw_text` | Drawing |
| `fill_node` / `text_node` | Paint a layout node `{x,y,w,h}` |
| `render` | Flush to terminal via `zen.sys.term` |
| `row_string` | Test helper |

Color names are strings (`green`, `black`, …).

# Module: zen.ui.layout

> Dual-path **map** flex layout: `box` / `vbox` / `hbox` / `add` / `set_expand` / `set_size` / `layout`.

```zen
let root -> layout.vbox()
layout.add(root, layout.box(80, 1))
layout.add(root, layout.set_expand(layout.box(0, 0), true))
layout.layout(root, 0, 0, 80, 24)
```

See `examples/layout_map_demo.zl`, `tests/lib/test_layout.zl`.

---

# Module: zen.ui.term

## Constant: `colors`

Terminal UI Module. Provides higher-level terminal control and styling.

---

## Function: `clear`

Clears the screen and moves cursor to home.

---

## Function: `move`

Moves the cursor to (x, y).

---

## Function: `color`

Sets the foreground and background colors.

**Parameters:**
- `fg`: Foreground color name.
- `bg`: Background color name.

---

## Function: `reset`

Resets all terminal attributes.

---

## Function: `size`

Gets terminal dimensions.

**Returns:** A map with `width` and `height`.

#### Example
let s -> term.size()
io.writeln(`Terminal: ` + s.width + `x` + s.height)


---

## Function: `alt_screen`

Runs a block of code in the alternate screen buffer. Automatically restores the terminal state on exit.

**Parameters:**
- `fn`: The function to execute.

#### Example
term.alt_screen(function() {
term.move(10, 10)
io.write(`Secret Screen`)
time.sleep(2)
})


---

# Module: zen.text.markdown

> Markdown Processing Module. Provides basic Markdown to HTML conversion.

---

## Function: `to_html`

Converts Markdown text to HTML.

**Parameters:**
- `text`: The Markdown string.

**Returns:** The HTML string.

---

# Module: zen.text.text

> Semantic Text module. Hierarchy: **Word → Sentence → Paragraph → Chapter → Book**.

---

### Structures

| Type | Fields | Role |
|------|--------|------|
| `Word` | `text` | Single word |
| `Sentence` | `text` | Words separated by spaces |
| `Paragraph` | `text` | Sentence body (plain text) |
| `Chapter` | `title`, `paragraphs` (list of Paragraph) | Ordered paragraphs under a title |
| `Book` | `title`, `chapters` (list of Chapter) | Ordered chapters under a title |

Scope helpers: `Word.*`, `Sentence.*`, `Paragraph.*`, `Chapter.*`, `Book.*` (e.g. `text.Chapter.from_paragraphs`, `text.Book.to_text`).

---

## Function: `is_uppercase`

Checks if the word is entirely uppercase.

**Parameters:**
- `w`: The Word structure.

**Returns:** True if all runes are uppercase.

---

## Function: `capitalize`

Returns a capitalized version of the word.

**Parameters:**
- `w`: The Word structure.

**Returns:** A new Word with the first letter capitalized.

---

## Function: `to_words`

Splits the sentence into a list of Words.

**Parameters:**
- `s`: The Sentence structure.

**Returns:** A list of Word structures.

---

## Function: `count_words`

Counts the number of words in the sentence.

**Parameters:**
- `s`: The Sentence structure.

**Returns:** The number of words.

---

## Function: `wrap`

Wraps the paragraph text to a maximum width.

**Parameters:**
- `p`: The Paragraph structure.
- `width`: The maximum line width.

**Returns:** A new Paragraph with wrapped text.

---

## Chapter helpers

| Function | Role |
|----------|------|
| `from_paragraphs(title, paragraphs)` | Build a Chapter |
| `count_paragraphs(ch)` | Length of `paragraphs` |
| `append_paragraph(ch, p)` | Copy with one more Paragraph |
| `to_text(ch)` | Title + blank-line-separated bodies |
| `wrap_all(ch, width)` | `Paragraph.wrap` on each paragraph |

## Book helpers

| Function | Role |
|----------|------|
| `from_chapters(title, chapters)` | Build a Book |
| `count_chapters(b)` | Length of `chapters` |
| `count_paragraphs(b)` | Sum of paragraphs in all chapters |
| `append_chapter(b, ch)` | Copy with one more Chapter |
| `to_text(b)` | Title + chapters joined with `\n\n---\n\n` |

---

# Module: zen.text.regex

> Regular Expression Module. Provides functions for pattern matching and replacement.

---

## Function: `match`

Checks if a pattern matches at the beginning of a string.

**Parameters:**
- `pattern`: The regex pattern.
- `s`: The string to check.

**Returns:** True if it matches, False otherwise.

---

## Function: `search`

Searches for a pattern anywhere in a string.

**Parameters:**
- `pattern`: The regex pattern.
- `s`: The string to search.

**Returns:** True if it matches, False otherwise.

---

## Function: `replace`

Replaces occurrences of a pattern with a replacement string.

**Parameters:**
- `pattern`: The regex pattern.
- `repl`: The replacement string.
- `s`: The string to process.

**Returns:** The resulting string.

---

## Function: `split`

Splits a string by a regex pattern.

**Parameters:**
- `pattern`: The regex pattern.
- `s`: The string to split.

**Returns:** A list of substrings.

---

## Function: `find_all`

Finds all occurrences of a pattern in a string.

**Parameters:**
- `pattern`: The regex pattern.
- `s`: The string to search.

**Returns:** A list of matches.

---

# Module: zen.text.columns

## Class: `Columns`

Text Columns module. Provides simple, predictable delimiter-based record parsing.

---

## Method: `Columns.init`

Initializes the Columns parser from a string.

**Parameters:**
- `text`: The input text.
- `delimiter`: The column delimiter.

---

## Method: `Columns.row`

Gets a row at the given index.

**Parameters:**
- `index`: The row index.

**Returns:** The row as a list of strings.

---

## Method: `Columns.count`

Gets the number of rows.

**Returns:** The row count.

---

## Method: `Columns.from_file`

Helper function to load columns from a file.

**Parameters:**
- `path`: The file path.
- `delimiter`: The column delimiter.

**Returns:** A Columns instance.

---

# Module: zen.text.string

> String manipulation module. Provides functions for string operations and conversions.

---

## Function: `split`

Splits a string into a list of substrings based on a separator.

**Parameters:**
- `s`: The string to split.
- `sep`: The separator string.

**Returns:** A list of substrings.

---

## Function: `join`

Joins a list of strings into a single string using a separator.

**Parameters:**
- `parts`: The list of strings to join.
- `sep`: The separator string.

**Returns:** The joined string.

---

## Function: `trim`

Trims whitespace from both ends of a string.

**Parameters:**
- `s`: The string to trim.

**Returns:** The trimmed string.

---

## Function: `substring`

Returns a substring of the given string.

**Parameters:**
- `s`: The string.
- `start`: The start index (inclusive).
- `end`: The end index (exclusive).

**Returns:** The substring.

---

## Function: `starts_with`

Checks if a string starts with the given prefix.

**Parameters:**
- `s`: The string.
- `prefix`: The prefix to check.

**Returns:** True if it starts with prefix, False otherwise.

---

## Function: `ends_with`

Checks if a string ends with the given suffix.

**Parameters:**
- `s`: The string.
- `suffix`: The suffix to check.

**Returns:** True if it ends with suffix, False otherwise.

---

## Function: `contains`

Checks if a string contains the given substring.

**Parameters:**
- `s`: The string.
- `sub`: The substring to check.

**Returns:** True if it contains sub, False otherwise.

---

## Function: `replace`

Replaces occurrences of a substring with another substring.

**Parameters:**
- `s`: The string.
- `old`: The substring to replace.
- `new`: The replacement substring.

**Returns:** The resulting string.

---

## Function: `length`

Returns the length of a string.

**Parameters:**
- `s`: The string.

**Returns:** The length of the string.

---

## Function: `to_lower`

Converts a string to lowercase.

**Parameters:**
- `s`: The string.

**Returns:** The lowercase string.

---

## Function: `to_upper`

Converts a string to uppercase.

**Parameters:**
- `s`: The string.

**Returns:** The uppercase string.

---

## Function: `index_of`

Returns the index of the first occurrence of a substring.

**Parameters:**
- `s`: The string.
- `sub`: The substring to find.

**Returns:** The index of the substring, or -1 if not found.

---

## Function: `at`

Returns the character at the specified index.

**Parameters:**
- `s`: The string.
- `i`: The index.

**Returns:** The character at index i.

---

## Function: `to_string`

Converts a value to its string representation.

**Parameters:**
- `x`: The value to convert.

**Returns:** The string representation of x.

---

# Module: zen.text.zenmark

## Class: `DocComment`

ZenMark Documentation Parser.

---

## Method: `DocComment.parse`

Parses a raw documentation comment string.

**Parameters:**
- `text`: The comment text.

**Returns:** A DocComment object.

---

# Module: zen.text.html

> HTML processing and generation module. Provides HTML escaping/unescaping, tag/document builders, and lightweight parsing.

---

## Function: `escape`

Escapes special HTML characters (`&`, `<`, `>`, `"`, `'`) in a string.

**Parameters:**
- `s`: The string to escape.

**Returns:** The escaped HTML-safe string.

---

## Function: `unescape`

Decodes standard HTML entities back into plain characters.

**Parameters:**
- `s`: The entity-encoded string.

**Returns:** The unescaped plain string.

---

## Function: `strip_tags`

Strips all HTML tags from a string.

**Parameters:**
- `s`: The HTML string.

**Returns:** Text content without markup.

---

## Function: `tag`

Constructs an HTML element with optional attributes and inner content.

**Parameters:**
- `name`: Tag name (e.g. "div", "a", "img").
- `attrs`: Map of attributes (e.g. `{"id" -> "main"}`).
- `content`: Inner HTML or text content.

---

## Function: `document`

Generates a full HTML5 document template.

**Parameters:**
- `title`: Page title.
- `body_content`: Main body inner HTML.
- `options`: Optional configuration (`lang`, `head`, `body_attrs`).

---

## Function: `parse_attributes`

Parses an HTML attribute string into a Map of key-value pairs.

**Parameters:**
- `attr_str`: Raw attribute string (e.g. `id="main" class="active" disabled`).

---

## Function: `find_tags`

Finds all occurrences of a specified HTML tag in a string.

**Parameters:**
- `html`: Source HTML markup.
- `target_tag`: Tag name to search for (case-insensitive).

**Returns:** List of maps containing `tag`, `attrs`, and `content`.

---

# Module: zen.io.io

> Standard Input/Output module.

---

# Module: zen.io.path

> Path manipulation module. Provides functions for interacting with Unix-style file paths.

---

## Function: `join`

Joins two or more path components using the system separator (/).

**Parameters:**
- `p1`: The first path component.
- `p2`: The second path component.

**Returns:** The joined path string.

---

## Function: `basename`

Returns the final component of a path.

**Parameters:**
- `p`: The path string.

**Returns:** The basename of the path.

---

## Function: `dirname`

Returns the parent directory of a path.

**Parameters:**
- `p`: The path string.

**Returns:** The directory name.

---

## Function: `is_absolute`

Checks if a path is absolute (starts with /).

**Parameters:**
- `p`: The path string.

**Returns:** True if absolute, False otherwise.

---

## Function: `extname`

Returns the extension of the file (including the dot).

**Parameters:**
- `p`: The path string.

**Returns:** The extension, or an empty string if none.

---

# Module: zen.io.file

> File operations module. Provides functions for interacting with the file system.

---

## Class: `File`

Represents an open file stream.

---

## Method: `File.init`

Initializes a file reference.

**Parameters:**
- `path`: The path to the file.
- `mode`: The open mode ('r', 'w', 'a').

---

## Method: `File.open`

Opens the file.

---

## Method: `File.read`

Reads the content of the file.

**Returns:** The file content as a string.

---

## Method: `File.write`

Writes content to the file.

**Parameters:**
- `content`: The content to write.

---

## Method: `File.close`

Closes the file.

---

## Method: `File.read`

Reads the entire content of a file.

**Parameters:**
- `path`: The path to the file.

**Returns:** The content of the file as a string.

#### Example
let text -> file.read(`config.json`)


---

## Method: `File.read_lines`

Reads a file and returns its content as a list of lines.

**Parameters:**
- `path`: The path to the file.

**Returns:** A list of strings representing the lines.

---

## Method: `File.write`

Writes content to a file, overwriting its current content.

**Parameters:**
- `path`: The path to the file.
- `content`: The content to write.

---

## Method: `File.write_bytes`

Writes raw bytes (list of integers 0-255) to a file.

**Parameters:**
- `path`: The path to the file.
- `bytes`: The list of integers to write.

---

## Function: `mkdir` / `mkdir_p`

- **`mkdir(path)`** — create one directory level (idempotent if already a dir).
- **`mkdir_p(path)`** — create path and parents (`mkdir -p`).

Returns boolean success.

## Function: `copy`

Copy a regular file (`src` → `dst`), overwriting destination. Returns boolean.

```zen
file.copy(`a.txt`, `b.txt`)
```

## Function: `remove_tree`

Recursively delete a file or directory tree. Returns true if the path is gone.

## Function: `list_dirs` / `list_file_names`

Immediate children of a directory (not recursive): subdirectory names or file names only. Sorted.

## Function: `list_dir`

Lists the names of entries in a directory (not recursive). Sorted ascending. Returns `[]` if missing/not a dir. Skips `.` / `..`.

**Parameters:**
- `path`: Directory path.

**Returns:** List of entry name strings.

---

## Function: `walk` / `walk_depth`

Recursively walk a directory tree. Calls `fn(full_path, is_directory)` for each entry under `root` (not including `root`). Directories are visited before their children.

- **`walk(root, fn)`** — unlimited depth.
- **`walk_depth(root, max_depth, fn)`** — depth 0 = immediate children only; negative = unlimited.

#### Example
```zl
use zen.io.file as file
use zen.io as io

file.walk(`lib/zen/sys`, function(p, is_dir) {
    when is_dir == false { io.writeln(p) }
})
```

---

## Function: `list_files` / `find_files`

- **`list_files(root)`** — all regular-file paths under `root` (recursive).
- **`find_files(root, suffix)`** — same, filtered by path suffix (e.g. `.zl`).

**Returns:** List of path strings.

---

## Method: `File.write_lines`

Writes a list of strings to a file as separate lines.

**Parameters:**
- `path`: The path to the file.
- `lines`: The list of strings to write.

---

## Method: `File.append`

Appends content to the end of a file.

**Parameters:**
- `path`: The path to the file.
- `content`: The content to append.

---

## Method: `File.exists`

Checks if a file or directory exists at the given path.

**Parameters:**
- `path`: The path to check.

**Returns:** True if it exists, False otherwise.

---

## Method: `File.remove`

Removes a file or directory.

**Parameters:**
- `path`: The path to remove.

---

## Method: `File.is_file`

Checks if the given path is a file.

**Parameters:**
- `path`: The path to check.

**Returns:** True if it's a file, False otherwise.

---

## Method: `File.is_dir`

Checks if the given path is a directory.

**Parameters:**
- `path`: The path to check.

**Returns:** True if it's a directory, False otherwise.

---

## Method: `File.list_dir`

Lists the contents of a directory.

**Parameters:**
- `path`: The path to the directory.

**Returns:** A list of strings representing the directory entries.

#### Example
let items -> file.list_dir(`.`)
do for item in items {
io.writeln(item)
}


---

# Module: zen.memory

## Constant: `__memory_builtin`

Memory management primitives. Provides interface for arena allocation and manual memory control.

---

## Function: `create_arena`

Creates a new memory arena of the specified size.

**Parameters:**
- `size`: The size of the arena in bytes.

**Returns:** A handle to the created arena.

---

## Function: `free_arena`

Frees a memory arena and all its associated memory.

**Parameters:**
- `arena`: The handle to the arena to free.

---

## Function: `reset_arena`

Resets a memory arena, making its memory available for reuse without freeing it.

**Parameters:**
- `arena`: The handle to the arena to reset.

---

## Function: `push_arena`

Pushes an arena onto the current allocation stack. All subsequent allocations will occur in this arena until popped.

**Parameters:**
- `arena`: The handle to the arena to push.

---

## Function: `pop_arena`

Pops the top arena from the allocation stack.

---

## Class: `Arena`

Object-oriented wrapper for memory arenas.

---

## Method: `Arena.init`

Initializes the arena with a specified size.

**Parameters:**
- `size`: The size of the arena.

---

## Method: `Arena.free`

Frees the arena.

---

## Method: `Arena.reset`

Resets the arena.

---

## Method: `Arena.push`

Pushes the arena onto the allocation stack.

---

## Method: `Arena.pop`

Pops the arena from the allocation stack.

---

## Method: `Arena.Region`

Context-based allocation region.

---

# Module: zen.data.json

> JSON module. Provides functions for serializing and deserializing JSON data in pure Zenlang.

---

## Function: `stringify`

Converts a Zenlang object to a JSON string.

**Parameters:**
- `value`: The object to stringify.

**Returns:** The JSON string representation.

---

## Class: `JsonParser`

Internal JSON Parser.

---

## Method: `JsonParser.parse`

Parses a JSON string into Zenlang types.

**Parameters:**
- `json_str`: The JSON string to parse.

**Returns:** The parsed Zenlang object.

---

# Module: zen.data.database

## Class: `Database`

Simple Persistent Key-Value Database. Uses JSON for storage.

---

## Method: `Database.init`

Initializes a database at the given file path.

**Parameters:**
- `path`: The file path for storage.

#### Example
let db -> Database(`data.json`)
db.set(`user`, `admin`)


---

## Method: `Database.set`

Sets a value for a key.

**Parameters:**
- `key`: The key string.
- `value`: The value.

---

## Method: `Database.get`

Retrieves a value for a key.

**Parameters:**
- `key`: The key string.

**Returns:** The value or nothing.

---

## Method: `Database.has`

Checks if a key exists in the database.

**Parameters:**
- `key`: The key string.

**Returns:** True if the key exists.

---

## Method: `Database.remove`

Removes a key and its value from the database.

**Parameters:**
- `key`: The key string.

---

## Method: `Database.load`

Loads the database from the file.

---

## Method: `Database.save`

Saves the database to the file.

---

## Method: `Database.clear`

Clears all data from the database.

---

# Module: zen.data.csv

> CSV parsing and serialization module. Provides robust handling for CSV format, including quoted fields and multiline data.

---

## Function: `parse`

Parses a CSV string into a list of rows (which are lists of strings).

**Parameters:**
- `csv_str`: The CSV string.
- `delimiter`: The delimiter string (defaults to `,`).

**Returns:** A list of rows.

---

## Function: `parse_with_headers`

Parses a CSV string with a header row into a list of maps.

**Parameters:**
- `csv_str`: The CSV string.
- `delimiter`: The delimiter string (defaults to `,`).

**Returns:** A list of maps, where keys are headers.

---

## Function: `stringify`

Serializes a list of rows (lists of strings) into a CSV string.

**Parameters:**
- `rows`: The list of rows.
- `delimiter`: The delimiter string (defaults to `,`).

**Returns:** The serialized CSV string.

---

# Module: zen.data.toml

> Simple TOML Parser Module.

---

## Function: `parse`

Parses a simple TOML string (key = "value" pairs).

**Parameters:**
- `text`: The TOML string.

**Returns:** A map of keys to values.

---

## Function: `stringify`

Converts a Map to a simple TOML string.

**Parameters:**
- `data`: The map to convert.

**Returns:** The TOML string.

---

# Module: zen.data.xml

> Simple XML Parser Module.

---

## Function: `parse`

Parses a simple XML string into a Map. Note: Only supports single-level tags with content.

**Parameters:**
- `xml`: The XML string.

**Returns:** A map of tag names to content.

---

## Function: `stringify`

Converts a Map to a simple XML string.

**Parameters:**
- `data`: The map of tag names to content.

**Returns:** The XML string.

---

# Module: zen.data.sexp

> S-Expression Parser. Converts Lisp-style data into nested Zenlang lists.

---

### Description

Parses an S-Expression string into nested lists.

**Parameters:**
- `text`: The S-Expression string.

**Returns:** Nested lists and strings.

---

## Function: `tokenize`

Tokenizes an S-Expression string.

---

## Function: `parse_recursive`

Recursively parses tokens into nested lists.

---

## Function: `parse`

Parses an S-Expression string into nested lists.

**Parameters:**
- `text`: The S-Expression string.

**Returns:** Nested lists and strings.

---

# Module: zen.data.yaml

> Simple YAML Parser Module.

---

## Function: `parse`

Parses a simple YAML string (key: value pairs).

**Parameters:**
- `text`: The YAML string.

**Returns:** A map of keys to values.

---

## Function: `stringify`

Converts a Map to a simple YAML string.

**Parameters:**
- `data`: The map to convert.

**Returns:** The YAML string.

---

# Module: zen.data.bytes

## Class: `Bytes`

Byte Array Library.

---

## Method: `Bytes.init`

Initializes a new byte array.

**Parameters:**
- `size_or_list`: Either an integer size or a list of bytes.

#### Example
let b -> Bytes([72, 101, 108, 108, 111])


---

## Method: `Bytes.get`

Gets a byte at a specific index.

**Parameters:**
- `index`: The index.

**Returns:** The byte value (0-255).

---

## Method: `Bytes.set`

Sets a byte at a specific index.

**Parameters:**
- `index`: The index.
- `value`: The byte value (0-255).

---

## Method: `Bytes.length`

Returns the length of the byte array.

---

## Method: `Bytes.to_list`

Converts the byte array to a standard list.

---

## Method: `Bytes.to_string`

Converts the byte array to a string (UTF-8).

---

## Method: `Bytes.slice`

Returns a slice of the byte array.

---

## Method: `Bytes.from_string`

Creates a byte array from a string.

**Parameters:**
- `s`: The input string.

#### Example
let b -> bytes.from_string(`Hello World`)


---

## Method: `Bytes.pack`

Packs a map of values into a byte array according to a structure.

**Parameters:**
- `spec`: A map of field names to types (u8, u16, u32, i8, i16, i32).
- `data`: A map of field names to values.

---

## Method: `Bytes.unpack`

Unpacks a byte array into a map according to a structure.

---

# Module: zen.data.logfmt

> Logfmt Parser and Generator. Designed for structured logging in a "Dumb but Honest" way.

---

## Function: `parse`

Parses a logfmt string into a map.

**Parameters:**
- `line`: The logfmt line to parse.

**Returns:** A map of keys and values.

---

## Function: `stringify`

Converts a map to a logfmt string.

**Parameters:**
- `data`: The map to stringify.

**Returns:** A logfmt string.

---

# Module: zen.data.serialize

## Constant: `registry`

Serialization and Deserialization Module. Allows saving and loading complex types like Classes and Structures.

---

## Function: `register_type`

Registers a type (Class or Structure) for deserialization.

**Parameters:**
- `name`: The type name (matching obj.kind).
- `type_obj`: The Class or Structure object.

---

## Function: `serialize`

Serializes an object to a plain data structure.

**Parameters:**
- `obj`: The object to serialize.

**Returns:** A map/list/primitive structure.

---

## Function: `deserialize`

Deserializes a plain data structure back into Zenlang objects.

**Parameters:**
- `data`: The serialized data structure.

**Returns:** The reconstructed object.

---

## Function: `save_to_file`

Convenience function to save an object to a JSON file.

---

## Function: `load_from_file`

Convenience function to load an object from a JSON file.

---

# Module: zen.core

> The core prelude module for Zenlang. Contains essential types and utilities for error handling, structural data, and functional combinators.

---

### Enumerator: `Option`

Represents an optional value that may or may not be present.

#### Variants:
- `Option.Something(value)`: The value is present.
- `Option.Nothing`: The value is absent.

---

### Enumerator: `Result`

Represents the result of an operation that can either succeed or fail.

#### Variants:
- `Result.Ok(value)`: The operation succeeded with a value.
- `Result.Error(message)`: The operation failed with an error message.

---

### Enumerator: `Ordering`

Represents the comparison outcome of two values.

#### Variants:
- `Ordering.Less`: The first value is less than the second.
- `Ordering.Equal`: The two values are equal.
- `Ordering.Greater`: The first value is greater than the second.

---

## Function: `unwrap`

Forcefully extracts the value from an Option or Result. Raises an error if the value is absent or represents a failure.

**Parameters:**
- `container`: The Option or Result to unwrap.

**Returns:** The internal value if present.

---

## Function: `unwrap_or`

Extracts the value from an Option or Result, or returns a default value.

**Parameters:**
- `container`: The Option or Result to inspect.
- `default_value`: The value to return if the container is empty or an error.

**Returns:** The internal value or the default value.

---

## Function: `expect`

Extracts the value from an Option or Result, raising a custom error message on failure.

**Parameters:**
- `container`: The Option or Result to inspect.
- `message`: The error message to raise if the container is empty or an error.

**Returns:** The internal value.

---

## Function: `is_ok`

Checks if a Result represents a successful outcome.

**Parameters:**
- `result`: The Result container to check.

**Returns:** True if the result is Ok, False otherwise.

---

## Function: `is_error`

Checks if a Result represents a failure.

**Parameters:**
- `result`: The Result container to check.

**Returns:** True if the result is Error, False otherwise.

---

## Function: `is_something`

Checks if an Option contains a value.

**Parameters:**
- `option`: The Option container to check.

**Returns:** True if the option is Something, False otherwise.

---

## Function: `is_nothing`

Checks if an Option is empty.

**Parameters:**
- `option`: The Option container to check.

**Returns:** True if the option is Nothing, False otherwise.

---

## Function: `map`

Transforms the value inside an Option or Result using the provided mapping function. Leaves Option.Nothing and Result.Error untouched.

**Parameters:**
- `container`: The Option or Result to map.
- `fn`: The mapping function to apply to the contained value.

**Returns:** A new Option or Result with the mapped value.

---

## Function: `map_error`

Transforms the error message inside a Result using the provided mapping function. Leaves Result.Ok untouched.

**Parameters:**
- `result`: The Result to map.
- `fn`: The mapping function to apply to the error message.

**Returns:** A new Result with the mapped error or original Ok value.

---

## Function: `map_flat`

Monadic chain: Applies a function returning an Option or Result to the contained value. Leaves Option.Nothing and Result.Error untouched.

**Parameters:**
- `container`: The Option or Result container.
- `fn`: A function taking the contained value and returning an Option or Result.

**Returns:** The Result/Option returned by fn, or the unchanged empty/error container.

---

## Function: `filter`

Filters an Option: returns Option.Something(value) if predicate(value) is true, otherwise returns Option.Nothing.

**Parameters:**
- `option`: The Option to filter.
- `predicate`: A predicate function returning Boolean.

**Returns:** Option.Something(value) if predicate holds, else Option.Nothing.

---

## Function: `to_result`

Converts an Option into a Result, using the provided error message if Nothing.

**Parameters:**
- `option`: The Option to convert.
- `error_message`: The error message to use if option is Nothing.

**Returns:** Result.Ok(value) if present, or Result.Error(error_message).

---

## Function: `to_option`

Converts a Result into an Option, discarding the error message if Error.

**Parameters:**
- `result`: The Result to convert.

**Returns:** Option.Something(value) if Ok, or Option.Nothing if Error.

---

## Function: `from_value`

Wraps a raw value into an Option: Option.Nothing if value is Nothing, otherwise Option.Something(value).

**Parameters:**
- `value`: The value to wrap.

**Returns:** Option.Nothing if value == Nothing, else Option.Something(value).

---

## Function: `to_value`

Unwraps an Option into a raw value or Nothing.

**Parameters:**
- `option`: The Option to unwrap.

**Returns:** The internal value if Option.Something, or Nothing if Option.Nothing.

---

## Function: `compare`

Compares two values and returns an Ordering variant.

**Parameters:**
- `a`: The first value.
- `b`: The second value.

**Returns:** Ordering.Less if a < b, Ordering.Greater if a > b, Ordering.Equal otherwise.

---

## Function: `identity`

Returns the passed argument unchanged.

**Parameters:**
- `x`: The value to return.

**Returns:** The value x.

---

# Module: zen.net.socket

## Class: `Socket`

Low-level Socket Networking.

---

## Method: `Socket.init`

Initializes a new socket.

**Parameters:**
- `family`: AF_INET, AF_INET6, or AF_UNIX.
- `type`: SOCK_STREAM or SOCK_DGRAM.

---

## Method: `Socket.connect`

Connects to a remote address.

**Parameters:**
- `host`: The hostname or IP.
- `port`: The port number.

---

## Method: `Socket.send`

Sends data over the socket.

**Parameters:**
- `data`: String or Bytes object.

---

## Method: `Socket.recv`

Receives data from the socket.

**Parameters:**
- `bufsize`: Maximum number of bytes to receive.

**Returns:** String of received data.

---

## Method: `Socket.close`

Closes the socket.

---

# Module: zen.net.http

> Thin dual-path HTTP client. **Interpret:** urllib. **Native `-g`:** curl on PATH.

All request helpers return `{ status, body, headers }`. Transport failure → `status = -1`.

Helpers: `ok(resp)` (2xx), `status(resp)`, `body(resp)`.

---

## Function: `get` / `post` / `request`

| API | Notes |
|-----|--------|
| `get(url)` | GET |
| `post(url, body, headers)` | POST; headers may be `{}` |
| `request(url, method, body, headers)` | Generic |

Supports `http(s)://` and offline `file://` (tests). Requires **curl** for native binaries.

---

# Module: zen.collections.stack

## Class: `Stack`

Stack utility (LIFO). Uses a list as the underlying container.

---

## Method: `Stack.init`

Initializes a new empty stack.

---

## Method: `Stack.push`

Pushes a value onto the stack.

**Parameters:**
- `v`: The value.

---

## Method: `Stack.pop`

Pops the top value from the stack.

**Returns:** The popped value.

---

## Method: `Stack.peek`

Returns the top value without removing it.

**Returns:** The top value.

---

## Method: `Stack.size`

Returns the number of items in the stack.

---

# Module: zen.collections.queue

## Class: `Queue`

Queue utility (FIFO). Uses a list as the underlying container.

---

## Method: `Queue.init`

Initializes a new empty queue.

---

## Method: `Queue.enqueue`

Adds an item to the back of the queue.

**Parameters:**
- `v`: The value.

---

## Method: `Queue.dequeue`

Removes and returns the front item from the queue.

**Returns:** The front value.

---

## Method: `Queue.peek`

Returns the front item without removing it.

**Returns:** The front value.

---

## Method: `Queue.size`

Returns the number of items in the queue.

---

# Module: zen.collections.set

> Set utilities.

---

## Function: `from_list`

Creates a set from a list of elements.

**Parameters:**
- `l`: The list.

**Returns:** A new set.

---

## Function: `to_list`

Converts a set back to a list.

**Parameters:**
- `s`: The set.

**Returns:** A list of elements.

---

# Module: zen.collections.list

> List utility module. Provides functional operations for lists.

---

## Function: `map`

Applies a function to each element of a list and returns a new list of results.

**Parameters:**
- `list`: The list to map.
- `fn`: The function to apply (element -> result).

**Returns:** A new list.

---

## Function: `filter`

Filters a list based on a predicate function.

**Parameters:**
- `list`: The list to filter.
- `fn`: The predicate function (element -> boolean).

**Returns:** A new list containing only elements that matched the predicate.

---

## Function: `reduce`

Reduces a list to a single value using an accumulator function.

**Parameters:**
- `list`: The list to reduce.
- `initial`: The initial accumulator value.
- `fn`: The reducer function (accumulator, element -> new_accumulator).

**Returns:** The final accumulator value.

---

## Function: `each`

Executes a function for each element of a list.

**Parameters:**
- `list`: The list.
- `fn`: The function to execute (element -> void).

---

## Function: `find`

Finds the first element in a list that matches a predicate.

**Parameters:**
- `list`: The list.
- `fn`: The predicate function.

**Returns:** The element, or nothing if not found.

---

## Function: `contains`

Checks if a list contains a specific value.

**Parameters:**
- `list`: The list.
- `val`: The value to search for.

**Returns:** True if found, False otherwise.

---

# Module: zen.math.math

> Mathematics module. Provides common mathematical constants and functions.

---

### Description

The Archimedes constant PI.

---

### Description

Euler's number E.

---

## Function: `min`

Returns the minimum of two numbers.

**Parameters:**
- `a`: The first number.
- `b`: The second number.

**Returns:** The smaller of a and b.

---

## Function: `max`

Returns the maximum of two numbers.

**Parameters:**
- `a`: The first number.
- `b`: The second number.

**Returns:** The larger of a and b.

---

## Function: `sqrt`

Returns the square root of x.

**Parameters:**
- `x`: The number.

**Returns:** The square root.

---

## Function: `pow`

Returns x raised to the power of y.

**Parameters:**
- `x`: The base.
- `y`: The exponent.

**Returns:** x^y.

---

## Function: `sin`

Returns the sine of x (in radians).

**Parameters:**
- `x`: The angle in radians.

**Returns:** The sine value.

---

## Function: `cos`

Returns the cosine of x (in radians).

**Parameters:**
- `x`: The angle in radians.

**Returns:** The cosine value.

---

## Function: `floor`

Returns the largest integer less than or equal to x.

**Parameters:**
- `x`: The number.

**Returns:** The floor value.

---

## Function: `ceil`

Returns the smallest integer greater than or equal to x.

**Parameters:**
- `x`: The number.

**Returns:** The ceiling value.

---

# Module: zen.math.random

> Deterministic Randomness module. Provides seedable PRNGs and global randomness functions.

---

## Function: `seed`

Initializes a new deterministic random number generator with a seed.

**Parameters:**
- `s`: The seed value.

**Returns:** An RNG object.

---

## Function: `integer`

Returns a random integer between min and max (inclusive).

**Parameters:**
- `min`: The minimum value.
- `max`: The maximum value.

**Returns:** A random integer.

---

## Function: `decimal`

Returns a random decimal between min and max.

**Parameters:**
- `min`: The minimum value.
- `max`: The maximum value.

**Returns:** A random decimal.

---

## Function: `range`

Returns a random value in the specified range. If min and max are integers, returns an integer. Otherwise returns a decimal.

**Parameters:**
- `min`: The minimum value.
- `max`: The maximum value.

**Returns:** A random value.

---

# Module: zen.math.range

> Range utility module. Prefer the language operators `start..end` (exclusive)
> and `start..=end` (inclusive) in new code; these helpers wrap those operators
> for call-style APIs.

---

## Function: `range`

Creates a list of integers from start (inclusive) to end (exclusive).
Same as the operator form `start..end`.

**Parameters:**
- `start`: The start value (integer).
- `end`: The end value (integer, exclusive).

**Returns:** A list of integers.

**Example:**
```zl
import zen.math.range as R
R.range(2, 6)   // [2, 3, 4, 5]
2..6            // same
```

---

## Function: `range_inclusive`

Creates a list of integers from start to end inclusive.
Same as the operator form `start..=end`.

**Parameters:**
- `start`: The start value (integer).
- `end`: The end value (integer, inclusive).

**Returns:** A list of integers.

**Example:**
```zl
import zen.math.range as R
R.range_inclusive(2, 4)   // [2, 3, 4]
2..=4                     // same
```

---

# Module: zen.graphics.ppm

## Class: `PPM`

Portable PixMap (PPM) Graphics Module. Implements the ASCII P3 format.

---

## Method: `PPM.init`

Initializes a new PPM image.

**Parameters:**
- `w`: The width in pixels.
- `h`: The height in pixels.

---

## Method: `PPM.set_pixel`

Sets a pixel at the given coordinates.

**Parameters:**
- `x`: The x coordinate.
- `y`: The y coordinate.
- `r`: Red value (0-255).
- `g`: Green value (0-255).
- `b`: Blue value (0-255).

---

## Method: `PPM.fill`

Fills the entire image with a single color.

**Parameters:**
- `r`: Red value (0-255).
- `g`: Green value (0-255).
- `b`: Blue value (0-255).

---

## Method: `PPM.save`

Writes the PPM image to a file.

**Parameters:**
- `path`: The path to write to.

---

# Module: zen.graphics.bmp

## Class: `BMP`

Bitmap (BMP) Graphics Module. Implements uncompressed 24-bit BMP image creation.

---

## Method: `BMP.init`

Initializes a new BMP image.

**Parameters:**
- `w`: The width in pixels.
- `h`: The height in pixels.

---

## Method: `BMP.set_pixel`

Sets a pixel at the given coordinates.

**Parameters:**
- `x`: The x coordinate.
- `y`: The y coordinate.
- `r`: Red value (0-255).
- `g`: Green value (0-255).
- `b`: Blue value (0-255).

---

## Method: `BMP.fill`

Fills the entire image with a single color.

**Parameters:**
- `r`: Red value (0-255).
- `g`: Green value (0-255).
- `b`: Blue value (0-255).

---

## Method: `BMP._write_u32`

Writes a 32-bit integer as 4 little-endian bytes to a list.

---

## Method: `BMP._write_u16`

Writes a 16-bit integer as 2 little-endian bytes to a list.

---

## Method: `BMP.save`

Writes the BMP image to a file.

**Parameters:**
- `path`: The path to write to.

---

# Module: zen.crypto.hash

> Cryptographic Hashing.

---

## Function: `md5`

Computes the MD5 hash of the data.

**Parameters:**
- `data`: String or Bytes.

**Returns:** Hex string.

---

## Function: `sha1`

Computes the SHA1 hash of the data.

**Parameters:**
- `data`: String or Bytes.

**Returns:** Hex string.

---

## Function: `sha256`

Computes the SHA256 hash of the data.

**Parameters:**
- `data`: String or Bytes.

**Returns:** Hex string.

---

# Module: zen.crypto.base64

> Base64 Encoding and Decoding.

---

## Function: `encode`

Encodes data to Base64 string.

**Parameters:**
- `data`: String or Bytes.

**Returns:** Base64 encoded string.

---

## Function: `decode`

Decodes Base64 string to original string.

**Parameters:**
- `data`: Base64 encoded string.

**Returns:** Decoded string.

---

# Module: zen.time

> Time and Duration utility module. Provides functions for time tracking, delays, and duration management.

---

### Description

Duration structure representing a length of time. Wraps a Decimal value representing seconds.

---

## Function: `now`

Returns the current wallclock time in seconds since the Epoch.

**Returns:** The current timestamp.

---

## Function: `wallclock`

Returns the current wallclock time in seconds since the Epoch. Alias for now().

**Returns:** The current timestamp.

---

## Function: `monotonic`

Returns the current monotonic time in seconds. Useful for measuring elapsed time without being affected by system clock changes.

**Returns:** The current monotonic timestamp.

---

## Function: `sleep`

Pauses the current execution for the specified duration.

**Parameters:**
- `d`: The duration to sleep (can be a number of seconds or a Duration).

---

## Class: `Timer`

Timer utility for measuring elapsed time.

---

## Method: `Timer.init`

Initializes a new timer.

---

## Method: `Timer.start`

Starts or restarts the timer.

---

## Method: `Timer.elapsed`

Returns the elapsed time since start() was called.

**Returns:** The elapsed time in seconds (as a Decimal).

---

## Method: `Timer.elapsed_ms`

Returns the elapsed time in milliseconds.

**Returns:** The elapsed time in ms.

---

## Method: `Timer.stop`

Stops the timer.

---

# Module: zen.patterns.fsm

## Class: `FSM`

Finite State Machine (FSM) Pattern. Provides a structured way to manage state transitions.

---

## Method: `FSM.init`

Initializes a new FSM with an initial state.

**Parameters:**
- `initial_state`: The starting state.

---

## Method: `FSM.add_transition`

Adds a transition between states.

**Parameters:**
- `from`: The source state.
- `event`: The event triggering the transition.
- `to`: The destination state.

---

## Method: `FSM.handle_event`

Processes an event and transitions to the next state if defined.

**Parameters:**
- `event`: The event to handle.

**Returns:** True if a transition occurred.

---

## Method: `FSM.get_state`

Returns the current state of the FSM.

**Returns:** The current state name.

---

## Method: `FSM.reset`

Resets the FSM to a specific state.

**Parameters:**
- `state`: The state to reset to.

---

# Module: zen.patterns.ecs

## Class: `ECS`

Entity Component System (ECS) Pattern. Provides a high-performance architecture for data-driven applications.

---

## Method: `ECS.init`

Initializes a new ECS registry.

---

## Method: `ECS.create_entity`

Creates a new entity and returns its ID.

**Returns:** The entity ID.

---

## Method: `ECS.destroy_entity`

Destroys an entity and all its components.

**Parameters:**
- `entity`: The entity ID.

---

## Method: `ECS.has_entity`

Checks if an entity exists in the registry.

**Parameters:**
- `entity`: The entity ID.

**Returns:** True if it exists.

---

## Method: `ECS.get_entity`

Retrieves all components for an entity as a map.

**Parameters:**
- `entity`: The entity ID.

**Returns:** A map of type names to components.

---

## Method: `ECS.add_component`

Adds a component to an entity.

**Parameters:**
- `entity`: The entity ID.
- `component`: The component object.

---

## Method: `ECS.get_component`

Retrieves a component from an entity by type name.

**Parameters:**
- `entity`: The entity ID.
- `type`: The component type name.

**Returns:** The component or nothing.

---

## Method: `ECS.has_component`

Checks if an entity has a specific component.

**Parameters:**
- `entity`: The entity ID.
- `type`: The component type name.

**Returns:** True if it has the component.

---

## Method: `ECS.destroy_component`

Removes a component from an entity by type name.

**Parameters:**
- `entity`: The entity ID.
- `type`: The component type name.

---

## Method: `ECS.query`

Queries entities that have all of the required components.

**Parameters:**
- `types`: A list of component type names.

**Returns:** A list of entity IDs.

---

## Method: `ECS.list_entities`

Returns a list of all entity IDs.

**Returns:** A list of entity IDs.

---

## Method: `ECS.count_entities`

Returns the total number of entities.

**Returns:** The entity count.

---

## Method: `ECS.list_components`

Returns a list of all component type names for an entity.

**Parameters:**
- `entity`: The entity ID.

**Returns:** A list of type names.

---

## Method: `ECS.clear`

Clears all entities and components from the registry.

---

# Module: zen.test

> Unit testing framework. Provides assertions and test management utilities.

---

## Function: `assert_equal`

Assets that two values are equal.

**Parameters:**
- `actual`: The actual value.
- `expected`: The expected value.
- `message`: Optional message to display on failure.

---

## Function: `assert_true`

Assets that a value is true.

**Parameters:**
- `value`: The value.
- `message`: Optional message.

---

## Function: `assert_false`

Assets that a value is false.

**Parameters:**
- `value`: The value.
- `message`: Optional message.

---

## Function: `run_unit`

Runs a test function and captures its success/failure.

**Parameters:**
- `name`: The name of the test.
- `fn`: The test function.

---

## Function: `run_suite`

Simple suite-like runner for multiple tests.

**Parameters:**
- `name`: The name of the suite.
- `tests`: A list of maps with 'name' and 'fn'.

---

# Module: zen.geometry.vector2

## Class: `Vector2`

Class representing a 2D vector.

---

## Method: `Vector2.init`

Initializes a new Vector2.

**Parameters:**
- `x`: The x-component.
- `y`: The y-component.

---

## Method: `Vector2.add`

Adds another vector to this vector.

---

## Method: `Vector2.sub`

Subtracts another vector from this vector.

---

## Method: `Vector2.scale`

Scales this vector by a scalar value.

---

## Method: `Vector2.length`

Calculates the length (magnitude) of this vector.

---

## Method: `Vector2.normalize`

Normalizes this vector to a length of 1.

---

# Module: zen.geometry.size

## Class: `Size`

Class representing a 2D size.

---

## Method: `Size.init`

Initializes a new Size.

**Parameters:**
- `w`: The width.
- `h`: The height.

---

# Module: zen.geometry.triangle

## Class: `Triangle`

Class representing a 2D triangle.

---

## Method: `Triangle.init`

Initializes a new Triangle.

**Parameters:**
- `p1`: The first point.
- `p2`: The second point.
- `p3`: The third point.

---

## Method: `Triangle.area`

Calculates the area of the triangle.

---

# Module: zen.geometry.rectangle

## Class: `Rectangle`

Class representing a 2D rectangle.

---

## Method: `Rectangle.init`

Initializes a new Rectangle.

**Parameters:**
- `x`: The x-coordinate.
- `y`: The y-coordinate.
- `w`: The width.
- `h`: The height.

---

## Method: `Rectangle.contains`

Checks if the rectangle contains a point.

---

## Method: `Rectangle.intersects`

Checks if the rectangle intersects with another rectangle.

---

## Method: `Rectangle.center`

Returns the center point of the rectangle.

---

# Module: zen.geometry.line

## Class: `Line`

Class representing a 2D line segment.

---

## Method: `Line.init`

Initializes a new Line.

**Parameters:**
- `start`: The starting point.
- `end`: The ending point.

---

## Method: `Line.length`

Calculates the length of this line segment.

---

## Method: `Line.direction`

Calculates the direction vector of this line segment.

---

## Method: `Line.midpoint`

Returns the midpoint of this line segment.

---

# Module: zen.geometry.point

## Class: `Point`

Class representing a 2D point.

---

## Method: `Point.init`

Initializes a new Point.

**Parameters:**
- `x`: The x-coordinate.
- `y`: The y-coordinate.

---

## Method: `Point.distance`

Calculates the distance between this point and another point.

---

## Method: `Point.to_vector`

Converts this point to a vector.

---

## Method: `Point.translate`

Translates this point by a vector, returning a new point.

---

# Module: zen.geometry.circle

## Class: `Circle`

Class representing a 2D circle.

---

## Method: `Circle.init`

Initializes a new Circle.

**Parameters:**
- `center`: The center point of the circle.
- `r`: The radius of the circle.

---

## Method: `Circle.contains`

Checks if the circle contains a point.

---

# Module: zen.geometry.vector3

## Class: `Vector3`

Class representing a 3D vector.

---

## Method: `Vector3.init`

Initializes a new Vector3.

**Parameters:**
- `x`: The x-component.
- `y`: The y-component.
- `z`: The z-component.

---

## Method: `Vector3.add`

Adds another vector to this vector.

---

## Method: `Vector3.sub`

Subtracts another vector from this vector.

---

## Method: `Vector3.scale`

Scales this vector by a scalar value.

---

## Method: `Vector3.length`

Calculates the length (magnitude) of this vector.

---

## Method: `Vector3.normalize`

Normalizes this vector to a length of 1.

---

# Module: zen.error

> Standard library module for error creation and management.

---

## Function: `new`

Creates a new error object with a dynamic message.

**Parameters:**
- `message`: The error message.

**Returns:** A new error object.

---

## Function: `literal`

Creates an error literal.

**Parameters:**
- `message`: The error message.

**Returns:** A new error literal.

---

# Module: zen.ui.prompt

> Interactive command-line prompts for CLI workflows. Import: `use zen.ui.prompt as prompt`.

| Function | Signature | Description |
|---|---|---|
| `confirm` | `confirm(msg, default_val)` | Boolean Yes/No prompt with fallback. |
| `text_input` | `text_input(msg, default_val)` | Text line input with default fallback. |
| `password` | `password(msg)` | Password input (masks keystrokes). |
| `select` | `select(msg, options, default_idx)` | Single-choice list selection. |
| `multiselect` | `multiselect(msg, options, default_selected)` | Multiple-choice list selection. |

---

# Module: zen.ui.tree

> Visual hierarchy and tree structure formatting for terminal applications. Import: `use zen.ui.tree as tree`.

| Function | Signature | Description |
|---|---|---|
| `format` | `format(node, use_unicode)` | Renders a hierarchical node tree map `{ "label" -> ..., "children" -> [...] }` with tree branch connectors (`├──`, `└──`). |

---

# Module: zen.ui.chart

> Terminal data visualizations (sparklines, bar charts). Import: `use zen.ui.chart as chart`.

| Function | Signature | Description |
|---|---|---|
| `sparkline` | `sparkline(values)` | Renders a 1-line UTF-8 block sparkline (` ▂▃▄▅▆▇█`). |
| `bar_chart_h` | `bar_chart_h(items, options)` | Renders a horizontal bar chart with labels and values. |
| `bar_chart_v` | `bar_chart_v(items, height)` | Renders a multi-column vertical bar chart. |

---

# Module: zen.ui.table

> Declarative terminal data table formatting with auto-column sizing and borders. Import: `use zen.ui.table as table`.

| Function / Class | Signature | Description |
|---|---|---|
| `format_table` | `format_table(headers, rows, options)` | Renders a multi-line formatted table string. |
| `Table` | `Table(headers, options)` | State-accumulating table class (`add_row`, `add_rows`, `render`, `print`). |

**Supported Border Styles (`options["style"]`):**
- `unicode` (default): Classic Unicode box drawing (`┌─┬─┐`, `├─┼─┤`, `└─┴─┘`)
- `rounded`: Rounded Unicode box drawing (`╭─┬─╮`, `├─┼─┤`, `╰─┴─╯`)
- `ascii`: ASCII grid characters (`+---+`, `| |`)
- `markdown`: GitHub Flavored Markdown table format (`|---|`)
- `minimal`: Clean horizontal dividers without vertical pipes

---

# Module: zen.ui.spinner

> Animated CLI activity loading spinners. Import: `use zen.ui.spinner as spinner`.

| Function / Class | Signature | Description |
|---|---|---|
| `create` | `create(message, style_name)` | Factory for a new `Spinner` instance. |
| `Spinner` | `Spinner(message, style_name)` | Interactive spinner class (`tick`, `next_frame`, `success`, `error`, `info`, `stop`). |

**Supported Spinner Styles:**
- `dots` (default): Unicode braille dots (`⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`)
- `line`: Classic ASCII rotating line (`- \ | /`)
- `arc`: Quarter circle arcs (`◜ ◠ ◝ ◞ ◡ ◟`)
- `circle`: Rotating shaded circles (`◐ ◓ ◑ ◒`)
- `bouncing_bar`: Bouncing bracket progress bar (`[==  ]`)

---

# Module: zen.text.fuzzy

> Fuzzy subsequence matching, scoring, and candidate ranking. Import: `use zen.text.fuzzy as fuzzy`.

| Function | Signature | Description |
|---|---|---|
| `levenshtein` | `levenshtein(s1, s2)` | Computes edit distance between two strings. |
| `match` | `match(pattern, text)` | Fuzzy subsequence match test. |
| `score` | `score(pattern, text)` | Match quality score (0.0 to 1.0). |
| `filter` | `filter(pattern, candidates, min_score)` | Returns ranked candidates above minimum score threshold. |

---

# Module: zen.text.inflect

> String casing, inflections, and slugification. Import: `use zen.text.inflect as inflect`.

| Function | Signature | Description |
|---|---|---|
| `camel_case` | `camel_case(s)` | Formats string to `camelCase`. |
| `snake_case` | `snake_case(s)` | Formats string to `snake_case`. |
| `kebab_case` | `kebab_case(s)` | Formats string to `kebab-case`. |
| `pascal_case` | `pascal_case(s)` | Formats string to `PascalCase`. |
| `title_case` | `title_case(s)` | Formats string to `Title Case`. |
| `slugify` | `slugify(s)` | URL-safe slug string. |
| `pluralize` | `pluralize(word)` | Pluralizes common English nouns. |

---

# Module: zen.collections.priority_queue

> Sorted Priority Queue collection (Min/Max). Import: `use zen.collections.priority_queue as pq`.

| Function | Signature | Description |
|---|---|---|
| `create` | `create(is_max_queue)` | Creates an empty priority queue. |
| `push` | `push(queue, item, priority)` | Inserts item with assigned priority score. |
| `pop` | `pop(queue)` | Removes and returns item with highest priority. |
| `peek` | `peek(queue)` | Returns highest priority item without removing. |
| `size` | `size(queue)` | Returns number of queued items. |

---

# Module: zen.collections.lru

> Fixed-capacity Least Recently Used (LRU) eviction cache. Import: `use zen.collections.lru as lru`.

| Function | Signature | Description |
|---|---|---|
| `create` | `create(capacity)` | Creates an LRU cache with capacity limit. |
| `get` | `get(cache, key)` | Retrieves key and marks as most recently used. |
| `put` | `put(cache, key, value)` | Inserts or updates key, evicting oldest item if full. |
| `size` | `size(cache)` | Current number of cached items. |

---

# Module: zen.collections.ring_buffer

> Sliding window circular ring buffer. Import: `use zen.collections.ring_buffer as ring_buffer`.

| Function | Signature | Description |
|---|---|---|
| `create` | `create(capacity)` | Creates a ring buffer with fixed capacity. |
| `push` | `push(rb, item)` | Adds item, overwriting oldest entry when full. |
| `to_list` | `to_list(rb)` | Returns all buffered items in chronological order. |
| `size` | `size(rb)` | Current item count. |

---

# Module: zen.math.stats

> Summary statistics, dispersion, and percentiles. Import: `use zen.math.stats as stats`.

| Function | Signature | Description |
|---|---|---|
| `sum` | `sum(numbers)` | Sum of numbers list. |
| `mean` | `mean(numbers)` | Arithmetic mean / average. |
| `median` | `median(numbers)` | Median value. |
| `variance` | `variance(numbers)` | Sample variance ($s^2$). |
| `stdev` | `stdev(numbers)` | Standard deviation ($s$). |
| `percentile` | `percentile(numbers, p)` | $P$-th percentile value ($0 \le p \le 100$). |
| `summary` | `summary(numbers)` | Map with count, sum, min, max, mean, median, stdev. |

---

# Module: zen.crypto.hash

> Pure Zenlang cryptographic and non-cryptographic hashing. Import: `use zen.crypto.hash as hash`.

| Function | Signature | Description |
|---|---|---|
| `sha256` | `sha256(data)` | Computes standard 256-bit SHA-256 hex digest. |
| `fnv1a` | `fnv1a(data)` | Computes fast 32-bit FNV-1a hex digest. |

---

# Module: zen.crypto.base64

> Standard and URL-safe Base64 encoding and decoding. Import: `use zen.crypto.base64 as base64`.

| Function | Signature | Description |
|---|---|---|
| `encode` | `encode(data)` | Standard Base64 string encoding. |
| `decode` | `decode(s)` | Decodes standard Base64 string to byte list. |
| `encode_url` | `encode_url(data)` | URL-safe Base64 encoding (`-` and `_`, unpadded). |
| `decode_url` | `decode_url(s)` | Decodes URL-safe Base64 string. |

---

# Module: zen.crypto.hmac

> RFC 2104 compliant HMAC-SHA256 authentication. Import: `use zen.crypto.hmac as hmac`.

| Function | Signature | Description |
|---|---|---|
| `sha256` | `sha256(key, message)` | Generates 64-char lowercase HMAC-SHA256 digest. |
| `verify` | `verify(mac1, mac2)` | Constant-time string comparison preventing timing attacks. |

---

# Module: zen.crypto.jwt

> JSON Web Token (JWT) signing and verification (HS256). Import: `use zen.crypto.jwt as jwt`.

| Function | Signature | Description |
|---|---|---|
| `sign` | `sign(payload_map, secret)` | Creates signed `header.payload.signature` token. |
| `decode` | `decode(token_str)` | Parses token without signature check (`{ header, payload }`). |
| `verify` | `verify(token_str, secret)` | Verifies HMAC signature and extracts payload. |

---

# Module: zen.time.cron

> Standard 5-field cron parsing and schedule matching. Import: `use zen.time.cron as cron`.

| Function | Signature | Description |
|---|---|---|
| `parse` | `parse(cron_expr)` | Parses 5-field cron string into structured map. |
| `matches` | `matches(cron_expr, min, hr, day, mon, wday)` | Tests if cron schedule matches given date/time components. |

---

# Module: zen.data.schema

> Declarative data validation rules. Import: `use zen.data.schema as schema`.

| Function | Signature | Description |
|---|---|---|
| `validate` | `validate(data, schema_spec)` | Validates data object against schema definition, returning `{ "valid" -> bool, "errors" -> list }`. Supports types, required keys, min/max, string length, and enums. |

---

# Module: zen.data.tar

> POSIX USTAR format TAR archive parser and creator. Import: `use zen.data.tar as tar`.

| Function | Signature | Description |
|---|---|---|
| `create` | `create(files_list)` | Generates raw tar archive bytes from a list of `{ "name" -> ..., "content" -> ... }` maps. |
| `parse` | `parse(tar_data)` | Parses tar archive into list of member file maps. |

---

# Module: zen.net.ip

> IP address parsing, CIDR subnets, and private range detection. Import: `use zen.net.ip as ip`.

| Function | Signature | Description |
|---|---|---|
| `parse_v4` | `parse_v4(ip_str)` | Parses IPv4 into 4-octet byte list `[a, b, c, d]`. |
| `to_string_v4` | `to_string_v4(octets)` | Formats octets list into `"A.B.C.D"`. |
| `is_v4` | `is_v4(ip_str)` | Checks if string is valid IPv4. |
| `is_private_v4` | `is_private_v4(ip_str)` | Checks if IPv4 is private (10.x, 172.16-31.x, 192.168.x, 127.x). |
| `is_loopback_v4` | `is_loopback_v4(ip_str)` | Checks if IPv4 is loopback (127.0.0.0/8). |
| `cidr_contains_v4` | `cidr_contains_v4(cidr, ip)` | Tests if IP is inside CIDR subnet block. |
| `is_v6` | `is_v6(ip_str)` | Validates IPv6 format. |

---

# Module: zen.net.server

> HTTP and network server routing and request dispatch. Import: `use zen.net.server as server`.

| Function | Signature | Description |
|---|---|---|
| `create_router` | `create_router()` | Creates a new request router. |
| `add_route` | `add_route(router, method, path, handler)` | Registers route handler with optional path parameters (`:id`). |
| `match_route` | `match_route(router, method, path)` | Matches method and path against routes. |
| `handle_request` | `handle_request(router, request_map)` | Dispatches request through router to matching handler. |
| `text_response` | `text_response(status, body)` | Creates plain text HTTP response map. |
| `json_response` | `json_response(status, json_str)` | Creates JSON HTTP response map. |

---

# Module: zen.test.mock

> Test spies, stubs, and function call recording. Import: `use zen.test.mock as mock`.

| Function | Signature | Description |
|---|---|---|
| `create` | `create(default_return)` | Creates a new mock/spy object. |
| `record_call` | `record_call(mock, args_list)` | Records a call and returns stubbed value. |
| `returns` | `returns(mock, value)` | Configures return value for mock. |
| `was_called` | `was_called(mock)` | Tests if mock was called $\ge 1$ times. |
| `called_times` | `called_times(mock, count)` | Tests if mock was called exactly $N$ times. |
| `last_called_with` | `last_called_with(mock, args_list)` | Tests arguments passed on most recent call. |

---

# Module: zen.util.bench

> Micro-benchmarking and execution profiling. Import: `use zen.util.bench as bench`.

| Function | Signature | Description |
|---|---|---|
| `benchmark` | `benchmark(name, fn, iterations)` | Measures execution time and throughput of `fn()`. |
| `format` | `format(result)` | Formats benchmark metrics into human-readable text. |

---

# Module: zen.util.inspect

> Deep runtime value inspection and type introspection. Import: `use zen.util.inspect as inspect`.

| Function | Signature | Description |
|---|---|---|
| `type_of` | `type_of(val)` | Returns string type of any Zenlang value. |
| `inspect` | `inspect(val)` | Formats value with detailed type annotations. |
| `dump` | `dump(val)` | Prints inspected value to stdout. |

---

# Module: zen.text.lorem

> Classical Latin placeholder text and dummy data generator. Import: `use zen.text.lorem as lorem`.

| Function | Signature | Description |
|---|---|---|
| `word` | `word()` | Returns a random single Latin word. |
| `words` | `words(n)` | Returns `n` random words as a space-separated string. |
| `words_list` | `words_list(n)` | Returns a list of `n` random words. |
| `sentence` | `sentence(min_words, max_words)` | Generates a capitalized sentence ending with a period. |
| `sentences` | `sentences(n)` | Generates `n` sentences joined by spaces. |
| `paragraph` | `paragraph(min_sentences, max_sentences)` | Generates a paragraph of randomized sentences. |
| `paragraphs` | `paragraphs(n)` | Generates `n` paragraphs separated by `\n\n`. |
| `title` | `title(min_words, max_words)` | Generates a Title Cased placeholder heading. |
| `slug` | `slug(n)` | Generates `n` random words separated by hyphens. |
| `standard` | `standard()` | Returns the canonical classical *"Lorem ipsum..."* passage. |
| `classic` | `classic()` | Alias for `standard()`. |
| `rng_word` | `rng_word(g)` | Seeded RNG variant: returns a random word using generator `g`. |
| `rng_sentence` | `rng_sentence(g, min_w, max_w)` | Seeded RNG variant: returns a randomized sentence. |
| `rng_paragraph` | `rng_paragraph(g, min_s, max_s)` | Seeded RNG variant: returns a randomized paragraph. |

---

# Module: zen.color

> Comprehensive color representation, conversions (Hex, RGB, HSL, 8/16 ANSI, 256-color), 24-bit TrueColor SGR escape generation, color blending, luminance, and WCAG contrast calculations. Import: `use zen.color as color` (or `use zen.ui.color as color`).

### Structures
- `Color { r: Integer, g: Integer, b: Integer, a: Integer }` — 8-bit RGBA channels (0–255).
- `Hsl { h: Integer, s: Integer, l: Integer }` — Hue (0–360), Saturation (0–100), Lightness (0–100).

| Function | Signature | Description |
|---|---|---|
| `rgb` | `rgb(r, g, b)` | Constructs a `Color` structure with alpha=255. |
| `rgba` | `rgba(r, g, b, a)` | Constructs a `Color` structure with custom alpha. |
| `hex` | `hex(str)` | Parses `#RRGGBB`, `RRGGBB`, `#RGB`, or `RGB` hex string into `Color`. |
| `hsl` | `hsl(h, s, l)` | Constructs a `Color` from Hue, Saturation, and Lightness. |
| `named` | `named(name)` | Looks up standard ANSI/CSS named color (e.g. `red`, `bright_cyan`, `gold`, `gray`). |
| `has_named` | `has_named(name)` | Checks if a named color exists in the palette. |
| `to_hex` | `to_hex(c)` | Formats a `Color` as a lowercase `#rrggbb` string. |
| `to_hex_alpha` | `to_hex_alpha(c)` | Formats a `Color` as a `#rrggbbaa` string. |
| `fg` | `fg(c)` | Returns 24-bit TrueColor foreground ANSI escape sequence (`\x1b[38;2;r;g;bm`). |
| `bg` | `bg(c)` | Returns 24-bit TrueColor background ANSI escape sequence (`\x1b[48;2;r;g;bm`). |
| `fg_16` | `fg_16(color_or_code)` | Returns standard 16-color ANSI foreground escape. |
| `bg_16` | `bg_16(color_or_code)` | Returns standard 16-color ANSI background escape. |
| `fg_256` | `fg_256(index)` | Returns 256-color palette foreground escape sequence. |
| `bg_256` | `bg_256(index)` | Returns 256-color palette background escape sequence. |
| `reset` | `reset()` | Returns ANSI reset escape sequence (`\x1b[0m`). |
| `paint` | `paint(text, fg_color, bg_color)` | Formats text with fg and optional bg color, appending reset. |
| `bold` | `bold(text)` | Wraps text in ANSI bold escape sequence. |
| `dim` | `dim(text)` | Wraps text in ANSI dim escape sequence. |
| `italic` | `italic(text)` | Wraps text in ANSI italic escape sequence. |
| `underline` | `underline(text)` | Wraps text in ANSI underline escape sequence. |
| `inverse` | `inverse(text)` | Wraps text in ANSI inverse video escape sequence. |
| `strikethrough` | `strikethrough(text)` | Wraps text in ANSI strikethrough escape sequence. |
| `blend` | `blend(c1, c2, t)` | Linearly interpolates between two colors by factor `t` (0.0 to 1.0). |
| `lighten` | `lighten(c, pct)` | Lightens a color towards white by percentage (0–100). |
| `darken` | `darken(c, pct)` | Darkens a color towards black by percentage (0–100). |
| `grayscale` | `grayscale(c)` | Converts color to grayscale using standard luminance weighting. |
| `luminance` | `luminance(c)` | Calculates relative luminance of color (0.0 to 1.0). |
| `is_dark` | `is_dark(c)` | Returns `True` if perceived luminance $< 0.5$. |
| `is_light` | `is_light(c)` | Returns `True` if perceived luminance $\ge 0.5$. |
| `contrast_ratio` | `contrast_ratio(c1, c2)` | Computes the WCAG readability contrast ratio between two colors (1.0 to 21.0). |

---

# Module: zen.data.zendata (alias: `zen.zendata`)

> Universal declarative data format (`.zd`) parser, serializer, and tagged struct engine.

### Functions

| Function | Signature | Description |
|---|---|---|
| `parse` | `parse(text)` | Parses a Zen Data string into native Zen values, maps, and typed struct nodes. |
| `stringify` | `stringify(value, indent_level)` | Serializes any Zen value, map, list, or struct into cleanly indented `.zd` text. |
| `get` | `get(data, key, default_val)` | Safely retrieves a key from a parsed Zen Data map with fallback. |
| `has` | `has(data, key)` | Checks if a key exists in a parsed Zen Data map. |

---

# Module: zen.tooling.zencode (alias: `zen.zencode`)

> Zen Code (`.zl`) tooling for formatting, syntax highlighting, tokenizing, and AST inspection.

### Functions

| Function | Signature | Description |
|---|---|---|
| `tokenize` | `tokenize(src)` | Lexes Zenlang source into a sequence of token objects with positions and categories. |
| `format` | `format(src)` | Formats raw Zenlang source code into standard 4-space indented layout. |
| `highlight` | `highlight(src, mode)` | Highlights Zenlang code for Terminal ANSI (`"term"`) or Web HTML spans (`"html"`). |
| `stats` | `stats(src)` | Computes code metrics (total lines, tokens, functions, keywords, strings, numbers). |

---

# Module: zen.text.zenmark (alias: `zen.zenmark`)

> Technical document and markup engine (`.zm`) with DOM elements, 2-character inline spans, and universal renderers.

### Functions & Struct Constructors

| Function / Struct | Signature | Description |
|---|---|---|
| `parse_spans` | `parse_spans(text)` | Parses 2-character doubled delimiters (`**`, `^^`, `!!`, `{{`, `++`, `--`, etc.) into span tuple arrays. |
| `render_spans_term`| `render_spans_term(spans)` | Renders span tuples to ANSI colored terminal text with inverse keycaps. |
| `render_spans_html`| `render_spans_html(spans)` | Renders span tuples to semantic HTML5 elements (`<strong>`, `<em>`, `<kbd>`, etc.). |
| `Heading` | `Heading(opts)` | Constructs a `Heading` block element struct (size 1 to 6). |
| `Paragraph` | `Paragraph(opts)` | Constructs a `Paragraph` block element struct with text or span content. |
| `CodeBlock` | `CodeBlock(opts)` | Constructs a `CodeBlock` element struct with language and line numbering options. |
| `Table` | `Table(opts)` | Constructs a `Table` element struct with headers and rows. |
| `HorizontalRule` | `HorizontalRule(opts)` | Constructs a `HorizontalRule` divider struct. |
| `Document` | `Document(elements)` | Constructs a root `Document` DOM container holding child block elements. |
| `render_term` | `render_term(doc)` | Renders a full `Document` DOM tree to ANSI terminal output. |
| `render_html` | `render_html(doc)` | Renders a full `Document` DOM tree to a responsive semantic HTML5 document. |
| `parse` | `parse(doc_comment)` | Backwards-compatible parser for function doc-comments (`@param`, `@return`). |




