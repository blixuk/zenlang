from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class SymbolOrigin(Enum):
    BUILTIN = "BUILTIN"
    USER = "USER"
    EXTERNAL = "EXTERNAL"


class SymbolKind(Enum):
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    FUNCTION = "FUNCTION"
    STRUCTURE = "STRUCTURE"
    ENUMERATOR = "ENUMERATOR"
    PARAMETER = "PARAMETER"
    MEMBER = "MEMBER"
    ELEMENT = "ELEMENT"
    ARGUMENT = "ARGUMENT"
    COLLECTION = "COLLECTION"
    CONTAINER = "CONTAINER"
    TYPE = "TYPE"
    VARIANT = "VARIANT"
    MODULE = "MODULE"
    CLASS = "CLASS"
    NAMESPACE = "NAMESPACE"


class Value:
    pass


@dataclass(frozen=True)
class ValueNothing(Value):
    pass


@dataclass(frozen=True)
class ValueDefault(Value):
    pass


class Type:
    pass


# Primitive Types


@dataclass(frozen=True)
class TypeVoid(Type):
    name: str = "Void"


@dataclass
class TypeVariant(Type):
    name: str = "Variant"


@dataclass(frozen=True)
class TypeNothing(Type):
    name: str = "Nothing"


@dataclass(frozen=True)
class TypeDefault(Type):
    name: str = "Default"


@dataclass(frozen=True)
class TypeBoolean(Type):
    name: str = "Boolean"


@dataclass(frozen=True)
class TypeInteger(Type):
    name: str = "Integer"
    bits: Optional[int] = 32
    signed: Optional[bool] = False


@dataclass(frozen=True)
class TypeDecimal(Type):
    name: str = "Decimal"
    bits: Optional[int] = 32


@dataclass(frozen=True)
class TypeString(Type):
    name: str = "String"
    bits: Optional[int] = 32


@dataclass(frozen=True)
class TypeByte(Type):
    name: str = "Byte"
    bits: Optional[int] = 8
    signed: Optional[bool] = False


@dataclass(frozen=True)
class TypeBytes(Type):
    name: str = "Bytes"


@dataclass(frozen=True)
class TypeRune(Type):
    name: str = "Rune"
    bits: Optional[int] = 32


PRIMITIVE_TYPES: Dict = {
    "Void": TypeVoid,
    "Nothing": TypeNothing,
    "Default": TypeDefault,
    "Variant": TypeVariant,
    "Integer": TypeInteger,
    "Decimal": TypeDecimal,
    "Byte": TypeByte,
    "Bytes": TypeBytes,
    "String": TypeString,
    "Rune": TypeRune,
    "Boolean": TypeBoolean,
}

def TypePrimitive(name: str) -> Type:
    if name in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[name]()
    return TypeVariant()



# Abstract Types


@dataclass(frozen=True)
class TypeNumber(Type):
    name: str = "Number"
    bound: Type | None = None


@dataclass(frozen=True)
class TypeText(Type):
    name: str = "Text"
    bound: Type | None = None


@dataclass(frozen=True)
class TypeCollection(Type):
    name: str = "Collection"
    bound: Type | None = None


@dataclass(frozen=True)
class TypeContainer(Type):
    name: str = "Container"
    bound: Type | None = None


ABSTRACT_TYPES: Dict = {
    "Number": TypeNumber,
    "Text": TypeText,
    "Collection": TypeCollection,
    "Container": TypeContainer,
}

# Collection Types


@dataclass(frozen=True)
class TypeParameter(Type):
    name: Optional[str]
    type: Type
    mutable: bool = False


@dataclass(frozen=True)
class TypeMember(Type):
    name: Optional[str]
    type: Type
    mutable: bool = False


@dataclass(frozen=True)
class TypeElement(Type):
    name: Optional[str]
    type: Type
    mutable: bool = False


@dataclass(frozen=True)
class TypeArgument(Type):
    name: Optional[str]
    type: Type
    mutable: bool = False


@dataclass(frozen=True)
class TypeList(Type):
    name: Optional[str]
    elements: List[TypeElement]


