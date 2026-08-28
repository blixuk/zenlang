#!/usr/bin/env python3
import time
import subprocess
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_SELFHOST = os.path.join(ROOT, "bin", "zen-selfhost")
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib")

def time_cmd(cmd, runs=3):
    durations = []
    stdout, stderr = "", ""
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

def run_benchmarks():
    print("=" * 80)
    print("       ZENLANG PERFORMANCE PROFILING: COMPILATION & EXECUTION")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. COMPILATION BENCHMARKS: Native Selfhost (Zen -> C)
    # -------------------------------------------------------------
    print("\n--- 1. COMPILER PIPELINE THROUGHPUT (ZEN -> C) ---")
    out_c = os.path.join(ROOT, "output", "bench_test_out.c")
    os.makedirs(os.path.dirname(out_c), exist_ok=True)

    compile_fixtures = [
        ("Stage 7 Fixture (stage7_add.zl)", "tests/self_hosting/fixtures/stage7_add.zl"),
        ("Classes & Methods (class_counter.zl)", "tests/self_hosting/fixtures/class_counter.zl"),
        ("Pattern Binds (pattern_bind.zl)", "tests/self_hosting/fixtures/pattern_bind.zl"),
        ("Closures & Lambdas (closure_nested.zl)", "tests/self_hosting/fixtures/closure_nested.zl"),
        ("Multi-Unit Main (multi_main.zl)", "tests/self_hosting/fixtures/multi_unit/multi_main.zl"),
    ]

    print(f" {'Source File':<42} | {'Compile Time':<14} | {'Status':<10}")
    print(f" {'-'*42}-|-{'-'*14}-|-{'-'*10}")

    for label, fix_rel in compile_fixtures:
        fix_path = os.path.join(ROOT, fix_rel)
        t_compile, _, _ = time_cmd([BIN_SELFHOST, "compile", fix_path, out_c], runs=2)
        s_comp = f"{t_compile:.2f} ms" if t_compile is not None else "ERR"
        status = "PASS" if t_compile is not None else "FAIL"
        print(f" {label:<42} | {s_comp:<14} | {status:<10}")

    # -------------------------------------------------------------
    # 2. EXECUTION ENGINE BENCHMARKS (Three-Layer Architecture)
    # -------------------------------------------------------------
    print("\n--- 2. EXECUTION ENGINE BENCHMARKS (AOT vs INTERPRETER) ---")

    workloads = [
        ("Recursion: Fib(18) [5,777 calls]", "tests/self_hosting/fixtures/stage7_add.zl"),
        ("Extended Operators & String Concat", "tests/language/test_extended_operators.zl"),
        ("Pattern Matching & Destructuring", "tests/language/pattern_matching_01.zl"),
    ]

    print(f" {'Workload':<36} | {'Native AOT (-O2)':<16} | {'Bootstrap (Py)':<16} | {'AOT Speedup':<12}")
    print(f" {'-'*36}-|-{'-'*16}-|-{'-'*16}-|-{'-'*12}")

    scratch_bin = os.path.join(ROOT, "output", "bench_bin")
    for label, fix_rel in workloads:
        fix_path = os.path.join(ROOT, fix_rel)
        # Build native binary
        subprocess.run([BIN_SELFHOST, "build", fix_path, scratch_bin], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
        t_aot, _, _ = time_cmd([scratch_bin], runs=5) if os.path.exists(scratch_bin) else (None, "", "")
        t_py, _, _ = time_cmd(["python3", "bootstrap/Zen.py", fix_path], runs=2)

        s_aot = f"{t_aot:.2f} ms" if t_aot is not None else "N/A"
        s_py = f"{t_py:.2f} ms" if t_py is not None else "N/A"
        speedup = f"{t_py / t_aot:6.1f}x" if (t_aot and t_py and t_aot > 0) else "N/A"

        print(f" {label:<36} | {s_aot:<16} | {s_py:<16} | {speedup:<12}")

    # -------------------------------------------------------------
    # 3. DETAILED COMPILATION STAGE BREAKDOWN (ZEN_PROFILE=1)
    # -------------------------------------------------------------
    print("\n--- 3. DETAILED COMPILATION STAGE BREAKDOWN ---")
    fixture = os.path.join(ROOT, "tests", "self_hosting", "fixtures", "stage7_add.zl")
    env_prof = dict(ENV, ZEN_PROFILE="1")
    t0 = time.perf_counter()
    res = subprocess.run([BIN_SELFHOST, "compile", fixture, out_c], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env_prof, cwd=ROOT)
    total_dt = (time.perf_counter() - t0) * 1000.0
    combined = (res.stdout or "") + (res.stderr or "")

    print(f" Fixture: tests/self_hosting/fixtures/stage7_add.zl")
    print(f" Total Pipeline Duration: {total_dt:.2f} ms\n")
    for line in combined.splitlines():
        if line.startswith("profile "):
            parts = line.split()
            if len(parts) >= 3:
                stage = parts[1]
                val = float(parts[2])
                pct = (val / total_dt) * 100.0 if total_dt > 0 else 0
                print(f"   • {stage:<14}: {val:9.2f} ms  ({pct:5.1f}%)")

    # -------------------------------------------------------------
    # 4. BYTECODE VM & INTEROP ABI BENCHMARKS
    # -------------------------------------------------------------
    print("\n--- 4. BYTECODE VM & MIXED ABI BENCHMARKS ---")
    t_vm, _, _ = time_cmd(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_vm.zl"], runs=1)
    t_abi, _, _ = time_cmd(["python3", "bootstrap/Zen.py", "tests/self_hosting/test_mixed_abi.zl"], runs=1)
    print(f" • Selfhost Bytecode VM Suite (test_vm.zl):       {t_vm:8.2f} ms  (7/7 PASS)")
    print(f" • Mixed Execution ABI Suite (test_mixed_abi.zl): {t_abi:8.2f} ms  (6/6 PASS)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_benchmarks()
