# import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    LITERAL = "LITERAL"
    OPERATOR = "OPERATOR"
    TYPE = "TYPE"
    UNKNOWN = "UNKNOWN"
    COMMENT = "COMMENT"
    DOC_COMMENT = "DOC_COMMENT"

    VOID = "VOID"
    NOTHING = "NOTHING"
    DEFAULT = "DEFAULT"
    VARIANT = "VARIANT"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    RUNE = "RUNE"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    BYTE = "BYTE"
    BYTES = "BYTES"

    FUNCTION = "FUNCTION"
    STRUCTURE = "STRUCTURE"
    OBJECT = "OBJECT"
    CLASS = "CLASS"
    ENUMERATOR = "ENUMERATOR"
    RAISE = "RAISE"
    CHECK = "CHECK"
    ASSERT = "ASSERT"
    DEFER = "DEFER"
    CASE = "CASE"
    WITH = "WITH"
    TASK = "TASK"
    CHANNEL = "CHANNEL"
    YIELD = "YIELD"
    AWAIT = "AWAIT"

    LIST = "LIST"
    TUPLE = "TUPLE"
    VECTOR = "VECTOR"
    MAP = "MAP"
    SET = "SET"
    ITERATOR = "ITERATOR"
    ITERABLE = "ITERABLE"
    AUTO = "AUTO"

    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"
    LEFT_BRACE = "LEFT_BRACE"
    RIGHT_BRACE = "RIGHT_BRACE"
    LEFT_BRACKET = "LEFT_BRACKET"
    RIGHT_BRACKET = "RIGHT_BRACKET"

    COMMA = "COMMA"
    DOT = "DOT"
    SEMICOLON = "SEMICOLON"

    TYPE_SET = "TYPE_SET"
    TYPE_LET = "TYPE_LET"
    TYPE_CAST = "TYPE_CAST"
    ASSIGNMENT = "ASSIGNMENT"
    RETURN = "RETURN"

    ADDITION = "ADDITION"
    SUBTRACTION = "SUBTRACTION"
    MULTIPLICATION = "MULTIPLICATION"
    DIVISION = "DIVISION"
    MODULO = "MODULO"
    EXPONENTIATION = "EXPONENTIATION"

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    NOR = "NOR"
    NAND = "NAND"
    XNOR = "XNOR"

    BITWISE_AND = "BITWISE_AND"
    BITWISE_OR = "BITWISE_OR"
    BITWISE_NOT = "BITWISE_NOT"
    BITWISE_XOR = "BITWISE_XOR"
    BITWISE_NOR = "BITWISE_NOR"
    BITWISE_NAND = "BITWISE_NAND"
    BITWISE_XNOR = "BITWISE_XNOR"
    BITWISE_MOD = "BITWISE_MOD"
    BITWISE_LEFT_SHIFT = "BITWISE_LEFT_SHIFT"
    BITWISE_RIGHT_SHIFT = "BITWISE_RIGHT_SHIFT"

    AND_EQUAL = "AND_EQUAL"
    OR_EQUAL = "OR_EQUAL"
    XOR_EQUAL = "XOR_EQUAL"
    MOD_EQUAL = "MOD_EQUAL"
    LEFT_SHIFT_EQUAL = "LEFT_SHIFT_EQUAL"
    RIGHT_SHIFT_EQUAL = "RIGHT_SHIFT_EQUAL"

    INCREMENT = "INCREMENT"
    DECREMENT = "DECREMENT"

    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"

    QUOTIENT = "QUOTIENT"
    RANGE = "RANGE"
    RANGE_INCLUSIVE = "RANGE_INCLUSIVE"
    RANGE_INCLUSIVE_END = "RANGE_INCLUSIVE_END"
    RANGE_EXCLUSIVE_END = "RANGE_EXCLUSIVE_END"
    RANGE_FULL_INCLUSIVE = "RANGE_FULL_INCLUSIVE"
    YIELD_ARROW = "YIELD_ARROW"


    NUMBER = "NUMBER"
    TEXT = "TEXT"
    CONTAINER = "CONTAINER"
    COLLECTION = "COLLECTION"

    SCOPE = "SCOPE"
    EXPORT = "EXPORT"
    IS = "IS"
    EXTENDS = "EXTENDS"
    PARENT = "PARENT"
    SELF = "SELF"
    IMPORT = "IMPORT"
    FROM = "FROM"
    AS = "AS"
    EXTERN = "EXTERN"

    CHECK_SYMBOL = "CHECK_SYMBOL"
    RAISE_SYMBOL = "RAISE_SYMBOL"
    ASSERT_SYMBOL = "ASSERT_SYMBOL"

    COALESCE = "COALESCE"
    PIPELINE = "PIPELINE"

    ELLIPSIS = "ELLIPSIS"

    EOF = "EOF"

    ERROR = "ERROR"
    ERROR_UNTERMINATED_STRING = "ERROR_UNTERMINATED_STRING"
    ERROR_UNTERMINATED_STRING_EOF = "ERROR_UNTERMINATED_STRING_EOF"
    ERROR_UNTERMINATED_CHARACTER = "ERROR_UNTERMINATED_CHARACTER"
    ERROR_UNTERMINATED_CHARACTER_EOF = "ERROR_UNTERMINATED_CHARACTER_EOF"
    ERROR_INVALID_NUMBER = "ERROR_INVALID_NUMBER"
    ERROR_INVALID_ASSIGNMENT = "ERROR_INVALID_ASSIGNMENT"
    ERROR_INVALID_ASSIGNMENT_OPERATOR = "ERROR_INVALID_ASSIGNMENT_OPERATOR"
    ERROR_UNEXPECTED_CHARACTER = "ERROR_UNEXPECTED_CHARACTER"
    ERROR_UNEXPECTED_TOKEN = "ERROR_UNEXPECTED_TOKEN"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int | None
    column: int | None
    end_line: int | None = None
    end_column: int | None = None
    message: Optional[str] = None


