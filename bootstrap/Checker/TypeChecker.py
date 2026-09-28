from typing import Optional, List, Dict, Any
from Checker.Scope import ScopeManager
from Checker.Type import (
    Symbol,
    SymbolKind,
    SymbolOrigin,
    Type,
    TypeBoolean,
    TypeEnum,
    TypeEnumVariant,
    TypeClass,
    TypeDecimal,
    TypeEnumerator,
    TypeFunction,
    TypeInteger,
    TypeList,
    TypeRune,
    TypeString,
    TypeStructure,
    TypeVariable,
    TypeVariant,
    TypeVoid,
    TypeNothing,
    TypeDefault,
    TypeVector,
    TypeSet,
    TypeMap,
    TypeTuple,
    TypeElement,
    TypeByte,
    TypeNumber,
    TypeText,
    TypeCollection,
    TypeContainer,
    PRIMITIVE_TYPES,
)
from Lexer.Token import COMPARATORS, OPERATORS
from Logging import Printer
from Logging.TypeCheckerLogger import TypeCheckerLogger
from Parser.AST import (
    AssignmentStatement,
    ASTNode,
    BinaryOperation,
    BlockExpression,
    BlockStatement,
    BooleanLiteral,
    BreakStatement,
    CallExpression,
    ContinueStatement,
    DecimalLiteral,
    DefaultLiteral,
    DoStatement,
    EnumeratorStatement,
    EnumVariant,
    ExpressionStatement,
    FromImportStatement,
    FunctionExpression,

    FunctionStatement,
    ClassStatement,
    Identifier,
    ImportStatement,
    IndexExpression,
    SliceExpression,
    IndexReassignmentStatement,
    IntegerLiteral,
    IteratorLiteral,
    ListLiteral,
    MemberExpression,
    MemberReassignmentStatement,
    Program,
    ReassignmentStatement,
    ReturnStatement,
    RuneLiteral,
    Scope,
    ScopeStatement,
    Statements,
    StringLiteral,
    StructureExpression,
    StructureStatement,
    UnaryOperation,
    VariantLiteral,
    WhenExpression,
    WhenInlineExpression,
    WhenStatement,
    VoidLiteral,
    NothingLiteral,
    ObjectStatement,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    CheckExpression,
    BlockStatement,
    VectorLiteral,
    DictionaryLiteral,
    MapLiteral,
    SetLiteral,
    TupleLiteral,
    ExportStatement,
    WithStatement,
    InExpression,
    IsExpression,
    Pattern,
    LiteralPattern,
    IdentifierPattern,
    ListPattern,
    MapPattern,
    IsMatchPattern,
    VariantPattern,
    WildcardPattern,
    CaseBranch,
)


def TypePrimitive(name: str) -> Type:
    if name in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[name]()
    return TypeVariant



from Checker.Handlers.ExpressionHandler import ExpressionHandler
from Checker.Handlers.StatementHandler import StatementHandler
from Checker.Handlers.PatternHandler import PatternHandler
from Checker.Handlers.LiteralHandler import LiteralHandler

