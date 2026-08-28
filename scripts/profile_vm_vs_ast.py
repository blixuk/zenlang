#!/usr/bin/env python3
import time
import subprocess
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV = dict(os.environ, ZEN_PATH=f"{ROOT}:{ROOT}/selfhost:{ROOT}/lib")

BENCH_SUITE = """
import compiler.Parser as Parser
import compiler.Bytecode as Bytecode
import zen.time.time as Time
import zen.io.io as io

function bench_fib_source() {
    <- `
        function fib(n) {
            when n <= 1 {
                <- n
            }
            <- fib(n - 1) + fib(n - 2)
        }
        let r -> fib(20)
        <- r
    `
}

function bench_loop_source() {
    <- `
        let i -> 0
        let total -> 0
        do while i < 50000 {
            total -> total + (i % 10)
            i -> i + 1
        }
        <- total
    `
}

function bench_collections_source() {
    <- `
        let l -> []
        let i -> 0
        do while i < 1000 {
            l.append(i * 2)
            i -> i + 1
        }
        let sum -> 0
        let j -> 0
        do while j < 1000 {
            sum -> sum + l[j]
            j -> j + 1
        }
        <- sum
    `
}

function run_vm_benchmark(name, src, iterations) {
    let prog -> Parser.parse_source(src)
    let c_res -> Bytecode.compile_program(prog)
    let chunk -> c_res[`chunk`]
    
    // Warmup
    Bytecode.eval_chunk(chunk, {})
    
    let t0 -> Time.now()
    let it -> 0
    let last_res -> 0
    do while it < iterations {
        last_res -> Bytecode.eval_chunk(chunk, {})
        it -> it + 1
    }
    let t1 -> Time.now()
    let elapsed_ms -> (t1 - t0)
    io.writeln(`[VM] ` + name + ` (` + iterations + ` runs): ` + elapsed_ms + ` ms | result: ` + last_res)
}

function main() {
    io.writeln(`=== ZENLANG BYTECODE VM PERFORMANCE BENCHMARKS ===`)
    run_vm_benchmark(`Fibonacci(20)`, bench_fib_source(), 5)
    run_vm_benchmark(`Tight Loop (50k iters)`, bench_loop_source(), 10)
    run_vm_benchmark(`List Append & Index (1k items)`, bench_collections_source(), 20)
    io.writeln(`=================================================`)
    <- 0
}
"""

def main():
    bench_file = os.path.join(ROOT, "scratch", "bench_vm_run.zl")
    os.makedirs(os.path.dirname(bench_file), exist_ok=True)
    with open(bench_file, "w") as f:
        f.write(BENCH_SUITE)

    print("============================================================")
    print("  RUNNING BYTECODE VM BENCHMARKS (Native -g Compiled)")
    print("============================================================")
    
    # Compile and run bench_vm_run with -g
    t0 = time.perf_counter()
    res = subprocess.run(["python3", "bootstrap/Zen.py", "-g", bench_file],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
    dt_comp = (time.perf_counter() - t0) * 1000.0
    print(f"Compilation time: {dt_comp:.2f} ms")
    if res.returncode == 0:
        print(res.stdout)
    else:
        print(f"FAIL: {res.stderr}")

    print("============================================================")
    print("  RUNNING BYTECODE VM BENCHMARKS (Interpreted)")
    print("============================================================")
    t0 = time.perf_counter()
    res = subprocess.run(["python3", "bootstrap/Zen.py", bench_file],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV, cwd=ROOT)
    dt_interp = (time.perf_counter() - t0) * 1000.0
    print(f"Interpreter execution total: {dt_interp:.2f} ms")
    if res.returncode == 0:
        print(res.stdout)
    else:
        print(f"FAIL: {res.stderr}")

if __name__ == "__main__":
    main()