ERRORS: list = [
    TokenType.ERROR,
    TokenType.ERROR_UNTERMINATED_STRING,
    TokenType.ERROR_UNTERMINATED_STRING_EOF,
    TokenType.ERROR_UNTERMINATED_CHARACTER,
    TokenType.ERROR_UNTERMINATED_CHARACTER_EOF,
    TokenType.ERROR_INVALID_NUMBER,
    TokenType.ERROR_INVALID_ASSIGNMENT,
    TokenType.ERROR_INVALID_ASSIGNMENT_OPERATOR,
    TokenType.ERROR_UNEXPECTED_CHARACTER,
    TokenType.ERROR_UNEXPECTED_TOKEN,
]

KEYWORDS: list = [
    "do",
    "for",
    "while",
    "until",
    "when",
    "break",
    "continue",
    "in",
    "let",
    "set",
    "function",
    "class",
    "structure",
    "type",
    "return",
    "enumerator",
    "auto",
    "import",
    "from",
    "extends",
    "parent",
    "self",
    "scope",
    "raise",
    "check",
    "assert",
    "defer",
    "object",
    "case",
    "with",
    "scope",
    "export",
    "is",
    "extend",
    "extends",
    "import",
    "use",  # alias for import (migration path toward preferred surface)
    "from",
    "as",
    "task",
    "yield",
    "await",
    "before",
    "after",
    "source",
    "target",
    "owned",
    "borrowed",
    "extern",
]

TYPES: list = [
    "Variant",
    "Void",
    "Nothing",
    "Default",
    "Boolean",
    "Byte",
    "Bytes",
    "Rune",
    "Integer",
    "Decimal",
    "String",
    "List",
    "Set",
    "Vector",
    "Tuple",
    "Map",
    "Structure",
    "Object",
    "Class",
    "Enumerator",
    "Function",
    "Task",
    "Channel",
    "Error",
    "Option",
    "Result",
    "Iterator",
    "Iterable",
    "Number",
    "Text",
    "Collection",
    "Container",
]

TYPE_TOKENS: list = [
    TokenType.VARIANT,
    TokenType.VOID,
    TokenType.NOTHING,
    TokenType.DEFAULT,
    TokenType.BOOLEAN,
    TokenType.BYTE,
    TokenType.BYTES,
    TokenType.RUNE,
    TokenType.INTEGER,
    TokenType.DECIMAL,
    TokenType.STRING,
    TokenType.LIST,
    TokenType.SET,
    TokenType.VECTOR,
    TokenType.TUPLE,
    TokenType.MAP,
    TokenType.STRUCTURE,
    TokenType.OBJECT,
    TokenType.CLASS,
    TokenType.ENUMERATOR,
    TokenType.FUNCTION,
    TokenType.TASK,
    TokenType.CHANNEL,
    TokenType.ITERATOR,
    TokenType.ITERABLE,
    TokenType.AUTO,
    TokenType.NUMBER,
    TokenType.TEXT,
    TokenType.COLLECTION,
    TokenType.CONTAINER,
]

