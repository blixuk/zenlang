import os
import shutil
import subprocess
from pathlib import Path


class CCompiler:
    def __init__(self) -> None:
        pass

    def compile(self, code: str, run_args: list | None = None) -> None:
        build_directory: Path = Path("output/build")
        build_directory.mkdir(parents=True, exist_ok=True)

        # Canonical C runtime lives at project root: runtime/
        # (bootstrap/Transpiler/runtime is a symlink to ../../runtime for tools
        # that still resolve relative to the Transpiler tree.)
        current_dir = Path(__file__).parent.resolve()
        project_root = current_dir.parent.parent  # bootstrap/Transpiler → repo root
        runtime_dir = project_root / "runtime"
        if not runtime_dir.is_dir():
            runtime_dir = current_dir / "runtime"
        if runtime_dir.is_dir():
            runtime_dir = runtime_dir.resolve()
        else:
            print(f"Warning: Runtime directory not found at {project_root / 'runtime'}")
            runtime_dir = project_root / "runtime"

        out_c = build_directory / "out.c"
        code_with_include = "#include \"bootstrap_runtime.h\"\n" + code
        out_c.write_text(code_with_include)

        compiler = self.find_compiler()
        if compiler is None:
            raise RuntimeError("No C compiler found (gcc/clang/tcc).")

        exe_path = build_directory / "zen_program"
        rt_obj = self._ensure_runtime_obj(compiler, runtime_dir, project_root)
        includes = [
            "-I", str(runtime_dir),
            "-I", str(runtime_dir / "core"),
            "-I", str(runtime_dir / "collections"),
            "-I", str(runtime_dir / "io"),
            "-I", str(runtime_dir / "memory"),
            "-I", str(runtime_dir / "concurrency"),
        ]
        cmd = [
                compiler,
                str(out_c),
                str(rt_obj),
                "-o",
                str(exe_path),
                self._c_opt_flag(),
                "-Wall",
                "-Wno-unused-variable",
                "-Wno-unused-value",
                "-Wno-unused-label",
                "-Wno-unused-function",
                *includes,
                "-lm",
                "-lpthread",
                "-ldl",
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("\n!!! C COMPILE FAILED !!!")
            print(result.stderr)
            import sys
            sys.exit(1)

        import sys
        print("Compiled successfully. Running program:", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()

        # Linux permission fix
        try:
            os.chmod(exe_path, 0o755)
        except Exception:
            pass

        # RUN THE EXECUTABLE (inherit stdio so program output is visible).
        # run_args are user/script argv after the program path (parity with interpret mode).
        cmd_run = [str(exe_path)]
        if run_args:
            cmd_run.extend(str(a) for a in run_args)
        run_result = subprocess.run(cmd_run)
        if run_result.returncode != 0:
            sys.exit(run_result.returncode)

    # Find compiler
    def _c_opt_flag(self) -> str:
        # Edit-loop: ZEN_OPT=0 (or ZEN_CC=tcc). Release/default: -O2.
        v = os.environ.get("ZEN_OPT", "2")
        if v in ("0", "1", "2", "3"):
            return f"-O{v}"
        if v in ("s", "Os"):
            return "-Os"
        if v in ("g", "Og"):
            return "-Og"
        return "-O2"

    def _ensure_runtime_obj(self, compiler: str, runtime_dir: Path, project_root: Path) -> Path:
        """Compile runtime/bootstrap_runtime.c once; share cache with selfhost CLink."""
        obj_dir = project_root / "output" / "selfhost_rt"
        obj_dir.mkdir(parents=True, exist_ok=True)
        obj = obj_dir / "bootstrap_runtime.o"
        src = runtime_dir / "bootstrap_runtime.c"
        if obj.is_file() and src.is_file() and obj.stat().st_mtime >= src.stat().st_mtime:
            return obj
        if not src.is_file():
            raise RuntimeError(f"missing runtime C: {src}")
        cmd = [
            compiler,
            "-c",
            str(src),
            "-o",
            str(obj),
            "-O2",
            "-Wno-unused-variable",
            "-Wno-unused-value",
            "-Wno-unused-label",
            "-Wno-unused-function",
            "-I", str(runtime_dir),
            "-I", str(runtime_dir / "core"),
            "-I", str(runtime_dir / "collections"),
            "-I", str(runtime_dir / "io"),
            "-I", str(runtime_dir / "memory"),
            "-I", str(runtime_dir / "concurrency"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("\n!!! C COMPILE FAILED (runtime .o) !!!")
            print(result.stderr)
            import sys
            sys.exit(1)
        return obj

    def find_compiler(self):
        want = os.environ.get("ZEN_CC") or ""
        if want and shutil.which(want):
            return want
        for c in ("gcc", "clang", "tcc"):
            if shutil.which(c):
                return c
        return None
