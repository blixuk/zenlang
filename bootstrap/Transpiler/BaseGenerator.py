import os
from typing import Any, List, Optional, Set

class BaseGenerator:
    def __init__(self, enable_source_map: bool = False):
        self.enable_source_map = enable_source_map
        self.AST: Any = None
        self.indent_level: int = 0
        self.temp_counter: int = 0
        self.defer_counter: int = 0
        self.code: List[str] = []
        self.imports: List[str] = []
        self.global_variables: List[Any] = []
        self.global_functions: List[Any] = []
        self.global_functions_code: List[str] = []
        self.current_class: Optional[str] = None
        self.global_variable_names: Set[str] = {
            "Str", "IO", "Sys", "TokenType", "ASTKind", 
            "SymbolKind", "TokenModule", "ASTModule"
        }
        self.is_in_condition = False
        self.current_function = None
        self.singletons = []
        self.init_singletons_code = []
        self.scope_defer_stack = []
        self.global_classes = set()
        self.symbol_allocs = {} # Map target -> Alloc instruction
        self.last_emitted_line = -1
        self.last_emitted_file = None
        self.source_mapping = True
        self.scope = None
        self.program = None
        self.defer_prototypes = []
        self.structure_members = {}
        self.class_parents = {}
        self.variable_types = {}
        self.imported_modules = set()
        self.global_enums = set()

    def indent(self) -> str:
        return "    " * self.indent_level

    def emit(self, line: str = ""):
        self.code.append(self.indent() + line)



    def emit_line_directive(self, node: Any):
        if (self.enable_source_map and 
            hasattr(node, "line") and 
            getattr(node, "filename", None)):
            self.code.append(f'#line {node.line} "{node.filename}"')
