import os
from typing import Dict, Any

class BuildSystem:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)

    def find_zbuild(self) -> str:
        path = os.path.join(self.project_root, ".zbuild")
        if os.path.exists(path):
            return path
        return None

    def parse_zbuild(self, path: str) -> Dict[str, str]:
        config = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        key, val = line.split(":", 1)
                        # Basic trimming of quotes
                        config[key.strip()] = val.strip().strip('"').strip("'")
            return config
        except Exception as e:
            print(f"Error parsing .zbuild: {e}")
            return {}

    def run_build(self, compiler) -> bool:
        zbuild_path = self.find_zbuild()
        if not zbuild_path:
            print(f"Error: No .zbuild file found in {self.project_root}")
            return False
        
        config = self.parse_zbuild(zbuild_path)
        if not config:
            return False
            
        project_name = config.get("name", "unnamed")
        print(f"--- Building Project: {project_name} ---")
        
        entry_rel = config.get("entry")
        if not entry_rel:
            print("Error: '.zbuild' must specify an 'entry' point (e.g., entry: src/main.zl)")
            return False
            
        entry_abs = os.path.join(self.project_root, entry_rel)
        if not os.path.exists(entry_abs):
            print(f"Error: Entry point not found at {entry_abs}")
            return False
            
        # Configure compiler
        compiler.load_source(entry_abs)
        
        # Run standard pipeline
        print(f"  [1/4] Parsing...")
        compiler.tokenize()
        compiler.parse()
        
        print(f"  [2/4] Validating...")
        compiler.validate()
        
        # Output handling
        output_rel = config.get("output")
        if output_rel:
            compiler.output_path = os.path.join(self.project_root, output_rel)
        
        # Generation
        print(f"  [3/4] Generating C code...")
        source_map = config.get("source_map", "true").lower() == "true"
        compiler.generate(source_map=source_map)
        
        print(f"  [4/4] Build complete.")
        return True
