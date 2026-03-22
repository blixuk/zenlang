import os
import shutil
import subprocess
from pathlib import Path


class CCompiler:
    def __init__(self) -> None:
        pass

    def compile(self, code: str) -> None:
        build_directory: Path = Path("output/build")
        build_directory.mkdir(parents=True, exist_ok=True)

        current_dir = Path(__file__).parent.resolve()
        # Navigate to project root (bootstrap/Transpiler -> bootstrap -> zen)
        # logical structure: zen/bootstrap/Transpiler/CCompile.py
        # root is ../../
        project_root = current_dir.parent.parent
        runtime_dir = project_root / "runtime"
        
        if not runtime_dir.exists():
             # Fallback to local runtime if project structure is different (e.g. running from different context)
             runtime_dir = current_dir / "runtime"
             
        if runtime_dir.exists():
            shutil.copytree(runtime_dir, build_directory, dirs_exist_ok=True)
        else:
             print(f"Warning: Runtime directory not found at {runtime_dir}")

        # Write the generated C code
        out_c = build_directory / "out.c"
        out_c.write_text(code)

        compiler = self.find_compiler()
        if compiler is None:
            raise RuntimeError("No C compiler found (gcc/clang/tcc).")

        exe_path = build_directory / "zen_program"
        
        # Explicit whitelist to avoid legacy/conflicting runtime files
        source_files = [
            build_directory / "out.c",
            build_directory / "bootstrap_runtime.c",
        ]
        
        # Ensure bootstrap_runtime.c exists in build_directory
        bootstrap_runtime_c = current_dir / "runtime" / "bootstrap_runtime.c"
        if bootstrap_runtime_c.exists():
            shutil.copy(bootstrap_runtime_c, build_directory / "bootstrap_runtime.c")
            shutil.copy(current_dir / "runtime" / "bootstrap_runtime.h", build_directory / "bootstrap_runtime.h")
        
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
                "-I", str(build_directory), # Include build dir for headers
                "-lm",                      # Link math library
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("Compile failed:")
            print(result.stderr)
            return

        print("Compiled successfully. Running program:\n")

        # Linux permission fix
        try:
            os.chmod(exe_path, 0o755)
        except:
            pass

        # RUN THE EXECUTABLE
        subprocess.run([str(exe_path)])

    # Find compiler
    def find_compiler(self):
        for c in ("gcc", "clang", "tcc"):
            if shutil.which(c):
                return c
        return None
