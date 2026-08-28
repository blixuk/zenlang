#!/usr/bin/env bash
# Multi-unit self-rebuild smoke (heavier than default selfhost-smoke).
# 1) bootstrap -g selfhost → bin/zen-selfhost (or use existing)
# 2) compile selfhost/zen.zl --multi → many .c
# 3) gcc all units + runtime → help + compile fixture
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"
BOOTSTRAP="${ZEN_BOOTSTRAP:-python3 $ROOT/bootstrap/Zen.py}"
BIN="${ZEN_SELFHOST_BIN:-$ROOT/bin/zen-selfhost}"
WORKDIR="${ZEN_MULTI_WORKDIR:-$ROOT/output/multi_selfhost_smoke}"

pass=0
fail=0
ok() { echo "  PASS: $*"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $*"; fail=$((fail + 1)); }

echo "=== Multi-unit selfhost smoke ==="
echo "ROOT=$ROOT WORKDIR=$WORKDIR"

mkdir -p "$ROOT/bin" "$WORKDIR"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

# --- driver ---
echo "--- ensure zen-selfhost ---"
# shellcheck disable=SC2086
if ! $BOOTSTRAP -g "$ROOT/selfhost/zen.zl" help >/dev/null; then
  bad "bootstrap -g selfhost"
  exit 1
fi
cp -f "$ROOT/output/build/zen_program" "$BIN"
chmod +x "$BIN"
ok "zen-selfhost"

# --- multi emit ---
echo "--- multi-unit compile selfhost/zen.zl ---"
OUT="$WORKDIR/units"
rm -rf "$OUT"
set +e
mout=$("$BIN" compile "$ROOT/selfhost/zen.zl" "$OUT" --multi 2>&1)
mcode=$?
set -e
if [[ "$mcode" -ne 0 ]] || [[ ! -f "$OUT/zen_host_main.c" ]]; then
  bad "multi emit"
  printf '%s\n' "$mout" | head -20
  exit 1
fi
n=$(find "$OUT" -name '*.c' | wc -l | tr -d ' ')
if [[ "$n" -lt 5 ]]; then
  bad "expected many C files, got $n"
  exit 1
fi
if ! grep -q 'extern ZenValue z_K_' "$OUT/Parser.c" 2>/dev/null; then
  bad "missing cross-unit global externs in Parser.c"
else
  ok "multi emit ($n C files, global externs)"
fi

# --- link ---
echo "--- gcc multi-unit ---"
LINK="$WORKDIR/link"
rm -rf "$LINK"
mkdir -p "$LINK"
cp -a "$ROOT/runtime/." "$LINK/"
cp -f "$OUT"/*.c "$LINK/"
# Build list of unit C files (not main_wrapper from runtime copy if any)
units=()
for f in "$LINK"/*.c; do
  base=$(basename "$f")
  case "$base" in
    bootstrap_runtime.c|main_wrapper.c) continue ;;
    *) units+=("$f") ;;
  esac
done
PROG="$WORKDIR/zen_multi"
set +e
gcc_out=$(gcc "${units[@]}" "$LINK/bootstrap_runtime.c" \
  -o "$PROG" -O2 \
  -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
  -I "$LINK" -I "$LINK/core" -I "$LINK/collections" \
  -I "$LINK/io" -I "$LINK/memory" \
  -lm -lpthread 2>&1)
gcc_code=$?
set -e
if [[ "$gcc_code" -ne 0 ]]; then
  bad "gcc multi-unit"
  printf '%s\n' "$gcc_out" | head -40
  exit 1
fi
ok "gcc multi-unit → $PROG"

# --- run ---
echo "--- multi binary help ---"
if out=$("$PROG" help 2>&1) && printf '%s\n' "$out" | grep -q 'Usage\|selfhost'; then
  ok "multi binary help"
else
  bad "multi binary help"
  printf '%s\n' "$out" | head -10
fi

echo "--- multi binary compile fixture ---"
FIX="$ROOT/tests/self_hosting/fixtures/stage7_add.zl"
FXC="$WORKDIR/stage7_from_multi.c"
if out=$("$PROG" compile "$FIX" "$FXC" 2>&1) && [[ -f "$FXC" ]] && grep -q 'zen_main' "$FXC"; then
  ok "multi binary compile fixture"
else
  bad "multi binary compile fixture"
  printf '%s\n' "$out" | head -15
fi

echo ""
if [[ "$fail" -eq 0 ]]; then
  echo "Multi-unit selfhost smoke: $pass passed, 0 failed"
  exit 0
fi
echo "Multi-unit selfhost smoke: $pass passed, $fail failed"
exit 1
