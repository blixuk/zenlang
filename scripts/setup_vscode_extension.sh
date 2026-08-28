#!/usr/bin/env bash
# Symlink editors/vscode into VS Code / Cursor / Antigravity extension dirs.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SRC="$ROOT/editors/vscode"
NAME="zenlang.zenlang-0.1.0"

if [[ ! -f "$SRC/package.json" ]]; then
  echo "missing $SRC/package.json" >&2
  exit 1
fi

# Validate JSON
python3 -c "import json; json.load(open('$SRC/package.json'))"
python3 -c "import json; json.load(open('$SRC/syntaxes/zen.tmLanguage.json'))"
python3 -c "import json; json.load(open('$SRC/snippets.json'))"

install_one() {
  local dest_root="$1"
  [[ -z "$dest_root" ]] && return 0
  mkdir -p "$dest_root"
  local dest="$dest_root/$NAME"
  # Remove stale short-name links that point at old checkouts
  if [[ -L "$dest_root/zenlang" ]]; then
    local old
    old="$(readlink "$dest_root/zenlang" || true)"
    if [[ "$old" != "$SRC" ]]; then
      echo "replacing stale $dest_root/zenlang -> $old"
      rm -f "$dest_root/zenlang"
      ln -sfn "$SRC" "$dest_root/zenlang"
    fi
  elif [[ ! -e "$dest_root/zenlang" ]]; then
    ln -sfn "$SRC" "$dest_root/zenlang"
  fi
  rm -rf "$dest"
  ln -sfn "$SRC" "$dest"
  echo "installed $dest"
}

install_one "${HOME}/.vscode/extensions"
install_one "${HOME}/.vscode-oss/extensions"
install_one "${HOME}/.cursor/extensions"
install_one "${HOME}/.antigravity/extensions"
install_one "${HOME}/.antigravity-ide/extensions"
# VSCodium / code-server common paths
install_one "${HOME}/.vscodium/extensions"
install_one "${HOME}/.local/share/code-server/extensions"

echo ""
echo "Reload the editor window (Developer: Reload Window)."
echo "Open a .zl file — status bar language should be 'Zenlang' / 'ZenLang'."
echo "If not: Ctrl+Shift+P → 'Change Language Mode' → Zenlang"
echo "Source: $SRC"
