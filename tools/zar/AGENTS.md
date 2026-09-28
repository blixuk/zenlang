# Purpose

Standalone CLI utility and management tool for the Zen Archive Format (`.zar`). Provides high-level terminal operations: archive creation (`pack`), extraction (`unpack`), table inspection (`list`), cryptographic tamper auditing (`verify`), single-file inclusion proofs (`prove`), mutable archive editing (`add`/`rm`), QR code passkey display (`qr`), and self-extracting executable bundling (`sfx`).

# Ownership

Zenlang developer tooling and standard library maintainers.

# Local Contracts

- Built on top of `zen.data.zar` (`lib/zen/data/zar.zl`).
- Manifest-driven: Uses `zen.pkg.zd` and `.zbuild` for the Zen build system.
- Modular layout: Subcommands reside in dedicated modules under `src/` (`cmd_pack.zl`, `cmd_unpack.zl`, `cmd_list.zl`, `cmd_verify.zl`, `cmd_edit.zl`, `cmd_qr.zl`, `cmd_sfx.zl`, `ui.zl`).
- Dual-path: Must run cleanly under script interpretation (`zen tools/zar/src/main.zl` / `./scripts/zen zar`) and native AOT compilation (`zen build` -> `build/zar`).
- Clean CLI argument handling: Uses `zen.sys.sys` (`Sys.user_args(args)`) for normalized argument parsing across both script interpretation and standalone native executable.
- Terminal UI: Rich colorized status banners and Unicode table layouts using `zen.util.table` and `zen.graphics.qrcode`.

# Work Guidance

- Keep UI/CLI argument handling distinct from standard library serialization in `lib/zen/data/zar.zl`.
- Preserve exit code conventions: 0 on success, 1 on error, 2 on tamper/auth failure.
- Ensure all paths handle relative and absolute conventions cleanly.

# Verification

From `tools/zar/`:
```bash
# Direct run via Zen router:
../../bin/zen src/main.zl help

# Build native binary:
../../bin/zen build

# Pack and list an archive:
../../bin/zen src/main.zl pack ./src test.zar --compress
../../bin/zen src/main.zl list test.zar
../../bin/zen src/main.zl verify test.zar
```

# Child DOX Index

- `zen.pkg.zd` — package manifest
- `.zbuild` — build manifest
- `README.md` — user guide and CLI manual
- `src/main.zl` — CLI router and entrypoint
- `src/zar_ui.zl` — terminal ANSI colors, table formatting, and banners
- `src/cmd_pack.zl` — archive creation command
- `src/cmd_unpack.zl` — extraction command
- `src/cmd_list.zl` — table listing command
- `src/cmd_verify.zl` — cryptographic integrity & Merkle verification command
- `src/cmd_edit.zl` — mutable add and remove commands
- `src/cmd_qr.zl` — QR code passkey generator & terminal display command
- `src/cmd_sfx.zl` — self-extracting executable command
