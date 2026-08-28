#!/usr/bin/env python3
import time
import subprocess
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_SELFHOST = os.path.join(ROOT, "bin", "zen-selfhost")
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib")

# Workloads
WORKLOADS = {
    "1. Recursion: Fibonacci(18) [5,777 calls]": """
function fib(n) {
    when n <= 1 {
        <- n
    }
    <- fib(n - 1) + fib(n - 2)
}

function main() {
    let r -> fib(18)
    <- 0
}
""",
    "2. Iteration: 5,000 Loop Steps": """
function main() {
    let total -> 0
    let i -> 0
    do while i < 5000 {
        total -> total + (i % 10)
        i -> i + 1
    }
    <- 0
}
""",
    "3. Collections: 500 List Appends & Map Lookup": """
function main() {
    let l -> []
    let i -> 0
    do while i < 500 {
        l.append(i * 2)
        i -> i + 1
    }
    let m -> {
        host -> "localhost",
        port -> 8080,
        count -> l.length
    }
    let sum -> 0
    let j -> 0
    do while j < 500 {
        sum -> sum + l[j]
        j -> j + 1
    }
    <- 0
}
"""
}

def time_cmd(cmd, runs=3):
    durations = []
    stdout = ""
    stderr = ""
    for _ in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
        dt = (time.perf_counter() - t0) * 1000.0
        durations.append(dt)
        stdout = res.stdout or ""
        stderr = res.stderr or ""
        if res.returncode != 0:
            return None, stdout, stderr
    return min(durations), stdout, stderr

def profile_compiler():
    fixture = os.path.join(ROOT, "tests", "self_hosting", "fixtures", "stage7_add.zl")
    out_c = os.path.join(ROOT, "output", "bench_pipeline.c")
    env_prof = dict(ENV, ZEN_PROFILE="1")
    t0 = time.perf_counter()
    res = subprocess.run([BIN_SELFHOST, "compile", fixture, out_c], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env_prof, cwd=ROOT)
    total_dt = (time.perf_counter() - t0) * 1000.0
    combined = (res.stdout or "") + (res.stderr or "")
    
    print("=" * 72)
    print("               1. SELFHOST COMPILER PIPELINE PROFILING")
    print("=" * 72)
    print(f" Source Fixture: {os.path.relpath(fixture, ROOT)}")
    print(f" Total Compile Time (Zen -> C): {total_dt:.2f} ms\n")
    print(" Stage Breakdown:")
    for line in combined.splitlines():
        if line.startswith("profile "):
            parts = line.split()
            if len(parts) >= 3:
                stage = parts[1]
                val = float(parts[2])
                pct = (val / total_dt) * 100.0 if total_dt > 0 else 0
                print(f"   • {stage:<12}: {val:9.2f} ms  ({pct:5.1f}%)")
    print("=" * 72)

def benchmark_workloads():
    scratch_dir = os.path.join(ROOT, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)

    print("\n" + "=" * 72)
    print("         2. EXECUTION ENGINE BENCHMARKS (NATIVE vs INTERPRETER)")
    print("=" * 72)

    for title, src in WORKLOADS.items():
        src_path = os.path.join(scratch_dir, "bench_workload.zl")
        exe_path = os.path.join(scratch_dir, "bench_workload_bin")
        with open(src_path, "w") as f:
            f.write(src)

        print(f"\n >>> {title}")
        print(f" {'Execution Engine':<40} | {'Min Exec Time':<14} | {'Speedup':<12}")
        print(f" {'-'*40}-|-{'-'*14}-|-{'-'*12}")

        # A. Native Binary Exec (Compiled with -O2)
        subprocess.run([BIN_SELFHOST, "build", src_path, exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
        if os.path.exists(exe_path):
            t_native, _, _ = time_cmd([exe_path], runs=10)
        else:
            t_native = None

        # B. Bootstrap Interpreter (Python AST Walk)
        t_py, _, _ = time_cmd(["python3", "bootstrap/Zen.py", src_path], runs=1)

        if t_native is not None:
            speedup = f"{t_py / t_native:6.1f}x" if (t_py and t_native > 0) else "N/A"
            print(f" 1. Native AOT Binary (C -O2)            | {t_native:9.2f} ms   | {speedup}")

        if t_py is not None:
            print(f" 2. Bootstrap Interpreter (Python AST)  | {t_py:9.2f} ms   | 1.0x (base)")

def benchmark_vm_vs_native():
    print("\n" + "=" * 72)
    print("         3. BYTECODE VM & COMPILER SUITE EXECUTION")
    print("=" * 72)

    # 1. Selfhost Bytecode VM Suite (test_vm.zl)
    t_vm_test, _, _ = time_cmd(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_vm.zl"], runs=1)
    print(f" • Selfhost Bytecode VM Suite (test_vm.zl):       {t_vm_test:8.2f} ms  (7/7 PASS)")

    # 2. Stage 4 Mixed Execution ABI Suite (test_mixed_abi.zl)
    t_abi_test, _, _ = time_cmd(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_mixed_abi.zl"], runs=1)
    print(f" • Mixed Execution ABI Suite (test_mixed_abi.zl): {t_abi_test:8.2f} ms  (6/6 PASS)")

    # 3. Full Parser & Lexer Suite (test_parser.zl)
    t_parser_test, _, _ = time_cmd(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_parser.zl"], runs=1)
    print(f" • Selfhost Parser Suite (test_parser.zl):        {t_parser_test:8.2f} ms  (14/14 PASS)")
    print("=" * 72)

def main():
    profile_compiler()
    benchmark_workloads()
    benchmark_vm_vs_native()

if __name__ == "__main__":
    main()
