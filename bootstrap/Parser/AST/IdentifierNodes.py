from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode


@dataclass
class Identifier(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    type: str
    symbol: Optional[Any] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "Identifier"


