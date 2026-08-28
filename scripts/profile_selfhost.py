#!/usr/bin/env python3
import time
import subprocess
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN = os.path.join(ROOT, "bin", "zen-selfhost")
FIXTURE = os.path.join(ROOT, "tests", "self_hosting", "fixtures", "stage7_add.zl")
OUT_C = os.path.join(ROOT, "output", "bench_stage7.c")
OUT_EXE = os.path.join(ROOT, "output", "bench_stage7")
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib", ZEN_PROFILE="1")

def time_cmd(cmd, label):
    t0 = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
    dt = (time.perf_counter() - t0) * 1000.0
    status = "OK" if res.returncode == 0 else f"FAIL ({res.returncode})"
    print(f"[{label:35s}] {dt:8.2f} ms  ({status})")
    if res.returncode != 0:
        print(f"  stderr: {res.stderr[:400]}")
    combined = (res.stdout or "") + (res.stderr or "")
    for line in combined.splitlines():
        if line.startswith("profile "):
            print(f"    {line}")
    return dt

def main():
    print("=" * 60)
    print("  ZENLANG PERFORMANCE BENCHMARK: selfhost vs bootstrap")
    print(f"  Fixture: {os.path.relpath(FIXTURE, ROOT)}")
    print("=" * 60)

    # 1. Selfhost compile (Zen -> C)
    time_cmd([BIN, "compile", FIXTURE, OUT_C], "1. Selfhost Compile (Zen -> C)")

    # 2. Selfhost build (Zen -> C -> GCC -> Exe)
    time_cmd([BIN, "build", FIXTURE, OUT_EXE], "2. Selfhost Build (C + Link)")

    # 3. Compiled binary execution
    time_cmd([OUT_EXE], "3. Compiled Binary Exec")

    # 4. Selfhost interpret (AST Walk in Zen)
    time_cmd([BIN, "interpret", FIXTURE], "4. Selfhost Interpret (AST Walk)")

    # 5. Bootstrap interpret (AST Walk in Python)
    time_cmd(["python3", "bootstrap/Zen.py", FIXTURE], "5. Bootstrap Interpret (Python)")

    # 6. Bootstrap compile (Python -> C -> GCC)
    time_cmd(["python3", "bootstrap/Zen.py", "-g", FIXTURE], "6. Bootstrap Compile (-g)")

    print("=" * 60)

if __name__ == "__main__":
    main()
