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
    TypeDefault,
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


## Statements


@dataclass
class AssignmentStatement(ASTNode):
    line: int
    column: int
    name: str
    value: Any
    declared_type: Type | None
    mutable: bool
    scope_level: int
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "AssignmentStatement"


@dataclass
class ReassignmentStatement(ASTNode):
    line: int
    column: int
    name: str
    value: Any
    inferred_type: Type | None
    mutable: bool
    scope_level: int
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ReassignmentStatement"


@dataclass
class MemberReassignmentStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    callee: Any
    expression: str
    value: Any
    declared_type: str
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "MemberReassignmentStatement"


@dataclass
class IndexReassignmentStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    callee: Any
    index: Any
    value: Any
    node_type: Optional[str] = "IndexReassignmentStatement"


@dataclass
class ExpressionStatement(ASTNode):
    expression: Any
    node_type: Optional[str] = "ExpressionStatement"


@dataclass
class BlockStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    scope_type: str
    statements: List[ASTNode | None]
    return_type: Optional[Type] = None
    node_type: Optional[str] = "BlockStatement"


@dataclass
class FunctionStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    parameters: List
    body: Any
    return_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    generic_params: Optional[list] = None
    node_type: Optional[str] = "FunctionStatement"


@dataclass
class StructureStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    members: list
    parent: Optional[str] = None
    reflectable: bool = False
    declared_type: str = "Structure"
    resolved_type: Optional[Type] = None
    generic_params: Optional[list] = None
    node_type: Optional[str] = "StructureStatement"


@dataclass
class ObjectStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    members: list
    parent: Optional[str] = None
    reflectable: bool = False
    declared_type: str = "Object"
    resolved_type: Optional[Type] = None
    generic_params: Optional[list] = None
    node_type: Optional[str] = "ObjectStatement"


@dataclass
class EnumVariant(ASTNode):
    line: int
    column: int
    name: str
    params: List[str]  # List of parameter names
    value: Optional[Any] = None
    node_type: Optional[str] = "EnumVariant"

@dataclass
class EnumeratorStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    members: List[EnumVariant]
    declared_type: str = "Enumerator"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "EnumeratorStatement"


@dataclass
class ClassStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    parent: Optional[str]
    members: list
    methods: list
    reflectable: bool = False
    declared_type: str = "Class"
    resolved_type: Optional[Type] = None
    generic_params: Optional[list] = None
    node_type: Optional[str] = "ClassStatement"


@dataclass
class ScopeStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    body: Any
    node_type: Optional[str] = "ScopeStatement"



@dataclass
class ReturnStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    value: Any
    inferred_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "ReturnStatement"


@dataclass
class RaiseStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    value: Any
    with_value: Optional[Any] = None
    node_type: Optional[str] = "RaiseStatement"


@dataclass
class DeferStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    body: Any
    node_type: Optional[str] = "DeferStatement"


@dataclass
class AssertStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    condition: Any
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "AssertStatement"


@dataclass
class WhenStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    condition: Any
    when_block: Any
    conditional_blocks: List[Dict[Any, Any]]
    or_block: Any
    branches: Optional[List["CaseBranch"]] = None
    node_type: Optional[str] = "WhenStatement"


@dataclass
class WithStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    expression: Any
    alias: str
    body: Any
    node_type: Optional[str] = "WithStatement"


@dataclass
class InExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    arena: str
    expression: Any
    node_type: Optional[str] = "InExpression"


@dataclass
@dataclass
class CaseBranch(ASTNode):
    line: int
    column: int
    pattern: Any
    body: Any
    node_type: Optional[str] = "CaseBranch"

@dataclass
class CheckStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    expression: Any
    cases: List[CaseBranch]
    or_block: Optional[Any] = None
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "CheckStatement"


@dataclass
class DoStatement(ASTNode):
    line: int
    column: int
    do_type: str
    scope_level: int
    body: Any
    condition: Optional[Any] = None
    iterator: Optional[Any] = None
    iterable: Optional[Any] = None
    or_block: Optional[Any] = None
    node_type: Optional[str] = "DoStatement"


