import os
import glob
import shutil

# 1. Create directories
dirs = [
    "lib/zen/collections",
    "lib/zen/math",
    "lib/zen/sys",
    "lib/zen/io",
    "lib/zen/text"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# 2. File Moves
moves = {
    "lib/zen/list.zl": "lib/zen/collections/list.zl",
    "lib/zen/math.zl": "lib/zen/math/math.zl",
    "lib/zen/random.zl": "lib/zen/math/random.zl",
    "lib/zen/range.zl": "lib/zen/math/range.zl",
    "lib/zen/sys.zl": "lib/zen/sys/sys.zl",
    "lib/zen/process.zl": "lib/zen/sys/process.zl",
    "lib/zen/term.zl": "lib/zen/sys/term.zl",
    "lib/zen/cli.zl": "lib/zen/sys/cli.zl",
    "lib/zen/io.zl": "lib/zen/io/io.zl",
    "lib/zen/file.zl": "lib/zen/io/file.zl",
    "lib/zen/path.zl": "lib/zen/io/path.zl",
    "lib/zen/string.zl": "lib/zen/text/string.zl",
    "lib/zen/text.zl": "lib/zen/text/text.zl"
}

for src, dst in moves.items():
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {src} -> {dst}")

# 3. Replacements
replacements = {
    "zen.list": "zen.collections.list",
    "zen.math": "zen.math.math",
    "zen.random": "zen.math.random",
    "zen.range": "zen.math.range",
    "zen.sys": "zen.sys.sys",
    "zen.process": "zen.sys.process",
    "zen.term": "zen.sys.term",
    "zen.cli": "zen.sys.cli",
    "zen.io": "zen.io.io",
    "zen.file": "zen.io.file",
    "zen.path": "zen.io.path",
    "zen.string": "zen.text.string",
    "zen.text": "zen.text.text",
    
    # Also fix some built-in strings if they exist, but generally import statements:
    # "import zen.math as math" becomes "import zen.math.math as math"
}

# Recursively replace in .zl and .md files
for ext in ["**/*.zl", "**/*.md"]:
    for filepath in glob.glob(ext, recursive=True):
        if not os.path.isfile(filepath): continue
        if "bootstrap/" in filepath: continue
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements.items():
            # Only replace if it is preceded by "import " or we could just safely replace it
            # To be safe, let's replace "import zen.math" with "import zen.math.math"
            new_content = new_content.replace(f"import {old} ", f"import {new} ")
            new_content = new_content.replace(f"import {old}\n", f"import {new}\n")
            
            # For docs referencing zen.math
            new_content = new_content.replace(f"`{old}`", f"`{new}`")
            new_content = new_content.replace(f"- {old}", f"- {new}")
            
        if content != new_content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filepath}")

