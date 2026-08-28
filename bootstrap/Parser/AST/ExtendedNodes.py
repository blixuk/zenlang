from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode
from Parser.AST.ContainerNodes import ElementLiteral


@dataclass
class Literal(ASTNode):
    line: int | None
    column: int | None
    elements: List[ElementLiteral]


@dataclass
class ListLiteral(Literal):
    type: Optional[TypeList] = None
    node_type: Optional[str] = "ListLiteral"


@dataclass
class TupleLiteral(Literal):
    type: Optional[TypeTuple] = None
    node_type: Optional[str] = "TupleLiteral"


@dataclass
class DictionaryLiteral(Literal):
    type: Optional[TypeMap] = None
    node_type: Optional[str] = "DictionaryLiteral"


@dataclass
class SetLiteral(Literal):
    type: Optional[TypeSet] = None
    node_type: Optional[str] = "SetLiteral"


@dataclass
class MapLiteral(Literal):
    resolved_type: Type = TypeMap(None, TypeVariant, TypeVariant)
    type: Optional[TypeMap] = None
    node_type: Optional[str] = "MapLiteral"


@dataclass
class VectorLiteral(Literal):
    type: Optional[TypeVector] = None
    node_type: Optional[str] = "VectorLiteral"

