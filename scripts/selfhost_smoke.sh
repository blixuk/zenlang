#!/usr/bin/env bash
# Stage 7: selfhost driver E2E smoke.
# 1) Ensure native bin/zen-selfhost (bootstrap -g of selfhost/zen.zl)
# 2) Native driver compiles fixture → C
# 3) gcc + runtime → run; expect exit 0
# 4) Optional self-rebuild probe (documents limits; non-fatal by default)
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"
BOOTSTRAP="${ZEN_BOOTSTRAP:-python3 $ROOT/bootstrap/Zen.py}"
BIN="${ZEN_SELFHOST_BIN:-$ROOT/bin/zen-selfhost}"
FIXTURE="${ZEN_SELFHOST_FIXTURE:-$ROOT/tests/self_hosting/fixtures/stage7_add.zl}"
WORKDIR="${ZEN_SELFHOST_WORKDIR:-$ROOT/output/selfhost_smoke}"
SELF_REBUILD="${ZEN_SELFHOST_REBUILD:-0}"

pass=0
fail=0

ok() { echo "  PASS: $*"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $*"; fail=$((fail + 1)); }

echo "=== Stage 7 selfhost smoke ==="
echo "ROOT=$ROOT"
echo "BIN=$BIN"
echo "FIXTURE=$FIXTURE"

mkdir -p "$ROOT/bin" "$WORKDIR"

# --- 1) Native driver binary ---
# Reuse bin/zen-selfhost when present (soak/install already built it).
# Force: ZEN_SMOKE_REBUILD=1.
echo "--- build native driver ---"
mkdir -p "$WORKDIR"
if [[ -x "$BIN" && "${ZEN_SMOKE_REBUILD:-0}" != "1" ]]; then
  ok "using existing $BIN (ZEN_SMOKE_REBUILD=1 to rebuild)"
else
boot_log="$WORKDIR/bootstrap_g.log"
# shellcheck disable=SC2086
set +e
$BOOTSTRAP -g "$ROOT/selfhost/zen.zl" help >"$boot_log" 2>&1
boot_code=$?
set -e
if [[ ! -x "$ROOT/output/build/zen_program" ]]; then
  bad "bootstrap -g selfhost/zen.zl (no zen_program, exit $boot_code)"
  tail -n 40 "$boot_log" || true
  echo "Stage 7 smoke FAILED (driver build)"
  exit 1
fi
if [[ "$boot_code" -ne 0 ]]; then
  echo "  note: bootstrap -g help exit $boot_code (binary present; continuing)"
fi
cp -f "$ROOT/output/build/zen_program" "$BIN"
chmod +x "$BIN"
ok "installed $BIN"
fi

# --- 2) CLI help ---
echo "--- native help ---"
if out="$("$BIN" help 2>&1)" && printf '%s\n' "$out" | grep -qi 'Usage'; then
  ok "native help"
else
  bad "native help"
  printf '%s\n' "$out"
fi

# --- 2b) Native interpret immediately (before compile/run can clobber outputs) ---
echo "--- native interpret fixtures ---"
interp_exit0() {
  local name="$1"
  local src="$ROOT/tests/self_hosting/fixtures/${name}.zl"
  local c
  set +e
  "$BIN" interpret "$src" >/dev/null 2>&1
  c=$?
  set -e
  if [[ "$c" -eq 0 ]]; then
    ok "interpret ${name} exit 0"
  else
    bad "interpret ${name} exit $c"
  fi
}
interp_exit0 "stage7_add"
interp_exit0 "class_counter"
interp_exit0 "enum_payload"
interp_exit0 "closure_nested"
interp_exit0 "pattern_bind"
interp_exit0 "with_region"
interp_exit0 "nothing_default"

# --- 3) Compile fixture with native driver ---
echo "--- native compile fixture ---"
OUT_C="$WORKDIR/stage7_add.c"
rm -f "$OUT_C"
if out="$("$BIN" compile "$FIXTURE" "$OUT_C" --typecheck 2>&1)" && [[ -f "$OUT_C" ]]; then
  if grep -q 'zen_main' "$OUT_C" && grep -q 'ZenValue_add' "$OUT_C"; then
    ok "native compile → $OUT_C"
  else
    bad "C missing zen_main/ZenValue_add"
    head -40 "$OUT_C" || true
  fi
else
  bad "native compile fixture"
  printf '%s\n' "$out"
fi

# --- 4) gcc + runtime link + run ---
echo "--- gcc + runtime ---"
if [[ -f "$OUT_C" ]]; then
  LINKDIR="$WORKDIR/link"
  rm -rf "$LINKDIR"
  mkdir -p "$LINKDIR"
  # Mirror bootstrap/Transpiler/CCompile.py whitelist
  cp -a "$ROOT/runtime/." "$LINKDIR/"
  cp -f "$OUT_C" "$LINKDIR/out.c"
  PROG="$WORKDIR/stage7_add"
  set +e
  gcc_out=$(gcc "$LINKDIR/out.c" "$LINKDIR/bootstrap_runtime.c" \
    -o "$PROG" -O2 \
    -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
    -I "$LINKDIR" -I "$LINKDIR/core" -I "$LINKDIR/collections" \
    -I "$LINKDIR/io" -I "$LINKDIR/memory" \
    -lm -lpthread 2>&1)
  gcc_code=$?
  set -e
  if [[ "$gcc_code" -ne 0 ]]; then
    bad "gcc link"
    printf '%s\n' "$gcc_out"
  else
    ok "gcc link → $PROG"
    set +e
    "$PROG"
    run_code=$?
    set -e
    if [[ "$run_code" -eq 0 ]]; then
      ok "run exit 0 (add(2,3)==5)"
    else
      bad "run exit $run_code (expected 0)"
    fi
  fi
else
  bad "skip link (no C)"
fi

# --- 4b) Selfhost-owned build/run (CLink; no bootstrap -g for the fixture) ---
echo "--- native selfhost run (build+link+exec) ---"
set +e
run_out=$("$BIN" run "$FIXTURE" 2>&1)
run_code=$?
set -e
if [[ "$run_code" -eq 0 ]] && printf '%s\n' "$run_out" | grep -q 'exit 0\|ran '; then
  ok "selfhost run stage7_add (CLink)"
else
  # message may be empty if program prints nothing; accept exit 0
  if [[ "$run_code" -eq 0 ]]; then
    ok "selfhost run stage7_add (CLink)"
  else
    bad "selfhost run stage7_add"
    printf '%s\n' "$run_out" | head -20
  fi
fi

# --- 5) Interpret path still works for same fixture ---
echo "--- interpret driver compile (parity host) ---"
OUT_C2="$WORKDIR/stage7_add_interp.c"
# shellcheck disable=SC2086
if out="$($BOOTSTRAP "$ROOT/selfhost/zen.zl" compile "$FIXTURE" "$OUT_C2" 2>&1)" && [[ -f "$OUT_C2" ]]; then
  ok "interpret host compile fixture"
else
  bad "interpret host compile"
  printf '%s\n' "$out"
fi

# --- 5b) Stage 5.x for-sum fixture (list + for-in) via native driver ---
echo "--- native compile + run stage5_for_sum ---"
FIX_SUM="$ROOT/tests/self_hosting/fixtures/stage5_for_sum.zl"
OUT_SUM_C="$WORKDIR/stage5_for_sum.c"
rm -f "$OUT_SUM_C"
if out="$("$BIN" compile "$FIX_SUM" "$OUT_SUM_C" 2>&1)" && [[ -f "$OUT_SUM_C" ]]; then
  if grep -qE 'ZenList_get_value_at_index|items\[' "$OUT_SUM_C"; then
    ok "native compile stage5_for_sum"
    LINKDIR2="$WORKDIR/link_sum"
    rm -rf "$LINKDIR2"
    mkdir -p "$LINKDIR2"
    cp -a "$ROOT/runtime/." "$LINKDIR2/"
    cp -f "$OUT_SUM_C" "$LINKDIR2/out.c"
    PROG_SUM="$WORKDIR/stage5_for_sum"
    set +e
    gcc_out=$(gcc "$LINKDIR2/out.c" "$LINKDIR2/bootstrap_runtime.c" \
      -o "$PROG_SUM" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR2" -I "$LINKDIR2/core" -I "$LINKDIR2/collections" \
      -I "$LINKDIR2/io" -I "$LINKDIR2/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc stage5_for_sum"
      printf '%s\n' "$gcc_out"
    else
      ok "gcc stage5_for_sum"
      set +e
      "$PROG_SUM"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run stage5_for_sum exit 0 (sum 1..4==10)"
      else
        bad "run stage5_for_sum exit $run_code"
      fi
    fi
  else
    bad "stage5_for_sum C missing for-in"
  fi
else
  bad "native compile stage5_for_sum"
  printf '%s\n' "$out"
fi

# --- 5c) Multi-file merge fixture ---
echo "--- native compile multi_main (dep merge) ---"
FIX_MULTI="$ROOT/tests/self_hosting/fixtures/multi_main.zl"
OUT_MULTI_C="$WORKDIR/multi_main.c"
rm -f "$OUT_MULTI_C"
if out="$("$BIN" compile "$FIX_MULTI" "$OUT_MULTI_C" 2>&1)" && [[ -f "$OUT_MULTI_C" ]]; then
  if grep -q 'z_multi_lib_val' "$OUT_MULTI_C" && grep -q 'zen_main' "$OUT_MULTI_C"; then
    ok "native multi-file merge emits lib+main"
    LINKDIR3="$WORKDIR/link_multi"
    rm -rf "$LINKDIR3"
    mkdir -p "$LINKDIR3"
    cp -a "$ROOT/runtime/." "$LINKDIR3/"
    cp -f "$OUT_MULTI_C" "$LINKDIR3/out.c"
    PROG_MULTI="$WORKDIR/multi_main"
    set +e
    gcc_out=$(gcc "$LINKDIR3/out.c" "$LINKDIR3/bootstrap_runtime.c" \
      -o "$PROG_MULTI" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR3" -I "$LINKDIR3/core" -I "$LINKDIR3/collections" \
      -I "$LINKDIR3/io" -I "$LINKDIR3/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc multi_main"
      printf '%s\n' "$gcc_out"
    else
      ok "gcc multi_main"
      set +e
      "$PROG_MULTI"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run multi_main exit 0 (3+4==7)"
      else
        bad "run multi_main exit $run_code"
      fi
    fi
  else
    bad "multi_main C missing merged symbols"
    head -40 "$OUT_MULTI_C" || true
  fi
else
  bad "native compile multi_main"
  printf '%s\n' "$out"
fi

# --- 5e) Class MVP: map-backed Type_method ---
echo "--- native compile + run class_counter ---"
FIX_CLS="$ROOT/tests/self_hosting/fixtures/class_counter.zl"
OUT_CLS_C="$WORKDIR/class_counter.c"
rm -f "$OUT_CLS_C"
if out="$("$BIN" compile "$FIX_CLS" "$OUT_CLS_C" 2>&1)" && [[ -f "$OUT_CLS_C" ]]; then
  if grep -q 'z_Counter_new' "$OUT_CLS_C" && grep -q 'z_Counter_inc' "$OUT_CLS_C"; then
    ok "native compile class_counter"
    LINKDIR_CLS="$WORKDIR/link_class"
    rm -rf "$LINKDIR_CLS"
    mkdir -p "$LINKDIR_CLS"
    cp -a "$ROOT/runtime/." "$LINKDIR_CLS/"
    cp -f "$OUT_CLS_C" "$LINKDIR_CLS/out.c"
    PROG_CLS="$WORKDIR/class_counter"
    set +e
    gcc_out=$(gcc "$LINKDIR_CLS/out.c" "$LINKDIR_CLS/bootstrap_runtime.c" \
      -o "$PROG_CLS" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR_CLS" -I "$LINKDIR_CLS/core" -I "$LINKDIR_CLS/collections" \
      -I "$LINKDIR_CLS/io" -I "$LINKDIR_CLS/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc class_counter"
      printf '%s\n' "$gcc_out" | head -30
    else
      ok "gcc class_counter"
      set +e
      "$PROG_CLS"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run class_counter exit 0 (inc twice == 2)"
      else
        bad "run class_counter exit $run_code"
      fi
    fi
  else
    bad "class_counter C missing Counter_new/inc"
    head -40 "$OUT_CLS_C" || true
  fi
else
  bad "native compile class_counter"
  printf '%s\n' "$out"
fi

# --- 5f) Class inheritance MVP ---
echo "--- native compile + run class_inherit ---"
FIX_INH="$ROOT/tests/self_hosting/fixtures/class_inherit.zl"
OUT_INH_C="$WORKDIR/class_inherit.c"
rm -f "$OUT_INH_C"
if out="$("$BIN" compile "$FIX_INH" "$OUT_INH_C" 2>&1)" && [[ -f "$OUT_INH_C" ]]; then
  if grep -q 'z_Dog_new' "$OUT_INH_C" && grep -q 'z_Animal_init' "$OUT_INH_C" && grep -q 'z_Dog_speak' "$OUT_INH_C"; then
    ok "native compile class_inherit"
    LINKDIR_INH="$WORKDIR/link_inherit"
    rm -rf "$LINKDIR_INH"
    mkdir -p "$LINKDIR_INH"
    cp -a "$ROOT/runtime/." "$LINKDIR_INH/"
    cp -f "$OUT_INH_C" "$LINKDIR_INH/out.c"
    PROG_INH="$WORKDIR/class_inherit"
    set +e
    gcc_out=$(gcc "$LINKDIR_INH/out.c" "$LINKDIR_INH/bootstrap_runtime.c" \
      -o "$PROG_INH" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR_INH" -I "$LINKDIR_INH/core" -I "$LINKDIR_INH/collections" \
      -I "$LINKDIR_INH/io" -I "$LINKDIR_INH/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc class_inherit"
      printf '%s\n' "$gcc_out" | head -30
    else
      ok "gcc class_inherit"
      set +e
      "$PROG_INH"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run class_inherit exit 0 (override+parent+fields)"
      else
        bad "run class_inherit exit $run_code"
      fi
    fi
  else
    bad "class_inherit C missing Dog/Animal symbols"
    head -40 "$OUT_INH_C" || true
  fi
else
  bad "native compile class_inherit"
  printf '%s\n' "$out"
fi

# --- 5g) Enum / closure / with-region fixtures (selfhost run exit 0) ---
run_fixture_exit0() {
  local name="$1"
  local fix="$ROOT/tests/self_hosting/fixtures/${name}.zl"
  echo "--- native compile + run ${name} ---"
  local out_c="$WORKDIR/${name}.c"
  rm -f "$out_c"
  if out="$("$BIN" compile "$fix" "$out_c" 2>&1)" && [[ -f "$out_c" ]]; then
    ok "native compile ${name}"
    local linkdir="$WORKDIR/link_${name}"
    rm -rf "$linkdir"
    mkdir -p "$linkdir"
    cp -a "$ROOT/runtime/." "$linkdir/"
    cp -f "$out_c" "$linkdir/out.c"
    local prog="$WORKDIR/${name}"
    set +e
    gcc_out=$(gcc "$linkdir/out.c" "$linkdir/bootstrap_runtime.c" \
      -o "$prog" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$linkdir" -I "$linkdir/core" -I "$linkdir/collections" \
      -I "$linkdir/io" -I "$linkdir/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc ${name}"
      printf '%s\n' "$gcc_out" | head -30
    else
      ok "gcc ${name}"
      set +e
      "$prog"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run ${name} exit 0"
      else
        bad "run ${name} exit $run_code"
      fi
    fi
  else
    bad "native compile ${name}"
    printf '%s\n' "$out"
  fi
}
run_fixture_exit0 "enum_color"
run_fixture_exit0 "closure_add"
run_fixture_exit0 "with_region"
run_fixture_exit0 "pattern_bind"
run_fixture_exit0 "enum_payload"
run_fixture_exit0 "class_dispatch"
run_fixture_exit0 "closure_nested"

# --- 5d) Multi-unit C (one TU per module + host main) ---
echo "--- native compile multi_main --multi (per-unit C + link) ---"
OUT_MULTI_DIR="$WORKDIR/multi_unit"
rm -rf "$OUT_MULTI_DIR"
if out="$("$BIN" compile "$FIX_MULTI" "$OUT_MULTI_DIR" --multi 2>&1)" \
  && [[ -f "$OUT_MULTI_DIR/zen_host_main.c" ]] \
  && [[ -f "$OUT_MULTI_DIR/multi_lib.c" ]] \
  && [[ -f "$OUT_MULTI_DIR/multi_main.c" ]]; then
  if grep -q 'zen_mod_init_' "$OUT_MULTI_DIR/zen_host_main.c" \
    && grep -q 'z_multi_lib_val' "$OUT_MULTI_DIR/multi_lib.c"; then
    ok "native multi-unit emit (lib+main+host)"
    LINKDIR4="$WORKDIR/link_multi_unit"
    rm -rf "$LINKDIR4"
    mkdir -p "$LINKDIR4"
    cp -a "$ROOT/runtime/." "$LINKDIR4/"
    cp -f "$OUT_MULTI_DIR"/*.c "$LINKDIR4/"
    PROG_MU="$WORKDIR/multi_unit_prog"
    set +e
    gcc_out=$(gcc "$LINKDIR4/multi_lib.c" "$LINKDIR4/multi_main.c" "$LINKDIR4/zen_host_main.c" \
      "$LINKDIR4/bootstrap_runtime.c" \
      -o "$PROG_MU" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR4" -I "$LINKDIR4/core" -I "$LINKDIR4/collections" \
      -I "$LINKDIR4/io" -I "$LINKDIR4/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc multi-unit"
      printf '%s\n' "$gcc_out" | head -30
    else
      ok "gcc multi-unit"
      set +e
      "$PROG_MU"
      run_code=$?
      set -e
      if [[ "$run_code" -eq 0 ]]; then
        ok "run multi-unit exit 0 (3+4==7)"
      else
        bad "run multi-unit exit $run_code"
      fi
    fi
  else
    bad "multi-unit C missing init/lib symbols"
  fi
else
  bad "native compile multi_main --multi"
  printf '%s\n' "$out"
fi

# --- 6) Self-rebuild: zen-selfhost compiles selfhost/zen.zl → C → gcc → run help ---
# Default off: the driver graph (Interpreter+Codegen) is too heavy for every smoke.
# Opt in: ZEN_SELFHOST_REBUILD=1 (also covered by multi-selfhost-smoke).
if [[ "${SELF_REBUILD}" != "1" ]]; then
  echo "--- self-rebuild skipped (set ZEN_SELFHOST_REBUILD=1 to run) ---"
else
echo "--- self-rebuild emit + gcc + help ---"
OUT_SELF="$WORKDIR/selfhost_zen.c"
PROG_SELF="$WORKDIR/zen_from_self"
rm -f "$OUT_SELF" "$PROG_SELF"
set +e
rebuild_out="$("$BIN" compile "$ROOT/selfhost/zen.zl" "$OUT_SELF" 2>&1)"
rebuild_code=$?
set -e
if [[ "$rebuild_code" -eq 0 && -f "$OUT_SELF" ]] && grep -q 'zen_main' "$OUT_SELF" && grep -q 'zen_module_init' "$OUT_SELF"; then
  bytes=$(wc -c < "$OUT_SELF" | tr -d ' ')
  if [[ "$bytes" -gt 100000 ]]; then
    ok "self-rebuild emit C ($bytes bytes, globals+init)"
    LINKDIR_S="$WORKDIR/link_self"
    rm -rf "$LINKDIR_S"
    mkdir -p "$LINKDIR_S"
    cp -a "$ROOT/runtime/." "$LINKDIR_S/"
    cp -f "$OUT_SELF" "$LINKDIR_S/out.c"
    set +e
    gcc_out=$(gcc "$LINKDIR_S/out.c" "$LINKDIR_S/bootstrap_runtime.c" \
      -o "$PROG_SELF" -O2 \
      -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
      -I "$LINKDIR_S" -I "$LINKDIR_S/core" -I "$LINKDIR_S/collections" \
      -I "$LINKDIR_S/io" -I "$LINKDIR_S/memory" \
      -lm -lpthread 2>&1)
    gcc_code=$?
    set -e
    if [[ "$gcc_code" -ne 0 ]]; then
      bad "gcc self-rebuild unit"
      printf '%s\n' "$gcc_out" | head -30
    else
      ok "gcc self-rebuild unit"
      set +e
      help_out=$("$PROG_SELF" help 2>&1)
      help_code=$?
      set -e
      if [[ "$help_code" -eq 0 ]] && echo "$help_out" | grep -q 'selfhost driver'; then
        ok "self-rebuild binary help"
      else
        bad "self-rebuild binary help (exit $help_code)"
        printf '%s\n' "$help_out" | head -15
      fi
      # Fixture compile + run via self-built binary (true self-host loop)
      set +e
      fix_out=$("$PROG_SELF" compile "$FIXTURE" "$WORKDIR/from_self_fixture.c" 2>&1)
      fix_code=$?
      set -e
      if [[ "$fix_code" -eq 0 && -f "$WORKDIR/from_self_fixture.c" ]] && grep -q 'zen_main' "$WORKDIR/from_self_fixture.c"; then
        ok "self-rebuild compile fixture"
        LINKDIR_F="$WORKDIR/link_from_self"
        rm -rf "$LINKDIR_F"
        mkdir -p "$LINKDIR_F"
        cp -a "$ROOT/runtime/." "$LINKDIR_F/"
        cp -f "$WORKDIR/from_self_fixture.c" "$LINKDIR_F/out.c"
        PROG_F="$WORKDIR/fixture_from_self"
        set +e
        gcc_f=$(gcc "$LINKDIR_F/out.c" "$LINKDIR_F/bootstrap_runtime.c" \
          -o "$PROG_F" -O2 \
          -Wno-unused-variable -Wno-unused-value -Wno-unused-label -Wno-unused-function \
          -I "$LINKDIR_F" -I "$LINKDIR_F/core" -I "$LINKDIR_F/collections" \
          -I "$LINKDIR_F/io" -I "$LINKDIR_F/memory" \
          -lm -lpthread 2>&1)
        gcc_fc=$?
        set -e
        if [[ "$gcc_fc" -ne 0 ]]; then
          bad "gcc fixture from self-built"
          printf '%s\n' "$gcc_f" | head -20
        else
          ok "gcc fixture from self-built"
          set +e
          "$PROG_F"
          run_fc=$?
          set -e
          if [[ "$run_fc" -eq 0 ]]; then
            ok "run fixture from self-built (add(2,3)==5)"
          else
            bad "run fixture from self-built exit $run_fc"
          fi
        fi
      else
        bad "self-rebuild compile fixture"
        printf '%s\n' "$fix_out" | head -15
      fi
    fi
  else
    bad "self-rebuild C too small ($bytes bytes)"
  fi
else
  bad "self-rebuild emit C"
  printf '%s\n' "$rebuild_out" | head -30
fi
fi

echo ""
echo "Stage 7 smoke: $pass passed, $fail failed"
if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
exit 0