@dataclass
class BreakStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    node_type: Optional[str] = "BreakStatement"


@dataclass
class ContinueStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    node_type: Optional[str] = "ContinueStatement"


@dataclass
class ExportStatement(ASTNode):
    line: int
    column: int
    scope_level: int
    statement: Any
    node_type: Optional[str] = "ExportStatement"


@dataclass
class ImportStatement(ASTNode):
    line: int
    column: int
    name: str # alias or module name
    path: str
    alias: Optional[str] = None
    node_type: Optional[str] = "ImportStatement"


@dataclass
class FromImportStatement(ASTNode):
    line: int
    column: int
    path: str
    symbols: List[Dict[str, str]] # List of {"name": str, "alias": Optional[str]}
    node_type: Optional[str] = "FromImportStatement"


## Expressions


@dataclass
class CallExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    callee: Any
    arguments: list
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "CallExpression"


@dataclass
class MemberExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    object: Any
    property: str
    node_type: Optional[str] = "MemberExpression"


@dataclass
class ParentExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    node_type: Optional[str] = "ParentExpression"


@dataclass
class IndexExpression(ASTNode):
    line: int
    column: int
    object: Any
    index: Any
    node_type: Optional[str] = "IndexExpression"


@dataclass
class SliceExpression(ASTNode):
    line: int
    column: int
    object: Any
    start: Optional[Any] = None
    end: Optional[Any] = None
    step: Optional[Any] = None
    node_type: Optional[str] = "SliceExpression"


@dataclass
class FunctionExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    parameters: list
    body: Any
    return_type: Optional[Type] = None
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "FunctionExpression"


@dataclass
class BlockExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    statements: list
    scope_type: str
    return_type: Optional[Type] = None
    node_type: Optional[str] = "BlockExpression"


@dataclass
class StructureExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    name: str
    members: list
    declared_type: str = "Structure"
    resolved_type: Optional[Type] = None
    node_type: Optional[str] = "StructureExpression"


@dataclass
class WhenExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    condition: Any
    when_block: Any
    conditional_blocks: List[Dict[Any, Any]]
    or_block: Any
    return_type: Optional[Type] = None
    node_type: Optional[str] = "WhenExpression"


@dataclass
class WhenInlineExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    condition: Any
    when_value: Any
    or_value: Any
    return_type: Optional[Type] = None
    node_type: Optional[str] = "WhenInlineExpression"


@dataclass
class CheckExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    expression: Any
    or_value: Optional[Any] = None
    raise_expression: Optional[Any] = None
    node_type: Optional[str] = "CheckExpression"


@dataclass
class IsExpression(ASTNode):
    line: int
    column: int
    scope_level: int
    left: Any
    right: Any
    node_type: Optional[str] = "IsExpression"


## Identifiers


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


## Operations


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


## Literals


@dataclass
class VoidLiteral(ASTNode):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = None
    type: Optional[Type] = TypeVoid()
    node_type: Optional[str] = "VoidLiteral"


@dataclass
class NothingLiteral(ASTNode):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = None
    type: Optional[Type] = TypeNothing()
    node_type: Optional[str] = "NothingLiteral"


@dataclass
class DefaultLiteral(ASTNode):
    line: int | None = None
    column: int | None = None
    value: Optional[Any] = "Default"
    type: Optional[Type] = TypeDefault()
    node_type: Optional[str] = "DefaultLiteral"



@dataclass
class NumberLiteral(ASTNode):
    line: int
    column: int
    value: Optional[Any] = None
    literal: Optional[Any] = None
    base: Optional[Any] = None
    type: Optional[Type] = None
    node_type: Optional[str] = "NumberLiteral"


@dataclass
class TextLiteral(ASTNode):
    line: int
    column: int
    value: Optional[Any] = None
    literal: Optional[Any] = None
    type: Optional[Type] = None
    node_type: Optional[str] = "TextLiteral"


