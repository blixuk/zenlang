# Purpose

Terminal UI building blocks: canvas buffer, map-based layout, optional widgets/geometry.

# Ownership

Stdlib / TUI maintainers under `lib/zen/ui/`.

# Local Contracts

- **Dual-path surface is maps + free functions**, not class inheritance.
- `app.zl` — Bubble Tea–style shell: `run(init, update, view, opts)`, `step` / `run_msgs`, msg helpers.
- `canvas.zl` — character grid; `render` → `__builtin_term.paint_canvas` (C hot path under `-g`; color-on-change + one flush).
- App loop: drain queued keys with `poll(0)` after first wait; `dirty` skips paint when clean.
- Prefer `-g` for interactive games; interpret is slower for full-screen paint.
- `layout.zl` — map nodes: `box` / `vbox` / `hbox` / `add` / `set_expand` / `set_size` / `layout`.
- `widget.zl` — map widgets: `label`, `panel`, `progress`, `list_view`, `status` + `draw(canvas, bounds, w)`.
- Do **not** name parameters `parent` (reserved for class inheritance).
- Do **not** name free functions `init` (treated as void constructors under `-g`).
- Do **not** `import` modules inside functions under `-g` (breaks mangling; see historical `canvas.render` bug).
- Prefer `do for x in a..b` for 2D loops; avoid rebinding loop indices that hang under `-g`.
- Color names are strings (`green`, `black`, …) for `__builtin_term.color`.
- App model: set `quit` -> true to exit; msgs have `type` key | tick | resize | quit | custom.
- Class widgets / old class layout demos may still exist; new code should use app + layout + canvas.

# Work Guidance

- Headless tests: `app.step` / `run_msgs` + canvas buffer asserts (no TTY).
- Interactive: `examples/tui_counter.zl`, `examples/tui_snake.zl` (tick game).
- CI: `ZEN_TUI_HEADLESS=1` for counter/snake.
- Other demos: `layout_map_demo.zl`, `zedit.zl`, `zless.zl`.
- After changes: `test_ui_app`, `test_ui_widget`, `test_canvas`, `test_layout` interpret + `-g`.

# Verification

```bash
python3 bootstrap/Zen.py -g tests/lib/test_ui_app.zl
python3 bootstrap/Zen.py -g tests/lib/test_ui_widget.zl
python3 bootstrap/Zen.py -g tests/lib/test_canvas.zl
python3 bootstrap/Zen.py -g tests/lib/test_layout.zl
ZEN_TUI_HEADLESS=1 python3 bootstrap/Zen.py -g examples/tui_counter.zl
ZEN_TUI_HEADLESS=1 python3 bootstrap/Zen.py -g examples/tui_snake.zl
```

# Child DOX Index

- app.zl — TUI program loop (init/update/view)
- widget.zl — map widgets (label/panel/list/progress/status)
- canvas.zl — buffer + render
- layout.zl — flex map layout
- table.zl — formatted terminal data tables with custom borders & alignment
- spinner.zl — animated CLI activity spinners (dots, line, arc, bouncing_bar)
- chart.zl — sparklines, bar charts, and histograms
- tree.zl — Unicode tree hierarchy visualization
- term.zl — UI-oriented term helpers
- geometry.zl — UIRect classes (legacy)
- widgets.zl — class widgets (legacy demos)
