#!/usr/bin/env python3
import time
import subprocess
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_SELFHOST = os.path.join(ROOT, "bin", "zen-selfhost")
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib", ZEN_PROFILE="1")

# Workload 1: Recursion (Fibonacci 20 -> 21,891 recursive calls)
FIB_SRC = """
function fib(n) {
    when n <= 1 {
        <- n
    }
    <- fib(n - 1) + fib(n - 2)
}

function main() {
    let res -> fib(20)
    <- 0
}
"""

# Workload 2: Tight Iteration & Arithmetic (50,000 iterations)
LOOP_SRC = """
function main() {
    let total -> 0
    let i -> 0
    do while i < 50000 {
        total -> total + (i % 10)
        i -> i + 1
    }
    <- 0
}
"""

# Workload 3: Collections (1,000 list appends, indexing, map operations)
COLLECTIONS_SRC = """
function main() {
    let items -> []
    let i -> 0
    do while i < 1000 {
        items.append(i * 2)
        i -> i + 1
    }
    let config -> {
        host -> "localhost",
        port -> 8080,
        count -> items.length
    }
    let sum -> 0
    let j -> 0
    do while j < 1000 {
        sum -> sum + items[j]
        j -> j + 1
    }
    <- 0
}
"""

def run_cmd(cmd, runs=3):
    durations = []
    stdout = ""
    stderr = ""
    for r in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
        dt = (time.perf_counter() - t0) * 1000.0
        durations.append(dt)
        stdout = res.stdout or ""
        stderr = res.stderr or ""
        if res.returncode != 0:
            return None, stdout, stderr
    return min(durations), stdout, stderr

def run_workload_across_engines(name, source_code):
    scratch_dir = os.path.join(ROOT, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    src_file = os.path.join(scratch_dir, f"bench_{name}.zl")
    c_file = os.path.join(scratch_dir, f"bench_{name}.c")
    exe_file = os.path.join(scratch_dir, f"bench_{name}_bin")

    with open(src_file, "w") as f:
        f.write(source_code)

    print(f"\n======================================================================")
    print(f" WORKLOAD: {name.upper()}")
    print(f"======================================================================")

    # 1. Native Compiled Binary (AOT C -O2)
    # Compile
    t_compile, _, _ = run_cmd(["python3", "bootstrap/Zen.py", "-g", src_file], runs=1)
    default_exe = os.path.join(ROOT, "output", "build", "zen_program")
    if os.path.exists(default_exe):
        t_native, _, _ = run_cmd([default_exe], runs=10)
    else:
        t_native = None

    # 2. Selfhost Bytecode VM (via zen-selfhost vm)
    if os.path.exists(BIN_SELFHOST):
        t_vm_cli, _, _ = run_cmd([BIN_SELFHOST, "vm", src_file], runs=5)
    else:
        t_vm_cli = None

    # 3. Bootstrap Python Interpreter (AST Walk)
    t_py_interp, _, _ = run_cmd(["python3", "bootstrap/Zen.py", src_file], runs=3)

    # 4. Selfhost Interpreter (AST Walk in Zen)
    if os.path.exists(BIN_SELFHOST):
        t_sh_interp, _, _ = run_cmd([BIN_SELFHOST, "interpret", src_file], runs=3)
    else:
        t_sh_interp = None

    print(f" {'Execution Tier':<36} | {'Min Time (ms)':<15} | {'Speedup vs Py Interp':<20}")
    print(f" {'-'*36}-|-{'-'*15}-|-{'-'*20}")

    if t_native is not None:
        speedup = f"{t_py_interp / t_native:6.1f}x faster" if (t_py_interp and t_native > 0) else "-"
        print(f" 1. Native Compiled Binary (AOT -O2)   | {t_native:10.2f} ms     | {speedup}")

    if t_vm_cli is not None:
        speedup = f"{t_py_interp / t_vm_cli:6.1f}x faster" if (t_py_interp and t_vm_cli > 0) else "-"
        print(f" 2. Bytecode VM Direct (bin/zen-selfhost) | {t_vm_cli:10.2f} ms     | {speedup}")

    if t_sh_interp is not None:
        speedup = f"{t_py_interp / t_sh_interp:6.1f}x faster" if (t_py_interp and t_sh_interp > 0) else "-"
        print(f" 3. Selfhost Interpret (AST Walk)       | {t_sh_interp:10.2f} ms     | {speedup}")

    if t_py_interp is not None:
        print(f" 4. Bootstrap Interpreter (Python)      | {t_py_interp:10.2f} ms     | 1.0x (baseline)")

def profile_compiler_pipeline():
    fixture = os.path.join(ROOT, "tests", "self_hosting", "fixtures", "stage7_add.zl")
    out_c = os.path.join(ROOT, "output", "bench_pipeline.c")

    print(f"\n======================================================================")
    print(f" SELFHOST COMPILER PIPELINE PROFILING")
    print(f" Fixture: {os.path.relpath(fixture, ROOT)}")
    print(f"======================================================================")

    if not os.path.exists(BIN_SELFHOST):
        print("  [WARN] bin/zen-selfhost not found. Run ./scripts/zen install-selfhost first.")
        return

    t_comp, stdout, stderr = run_cmd([BIN_SELFHOST, "compile", fixture, out_c], runs=1)
    combined = stdout + stderr

    print(f" Full Compiler Pipeline (Zen -> C): {t_comp:.2f} ms\n")
    print(f" Stage Breakdown (via ZEN_PROFILE=1):")
    for line in combined.splitlines():
        if line.startswith("profile "):
            print(f"   • {line}")

def main():
    print("=" * 70)
    print("      ZENLANG MULTI-TIER PROFILING & BENCHMARK SUITE")
    print("      (Compiler Pipeline, Interpreters, Bytecode VM, Native AOT)")
    print("=" * 70)

    profile_compiler_pipeline()

    run_workload_across_engines("fibonacci_20", FIB_SRC)
    run_workload_across_engines("loop_50k", LOOP_SRC)
    run_workload_across_engines("collections_1k", COLLECTIONS_SRC)

    print("\n" + "=" * 70)
    print(" Benchmark completed successfully.")
    print("=" * 70)

if __name__ == "__main__":
    main()
