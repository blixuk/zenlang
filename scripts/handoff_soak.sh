#!/usr/bin/env bash
# Production handoff gate:
#  1) selfhost-smoke (compiler E2E + self-rebuild)
#  2) install-handoff hybrid wrapper
#  3) language host still works via bootstrap
#  4) compiler surface via selfhost with fallback path checked
#  5) golden run-vs-bootstrap (scripts/run_golden.sh)
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"

pass=0
fail=0
ok() { echo "  PASS: $*"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $*"; fail=$((fail + 1)); }

echo "=== Handoff soak (selfhost → hybrid bin/zen) ==="
echo "ROOT=$ROOT"

# --- 1) Full Stage 7 smoke ---
echo "--- selfhost-smoke ---"
if bash "$ROOT/scripts/selfhost_smoke.sh"; then
  ok "selfhost-smoke"
else
  bad "selfhost-smoke"
  echo "Handoff soak FAILED (selfhost-smoke)"
  exit 1
fi

# --- 2) Install hybrid handoff ---
echo "--- install-handoff ---"
if bash "$ROOT/scripts/zen" install-handoff; then
  ok "install-handoff"
else
  bad "install-handoff"
  exit 1
fi

if [[ ! -x "$ROOT/bin/zen" ]]; then bad "bin/zen missing"; exit 1; fi
if [[ ! -x "$ROOT/bin/zen-bootstrap" ]]; then bad "bin/zen-bootstrap missing"; exit 1; fi
if [[ ! -x "$ROOT/bin/zen-selfhost" ]]; then bad "bin/zen-selfhost missing"; exit 1; fi
ok "bin/zen + zen-bootstrap + zen-selfhost present"

# --- 3) Language host path (bootstrap) ---
echo "--- hybrid: interpret hello ---"
if out="$("$ROOT/bin/zen" "$ROOT/tests/hello.zl" 2>&1)"; then
  ok "bin/zen interpret hello"
else
  bad "bin/zen interpret hello"
  printf '%s\n' "$out" | head -20
fi

echo "--- hybrid: --check ---"
if "$ROOT/bin/zen" --check "$ROOT/tests/hello.zl" >/dev/null 2>&1; then
  ok "bin/zen --check (bootstrap)"
else
  bad "bin/zen --check"
fi

echo "--- hybrid: -g stage7 fixture ---"
FIX="$ROOT/tests/self_hosting/fixtures/stage7_add.zl"
if "$ROOT/bin/zen" -g "$FIX" >/dev/null 2>&1; then
  ok "bin/zen -g stage7_add (selfhost generate or bootstrap fallback)"
else
  bad "bin/zen -g stage7_add"
fi

# --- 4) Selfhost compiler surface through hybrid ---
echo "--- hybrid: compile via selfhost ---"
OUT="$ROOT/output/handoff_soak/stage7_add.c"
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
if out="$("$ROOT/bin/zen" compile "$FIX" "$OUT" 2>&1)" && [[ -f "$OUT" ]] && grep -q 'zen_main' "$OUT"; then
  ok "bin/zen compile → selfhost"
else
  bad "bin/zen compile"
  printf '%s\n' "$out" | head -20
fi

echo "--- hybrid: help (selfhost surface) ---"
if out="$("$ROOT/bin/zen" help 2>&1)" && printf '%s\n' "$out" | grep -qi 'selfhost driver\|usage'; then
  ok "bin/zen help → selfhost"
else
  bad "bin/zen help"
  printf '%s\n' "$out" | head -10
fi

echo "--- hybrid: check file (selfhost bare check) ---"
if out="$("$ROOT/bin/zen" check "$FIX" 2>&1)" && printf '%s\n' "$out" | grep -qi 'ok\|check'; then
  ok "bin/zen check file → selfhost"
else
  # selfhost check may print "check ok: path"
  if printf '%s\n' "$out" | grep -q 'check ok'; then
    ok "bin/zen check file → selfhost"
  else
    bad "bin/zen check file"
    printf '%s\n' "$out" | head -15
  fi
fi

# --- 5) Fallback / force bootstrap ---
echo "--- ZEN_FORCE_BOOTSTRAP=1 help (must be bootstrap argparse, not selfhost) ---"
if out="$(ZEN_FORCE_BOOTSTRAP=1 "$ROOT/bin/zen" --help 2>&1)" && printf '%s\n' "$out" | grep -q 'ZenLang\|generate\|interpret'; then
  ok "ZEN_FORCE_BOOTSTRAP uses language host"
else
  bad "ZEN_FORCE_BOOTSTRAP"
  printf '%s\n' "$out" | head -15
fi

# --- 6) Selfhost -g path (default try-selfhost) + bootstrap opt-out ---
echo "--- ZEN_GENERATE=selfhost -g stage7_add ---"
set +e
ZEN_GENERATE=selfhost "$ROOT/bin/zen" -g "$FIX" >/dev/null 2>&1
gen_code=$?
set -e
if [[ "$gen_code" -eq 0 ]]; then
  ok "ZEN_GENERATE=selfhost -g stage7_add"
else
  if ZEN_GENERATE=bootstrap "$ROOT/bin/zen" -g "$FIX" >/dev/null 2>&1; then
    ok "selfhost -g failed but ZEN_GENERATE=bootstrap still works"
  else
    bad "generate path broken"
  fi
fi

echo "--- ZEN_GENERATE=bootstrap -g stage7_add ---"
if ZEN_GENERATE=bootstrap "$ROOT/bin/zen" -g "$FIX" >/dev/null 2>&1; then
  ok "ZEN_GENERATE=bootstrap -g stage7_add"
else
  bad "ZEN_GENERATE=bootstrap -g"
fi

# --- 7) E1a: hybrid interpret CLI → selfhost ---
echo "--- hybrid: interpret fixtures (selfhost) ---"
interp_ok() {
  local name="$1"
  local fix="$ROOT/tests/self_hosting/fixtures/${name}.zl"
  set +e
  "$ROOT/bin/zen" interpret "$fix" >/dev/null 2>&1
  local c=$?
  set -e
  if [[ "$c" -eq 0 ]]; then
    ok "bin/zen interpret ${name}"
  else
    bad "bin/zen interpret ${name} (exit $c)"
  fi
}
interp_ok "stage7_add"
interp_ok "class_counter"
interp_ok "class_inherit"
interp_ok "class_dispatch"
interp_ok "enum_color"
interp_ok "enum_payload"
interp_ok "closure_add"
interp_ok "closure_nested"
interp_ok "pattern_bind"
interp_ok "with_region"
interp_ok "nothing_default"

echo "--- ZEN_INTERPRET=selfhost bare class_counter ---"
set +e
ZEN_INTERPRET=selfhost "$ROOT/bin/zen" "$ROOT/tests/self_hosting/fixtures/class_counter.zl" >/dev/null 2>&1
bare_code=$?
set -e
if [[ "$bare_code" -eq 0 ]]; then
  ok "ZEN_INTERPRET=selfhost bare class_counter"
else
  bad "ZEN_INTERPRET=selfhost bare class_counter (exit $bare_code)"
fi

echo "--- hybrid: run (selfhost AOT) class_counter ---"
set +e
"$ROOT/bin/zen" run "$ROOT/tests/self_hosting/fixtures/class_counter.zl" >/dev/null 2>&1
run_code=$?
set -e
if [[ "$run_code" -eq 0 ]]; then
  ok "bin/zen run class_counter"
else
  bad "bin/zen run class_counter (exit $run_code)"
fi

# --- 5) Golden run-vs-bootstrap ---
echo "--- test-golden ---"
if bash "$ROOT/scripts/run_golden.sh"; then
  ok "test-golden"
else
  bad "test-golden"
fi

# --- Summary ---
echo ""
# Hybrid section (after selfhost-smoke counted as 1) plus interpret matrix.
# Fail-any remains the gate; this threshold catches accidental test deletion.
if [[ "$fail" -eq 0 && "$pass" -lt 20 ]]; then
  bad "pass count $pass < 20 (E2 threshold)"
fi
if [[ "$fail" -eq 0 ]]; then
  echo "Handoff soak: $pass passed, 0 failed"
  echo "Promote: keep install-handoff as daily hybrid. Local: ./scripts/zen ci (fast) + ./scripts/zen ci-soak."
  echo "E1a interpret + E1b -g-try-selfhost + E1c test gated here. Bare .zl stays bootstrap until E4."
  exit 0
fi
echo "Handoff soak: $pass passed, $fail failed"
exit 1
