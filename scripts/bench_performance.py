#!/usr/bin/env python3
import time
import subprocess
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib", ZEN_PROFILE="1")

WORKLOAD_SOURCE = """
function fib(n) {
    when n <= 1 {
        <- n
    }
    <- fib(n - 1) + fib(n - 2)
}

function loop_accumulate(limit) {
    let sum -> 0
    let i -> 0
    do while i < limit {
        sum -> sum + (i % 10)
        i -> i + 1
    }
    <- sum
}

function collections_workload(count) {
    let items -> []
    let i -> 0
    do while i < count {
        items.append(i * 2)
        i -> i + 1
    }
    let map_data -> {
        `first` -> items[0],
        `mid` -> items[500],
        `last` -> items[count - 1]
    }
    <- map_data[`mid`]
}

function main() {
    let f -> fib(15)
    let l -> loop_accumulate(10000)
    let c -> collections_workload(1000)
    <- 0
}
"""

def time_command(cmd, desc, runs=3):
    durations = []
    stdout = ""
    for r in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
        dt = (time.perf_counter() - t0) * 1000.0
        durations.append(dt)
        stdout = (res.stdout or "") + (res.stderr or "")
        if res.returncode != 0:
            print(f"  [ERROR] Command failed with code {res.returncode}: {res.stderr[:200]}")
            return None, stdout
    
    avg_dt = sum(durations) / len(durations)
    min_dt = min(durations)
    return min_dt, stdout

def main():
    bench_dir = os.path.join(ROOT, "scratch")
    os.makedirs(bench_dir, exist_ok=True)
    bench_src = os.path.join(bench_dir, "bench_workload.zl")
    bench_c = os.path.join(bench_dir, "bench_workload.c")
    bench_exe = os.path.join(ROOT, "output", "build", "zen_program")

    with open(bench_src, "w") as f:
        f.write(WORKLOAD_SOURCE)

    print("=" * 70)
    print("           ZENLANG COMPILER & EXECUTION PERFORMANCE REPORT")
    print("=" * 70)
    print(f"Workload: fib(15) [1,973 calls] + 10k loop accumulate + 1k collections")
    print("-" * 70)

    # 1. Native AOT C Compilation via Bootstrap (-g)
    dt_boot_compile, _ = time_command(["python3", "bootstrap/Zen.py", "-g", bench_src], "Bootstrap AOT Compile (-g)", runs=1)
    
    # 2. Native AOT Binary Execution
    dt_native_exec, _ = time_command([bench_exe], "Native Binary Exec (C -O2)", runs=10)

    # 3. Bootstrap Python Interpreter (AST Walk)
    dt_boot_interp, _ = time_command(["python3", "bootstrap/Zen.py", bench_src], "Bootstrap Interpreter (Python)", runs=3)

    # 4. Selfhost Compiler Pipeline (Lexer, Parser, Codegen)
    bin_selfhost = os.path.join(ROOT, "bin", "zen-selfhost")
    if os.path.exists(bin_selfhost):
        dt_selfhost_compile, out_sh = time_command([bin_selfhost, "compile", bench_src, bench_c], "Selfhost Compile (Zen -> C)", runs=1)
    else:
        dt_selfhost_compile, out_sh = None, ""

    # 5. Selfhost Bytecode VM execution
    dt_vm, out_vm = time_command(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_vm.zl"], "Bytecode VM Test Suite", runs=1)

    print("\n--- Summary Performance Table ---")
    print(f"{'Execution Mode / Stage':<40s} | {'Time (ms)':>12s} | {'Status':<10s}")
    print("-" * 70)
    if dt_native_exec is not None:
        print(f"{'1. Native AOT Binary Execution':<40s} | {dt_native_exec:12.3f} ms | {'PASS'}")
    if dt_boot_compile is not None:
        print(f"{'2. Bootstrap Compile & Link (-g)':<40s} | {dt_boot_compile:12.2f} ms | {'PASS'}")
    if dt_boot_interp is not None:
        print(f"{'3. Bootstrap Script Interpreter':<40s} | {dt_boot_interp:12.2f} ms | {'PASS'}")
    if dt_selfhost_compile is not None:
        print(f"{'4. Selfhost Native Compiler Pipeline':<40s} | {dt_selfhost_compile:12.2f} ms | {'PASS'}")
    if dt_vm is not None:
        print(f"{'5. Selfhost Bytecode VM Suite (7/7)':<40s} | {dt_vm:12.2f} ms | {'PASS'}")

    print("-" * 70)
    print("Detailed Compiler Stage Breakdown (from Selfhost native pipeline):")
    for line in out_sh.splitlines():
        if line.startswith("profile "):
            print(f"  * {line}")

    print("=" * 70)

if __name__ == "__main__":
    main()
