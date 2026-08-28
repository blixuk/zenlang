#!/bin/sh
# Hybrid production entry for bin/zen (installed by ./scripts/zen install-handoff).
#
# Layout:
#   Compiler CLI (compile | build | run | check | deps | help):
#     → bin/zen-selfhost when present, else selfhost/zen.zl via bootstrap
#   interpret | eval:
#     → zen-selfhost (native AST walk); fallback: bootstrap hosts selfhost/zen.zl
#   Language host (bare .zl, -g/--generate, --check, --test, --repl, …):
#     → bin/zen-bootstrap (Python bootstrap) — full fidelity
#     -g/--generate: try selfhost compile+link+run first, then bootstrap
#                    (ZEN_GENERATE=bootstrap skips the selfhost attempt)
#
# Overrides:
#   ZEN_FORCE_BOOTSTRAP=1   always use zen-bootstrap
#   ZEN_INTERPRET=selfhost  bare `zen file.zl` → selfhost interpret (no stdout builtins)
#   ZEN_GENERATE=bootstrap  skip selfhost -g attempt
#   ZEN_GENERATE=selfhost   same as default for -g (explicit)
#
# Bare scripts and --test stay on bootstrap: selfhost interpret has no real
# stdout and no zen.test runner (ENDGAME Phase D residual / E1c).

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"

BOOTSTRAP_BIN="$ROOT/bin/zen-bootstrap"
SELFHOST_BIN="$ROOT/bin/zen-selfhost"
BOOTSTRAP_PY="python3 $ROOT/bootstrap/Zen.py"

run_bootstrap() {
  if [ -x "$BOOTSTRAP_BIN" ]; then
    exec "$BOOTSTRAP_BIN" "$@"
  fi
  # shellcheck disable=SC2086
  exec $BOOTSTRAP_PY "$@"
}

run_selfhost_cli() {
  if [ -x "$SELFHOST_BIN" ]; then
    exec "$SELFHOST_BIN" "$@"
  fi
  # Fallback: interpret selfhost driver under bootstrap
  # shellcheck disable=SC2086
  exec $BOOTSTRAP_PY "$ROOT/selfhost/zen.zl" "$@"
}

# --- force bootstrap ---
if [ "${ZEN_FORCE_BOOTSTRAP:-0}" = "1" ]; then
  run_bootstrap "$@"
fi

# --- optional selfhost native -g path with bootstrap fallback ---
try_selfhost_generate() {
  # Args: -g|--generate then source then script args...
  gen_flag=$1
  shift
  src=$1
  shift || true
  if [ -z "$src" ] || [ ! -f "$src" ]; then
    return 1
  fi
  if [ ! -x "$SELFHOST_BIN" ]; then
    return 1
  fi
  work="$ROOT/output/handoff_generate"
  mkdir -p "$work" || return 1
  out_c="$work/out.c"
  prog="$work/prog"
  link="$work/link"
  rm -f "$out_c" "$prog"
  if ! "$SELFHOST_BIN" compile "$src" "$out_c" >/dev/null 2>&1; then
    return 1
  fi
  if [ ! -f "$out_c" ]; then
    return 1
  fi
  rm -rf "$link"
  mkdir -p "$link" || return 1
  # shellcheck disable=SC2086
  cp -a "$ROOT/runtime/." "$link/" 2>/dev/null || return 1
  cp -f "$out_c" "$link/out.c" || return 1
  if ! gcc "$link/out.c" "$link/bootstrap_runtime.c" \
      -o "$prog" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$link" -I "$link/core" -I "$link/collections" \
      -I "$link/io" -I "$link/memory" \
      -lm -lpthread >/dev/null 2>&1; then
    return 1
  fi
  exec "$prog" "$@"
}

run_zenpm() {
  # shellcheck disable=SC2086
  exec $BOOTSTRAP_PY "$ROOT/tools/zenpm.zl" "$@"
}

# First-arg dispatch
# Note: bootstrap uses --check; selfhost uses bare "check".
case "${1:-}" in
  init|new|watch|dash|dashboard|graph|clean|todo|doc|pkg|bump|publish|benchmark|bench|env)
    run_zenpm "$@"
    ;;
  build)
    case "${2:-}" in
      *.zl)
        run_selfhost_cli "$@"
        ;;
      *)
        run_zenpm "$@"
        ;;
    esac
    ;;
  run)
    case "${2:-}" in
      *.zl)
        run_selfhost_cli "$@"
        ;;
      *)
        run_zenpm "$@"
        ;;
    esac
    ;;
  compile|deps|help|interpret|eval|test)
    run_selfhost_cli "$@"
    ;;
  lsp)
    # Separate entry: do not link LSP into zen-selfhost.
    shift
    if [ -x "$BOOTSTRAP_BIN" ]; then
      exec "$BOOTSTRAP_BIN" "$ROOT/tools/zenlsp.zl" "$@"
    fi
    # shellcheck disable=SC2086
    exec $BOOTSTRAP_PY "$ROOT/tools/zenlsp.zl" "$@"
    ;;
  --test)
    shift
    run_selfhost_cli test "$@"
    ;;
  check)
    # selfhost: check <file.zl>
    # If user meant bootstrap, they use --check
    run_selfhost_cli "$@"
    ;;
  -g|--generate)
    # E1b: try selfhost generate first unless opted out.
    if [ "${ZEN_GENERATE:-selfhost}" != "bootstrap" ]; then
      if try_selfhost_generate "$@"; then
        :
      fi
      # fall through to bootstrap on failure
    fi
    run_bootstrap "$@"
    ;;
  *)
    # E1a soak flag: bare file.zl via selfhost interpret
    if [ "${ZEN_INTERPRET:-}" = "selfhost" ]; then
      case "${1:-}" in
        *.zl)
          run_selfhost_cli interpret "$@"
          ;;
      esac
    fi
    run_bootstrap "$@"
    ;;
esac
