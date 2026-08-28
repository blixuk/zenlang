from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import (
    Type,
    TypeArgument,
    TypeBoolean,
    TypeDecimal,
    TypeElement,
    TypeFunction,
    TypeInteger,
    TypeList,
    TypeMember,
    TypeNothing,
    TypeNumber,
    TypeParameter,
    TypeRune,
    TypeString,
    TypeStructure,
    TypeTuple,
    TypeVariable,
    TypeVariant,
    TypeVoid,
    TypeMap,
    TypeSet,
    TypeVector,
)


class ASTNode:
    node_type: str | None = "ASTNode"
    doc_comment: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class Statements(ASTNode):
    statements: List[ASTNode]
    node_type: Optional[str] = "Statements"


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]
    entry_point: Optional[str] = "main"
    return_code: Optional[int] = None
    node_type: Optional[str] = "Program"


@dataclass
class Script(ASTNode):
    statements: List[ASTNode]
    return_code: Optional[int] = None
    node_type: Optional[str] = "Script"


@dataclass
class Scope(ASTNode):
    scope: Scope
    node_type: Optional[str] = "Scope"


