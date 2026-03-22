import os

class Resolver:
    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        self.search_paths = [self.root_path]
        
        # Add ZEN_PATH support if needed
        if "ZEN_PATH" in os.environ:
             self.search_paths.extend(os.environ["ZEN_PATH"].split(os.pathsep))

    def resolve(self, import_path: str, base_dir: str = None) -> str:
        """
        Resolves a dotted import path (e.g. 'tests.modules.MyLib') 
        to an absolute file path (e.g. '/path/to/tests/modules/MyLib.zl').
        """
        # Convert dotted path to file path
        # 'tests.modules.MyLib' -> 'tests/modules/MyLib'
        if os.sep in import_path or "/" in import_path:
             relative_path = import_path
        else:
             relative_path = import_path.replace(".", os.sep)
        
        search_paths = self.search_paths
        if base_dir:
            search_paths = [base_dir] + search_paths
            
        # Try finding the file in search paths
        for base_path in search_paths:
            # 1. Check for file.zl
            # 1. Check for file.zl
            candidate = os.path.join(base_path, relative_path + ".zl")
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
                
            # 2. Check for package/mod.zl (if implicit) or package/__init__.zl?
            # ZenLang spec is silent on __init__, assuming direct mapping for now.
            
            # 3. Check exact path if it was already a file path (e.g. local import)
            candidate = os.path.join(base_path, relative_path)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

        raise FileNotFoundError(f"Module '{import_path}' not found in search paths: {self.search_paths}")
