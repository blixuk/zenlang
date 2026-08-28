from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode

@dataclass
class Literal(ASTNode):
    line: int | None
    column: int | None

@dataclass
class VoidLiteral(Literal):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = None
    type: Optional[Type] = TypeVoid()
    node_type: Optional[str] = "VoidLiteral"


@dataclass
class NothingLiteral(Literal):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = None
    type: Optional[Type] = TypeNothing()
    node_type: Optional[str] = "NothingLiteral"


@dataclass
class DefaultLiteral(Literal):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = None
    type: Optional[Type] = TypeDefault()
    node_type: Optional[str] = "DefaultLiteral"



@dataclass
class NumberLiteral(Literal):
    value: Optional[Any] = None
    literal: Optional[Any] = None
    base: Optional[Any] = None
    type: Optional[Type] = None
    node_type: Optional[str] = "NumberLiteral"


@dataclass
class TextLiteral(Literal):
    value: Optional[Any] = None
    literal: Optional[Any] = None
    type: Optional[Type] = None
    node_type: Optional[str] = "TextLiteral"


@dataclass
class VariantLiteral(Literal):
    value: Any
    type: Optional[Type] = None
    node_type: Optional[str] = "VariantLiteral"


@dataclass
class IntegerLiteral(Literal):
    value: int
    type: Optional[Type] = TypeInteger()
    node_type: Optional[str] = "IntegerLiteral"


@dataclass
class DecimalLiteral(Literal):
    value: float
    type: Optional[Type] = TypeDecimal()
    node_type: Optional[str] = "DecimalLiteral"


@dataclass
class StringLiteral(Literal):
    value: str
    prefix: Optional[str] = None
    type: Optional[Type] = TypeString()
    node_type: Optional[str] = "StringLiteral"


@dataclass
class RuneLiteral(Literal):
    value: str
    type: Optional[Type] = TypeRune()
    node_type: Optional[str] = "RuneLiteral"


@dataclass
class BooleanLiteral(Literal):
    value: str
    type: Optional[Type] = TypeBoolean()
    node_type: Optional[str] = "BooleanLiteral"
