from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode



@dataclass
class Container(ASTNode):
    line: int | None
    column: int | None
    

@dataclass
class TypeLiteral(Container):
    name: str
    type: Optional[Type | None] = None
    subtypes: Optional[List["TypeLiteral"]] = None
    bits: Optional[int | None] = None
    node_type: Optional[str] = "TypeLiteral"


@dataclass
class AutoLiteral(Container):
    value: int
    node_type: Optional[str] = "AutoLiteral"


@dataclass
class ParameterLiteral(Container):
    name: str
    value: Optional[Any]
    declared_type: Type
    type: TypeParameter
    node_type: Optional[str] = "ParametersLiteral"


@dataclass
class MemberLiteral(Container):
    name: str
    value: Any
    declared_type: Type
    mutable: bool
    type: TypeMember
    node_type: Optional[str] = "MemberLiteral"


@dataclass
class ElementLiteral(Container):
    name: Any = None
    value: Optional[Any] = None
    mutable: Optional[bool] = False
    declared_type: Optional[Type] = None
    type: Optional[TypeElement] = None
    node_type: Optional[str] = "ElementLiteral"


@dataclass
class ArgumentLiteral(Container):
    name: str
    value: Any
    declared_type: Type
    type: TypeArgument
    node_type: Optional[str] = "ArgumentsLiteral"


@dataclass
class IteratorLiteral(Container):
    value: List[ASTNode]
    type: Optional[str] = "Iterator"
    node_type: Optional[str] = "IteratorLiteral"


