from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode


@dataclass
class BinaryOperation(ASTNode):
    line: int
    column: int
    operator: str
    left: Any
    right: Any
    type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "BinaryOperation"


@dataclass
class UnaryOperation(ASTNode):
    line: int
    column: int
    operator: str
    right: Any
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "UnaryOperation"


