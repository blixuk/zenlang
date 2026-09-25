#!/usr/bin/env python3
"""
Test suite verifying that forbidden types and single-letter collection abbreviations
are strictly rejected at compile-time across both bin/zen (selfhost) and bootstrap.
"""

import subprocess
import tempfile
import sys

FORBIDDEN_TYPES = [
    "Int", "Int64", "Int32", "Int16", "Int8",
    "UInt8", "UInt16", "UInt32", "UInt64",
    "Float", "Float64", "Float32", "Double",
    "Str", "Bool", "Char", "Character", "Glyph", "Buffer",
    "V", "L", "S", "T", "M",
]

def check_rejection(source: str, expected_snippet: str, desc: str):
    with tempfile.NamedTemporaryFile("w", suffix=".zl", delete=False) as f:
        f.write(source)
        f.flush()
        
        # Test selfhost VM
        p_selfhost = subprocess.run(["bin/zen", f.name], capture_output=True, text=True)
        assert p_selfhost.returncode != 0, f"Expected bin/zen to reject {desc}, but it succeeded!"
        err_out = (p_selfhost.stderr or p_selfhost.stdout)
        assert expected_snippet in err_out, f"Expected '{expected_snippet}' in bin/zen error for {desc}, got: {err_out}"
        
        # Test Python bootstrap
        p_bootstrap = subprocess.run(["python3", "bootstrap/Zen.py", f.name], capture_output=True, text=True)
        assert p_bootstrap.returncode != 0, f"Expected bootstrap to reject {desc}, but it succeeded!"

def main():
    print("Testing compile-time rejection of forbidden types...")
    for t in FORBIDDEN_TYPES:
        check_rejection(
            f"let x : {t} -> 10\n",
            f"Type '{t}' is not supported in Zenlang",
            f"type annotation let x : {t}"
        )
        check_rejection(
            f"let x -> 10 <: {t}\n",
            f"Type '{t}' is not supported in Zenlang",
            f"type cast <: {t}"
        )
    
    # Test single-letter collection literals
    for letter in ["V", "L", "S", "T", "M"]:
        with tempfile.NamedTemporaryFile("w", suffix=".zl", delete=False) as f:
            f.write(f"let x -> {letter}{{1, 2}}\n")
            f.flush()
            p = subprocess.run(["bin/zen", f.name], capture_output=True, text=True)
            assert p.returncode != 0, f"Expected bin/zen to reject {letter}{{...}}, but it succeeded!"
            
            p_boot = subprocess.run(["python3", "bootstrap/Zen.py", f.name], capture_output=True, text=True)
            assert p_boot.returncode != 0, f"Expected bootstrap to reject {letter}{{...}}, but it succeeded!"

    print("PASS: All forbidden types and abbreviations were rejected as expected.")

if __name__ == "__main__":
    main()