@dataclass(frozen=True)
class TypeTuple(Type):
    name: Optional[str]
    elements: List[TypeElement]


@dataclass(frozen=True)
class TypeMap(Type):
    name: Optional[str]
    key_type: Type
    value_type: Type


@dataclass(frozen=True)
class TypeSet(Type):
    name: Optional[str]
    element_type: Type


@dataclass(frozen=True)
class TypeVector(Type):
    name: Optional[str]
    element_type: Type
    size: int


COLLECTION_TYPES: Dict = {
    "Parameter": TypeParameter,
    "Member": TypeMember,
    "Element": TypeElement,
    "Argument": TypeArgument,
    "List": TypeList,
    "Tuple": TypeTuple,
    "Map": TypeMap,
    "Dictionary": TypeMap,
    "Set": TypeSet,
    "Vector": TypeVector,
}


@dataclass(frozen=True)
class TypeParam(Type):
    name: str


@dataclass(frozen=True)
class TypeFunction(Type):
    name: str
    parameters: Optional[List[TypeParameter]]
    return_type: Type
    generic_params: Optional[List[str]] = None


@dataclass(frozen=True)
class TypeTask(Type):
    name: str
    parameters: Optional[List[TypeParameter]]
    return_type: Type
    generic_params: Optional[List[str]] = None


@dataclass(frozen=True)
class TypeTaskHandle(Type):
    inner_type: Type
    name: str = "TaskHandle"


@dataclass
class TypeStructure(Type):
    name: str
    members: Any # Dict[str, Type]
    parent: Optional['TypeStructure'] = None
    filename: Optional[str] = None
    methods: Optional[Any] = None # Dict[str, TypeFunction]
    generic_params: Optional[List[str]] = None


@dataclass
class TypeClass(Type):
    name: str
    members: Any # Dict[str, TypeVariable]
    methods: Any # Dict[str, TypeFunction]
    parent: Optional['TypeClass'] = None
    filename: Optional[str] = None
    generic_params: Optional[List[str]] = None



@dataclass(frozen=True)
class TypeEnumerator(Type):
    name: str
    members: List[TypeMember]


@dataclass(frozen=True)
class TypeEnum(Type):
    name: str
    variants: Dict[str, "TypeEnumVariant"]
    filename: Optional[str] = None

@dataclass(frozen=True)
class TypeEnumVariant(Type):
    name: str
    params: List[Type]
    parent_enum: str

@dataclass(frozen=True)
class TypeOption(Type):
    inner_type: Type
    name: str = "Option"

@dataclass(frozen=True)
class TypeResult(Type):
    inner_type: Type
    error_type: Type
    name: str = "Result"

@dataclass(frozen=True)
class TypeReference(Type):
    inner_type: Type
    name: str = "Reference"
    borrowed_name: Optional[str] = None

@dataclass(frozen=True)
class TypePointer(Type):
    inner_type: Type
    name: str = "Pointer"

OBJECT_TYPES: Dict = {
    "Function": TypeFunction,
    "Structure": TypeStructure,
    "Class": TypeClass,
    "Enumerator": TypeEnum,
    "Task": TypeTask,
    "TaskHandle": TypeTaskHandle,
    "Option": TypeOption,
    "Result": TypeResult,
}


@dataclass
class TypeVariable(Type):
    id: int
    bound: Type | None = None

    def resolve(self) -> Type:
        if isinstance(self.bound, TypeVariable):
            return self.bound.resolve()

        return self.bound or self


class MemoryKind(Enum):
    UNIQUE = "UNIQUE"   # Owned, can be moved
    SHARED = "SHARED"   # Reference counted
    REGION = "REGION"   # Arena allocated
    STACK = "STACK"     # Value type

class SymbolState(Enum):
    VALID = "VALID"
    MOVED = "MOVED"
    EXPIRED = "EXPIRED"

@dataclass
class Symbol:
    name: str
    type: Type
    value: Value | None
    mutable: bool
    kind: SymbolKind
    scope_level: int
    memory_kind: MemoryKind = MemoryKind.STACK
    state: SymbolState = SymbolState.VALID
    region: Optional[Any] = None # Will hold RegionNode
    filename: Optional[str] = None
