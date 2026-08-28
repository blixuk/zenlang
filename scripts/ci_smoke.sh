#!/usr/bin/env bash
# Minimal local smoke after clone / reorg.
# Keep this fast and dependency-light (Python3 + gcc/clang for -g).
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

echo "=== zen ci_smoke: install ==="
bash scripts/zen install

echo "=== zen ci_smoke: test-core ==="
bash scripts/zen test-core

echo "=== zen ci_smoke: test-parity ==="
bash scripts/zen test-parity

echo "=== zen ci_smoke: test-lib-native ==="
bash scripts/zen test-lib-native

echo "=== zen ci_smoke: PASSED ==="
