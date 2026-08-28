#!/usr/bin/env bash
# E3 golden: bootstrap vs selfhost on a frozen program list.
# Modes per tests/self_hosting/fixtures/GOLDEN.txt: both | interpret | aot
# Requires bin/zen-selfhost (./scripts/zen install-selfhost).
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"

BOOTSTRAP="${ZEN_BOOTSTRAP:-python3 $ROOT/bootstrap/Zen.py}"
SELF="${ZEN_SELFHOST_BIN:-$ROOT/bin/zen-selfhost}"
LIST="${ZEN_GOLDEN_LIST:-$ROOT/tests/self_hosting/fixtures/GOLDEN.txt}"
WORKDIR="${ZEN_GOLDEN_WORKDIR:-$ROOT/output/golden}"
# Set ZEN_GOLDEN_AOT=0 to skip AOT pairs (interpret-only, faster).
DO_AOT="${ZEN_GOLDEN_AOT:-1}"

normalize() {
  sed -E \
    -e 's/\x1B\[[0-9;]*[A-Za-z]//g' \
    -e 's/Compiled successfully\. Running program://g' \
    -e 's/Running program://g' \
    -e '/^DEBUG:/d' \
    -e '/^DEBUG /d' \
    -e '/^!!! C COMPILE FAILED/d' \
    -e 's/ran .+ \(exit [0-9]+\)//g' \
    -e '/^wrote /d' \
    -e '/^built /d' \
    -e '/^run: build failed/d' \
    | tr -d '\r' \
    | sed -E 's/[[:space:]]+$//' \
    | awk 'NF'
}

pass=0
fail=0
skip=0

ok() { echo "  PASS: $*"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $*"; fail=$((fail + 1)); }
note() { echo "  SKIP: $*"; skip=$((skip + 1)); }

echo "=== E3 golden run-vs-bootstrap ==="
echo "ROOT=$ROOT"
echo "SELF=$SELF"
echo "LIST=$LIST"

if [[ ! -x "$SELF" ]]; then
  echo "missing $SELF — run: ./scripts/zen install-selfhost" >&2
  exit 1
fi
if [[ ! -f "$LIST" ]]; then
  echo "missing golden list $LIST" >&2
  exit 1
fi

mkdir -p "$WORKDIR"

compare_pair() {
  local label="$1"
  local file="$2"
  local left_cmd="$3"
  local right_cmd="$4"
  local left_out left_err right_out right_err left_n right_n

  left_out="$(mktemp)"
  right_out="$(mktemp)"
  left_err=0
  right_err=0

  set +e
  # shellcheck disable=SC2086
  eval "$left_cmd" >"$left_out" 2>&1
  left_err=$?
  # shellcheck disable=SC2086
  eval "$right_cmd" >"$right_out" 2>&1
  right_err=$?
  set -e

  if [[ "$left_err" -ne "$right_err" ]]; then
    bad "$label $file exit boot=$left_err self=$right_err"
    echo "    --- bootstrap ---"
    tail -n 20 "$left_out" | sed 's/^/    /'
    echo "    --- selfhost ---"
    tail -n 20 "$right_out" | sed 's/^/    /'
    rm -f "$left_out" "$right_out"
    return 0
  fi
  if [[ "$left_err" -ne 0 ]]; then
    bad "$label $file both exit $left_err (bootstrap must be 0)"
    tail -n 15 "$left_out" | sed 's/^/    /'
    rm -f "$left_out" "$right_out"
    return 0
  fi

  left_n="$(normalize <"$left_out")"
  right_n="$(normalize <"$right_out")"
  if [[ "$left_n" != "$right_n" ]]; then
    bad "$label $file stdout mismatch"
    echo "    --- bootstrap ---"
    printf '%s\n' "$left_n" | sed 's/^/    /'
    echo "    --- selfhost ---"
    printf '%s\n' "$right_n" | sed 's/^/    /'
    rm -f "$left_out" "$right_out"
    return 0
  fi

  ok "$label $file"
  rm -f "$left_out" "$right_out"
}

stem_of() {
  local b
  b="$(basename "$1")"
  echo "${b%.zl}"
}

while IFS= read -r raw || [[ -n "$raw" ]]; do
  line="${raw%%#*}"
  line="$(echo "$line" | sed -E 's/^[[:space:]]+//;s/[[:space:]]+$//')"
  [[ -z "$line" ]] && continue
  file="${line%%[[:space:]]*}"
  mode="$(echo "$line" | awk '{print $2}')"
  [[ -z "$mode" ]] && mode="both"
  if [[ ! -f "$file" ]]; then
    bad "missing file $file"
    continue
  fi

  echo "--- $file ($mode) ---"
  if [[ "$mode" == "both" || "$mode" == "interpret" ]]; then
    compare_pair "interpret" "$file" \
      "$BOOTSTRAP \"$file\"" \
      "\"$SELF\" interpret \"$file\""
  fi
  if [[ "$mode" == "both" || "$mode" == "aot" ]]; then
    if [[ "$DO_AOT" != "1" ]]; then
      note "aot $file (ZEN_GOLDEN_AOT=0)"
    else
      stem="$(stem_of "$file")"
      wdir="$WORKDIR/$stem"
      mkdir -p "$wdir"
      compare_pair "aot" "$file" \
        "$BOOTSTRAP -g \"$file\"" \
        "\"$SELF\" run \"$file\" --workdir \"$wdir\""
    fi
  fi
done < "$LIST"

echo
echo "Golden: $pass passed, $fail failed, $skip skipped"
if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
exit 0
