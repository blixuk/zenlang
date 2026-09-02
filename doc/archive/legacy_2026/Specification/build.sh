#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 bootstrap/Zen.py tools/build_spec.zl
echo "Zenlang Specification built successfully: $ROOT/doc/Specification/Zenlang.pdf"