@dataclass
class VariantLiteral(ASTNode):
    line: int
    column: int
    value: Any
    type: Optional[Type] = None
    node_type: Optional[str] = "VariantLiteral"


@dataclass
class IntegerLiteral(ASTNode):
    line: int
    column: int
    value: int
    type: Optional[Type] = TypeInteger()
    node_type: Optional[str] = "IntegerLiteral"


@dataclass
class DecimalLiteral(ASTNode):
    line: int
    column: int
    value: float
    type: Optional[Type] = TypeDecimal()
    node_type: Optional[str] = "DecimalLiteral"


@dataclass
class StringLiteral(ASTNode):
    line: int
    column: int
    value: str
    prefix: Optional[str] = None
    type: Optional[Type] = TypeString()
    node_type: Optional[str] = "StringLiteral"


@dataclass
class RuneLiteral(ASTNode):
    line: int
    column: int
    value: str
    type: Optional[Type] = TypeRune()
    node_type: Optional[str] = "RuneLiteral"


@dataclass
class BooleanLiteral(ASTNode):
    line: int
    column: int
    value: str
    type: Optional[Type] = TypeBoolean()
    node_type: Optional[str] = "BooleanLiteral"


## Container Types


@dataclass
class TypeLiteral(ASTNode):
    line: int
    column: int
    name: str
    type: Optional[Type | None] = None
    subtypes: Optional[List["TypeLiteral"]] = None
    bits: Optional[int | None] = None
    node_type: Optional[str] = "TypeLiteral"


@dataclass
class AutoLiteral(ASTNode):
    line: int
    column: int
    value: int
    node_type: Optional[str] = "AutoLiteral"


@dataclass
class ParameterLiteral(ASTNode):
    line: int
    column: int
    name: str
    value: Optional[Any]
    declared_type: Type
    type: TypeParameter
    node_type: Optional[str] = "ParametersLiteral"


@dataclass
class MemberLiteral(ASTNode):
    line: int
    column: int
    name: str
    value: Any
    declared_type: Type
    mutable: bool
    type: TypeMember
    node_type: Optional[str] = "MemberLiteral"


@dataclass
class ElementLiteral(ASTNode):
    line: int
    column: int
    name: Any = None
    value: Optional[Any] = None
    mutable: Optional[bool] = False
    declared_type: Optional[Type] = None
    type: Optional[TypeElement] = None
    node_type: Optional[str] = "ElementLiteral"


@dataclass
class ArgumentLiteral(ASTNode):
    line: int
    column: int
    name: str
    value: Any
    declared_type: Type
    type: TypeArgument
    node_type: Optional[str] = "ArgumentsLiteral"


@dataclass
class IteratorLiteral(ASTNode):
    line: int
    column: int
    value: List[ASTNode]
    type: Optional[str] = "Iterator"
    node_type: Optional[str] = "IteratorLiteral"


## Extended Types


@dataclass
class ListLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral]
    type: Optional[TypeList] = None
    node_type: Optional[str] = "ListLiteral"


@dataclass
class TupleLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral]
    type: Optional[TypeTuple] = None
    node_type: Optional[str] = "TupleLiteral"


@dataclass
class DictionaryLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral] # ElementLiteral can represent key -> value
    type: Optional[TypeMap] = None
    node_type: Optional[str] = "DictionaryLiteral"


@dataclass
class SetLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral]
    type: Optional[TypeSet] = None
    node_type: Optional[str] = "SetLiteral"


@dataclass
class MapLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral] # ElementLiteral can represent key -> value
    resolved_type: Type = TypeMap(None, TypeVariant, TypeVariant)
    type: Optional[TypeMap] = None
    node_type: Optional[str] = "MapLiteral"


@dataclass
class VectorLiteral(ASTNode):
    line: int
    column: int
    elements: List[ElementLiteral]
    type: Optional[TypeVector] = None
    node_type: Optional[str] = "VectorLiteral"

## Patterns

@dataclass
class Pattern(ASTNode):
    line: int
    column: int

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
