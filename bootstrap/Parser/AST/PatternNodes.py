from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode

@dataclass
class Pattern(ASTNode):
    line: int | None
    column: int | None

@dataclass
class LiteralPattern(Pattern):
    value: Any
    node_type: Optional[str] = "LiteralPattern"

@dataclass
class IdentifierPattern(Pattern):
    name: str
    node_type: Optional[str] = "IdentifierPattern"

@dataclass
class ListPattern(Pattern):
    elements: List[Pattern]
    node_type: Optional[str] = "ListPattern"

@dataclass
class MapPattern(Pattern):
    pairs: List[Tuple[Any, Pattern]]
    node_type: Optional[str] = "MapPattern"

@dataclass
class IsMatchPattern(Pattern):
    type_name: str
    node_type: Optional[str] = "IsMatchPattern"

@dataclass
class VariantPattern(Pattern):
    name: str
    enum_name: str
    params: List[Pattern]
    node_type: Optional[str] = "VariantPattern"

@dataclass
class WildcardPattern(Pattern):
    node_type: Optional[str] = "WildcardPattern"

@dataclass
class RestPattern(Pattern):
    name: str
    node_type: Optional[str] = "RestPattern"

@dataclass
class DestructurePattern(Pattern):
    name: str
    members: List[Tuple[str, Pattern]]
    node_type: Optional[str] = "DestructurePattern"
