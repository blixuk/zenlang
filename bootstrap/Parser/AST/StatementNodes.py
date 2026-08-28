from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from Checker.Scope import Scope
from Checker.Type import *
from Parser.AST.Base import ASTNode


@dataclass
class Statement(ASTNode):
    line: int | None
    column: int | None


@dataclass
class AssignmentStatement(Statement):
    name: str
    value: Any
    declared_type: Type | None
    mutable: bool
    scope_level: int
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "AssignmentStatement"


@dataclass
class ReassignmentStatement(Statement):
    name: str
    value: Any
    inferred_type: Type | None
    mutable: bool
    scope_level: int
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ReassignmentStatement"


@dataclass
class MemberReassignmentStatement(Statement):
    scope_level: int
    callee: Any
    property: str
    value: Any
    declared_type: str
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "MemberReassignmentStatement"


@dataclass
class IndexReassignmentStatement(Statement):
    scope_level: int
    callee: Any
    index: Any
    value: Any
    node_type: Optional[str] = "IndexReassignmentStatement"


@dataclass
class DereferenceReassignmentStatement(Statement):
    pointer_expression: Any
    value: Any
    scope_level: int
    node_type: Optional[str] = "DereferenceReassignmentStatement"


@dataclass
class ExpressionStatement(Statement):
    expression: Any
    node_type: Optional[str] = "ExpressionStatement"


@dataclass
class BlockStatement(Statement):
    scope_level: int
    scope_type: str
    statements: List[ASTNode | None]
    return_type: Optional[Type] = None
    node_type: Optional[str] = "BlockStatement"


@dataclass
class FunctionStatement(Statement):
    scope_level: int
    name: str
    parameters: List
    body: Any
    return_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "FunctionStatement"


@dataclass
class TaskStatement(Statement):
    scope_level: int
    name: str
    parameters: List
    body: Any
    return_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "TaskStatement"


@dataclass
class StructureStatement(Statement):
    scope_level: int
    name: str
    members: list
    parent: Optional[str] = None
    reflectable: bool = False
    declared_type: str = "Structure"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "StructureStatement"


@dataclass
class ObjectStatement(Statement):
    scope_level: int
    name: str
    members: list
    parent: Optional[str] = None
    reflectable: bool = False
    declared_type: str = "Object"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ObjectStatement"


@dataclass
class EnumVariant(Statement):
    name: str
    params: List[str]  # List of parameter names
    value: Optional[Any] = None
    node_type: Optional[str] = "EnumVariant"

@dataclass
class EnumeratorStatement(Statement):
    scope_level: int
    name: str
    members: List[EnumVariant]
    declared_type: str = "Enumerator"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "EnumeratorStatement"


@dataclass
class ClassStatement(Statement):
    scope_level: int
    name: str
    parent: Optional[str]
    members: list
    methods: list
    reflectable: bool = False
    declared_type: str = "Class"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ClassStatement"


@dataclass
class ScopeStatement(Statement):
    scope_level: int
    name: str
    body: Any
    node_type: Optional[str] = "ScopeStatement"



@dataclass
class ReturnStatement(Statement):
    scope_level: int
    value: Any
    inferred_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ReturnStatement"


@dataclass
class RaiseStatement(Statement):
    scope_level: int
    value: Any
    with_value: Optional[Any] = None
    node_type: Optional[str] = "RaiseStatement"


@dataclass
class DeferStatement(Statement):
    scope_level: int
    body: Any
    node_type: Optional[str] = "DeferStatement"


@dataclass
class AssertStatement(Statement):
    scope_level: int
    condition: Any
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "AssertStatement"


@dataclass
class WhenStatement(Statement):
    scope_level: int
    condition: Any
    when_block: Any
    conditional_blocks: List[Dict[Any, Any]]
    or_block: Any
    branches: Optional[List["CaseBranch"]] = None
    node_type: Optional[str] = "WhenStatement"


@dataclass
class WithStatement(Statement):
    scope_level: int
    expression: Any
    alias: str
    body: Any
    node_type: Optional[str] = "WithStatement"


@dataclass
class InExpression(Statement):
    scope_level: int
    arena: str
    expression: Any
    node_type: Optional[str] = "InExpression"


@dataclass
class CaseBranch(Statement):
    pattern: Any
    body: Any
    guard: Optional[Any] = None
    node_type: Optional[str] = "CaseBranch"

@dataclass
class CheckStatement(Statement):
    scope_level: int
    expression: Any
    cases: List[CaseBranch]
    or_block: Optional[Any] = None
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "CheckStatement"


@dataclass
class DoStatement(Statement):
    do_type: str
    scope_level: int
    body: Any
    condition: Optional[Any] = None
    iterator: Optional[Any] = None
    iterable: Optional[Any] = None
    or_block: Optional[Any] = None
    node_type: Optional[str] = "DoStatement"


@dataclass
class BreakStatement(Statement):
    scope_level: int
    node_type: Optional[str] = "BreakStatement"


@dataclass
class ContinueStatement(Statement):
    scope_level: int
    node_type: Optional[str] = "ContinueStatement"


@dataclass
class ExportStatement(Statement):
    scope_level: int
    statement: Any
    node_type: Optional[str] = "ExportStatement"


@dataclass
class ImportStatement(Statement):
    name: str # alias or module name
    path: str
    alias: Optional[str] = None
    node_type: Optional[str] = "ImportStatement"


@dataclass
class FromImportStatement(Statement):
    path: str
    symbols: List[Dict[str, str]] # List of {"name": str, "alias": Optional[str]}
    node_type: Optional[str] = "FromImportStatement"