ASSIGNMENTS: dict = {
    "->": TokenType.ASSIGNMENT,
    "<-": TokenType.RETURN,
    "<~": TokenType.YIELD_ARROW,
    ":": TokenType.TYPE_SET,
    ":>": TokenType.TYPE_LET,
    "<:": TokenType.TYPE_CAST,
    "?": TokenType.CHECK_SYMBOL,
    "^": TokenType.RAISE_SYMBOL,
    "!": TokenType.ASSERT_SYMBOL,
    "&=": TokenType.AND_EQUAL,
    "|=": TokenType.OR_EQUAL,
    "^=": TokenType.XOR_EQUAL,
    "%=": TokenType.MOD_EQUAL,
    "<<=": TokenType.LEFT_SHIFT_EQUAL,
    ">>=": TokenType.RIGHT_SHIFT_EQUAL,
}

LITERALS: dict = {
    "True": TokenType.BOOLEAN,
    "False": TokenType.BOOLEAN,
    "Nothing": TokenType.NOTHING,
    "Default": TokenType.DEFAULT,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    "nothing": TokenType.NOTHING, # DEPRECATED: use Nothing
    "default": TokenType.DEFAULT, # DEPRECATED: use Default
}

OPERATORS: dict = {
    "+": TokenType.ADDITION,
    "-": TokenType.SUBTRACTION,
    "*": TokenType.MULTIPLICATION,
    "/": TokenType.DIVISION,
    "%": TokenType.MODULO,
    "**": TokenType.EXPONENTIATION,
    "++": TokenType.INCREMENT,
    "--": TokenType.DECREMENT,
    "&&": TokenType.BITWISE_AND,
    "||": TokenType.BITWISE_OR,
    "!!": TokenType.BITWISE_NOT,
    "^^": TokenType.BITWISE_XOR,
    "!|": TokenType.BITWISE_NOR,
    "!&": TokenType.BITWISE_NAND,
    "!^": TokenType.BITWISE_XNOR,
    "%%": TokenType.BITWISE_MOD,
    "<<": TokenType.BITWISE_LEFT_SHIFT,
    ">>": TokenType.BITWISE_RIGHT_SHIFT,
    "&": TokenType.BITWISE_AND,
    "|": TokenType.BITWISE_OR,
    "~": TokenType.BITWISE_NOT,
    "//": TokenType.QUOTIENT,
    "??": TokenType.COALESCE,
    "|>": TokenType.PIPELINE,
}

COMPARATORS: dict = {
    "=": TokenType.EQUAL,
    "==": TokenType.EQUAL,
    "!=": TokenType.NOT_EQUAL,
    ">": TokenType.GREATER_THAN,
    "<": TokenType.LESS_THAN,
    ">=": TokenType.GREATER_THAN_OR_EQUAL,
    "<=": TokenType.LESS_THAN_OR_EQUAL,
}

LOGICALS: dict = {
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "xor": TokenType.XOR,
    "nor": TokenType.NOR,
    "nand": TokenType.NAND,
    "xnor": TokenType.XNOR,
}

BRACKETS: dict = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    "[": TokenType.LEFT_BRACKET,
    "]": TokenType.RIGHT_BRACKET,
}

IDENTIFIER_MAP: dict = {}
for _t in TYPES:
    IDENTIFIER_MAP[_t] = TokenType.TYPE
for _k in KEYWORDS:
    IDENTIFIER_MAP[_k] = TokenType.KEYWORD
IDENTIFIER_MAP["extern"] = TokenType.EXTERN
for _k, _v in LOGICALS.items():
    IDENTIFIER_MAP[_k] = _v
for _k, _v in LITERALS.items():
    IDENTIFIER_MAP[_k] = _v
for _k, _v in ASSIGNMENTS.items():
    if _k.isalpha() or "_" in _k:
        IDENTIFIER_MAP[_k] = _v
