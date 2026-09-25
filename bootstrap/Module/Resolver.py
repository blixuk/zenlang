import os

class Resolver:
    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        self.search_paths = [self.root_path]
        
        # Add ZEN_PATH support if needed
        if "ZEN_PATH" in os.environ:
             self.search_paths.extend(os.environ["ZEN_PATH"].split(os.pathsep))

    # Short names → nested canonical modules (flat lib/zen/*.zl removed).
    # Exact-match only so zen.sys.term is not rewritten by a zen.sys alias.
    _IMPORT_ALIASES = {
        "zen.string": "zen.text.string",
        "lib/zen/string": "lib/zen/text/string",
        "zen.file": "zen.io.file",
        "lib/zen/file": "lib/zen/io/file",
        "zen.path": "zen.io.path",
        "lib/zen/path": "lib/zen/io/path",
        "zen.io": "zen.io.io",
        "lib/zen/io": "lib/zen/io/io",
        "zen.process": "zen.sys.process",
        "lib/zen/process": "lib/zen/sys/process",
        "zen.term": "zen.sys.term",
        "lib/zen/term": "lib/zen/sys/term",
        "zen.random": "zen.math.random",
        "lib/zen/random": "lib/zen/math/random",
        "zen.list": "zen.collections.list",
        "lib/zen/list": "lib/zen/collections/list",
        "zen.json": "zen.data.json",
        "lib/zen/json": "lib/zen/data/json",
        "zen.html": "zen.text.html",
        "lib/zen/html": "lib/zen/text/html",
        "zen.lorem": "zen.text.lorem",
        "lib/zen/lorem": "lib/zen/text/lorem",
        "zen/lorem": "lib/zen/text/lorem",
        "zen.color": "zen.color.color",
        "lib/zen/color": "lib/zen/color/color",
        "zen/color": "lib/zen/color/color",
        "zen.zendata": "zen.data.zendata.zendata",
        "lib/zen/zendata": "lib/zen/data/zendata/zendata",
        "zen/zendata": "lib/zen/data/zendata/zendata",
        "zen.zencode": "zen.tooling.zencode.zencode",
        "lib/zen/zencode": "lib/zen/tooling/zencode/zencode",
        "zen/zencode": "lib/zen/tooling/zencode/zencode",
        "zen.zenmark": "zen.text.zenmark.zenmark",
        "lib/zen/zenmark": "lib/zen/text/zenmark/zenmark",
        "zen/zenmark": "lib/zen/text/zenmark/zenmark",
        "zen.qrcode": "zen.graphics.qrcode",
        "lib/zen/qrcode": "lib/zen/graphics/qrcode",
        "zen/qrcode": "lib/zen/graphics/qrcode",
        "zen.data.qrcode": "zen.graphics.qrcode",
        "lib/zen/data/qrcode": "lib/zen/graphics/qrcode",
        "zen/data/qrcode": "lib/zen/graphics/qrcode",
    }

    def resolve(self, import_path: str, base_dir: str = None) -> str:
        """
        Resolves a dotted import path (e.g. 'tests.modules.MyLib') 
        to an absolute file path (e.g. '/path/to/tests/modules/MyLib.zl').
        """
        import_path = self._IMPORT_ALIASES.get(import_path, import_path)

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
                
            # 2. Check for package/package.zl
            last_part = os.path.basename(relative_path)
            candidate = os.path.join(base_path, relative_path, last_part + ".zl")
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

            # 3. Check exact path if it was already a file path (e.g. local import)
            candidate = os.path.join(base_path, relative_path)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

        raise FileNotFoundError(f"Module '{import_path}' not found in search paths: {self.search_paths}")
