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
            # Fallback: vendored/symlink next to the transpiler
            runtime_dir = current_dir / "runtime"

        if runtime_dir.is_dir():
            # Clean build directory
            if build_directory.exists():
                shutil.rmtree(build_directory)
            build_directory.mkdir(parents=True, exist_ok=True)

            # Copy runtime directory contents recursively (follow symlink)
            runtime_dir = runtime_dir.resolve()
            for item in runtime_dir.iterdir():
                dest = build_directory / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, symlinks=False)
                else:
                    shutil.copy(item, dest)
        else:
            print(f"Warning: Runtime directory not found at {project_root / 'runtime'}")

        # Write the generated C code
        out_c = build_directory / "out.c"
        code_with_include = "#include \"bootstrap_runtime.h\"\n" + code
        out_c.write_text(code_with_include)

        compiler = self.find_compiler()
        if compiler is None:
            raise RuntimeError("No C compiler found (gcc/clang/tcc).")

        exe_path = build_directory / "zen_program"
        
        # Explicit whitelist to avoid legacy/conflicting runtime files
        source_files = [
            build_directory / "out.c",
            build_directory / "bootstrap_runtime.c",
        ]
        
        cmd = [
                compiler,
                # match sources
                *[str(s) for s in source_files],
                "-o",
                str(exe_path),
                "-O2",
                "-Wall",
                "-Wno-unused-variable", # Suppress unused variable warnings for now
                "-Wno-unused-value",
                "-Wno-unused-label",
                "-Wno-unused-function",
                "-I", str(build_directory), # Include build dir for headers
                "-I", str(build_directory / "core"),
                "-I", str(build_directory / "collections"),
                "-I", str(build_directory / "io"),
                "-I", str(build_directory / "memory"),
                "-lm",                      # Link math library
                "-lpthread",                 # Link pthreads for concurrency
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
    def find_compiler(self):
        for c in ("gcc", "clang", "tcc"):
            if shutil.which(c):
                return c
        return None
