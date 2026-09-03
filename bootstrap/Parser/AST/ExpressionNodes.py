from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode


@dataclass
class Expression(ASTNode):
    line: int | None
    column: int | None


@dataclass
class CallExpression(Expression):
    scope_level: int
    callee: Any
    arguments: list
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "CallExpression"


@dataclass
class MemberExpression(Expression):
    scope_level: int
    object: Any
    property: str
    node_type: Optional[str] = "MemberExpression"


@dataclass
class ParentExpression(Expression):
    scope_level: int
    node_type: Optional[str] = "ParentExpression"


@dataclass
class IndexExpression(Expression):
    object: Any
    index: Any
    node_type: Optional[str] = "IndexExpression"


@dataclass
class SliceExpression(Expression):
    object: Any
    start: Optional[Any] = None
    end: Optional[Any] = None
    step: Optional[Any] = None
    node_type: Optional[str] = "SliceExpression"


@dataclass
class FunctionExpression(Expression):
    scope_level: int
    name: str
    parameters: list
    body: Any
    return_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "FunctionExpression"


@dataclass
class BlockExpression(Expression):
    scope_level: int
    statements: list
    scope_type: str
    return_type: Optional[Type] = None
    node_type: Optional[str] = "BlockExpression"


@dataclass
class StructureExpression(Expression):
    scope_level: int
    name: str
    members: list
    declared_type: str = "Structure"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "StructureExpression"


@dataclass
class WhenExpression(Expression):
    scope_level: int
    condition: Any
    when_block: Any
    conditional_blocks: List[Dict[Any, Any]]
    or_block: Any
    return_type: Optional[Type] = None
    node_type: Optional[str] = "WhenExpression"


@dataclass
class WhenInlineExpression(Expression):
    scope_level: int
    condition: Any
    when_value: Any
    or_value: Any
    return_type: Optional[Type] = None
    node_type: Optional[str] = "WhenInlineExpression"


@dataclass
class CheckExpression(Expression):
    scope_level: int
    expression: Any
    or_value: Optional[Any] = None
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "CheckExpression"


@dataclass
class IsExpression(Expression):
    scope_level: int
    left: Any
    right: Any
    node_type: Optional[str] = "IsExpression"


@dataclass
class AwaitExpression(Expression):
    scope_level: int
    expression: Any
    node_type: Optional[str] = "AwaitExpression"
    resolved_type: Optional[Type] = None
