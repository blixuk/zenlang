# Zenlang for Zed

Language extension for [Zed](https://zed.dev): syntax highlighting, brackets, outline, and indent for `.zl` / `.zs`.

## Why install failed before

Zed compiles Tree-sitter grammars by **git checkout of a revision**.  
`rev = "local"` is **not** a valid git ref, which produces:

```text
failed to compile grammar 'zen'
failed to fetch revision local in directory '…/grammars/zen'
```

`./scripts/setup_zed_extension.sh` creates a small nested git repo under `editors/tree-sitter-zen` and writes a real commit SHA into `extension.toml`.

## Install (local)

From the **repo root**:

```bash
./scripts/setup_zed_extension.sh
```

Then in Zed:

1. **Extensions** → remove any previous Zenlang entry if present  
2. **Install Dev Extension…** → select **`editors/zed`** (this folder)  
3. Open `examples/getting_started/01_hello.zl`  
4. Language mode should be **Zenlang**

### After grammar changes

```bash
./scripts/setup_zed_extension.sh
# In Zed: uninstall + Install Dev Extension again (or restart Zed)
```

## Troubleshooting

| Message | Cause | Fix |
|---------|--------|-----|
| `failed to fetch revision local` | Invalid `rev` | Re-run `setup_zed_extension.sh` |
| `failed to compile grammar 'zen'` | WASI / parser C error | Check `zed: open log`; ensure `src/parser.c` exists after generate |
| No highlighting | Extension not active | Confirm Install Dev Extension path is `editors/zed` |
| Stale grammar | Old checkout cache | Delete `editors/zed/grammars` if present; reinstall |

Log: command palette → **zed: open log** → search `grammar zen`.

## Features

| Feature | Source |
|---------|--------|
| Highlighting | `languages/zen/highlights.scm` |
| Outline | `outline.scm` |
| Brackets | `brackets.scm` |
| Indent | `indents.scm` |
| Vim textobjects | `textobjects.scm` |

## Related

- VS Code / Cursor / Antigravity: `./scripts/setup_vscode_extension.sh`
- Grammar: `editors/tree-sitter-zen/`