class TypeChecker(ExpressionHandler, StatementHandler, PatternHandler, LiteralHandler):
    def __init__(
        self,
        AST: Statements,
        source_path: str,
        strict: bool = False,
        debug: bool = False,
        recover: bool = False,
    ) -> None:
        if debug:
            print("\n" + "!"*40 + "\nTYPECHECKER __INIT__\n" + "!"*40 + "\n", flush=True)
        self.debugging: bool = debug
        self.strict: bool = strict
        self.recover: bool = recover  # When True: collect all errors without stopping on first
        # Declare all functions first so later siblings (e.g. Lexer._read_doc)
        # resolve when an earlier function body is checked.
        self.defer_function_bodies: bool = True
        self.deferred_functions: list = []

        self.source_path: str = source_path
        self.AST: Statements = AST
        self.scope: ScopeManager = ScopeManager()
        self.current_class = None # Context for methods

        self.typevariable_counter: int = 0

        self.has_extern: bool = False
        self._register_builtins()

        self.logger: TypeCheckerLogger = TypeCheckerLogger(source_path)

    ## Scopes

    def _register_builtins(self) -> None:
        self.scope.define(
            Symbol(
                "print",
                TypeFunction("print", None, TypeVoid()),
                None,
                True,
                SymbolKind.FUNCTION,
                0,
            )
        )
        self.scope.define(
            Symbol(
                "write",
                TypeFunction("write", None, TypeVoid()),
                None,
                True,
                SymbolKind.FUNCTION,
                0,
            )
        )
        
        # Built-in capabilities
        self.scope.define(Symbol("__builtin", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_io", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("IO", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("io", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_output", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_input", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("stdout", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("stderr", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("stdin", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("args", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("env", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("writeln", TypeVariant(), None, False, SymbolKind.FUNCTION, 1))
        self.scope.define(Symbol("read", TypeVariant(), None, False, SymbolKind.FUNCTION, 0))
        self.scope.define(Symbol("readln", TypeVariant(), None, False, SymbolKind.FUNCTION, 0))
        self.scope.define(Symbol("type", TypeString(), None, False, SymbolKind.FUNCTION, 1))

        # Built-in Enums
        self.scope.define(Symbol("Result", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Option", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Some", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Nothing", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Ok", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Error", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_file", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("file", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_sys", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("sys", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_time", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("time", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_process", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("process", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_dictionary", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_string", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_list", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_map", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_set", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_range", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_error", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_reflect", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_net", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_vm", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("vm", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("VM", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_ffi", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("ffi", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))

        # Concurrency primitives
        self.scope.define(Symbol("__builtin_concurrency", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("concurrency", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_channel", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_task", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("channel", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("spawn", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("spawn_blocking", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("sleep", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("poll_fd", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Task", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Channel", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))

        # Internal compiler structures
        self.scope.define(Symbol("__builtin_memory", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_math", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_regex", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("math", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_term", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_random", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_json", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("json", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_string", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("string", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))

        self.scope.define(Symbol("__builtin_memory", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("Memory", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_ast", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("ast", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))

    def print_ast(self, as_json: bool = False) -> None:
        Printer.print_data(self.AST, as_json, "TYPE CHECKER AST")

    def new_typevariable(self):
        typevariable: TypeVariable = TypeVariable(id=self.typevariable_counter)
        self.typevariable_counter += 1

        self.logger.debug("new typevariable", typevariable)
        return typevariable

    def occurs_check(self, type_variable: TypeVariable, type: Type) -> bool:
        if type is type_variable:
            return True

        if isinstance(type, TypeVariable) and type.bound is not None:
            return self.occurs_check(type_variable, type.bound)

        # Add structural checks for FunctionType, StructType if you implement them:
        # e.g. if isinstance(typ, FunctionType):
        #         for p in typ.param_types: if occurs_check(tv, p): return True
        #         return occurs_check(tv, typ.return_type)
        return False

    def check_program(self, AST=None):
        from Logging.Trace import zen_trace
        if AST is None: AST = self.AST
        zen_trace(f"TYPECHECKER STARTING on {len(AST.statements)} statements")
        self.logger.debug("check_program")

        if AST is None:
            AST = self.AST

        if self.debugging:
            print("First Pass!")

        if self.recover:
            # Recovery mode: check every statement independently so all errors surface.
            for statement in AST.statements:
                try:
                    self.check_statement(statement)
                except Exception as error:
                    if self.debugging:
                        import traceback
                        traceback.print_exc()
                    if self.strict:
                        raise
                    # Error already appended to self.logger by the raising handler;
                    # if not (e.g. bare raise), log it now.
                    if not self.logger.has_errors:
                        self.logger.error(str(error))
            try:
                self._flush_deferred_functions()
            except Exception as error:
                if self.debugging:
                    import traceback
                    traceback.print_exc()
                if self.strict:
                    raise
                if not self.logger.has_errors:
                    self.logger.error(str(error))
        else:
            try:
                for statement in AST.statements:
                    self.check_statement(statement)
                self._flush_deferred_functions()
            except Exception as error:
                if self.debugging:
                    import traceback
                    traceback.print_exc()
                if self.strict:
                    raise error
                # Errors already logged via self.logger; let the caller (Zen.py) print and exit.

        self.scope.current_scope = self.scope.global_scope
        AST.scope = self.scope

        return AST

    def _get_literal_class_for_type(self, node_type: str):
        from Parser.AST import (
            IntegerLiteral,
            BooleanLiteral,
            DecimalLiteral,
            RuneLiteral,
            StringLiteral,
            NothingLiteral,
        )
        return {
            "IntegerLiteral": IntegerLiteral,
            "BooleanLiteral": BooleanLiteral,
            "DecimalLiteral": DecimalLiteral,
            "RuneLiteral": RuneLiteral,
            "StringLiteral": StringLiteral,
            "NothingLiteral": NothingLiteral,
        }.get(node_type)

    def _flush_deferred_functions(self):
        while self.deferred_functions:
            batch = self.deferred_functions
            self.deferred_functions = []
            for item in batch:
                if self.recover:
                    try:
                        self._check_deferred_function(item)
                    except Exception as error:
                        if self.debugging:
                            import traceback
                            traceback.print_exc()
                        if self.strict:
                            raise
                        if not self.logger.has_errors:
                            self.logger.error(str(error))
                else:
                    self._check_deferred_function(item)

    def _check_deferred_function(self, item):
        (
            statement,
            source_path,
            current_class,
            symbol,
            enclosing_scope,
            enclosing_level,
            enclosing_region,
        ) = item

        saved_path = self.source_path
        saved_class = self.current_class
        saved_scope = self.scope.current_scope
        saved_level = self.scope.level
        saved_region = self.scope.current_region

        self.source_path = source_path
        self.current_class = current_class
        self.scope.current_scope = enclosing_scope
        self.scope.level = enclosing_level
        self.scope.current_region = enclosing_region

        from Parser.AST import TaskStatement
        region_prefix = "task" if isinstance(statement, TaskStatement) else "func"
        self.scope.push(region_id=f"{region_prefix}_{statement.name}")

        if self.current_class:
            self.scope.define(
                Symbol(
                    "self",
                    self.current_class,
                    None,
                    False,
                    SymbolKind.VARIABLE,
                    statement.scope_level,
                )
            )

        for parameter in statement.parameters:
            parameter_type = getattr(parameter, "declared_type", None)
            if parameter_type is None:
                parameter_type = self.new_typevariable()
            self.scope.define(
                Symbol(
                    parameter.name,
                    parameter_type,
                    getattr(parameter, "value", None),
                    True,
                    SymbolKind.PARAMETER,
                    self.scope.get_current_level(),
                )
            )

        result_type = self.check_block_statement(statement.body)
        self.scope.pop()

        symbol.resolved_type = result_type
        if hasattr(symbol, "type") and symbol.type is not None:
            try:
                new_func_type = type(symbol.type)(
                    symbol.type.name,
                    symbol.type.parameters,
                    result_type,
                )
                symbol.type = new_func_type
                statement.resolved_type = new_func_type
            except Exception:
                statement.resolved_type = result_type

        self.source_path = saved_path
        self.current_class = saved_class
        self.scope.current_scope = saved_scope
        self.scope.level = saved_level
        self.scope.current_region = saved_region

    ## Check Statements

    def check_statement(self, statement: ASTNode):
        from Logging.Trace import zen_trace
        zen_trace(f"check_statement: {type(statement).__name__} at line {getattr(statement, 'line', '?')}")
        # self.logger.debug("check_statement", statement)
        
        if isinstance(statement, AssignmentStatement):
            return self.check_assignment_statement(statement)

        elif isinstance(statement, ReassignmentStatement):
            return self.check_reassignment_statement(statement)

        elif isinstance(statement, ExpressionStatement):
            return self.check_expression(statement.expression)

        elif isinstance(statement, FunctionStatement):
            return self.check_function_statement(statement)

        elif isinstance(statement, BlockStatement):
            return self.check_block_statement(statement)

        elif isinstance(statement, ReturnStatement):
            return self.check_return_statement(statement)



        elif isinstance(statement, ClassStatement):
            return self.check_class_statement(statement)

        elif isinstance(statement, StructureStatement):
            return self.check_structure_statement(statement)

        elif isinstance(statement, EnumeratorStatement):
            return self.check_enumerator_statement(statement)

        elif isinstance(statement, ScopeStatement):
            return self.check_scope_statement(statement)

        elif isinstance(statement, MemberReassignmentStatement):
            return self.check_member_reassignment_statement(statement)

        elif isinstance(statement, WhenStatement):
            return self.check_when_statement(statement)

        elif isinstance(statement, IndexReassignmentStatement):
            return self.check_index_reassignment_statement(statement)

        elif isinstance(statement, ImportStatement):
            return self.check_import_statement(statement)

        elif isinstance(statement, FromImportStatement):
            return self.check_from_import_statement(statement)


        elif isinstance(statement, DoStatement):
            return self.check_do_statement(statement)

        elif isinstance(statement, BreakStatement):
            return self.check_break_statement(statement)
        elif isinstance(statement, ContinueStatement):
            return self.check_continue_statement(statement)

        elif isinstance(statement, ObjectStatement):
            return self.check_object_statement(statement)

        elif isinstance(statement, ExportStatement):
            return self.check_export_statement(statement)

        elif isinstance(statement, DeferStatement):
            return self.check_defer_statement(statement)

        elif isinstance(statement, WithStatement):
            return self.check_with_statement(statement)

        elif isinstance(statement, RaiseStatement):
            return self.check_raise_statement(statement)

        elif isinstance(statement, AssertStatement):
            return self.check_assert_statement(statement)

        elif isinstance(statement, CheckStatement):
            return self.check_check_statement(statement)

        elif isinstance(statement, BlockExpression):
            return self.check_block_expression(statement)

        elif isinstance(statement, CheckExpression):
            return self.check_check_expression(statement)

        else:
            raise self.logger.error("unknown statement type", statement)



    ## Statements
























    ## Check Expressions

    def check_expression(self, expression: ASTNode) -> Type:
        self.logger.debug("check_expression", expression)

        if isinstance(expression, InExpression):
            return self.check_in_expression(expression)

        if isinstance(expression, WhenExpression):
            return self.check_when_expression(expression)

        elif isinstance(expression, WhenInlineExpression):
            return self.check_when_inline_expression(expression)

        elif isinstance(expression, FunctionExpression):
            return self.check_function_expression(expression)

        elif isinstance(expression, BlockExpression):
            return self.check_block_expression(expression)

        elif isinstance(expression, CallExpression):
            return self.check_call_expression(expression)

        elif isinstance(expression, MemberExpression):
            return self.check_member_expression(expression)

        elif isinstance(expression, IndexExpression):
            return self.check_index_expression(expression)

        elif isinstance(expression, SliceExpression):
            return self.check_slice_expression(expression)

        elif isinstance(expression, Identifier):
            return self.check_identifier(expression)

        elif isinstance(expression, BinaryOperation):
            return self.check_binary_operation(expression)

        elif isinstance(expression, CheckExpression):
            return self.check_check_expression(expression)

        elif isinstance(expression, IsExpression):
            return self.check_is_expression(expression)

        elif isinstance(expression, UnaryOperation):
            return self.check_unary_operation(expression)

        elif isinstance(expression, AssignmentStatement):
            return self.check_assignment_statement(expression)

        elif isinstance(expression, ReassignmentStatement):
            return self.check_reassignment_statement(expression)

        elif isinstance(expression, IntegerLiteral):
            expression.resolved_type = TypeInteger()
            return expression.resolved_type

        elif isinstance(expression, DecimalLiteral):
            expression.resolved_type = TypeDecimal()
            return expression.resolved_type

        elif isinstance(expression, StringLiteral):
            expression.resolved_type = TypeString()
            return expression.resolved_type

        elif isinstance(expression, RuneLiteral):
            expression.resolved_type = TypeRune()
            return expression.resolved_type

        elif isinstance(expression, NothingLiteral):
            expression.resolved_type = TypeNothing()
            return expression.resolved_type

        elif isinstance(expression, DefaultLiteral):
            return self._check_default_literal(expression)

        elif isinstance(expression, VoidLiteral):
            expression.resolved_type = TypeVoid()
            return expression.resolved_type

        elif isinstance(expression, BooleanLiteral):
            expression.resolved_type = TypeBoolean()
            return expression.resolved_type

        elif isinstance(expression, VariantLiteral):
            expression.resolved_type = TypeVariant()
            return expression.resolved_type

        elif isinstance(expression, ListLiteral):
            return self.check_list_literal(expression)

        elif isinstance(expression, MemberReassignmentStatement):
            return self.check_member_reassignment_statement(expression)

        elif isinstance(expression, StructureExpression):
            return self.check_structure_expression(expression)

        elif isinstance(expression, VectorLiteral):
            return self.check_vector_literal(expression)

        elif isinstance(expression, DictionaryLiteral):
            return self.check_dictionary_literal(expression)

        elif isinstance(expression, MapLiteral):
            return self.check_map_literal(expression)

        elif isinstance(expression, SetLiteral):
            return self.check_set_literal(expression)

        elif isinstance(expression, TupleLiteral):
            return self.check_tuple_literal(expression)

        return None



    ## Expressions





        




        



    def unify(
        self, a: Type, b: Type, attachment: any = None, variant_fallback: bool = True
    ) -> Type:
        # self.logger.debug("unify", (a, b))

        # DEBUG
        # print(f"UNIFY CHECK: {a} vs {b}")
        
        if a is None:
            return b
        if b is None:
            return a

        # Handle direct equality or exact match
        if a == b:
            return a

        # Type variables bidirectional binding
        if isinstance(a, TypeVariable):
            if a is b:
                return a
            if a.bound is not None:
                return self.unify(a.bound, b, attachment)

            if self.occurs_check(a, b):
                raise self.logger.error_type_unification(a, b, attachment)

            a.bound = b
            return b

        if isinstance(b, TypeVariable):
            if a is b:
                return b
            return self.unify(b, a, attachment)

        # Handle Default literal zero-value materialization
        if isinstance(a, TypeDefault) and b is not None and not isinstance(b, (TypeDefault, TypeVariant)):
            # Find the DefaultLiteral node via attachment
            node_to_materialize = None
            if attachment is not None:
                from Parser.AST import DefaultLiteral
                if isinstance(attachment, DefaultLiteral):
                    node_to_materialize = attachment
                elif hasattr(attachment, "value") and isinstance(attachment.value, DefaultLiteral):
                    node_to_materialize = attachment.value
                elif hasattr(attachment, "expression") and isinstance(attachment.expression, DefaultLiteral):
                    node_to_materialize = attachment.expression
                elif hasattr(attachment, "left") and isinstance(attachment.left, DefaultLiteral):
                    node_to_materialize = attachment.left
                elif hasattr(attachment, "right") and isinstance(attachment.right, DefaultLiteral):
                    node_to_materialize = attachment.right
            
            if node_to_materialize is not None:
                # Materialize the correct zero value in the AST
                if isinstance(b, TypeInteger):
                    node_to_materialize.node_type = "IntegerLiteral"
                    node_to_materialize.value = 0
                elif isinstance(b, TypeBoolean):
                    node_to_materialize.node_type = "BooleanLiteral"
                    node_to_materialize.value = False
                elif isinstance(b, TypeDecimal):
                    node_to_materialize.node_type = "DecimalLiteral"
                    node_to_materialize.value = 0.0
                elif isinstance(b, TypeRune):
                    node_to_materialize.node_type = "RuneLiteral"
                    node_to_materialize.value = ""
                elif isinstance(b, TypeString):
                    node_to_materialize.node_type = "StringLiteral"
                    node_to_materialize.value = ""
                elif isinstance(b, TypeList):
                    node_to_materialize.node_type = "ListLiteral"
                    node_to_materialize.elements = []
                elif isinstance(b, TypeMap):
                    node_to_materialize.node_type = "MapLiteral"
                    node_to_materialize.elements = []
                elif isinstance(b, TypeSet):
                    node_to_materialize.node_type = "SetLiteral"
                    node_to_materialize.elements = []
                elif isinstance(b, TypeVector):
                    node_to_materialize.node_type = "VectorLiteral"
                    node_to_materialize.elements = []
                elif isinstance(b, TypeTuple):
                    node_to_materialize.node_type = "TupleLiteral"
                    node_to_materialize.elements = []
                
                cls = self._get_literal_class_for_type(node_to_materialize.node_type)
                if cls is not None:
                    node_to_materialize.__class__ = cls
                node_to_materialize.resolved_type = b
            return b

        if isinstance(b, TypeDefault) and a is not None and not isinstance(a, (TypeDefault, TypeVariant)):
            return self.unify(b, a, attachment)

        # Void unification (used in optional returns or empty blocks)
        # Check instance or class equality
        if isinstance(a, TypeVoid):
            return b
        if isinstance(b, TypeVoid):
            return a

        # Variant unifies with anything by preferring the specific type
        if isinstance(a, TypeVariant) and not isinstance(b, TypeVariant):
             return b
        if isinstance(b, TypeVariant) and not isinstance(a, TypeVariant):
             return a
        if isinstance(a, TypeVariant) and isinstance(b, TypeVariant):
             return TypeVariant()

        # Numeric promotion (Integer vs Decimal)
        # Use isinstance check
        is_a_int = isinstance(a, TypeInteger)
        is_b_int = isinstance(b, TypeInteger)
        is_a_dec = isinstance(a, TypeDecimal)
        is_b_dec = isinstance(b, TypeDecimal)

        if (is_a_int and is_b_dec) or (is_a_dec and is_b_int):
            return TypeDecimal()

        # String/Character promotion
        is_a_str = isinstance(a, TypeString)
        is_b_str = isinstance(b, TypeString)
        is_a_rune = isinstance(a, TypeRune)
        is_b_rune = isinstance(b, TypeRune)

        if (is_a_str and is_b_rune) or (is_a_rune and is_b_str):
            return TypeString()

        # Boolean unification (boolean-only)
        if isinstance(a, TypeBoolean) and isinstance(b, TypeBoolean):
            return TypeBoolean()

        # Abstract Type unification
        if isinstance(a, TypeNumber) or isinstance(b, TypeNumber):
            target = b if isinstance(a, TypeNumber) else a
            if isinstance(target, (TypeNumber, TypeInteger, TypeDecimal, TypeByte)):
                return target
            if variant_fallback:
                return TypeVariant()
            raise self.logger.error_type_unification(a, b, attachment)

        if isinstance(a, TypeText) or isinstance(b, TypeText):
            target = b if isinstance(a, TypeText) else a
            if isinstance(target, (TypeText, TypeString, TypeRune)):
                return target
            if variant_fallback:
                return TypeVariant()
            raise self.logger.error_type_unification(a, b, attachment)

        if isinstance(a, TypeCollection) or isinstance(b, TypeCollection):
            target = b if isinstance(a, TypeCollection) else a
            if isinstance(target, (TypeCollection, TypeList, TypeVector, TypeSet, TypeMap, TypeTuple)):
                return target
            if variant_fallback:
                return TypeVariant()
            raise self.logger.error_type_unification(a, b, attachment)

        if isinstance(a, TypeContainer) or isinstance(b, TypeContainer):
            target = b if isinstance(a, TypeContainer) else a
            if isinstance(target, (TypeContainer, TypeStructure, TypeClass, TypeEnumerator, TypeEnum, TypeEnumVariant, TypeMap)):
                return target
            if variant_fallback:
                return TypeVariant()
            raise self.logger.error_type_unification(a, b, attachment)

        # Parameterized Collection Unification
        if isinstance(a, TypeList) and isinstance(b, TypeList):
            if not a.elements and not b.elements:
                return TypeList(None, [])
            if not a.elements:
                return b
            if not b.elements:
                return a
            unified_elem = self.unify(a.elements[0].type, b.elements[0].type, attachment, variant_fallback=variant_fallback)
            return TypeList(None, [TypeElement(None, unified_elem)])

        if isinstance(a, TypeSet) and isinstance(b, TypeSet):
            unified_elem = self.unify(a.element_type, b.element_type, attachment, variant_fallback=variant_fallback)
            return TypeSet(None, unified_elem)

        if isinstance(a, TypeMap) and isinstance(b, TypeMap):
            unified_key = self.unify(a.key_type, b.key_type, attachment, variant_fallback=variant_fallback)
            unified_val = self.unify(a.value_type, b.value_type, attachment, variant_fallback=variant_fallback)
            return TypeMap(None, unified_key, unified_val)

        if isinstance(a, TypeVector) and isinstance(b, TypeVector):
            if a.size != 0 and b.size != 0 and a.size != b.size:
                raise self.logger.error_type_unification(a, b, attachment)
            size = a.size if a.size != 0 else b.size
            unified_elem = self.unify(a.element_type, b.element_type, attachment, variant_fallback=variant_fallback)
            return TypeVector(None, unified_elem, size)

        if isinstance(a, TypeTuple) and isinstance(b, TypeTuple):
            if not a.elements:
                return b
            if not b.elements:
                return a
            if len(a.elements) != len(b.elements):
                raise self.logger.error_type_unification(a, b, attachment)
            unified_elements = []
            for ea, eb in zip(a.elements, b.elements):
                u_type = self.unify(ea.type, eb.type, attachment, variant_fallback=variant_fallback)
                unified_elements.append(TypeElement(ea.name or eb.name, u_type))
            return TypeTuple(None, unified_elements)

        # Optional lenient fallback
        if variant_fallback:
            # self.logger.debug(
            #     f"Unify fallback: incompatible types {a} and {b}, returning Variant"
            # )
            return TypeVariant()

        # TODO: add FunctionType/StructType structural checks here

        raise self.logger.error_type_unification(a, b, attachment)






