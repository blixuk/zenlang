from typing import Optional, List, Dict, Any
from Checker.Scope import ScopeManager
from Checker.Type import (
    Symbol,
    SymbolKind,
    SymbolOrigin,
    Type,
    TypeBoolean,
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
    TypeVector,
    TypeSet,
    TypeMap,
    TypeTuple,
    TypeElement,
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
    DoStatement,
    EnumeratorStatement,
    ExpressionStatement,
    FromImportStatement,
    FunctionExpression,

    FunctionStatement,
    ClassStatement,
    Identifier,
    ImportStatement,
    IndexExpression,
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
    SetLiteral,
    TupleLiteral,
    ExportStatement,
)


def TypePrimitive(name: str) -> Type:
    if name in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[name]()
    return TypeVariant


class TypeChecker:
    def __init__(
        self,
        AST: Statements,
        source_path: str,
        strict: bool = False,
        debug: bool = False,
    ) -> None:
        self.debugging: bool = debug
        self.strict: bool = strict

        self.source_path: str = source_path
        self.AST: Statements = AST
        self.scope: ScopeManager = ScopeManager()
        self.current_class = None # Context for methods

        self.typevariable_counter: int = 0

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
        
        # Built-in capabilities
        self.scope.define(Symbol("__builtin_output", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("__builtin_input", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_file", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("file", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_sys", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("sys", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        
        self.scope.define(Symbol("__builtin_string", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))
        self.scope.define(Symbol("string", TypeVariant(), None, False, SymbolKind.VARIABLE, 0))

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
        self.logger.debug("check_program")

        if AST is None:
            AST = self.AST

        try:
            print("First Pass!")
            for statement in AST.statements:
                self.check_statement(statement)
        except Exception as error:
            import traceback
            traceback.print_exc()
            self.logger.print_errors()

            if self.strict:
                raise error

        self.scope.current_scope = self.scope.global_scope
        AST.scope = self.scope

        return AST

    ## Check Statements

    def check_statement(self, statement: ASTNode):
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
            print(f"DEBUG: Found StructureStatement {statement.name}")
            return self.check_structure_statement(statement)

        elif isinstance(statement, EnumeratorStatement):
            return self.check_enumerator_statement(statement)

        elif isinstance(statement, ScopeStatement):
            return self.check_scope_statement(statement)

        elif isinstance(statement, MemberReassignmentStatement):
            return self.check_member_reassignment_statement(statement)

        elif isinstance(statement, WhenStatement):
            return self.check_when_statement(statement)

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

    def check_break_statement(self, statement: BreakStatement) -> Type:
        return PRIMITIVE_TYPES["Void"]()

    def check_continue_statement(self, statement: ContinueStatement) -> Type:
        return PRIMITIVE_TYPES["Void"]()

    ## Statements

    def check_assignment_statement(self, statement: AssignmentStatement):
        self.logger.debug("check_assignment_statement", statement)
        
        declared_type: Type | None = None
        
        if statement.declared_type:
             if isinstance(statement.declared_type, str):
                  type_name = statement.declared_type
             else:
                  type_name = getattr(statement.declared_type, "name", None)
             if type_name:
                 # Check Primitives
                 if type_name in PRIMITIVE_TYPES:
                     # Instantiate the type (e.g. TypeString())
                     declared_type = PRIMITIVE_TYPES[type_name]()
                 else:
                     # Check Symbol Table (Class, Struct, Enum)
                     symbol = self.scope.lookup(type_name)
                     if symbol:
                         declared_type = symbol.type
                     else:
                         # Fallback/Error
                         print(f"[TypeChecker] Warning: Type '{type_name}' not resolved.")
                         declared_type = self.new_typevariable()
        
        #     declared_type = self.new_typevariable()
        
        value_type: Type = (
            self.check_expression(statement.value)
            if statement.value is not None
            else self.new_typevariable()
        )

        if declared_type is None:
            declared_type = value_type

        # if declared_type is None:
        #    declared_type = TypeVariant # Explicitly set to Variant instead of typevariable for now to match symptoms
        #    # declared_type = self.new_typevariable()

        resolved_type: Type = self.unify(declared_type, value_type)

        kind: SymbolKind = (
            SymbolKind.VARIABLE if statement.mutable else SymbolKind.CONSTANT
        )

        symbol: Symbol = Symbol(
            statement.name,
            resolved_type,
            statement.value,
            statement.mutable,
            kind,
            statement.scope_level,
        )

        self.scope.define(symbol)

        statement.resolved_type = resolved_type

        return resolved_type

    def check_reassignment_statement(self, statement: ReassignmentStatement):
        self.logger.debug("check_reassignment_statement", statement)

        symbol: Symbol = self.scope.lookup(statement.name)

        if not symbol:
            raise self.logger.error_variable_undefined(statement)

        elif not symbol.mutable:
            raise self.logger.error_variable_immutable(statement)

        else:
            declared_type: Type = (
                symbol.type if symbol.type else self.new_typevariable()
            )

            value_type: Type = self.check_expression(statement.value)

            resolved_type: Type = self.unify(declared_type, value_type, statement)

            symbol.type = resolved_type

            statement.resolved_type = resolved_type

    def check_function_statement(self, statement: FunctionStatement):
        self.logger.debug("check_function_statement", statement)

        symbol: Symbol = Symbol(
            statement.name,
            TypeFunction(statement.name, statement.parameters, statement.return_type),
            None,
            True,
            SymbolKind.FUNCTION,
            statement.scope_level,
        )

        try:
            self.scope.define(symbol)
        except Exception as e:
            if "redeclaration" in str(e) and statement.scope_level == 0:
                 pass # Ignore global redeclarations for bootstrap
            else:
                 raise e

        self.scope.push(region_id=f"func_{statement.name}")
    
        # Define 'self' if in class context
        if self.current_class:
            self_symbol = Symbol(
                "self",
                self.current_class,
                None,
                False, # self is usually immutable pointer
                SymbolKind.VARIABLE, # or PARAMETER
                statement.scope_level
            )
            self.scope.define(self_symbol)

        for parameter in statement.parameters:
            
            p_type_name = parameter.declared_type if hasattr(parameter, 'declared_type') else None
            # If it's a TypeLiteral object, get name.
            if hasattr(p_type_name, 'name'):
                 p_type_name = p_type_name.name
            
            parameter_type: Type | None = None
            if p_type_name:
                 if p_type_name in PRIMITIVE_TYPES:
                     parameter_type = PRIMITIVE_TYPES[p_type_name]()
                 else:
                     sym = self.scope.lookup(p_type_name)
                     if sym:
                         parameter_type = sym.type
            
            if parameter_type is None:
                 parameter_type = self.new_typevariable()
            
            # Update AST node
            parameter.declared_type = parameter_type

            symbol_parameter: Symbol = Symbol(
                parameter.name,
                parameter_type,
                parameter.value,
                True,
                SymbolKind.PARAMETER,
                statement.scope_level,
            )

            self.scope.define(symbol_parameter)

        result_type: Type = TypeVoid

        for _statement in statement.block.statements:
            _type = self.check_statement(_statement)
            if isinstance(_statement, ReturnStatement):
                result_type = _type
                break
            result_type = _type # Last statement determines function return type if no explicit return? 
                                # (Actually Zen might require explicit return for some cases, but for now this is fine)
        
        statement.return_type = result_type or TypeVoid()
        self.scope.pop()

        symbol.resolved_type = result_type
        # symbol.type.return_type = result_type (frozen)
        
        # Create new TypeFunction with updated return type
        new_func_type = TypeFunction(
             symbol.type.name,
             symbol.type.parameters,
             result_type
        )
        symbol.type = new_func_type

        statement.resolved_type = result_type
        return result_type

    def check_member_reassignment_statement(self, statement: MemberReassignmentStatement):
        self.logger.debug("check_member_reassignment_statement", statement)
        
        obj_type = self.check_expression(statement.callee)
        value_type = self.check_expression(statement.value)
        
        # In a real compiler, we'd verify the member exists and is mutable.
        # For bootstrap, we'll unify and return.
        resolved_type = self.unify(obj_type, value_type, statement)
        statement.resolved_type = resolved_type
        return resolved_type

    def check_block_statement(self, statement: BlockStatement, region_id: Optional[str] = None):
        self.logger.debug("check_block_statement", statement)

        self.scope.push(region_id=region_id or f"block_{statement.line}")

        result_type: Type = TypeVoid

        for _statement in statement.statements:
            _type: Type = self.check_statement(_statement)
            result_type = _type
            if isinstance(_statement, ReturnStatement):
                self.scope.pop()
                return result_type

        statement.return_type = result_type

        self.scope.pop()
        return result_type

        return result_type

    def check_return_statement(self, statement: ReturnStatement):
        self.logger.debug("check_return_statement", statement)

        if statement.value:
            value_type: Type = self.check_expression(statement.value)

            statement.resolved_type = value_type

            return value_type
        else:
            statement.resolved_type = TypeVoid

            return TypeVoid

    def check_structure_statement(self, statement: StructureStatement):
        self.logger.debug("check_structure_statement", statement)
        self.scope.push()
#        self.scope.define(Symbol(statement.name, TypeStructure(statement.name, {})))
# The above line was already there or being handled

        parent_type = None
        if statement.parent:
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol:
                parent_type = parent_symbol.type
            else:
                print(f"[TypeChecker] Warning: Parent structure '{statement.parent}' not found for '{statement.name}'")

        member_types: dict = {}
        if parent_type and hasattr(parent_type, "members"):
            member_types.update(parent_type.members)

        for member in statement.members:  # MembersLiteral
            m_type_name = member.declared_type
            if hasattr(m_type_name, 'name'):
                m_type_name = m_type_name.name
            
            print(f"DEBUG: member {member.name} type name: {m_type_name}")

            declared_type = (
                TypePrimitive(m_type_name)
                if m_type_name
                else self.new_typevariable()
            )
            value_type = (
                self.check_expression(member.value)
                if member.value is not None
                else self.new_typevariable()
            )

            resolved_type: Type = self.unify(declared_type, value_type)
            member_types[member.name] = resolved_type
            member.declared_type = resolved_type

            symbol = Symbol(
                member.name,
                resolved_type,
                member.mutable,
                True, # exported?
                SymbolKind.MEMBER,
                statement.scope_level,
            )
            self.scope.define(symbol)

        self.scope.pop()

        struct_type = TypeStructure(statement.name, member_types, parent_type)
        symbol = Symbol(statement.name, struct_type, None, True, SymbolKind.STRUCTURE, statement.scope_level)
        self.scope.define(symbol)

        statement.resolved_type = struct_type
        return struct_type

    def check_enumerator_statement(self, statement: EnumeratorStatement):
        self.logger.debug("check_enumerator_statement", statement)

        self.scope.push()

        member_types: dict = {}

        if isinstance(statement.members, list):
            members_list = statement.members
        else:
            members_list = statement.members.value
            
        for member in members_list:  # MembersLiteral or list
            declared_type = (
                TypePrimitive(member.declared_type)
                if member.declared_type
                else self.new_typevariable()
            )
            value_type = (
                self.check_expression(member.value)
                if member.value is not None
                else self.new_typevariable()
            )

            resolved_type: Type = self.unify(declared_type, value_type)
            member_types[member.name] = resolved_type

            symbol = Symbol(
                member.name,
                resolved_type,
                None,
                member.mutable,
                SymbolKind.MEMBER,
                self.scope.level
            )
            self.scope.define(symbol)

        self.scope.pop()

        struct_type: TypeEnumerator = TypeEnumerator(statement.name, member_types)
        symbol = Symbol(
            statement.name,
            struct_type,
            None,
            True,
            SymbolKind.ENUMERATOR,
            statement.scope_level
        )
        self.scope.define(symbol)

        statement.resolved_type = struct_type
        return struct_type

    def check_scope_statement(self, statement: ScopeStatement):
        self.logger.debug("check_scope_statement", statement)

        # We need to register the scope name as a symbol in the parent scope
        
        # But wait, named scope is a Namespace.
        # We process the block.
        self.check_block_statement(statement.block)
        
        target_type = TypeVariant # Simplify for now
        symbol = Symbol(statement.name, target_type, None, False, SymbolKind.VARIABLE, self.scope.get_current_level())
        

        self.scope.define(symbol)
        
        statement.resolved_type = target_type
        return target_type

    def check_when_statement(self, statement: WhenStatement):
        self.logger.debug("check_when_statement", statement)

        condition_type: Type = self.check_expression(statement.condition)
        resolved_type: Type = self.unify(
            condition_type, TypeBoolean(), statement.condition
        )

        if not (isinstance(resolved_type, TypeBoolean) or resolved_type == TypeBoolean or isinstance(resolved_type, TypeVariant)):
            raise self.logger.error_type_unification(
                resolved_type, TypeBoolean(), statement.condition
            )

        # main block
        res = self.check_block_statement(statement.when_block)
        if res and not isinstance(res, TypeVoid): return res

        # conditional or-blocks
        for conditional_block in statement.conditional_blocks:
            condition_type: Type = self.check_expression(conditional_block["condition"])
            resolved_type: Type = self.unify(
                condition_type, TypeBoolean(), conditional_block["condition"]
            )

            if not (isinstance(resolved_type, TypeBoolean) or resolved_type == TypeBoolean or isinstance(resolved_type, TypeVariant)):
                raise self.logger.error_type_unification(
                    resolved_type, TypeBoolean(), conditional_block["condition"]
                )

            self.check_block_statement(conditional_block["block"])

        # optional final or-block
        if statement.or_block:
            self.check_block_statement(statement.or_block)

    def check_do_statement(self, statement: DoStatement):
        self.logger.debug("check_do_statement", statement)
        
        # Check condition if present (for 'loop' it might be None? Spec says 'loop' is infinite?)
        # StatementHandler:
        # 'loop' -> no condition
        # 'while' -> condition
        # 'until' -> condition
        # 'for' -> iterator/iterable
        
        if statement.condition:
            condition_type: Type = self.check_expression(statement.condition)
            resolved_type: Type = self.unify(
                condition_type, TypeBoolean(), statement.condition
            )
            
            if not (isinstance(resolved_type, TypeBoolean) or resolved_type == TypeBoolean):
               pass # TODO: raise error? Unify already logs error if strict?

        if statement.iterator and statement.iterable:
            iterable_type = self.check_expression(statement.iterable)
            # TODO: Infer element type from iterable_type
            element_type = PRIMITIVE_TYPES["Variant"]()
            
            self.scope.push(region_id=f"loop_{statement.line}")
            print(f"[DEBUG] check_do: Defining iterator '{statement.iterator}' in scope level {self.scope.level}")
            symbol = Symbol(
                statement.iterator,
                element_type,
                None,
                False, # Immutable iterator?
                SymbolKind.VARIABLE,
                self.scope.level
            )
            self.scope.define(symbol)
            print(f"[DEBUG] Scope check: lookup('{statement.iterator}') -> {self.scope.lookup(statement.iterator)}")
            
            self.check_block_statement(statement.block)
            
            self.scope.pop()
        else:
            self.check_block_statement(statement.block)
        
        if statement.or_block:
            self.check_block_statement(statement.or_block)

        statement.resolved_type = TypeVoid
        return TypeVoid

    def check_import_statement(self, statement: ImportStatement):
        self.logger.debug("check_import_statement", statement)
        
        # Mock module as a Variant variable so we can access properties on it
        symbol_name = statement.alias if statement.alias else statement.name
        symbol = Symbol(
            symbol_name,
            TypeVariant(), # Use instance
            None,
            False,
            SymbolKind.VARIABLE, # or MODULE if we add it
            0 # scope_level
        )
        # Check if already defined
        existing = self.scope.lookup(symbol_name, current_scope_only=True)
        if not existing:
            self.scope.define(symbol)

        
        statement.resolved_type = TypeVariant
        return TypeVariant

    def check_from_import_statement(self, statement: FromImportStatement):
        self.logger.debug("check_from_import_statement", statement)
        for symbol_info in statement.symbols:
            name = symbol_info["name"]
            alias = symbol_info["alias"]
            
            symbol_name = alias if alias else name
            
            symbol = Symbol(
                symbol_name,
                TypeStructure(symbol_name, {}), # Type stub for imported class/struct
                None,
                False,
                SymbolKind.VARIABLE,
                0
            )
            # Check if already defined
            existing = self.scope.lookup(symbol_name, current_scope_only=True)
            if not existing:
                self.scope.define(symbol)

            
        statement.resolved_type = TypeVariant
        return TypeVariant


    def check_class_statement(self, statement: ClassStatement):
        self.logger.debug("check_class_statement", statement)
        
        parent_type = None
        if statement.parent:
            # Resolve parent class
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol and isinstance(parent_symbol.type, TypeClass):
                parent_type = parent_symbol.type
            else:
                print(f"[TypeChecker] Error: Parent class '{statement.parent}' not found or not a class.")

        # New scope for class members
        self.scope.push()
        if parent_type:
            pass

        member_types: dict = {}
        # members are AssignmentStatements
        for member in statement.members:
             member_type = self.check_statement(member)
             member_types[member.name] = member_type
             
        method_types: dict = {}
        # methods are FunctionStatements
        
        # Set context
        previous_class = self.current_class
        # We need the TypeClass OBJECT for the current class.
        # It's not created yet? Wait.
        # We need a TypeClass representing the class being defined to set as 'self' type.
        # declared members above?
        # Actually, to define 'self', we need a TypeClass instance referring to THIS class.
        # Using TypeClass(statement.name, ...) potentially partial.
        
        # Construct TypeClass
        current_class_type = TypeClass(
             name=statement.name,
             members=member_types, # partially filled? Members are processed above.
             methods=method_types, # Empty for now but will be filled.
             parent=parent_type
        )
        self.current_class = current_class_type

        for method in statement.methods:
             method_type = self.check_statement(method)
             method_types[method.name] = method_type

        # Restore
        self.current_class = previous_class

        # Update methods in the type (since we passed empty dict)
        # current_class_type.methods = method_types # TypeClass is frozen dataclass?
        # If frozen, we can't update.
        # But we need 'self' to have the type.
        # It's fine if methods are missing in 'self' type during checking of methods (usually).
        # Important is the Name and Members.
        
        statement.resolved_type = current_class_type
             
        self.scope.pop()
        
        class_type: TypeClass = TypeClass(statement.name, member_types, method_types, parent_type)
        symbol = Symbol(statement.name, class_type, None, False, SymbolKind.VARIABLE, self.scope.get_current_level())
        self.scope.define(symbol)
        
        statement.resolved_type = class_type
        return class_type

    def check_object_statement(self, statement: ObjectStatement):
        self.logger.debug("check_object_statement", statement)
        self.scope.push()
        parent_type = None
        if statement.parent:
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol:
                parent_type = parent_symbol.type
            else:
                 print(f"[TypeChecker] Warning: Parent object '{statement.parent}' not found for '{statement.name}'")

        member_types: dict = {}
        if parent_type and hasattr(parent_type, "members"):
             member_types.update(parent_type.members)

        for member in statement.members:
            m_type_name = member.declared_type
            if hasattr(m_type_name, 'name'):
                m_type_name = m_type_name.name
            
            declared_type = (
                TypePrimitive(m_type_name)
                if m_type_name
                else self.new_typevariable()
            )
            value_type = (
                self.check_expression(member.value)
                if member.value is not None
                else self.new_typevariable()
            )

            resolved_type: Type = self.unify(declared_type, value_type)
            member_types[member.name] = resolved_type
            member.declared_type = resolved_type

            symbol = Symbol(
                member.name,
                resolved_type,
                member.mutable,
                True,
                SymbolKind.MEMBER,
                statement.scope_level,
            )
            self.scope.define(symbol)

        self.scope.pop()

        obj_type = TypeStructure(statement.name, member_types, parent_type)
        # Define as a type/structure
        type_symbol = Symbol(statement.name, obj_type, None, True, SymbolKind.STRUCTURE, statement.scope_level)
        self.scope.define(type_symbol)
        
        # ALSO define as a variable instance (singleton)
        instance_symbol = Symbol(statement.name, obj_type, None, False, SymbolKind.VARIABLE, statement.scope_level)
        existing = self.scope.lookup(statement.name, current_scope_only=True)
        if not existing:
             self.scope.define(instance_symbol)

        statement.resolved_type = obj_type
        return obj_type

    def check_defer_statement(self, statement: DeferStatement):
        self.logger.debug("check_defer_statement", statement)
        return self.check_block_statement(statement.block)

    def check_raise_statement(self, statement: RaiseStatement):
        self.logger.debug("check_raise_statement", statement)
        if statement.value:
            self.check_expression(statement.value)
        if statement.with_value:
            self.check_expression(statement.with_value)
        return TypeVoid()

    def check_assert_statement(self, statement: AssertStatement):
        self.logger.debug("check_assert_statement", statement)
        condition_type = self.check_expression(statement.condition)
        self.unify(condition_type, TypeBoolean(), statement.condition)
        
        if statement.raise_expression:
            self.check_expression(statement.raise_expression)
            
        return TypeVoid()

    def check_check_statement(self, statement: CheckStatement):
        self.logger.debug("check_check_statement", statement)
        res = self.check_expression(statement.expression)
        if res and not isinstance(res, TypeVoid): return res
        for case in statement.cases:
            self.check_expression(case["condition"])
            res = self.check_block_statement(case["block"])
            if res and not isinstance(res, TypeVoid): return res
        if statement.or_block:
            res = self.check_statement(statement.or_block)
            if res and not isinstance(res, TypeVoid): return res
        return TypeVoid()

    ## Check Expressions

    def check_expression(self, expression: ASTNode) -> Type:
        self.logger.debug("check_expression", expression)

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

        elif isinstance(expression, Identifier):
            return self.check_identifier(expression)

        elif isinstance(expression, BinaryOperation):
            return self.check_binary_operation(expression)

        elif isinstance(expression, CheckExpression):
            return self.check_check_expression(expression)

        elif isinstance(expression, UnaryOperation):
            return self.check_unary_operation(expression)

        if isinstance(expression, IntegerLiteral):
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

        elif isinstance(expression, SetLiteral):
            return self.check_set_literal(expression)

        elif isinstance(expression, TupleLiteral):
            return self.check_tuple_literal(expression)

        return None

    def check_check_expression(self, expression: CheckExpression) -> Type:
        self.logger.debug("check_check_expression", expression)
        expr_type = self.check_expression(expression.expression)
        
        if expression.or_value:
            or_type = self.check_expression(expression.or_value)
            # Both branches should unify
            resolved_type = self.unify(expr_type, or_type, expression)
            expression.resolved_type = resolved_type
            return resolved_type
            
        expression.resolved_type = expr_type
        return expr_type

    def check_structure_expression(self, expression: StructureExpression) -> Type:
        self.logger.debug("check_structure_expression", expression)
        
        # Look up the structure/object type by name
        symbol = self.scope.lookup(expression.name)
        if not symbol:
            print(f"[TypeChecker] Warning: Structure/Object '{expression.name}' not found.")
            return TypeVariant()
            
        struct_type = symbol.type
        if not isinstance(struct_type, (TypeStructure, TypeClass)):
            print(f"[TypeChecker] Warning: '{expression.name}' is not a structure or class.")
            return TypeVariant()
            
        # Check members
        for member in expression.members:
            # members is a list of Member (Assignments but in expression form)
            # Actually parse_members likely returns something like list of Member assignments.
            # Let's check Parser/ExpressionHandler.parse_members
            member_name = member.name
            if member_name in struct_type.members:
                declared_type = struct_type.members[member_name]
                value_type = self.check_expression(member.value)
                self.unify(declared_type, value_type, member)
            else:
                print(f"[TypeChecker] Warning: Member '{member_name}' not in '{expression.name}'")
                
        expression.resolved_type = struct_type
        return struct_type

    ## Expressions

    def check_function_expression(self, expression: FunctionExpression):
        self.logger.debug("check_function_expression", expression)

        symbol: TypeSymbol = TypeSymbol(
            expression.name,
            TypeFunction(
                expression.name, expression.parameters, expression.return_type
            ),
            True,
            Kind.FUNCTION,
        )

        self.scope.define(symbol)

        self.scope.push()

        result_type: Type = TypeVoid

        for statement in expression.block.statements:
            type = self.check_statement(statement)

            if isinstance(statement, ReturnStatement):
                result_type = type
                break

            result_type = type or TypeVoid
            statement.return_type = result_type

        self.scope.pop()

        symbol.resolved_type = result_type
        symbol.type.return_type = result_type

        return result_type

    def check_block_expression(self, expression: BlockExpression) -> Type:
        self.logger.debug("check_block_expression", expression)

        self.scope.push()

        result_type: Type = TypeVoid

        for statement in expression.statements:
            type: Type = self.check_statement(statement)

            if isinstance(statement, ReturnStatement):
                result_type = type
                break

            result_type = type if type is not None else TypeVoid
            statement.return_type = result_type

        self.scope.pop()
        expression.resolved_type = result_type
        return result_type

    def check_when_expression(self, expression: WhenExpression) -> Type:
        self.logger.debug("check_when_expression", expression)

        condition_type: Type = self.check_expression(expression.condition)
        resolved_type: Type = self.unify(
            condition_type, TypeBoolean(), expression.condition
        )

        branch_types: list[Type] = []

        when_type = self.check_block_expression(expression.when_block)
        if when_type:
            branch_types.append(when_type)

        for conditional_block in getattr(expression, "conditional_blocks", []):
            condition_type: Type = self.check_expression(conditional_block["condition"])
            resolved_type: Type = self.unify(
                condition_type, TypeBoolean(), conditional_block["condition"]
            )

            conditional_type = self.check_block_expression(conditional_block["block"])
            if conditional_type:
                branch_types.append(conditional_type)

        if expression.or_block:
            or_type = self.check_block_expression(expression.or_block)
            if or_type:
                branch_types.append(or_type)

        if not branch_types:
            return TypeVoid

        result_type = branch_types[0]
        for type in branch_types[1:]:
            result_type = self.unify(result_type, type, expression)

        expression.return_type = result_type
        expression.resolved_type = result_type

        return result_type

    def check_when_inline_expression(self, expression: WhenInlineExpression) -> Type:
        self.logger.debug("check_when_inline_expression", expression)

        condition_type: Type = self.check_expression(expression.condition)
        resolved_type: Type = self.unify(
            condition_type, TypeBoolean(), expression.condition
        )

        if not (isinstance(resolved_type, TypeBoolean) or resolved_type == TypeBoolean or isinstance(resolved_type, TypeVariant)):
            raise self.logger.error_type_unification(
                resolved_type, TypeBoolean(), expression.condition
            )

        when_type: Type = (
            self.check_expression(expression.when_value)
            if expression.when_value
            else TypeVoid
        )
        or_type: Type = (
            self.check_expression(expression.or_value)
            if expression.or_value
            else TypeVoid
        )

        result_type: Type = self.unify(when_type, or_type, expression)

        expression.return_type = result_type
        expression.resolved_type = result_type

        return result_type

    def check_identifier(self, expression: Identifier) -> Type:
        self.logger.debug("check_identifier", expression)

        symbol: TypeSymbol = self.scope.lookup(expression.name)

        if not symbol:
            raise self.logger.error_variable_undefined(expression)

        expression.symbol = symbol
        expression.resolved_type = symbol.type

        return symbol.type
        
    def check_list_literal(self, expression: ListLiteral) -> Type:
        self.logger.debug("check_list_literal", expression)
        
        element_types = []
        for element in expression.elements:
             # Unwrap ElementLiteral
             item_node = element.value
             t = self.check_expression(item_node)
             # Store type on both element and value for safety
             element.resolved_type = t
             item_node.resolved_type = t
             element_types.append(t)
             
        # For now, return a generic list or infer type
        # TODO: Homogenous check
        expression.resolved_type = TypeList(None, [])
        return expression.resolved_type

    def check_call_expression(self, expression: CallExpression) -> Type:
        self.logger.debug("check_call_expression", expression)

        callee_type = self.check_expression(expression.callee)

        # Allow calls on Variants (e.g. io.write)
        if isinstance(callee_type, TypeVariant) or callee_type == TypeVariant:
             # Variant call returns Variant (dynamic)
             expression.resolved_type = TypeVariant()
             return TypeVariant()
        elif isinstance(callee_type, TypeFunction):
             expression.resolved_type = callee_type.return_type
        else:
             # Fallback or error?
             # For now defaulting to Void to avoid crash if type is generic/unknown
             expression.resolved_type = TypeVoid
             # prevent error for now while bootstrapping
             # raise self.logger.error_type_mismatch(TypeFunction, callee_type, expression)

        # callee_type: Type = self.check_expression(expression.callee)

        for i, argument in enumerate(expression.arguments):
            argument_type = self.check_expression(argument)
            argument.resolved_type = argument_type

        return expression.resolved_type

    def check_member_expression(self, expression: MemberExpression) -> Type:
        self.logger.debug("check_member_expression", expression)

        object_type = self.check_expression(expression.object)
        
        if isinstance(object_type, TypeVariant) or object_type == TypeVariant:
            # If it's a variant, we allow dynamic access. 
            expression.resolved_type = TypeVariant()
            return TypeVariant()
            
        # Structure Member Access
        if isinstance(object_type, TypeStructure):
            member_name = expression.property
            if member_name in object_type.members:
                t = object_type.members[member_name]
                expression.resolved_type = t
                return t
            else:
                print(f"[TypeChecker] Error: Member '{member_name}' not found in Structure '{object_type.name}'")
                return TypeVariant()

        # Class Member Access (with Inheritance)
        if isinstance(object_type, TypeClass):
            member_name = expression.property
            
            # 1. Check current class members
            if member_name in object_type.members:
                t = object_type.members[member_name]
                expression.resolved_type = t
                return t
            
            # 2. Check current class methods
            if member_name in object_type.methods:
                t = object_type.methods[member_name]
                expression.resolved_type = t
                return t

            # 3. Check Parent Hierarchy
            current_type = object_type.parent
            while current_type:
                 if member_name in current_type.members:
                     # Found in parent!
                     # TODO: Maybe annotate expression to indicate parent access?
                     t = current_type.members[member_name]
                     expression.resolved_type = t
                     return t
                 
                 if member_name in current_type.methods:
                     t = current_type.methods[member_name]
                     expression.resolved_type = t
                     return t

                 current_type = current_type.parent
        # Fallback
        expression.resolved_type = TypeVariant()
        return TypeVariant()

    def check_member_reassignment_statement(self, statement: MemberReassignmentStatement) -> Type:
         self.logger.debug("check_member_reassignment_statement", statement)
         
         # Left side must be a MemberExpression (already checked by parser?)
         # check_expression on LHS
         lhs_type = self.check_expression(statement.expression)
         
         # Right side
         rhs_type = self.check_expression(statement.value)
         
         # Unify?
         # TODO: Verify assignment validity (mutable, type match)
         
         statement.resolved_type = lhs_type
         return lhs_type
        
    def check_index_expression(self, expression: IndexExpression) -> Type:
        self.logger.debug("check_index_expression", expression)
        
        object_type = self.check_expression(expression.object)
        index_type = self.check_expression(expression.index)
        
        if not isinstance(index_type, (TypeInteger, TypeVariant)): # Allow variant for now?
             print(f"[TypeChecker] Error: Index must be Integer, got {index_type}")
             # raise self.logger.error_type_mismatch(TypeInteger, index_type, expression)
        
        if isinstance(object_type, TypeList):
            # TODO: Return specific element type if known
            expression.resolved_type = TypeVariant()
            return TypeVariant()
        elif isinstance(object_type, TypeVariant):
            expression.resolved_type = TypeVariant()
            return TypeVariant()
        elif isinstance(object_type, TypeString):
            # String indexing returns Rune or String?
            expression.resolved_type = TypeString() # or TypeRune
            return TypeString()
            
        print(f"[TypeChecker] Error: Indexing not supported on {object_type}")
        expression.resolved_type = TypeVariant()
        return TypeVariant()

    def check_unary_operation(self, expression: UnaryOperation) -> Type:
        self.logger.debug("check_unary_operation", expression)
        right_type = self.check_expression(expression.right)
        
        if expression.operator == "not":
            self.unify(right_type, TypeBoolean(), expression)
            expression.resolved_type = TypeBoolean()
            return TypeBoolean()
        
        if expression.operator == "!!":
            self.unify(right_type, TypeInteger(), expression)
            expression.resolved_type = TypeInteger()
            return TypeInteger()
            
        return right_type

    def check_binary_operation(self, expression: BinaryOperation) -> Type:
        self.logger.debug("check_binary_operation", expression)

        left_type: Type = self.check_expression(expression.left)
        right_type: Type = self.check_expression(expression.right)

        operator: str = expression.operator

        if operator in OPERATORS.keys() or operator in ["xor", "nor", "nand", "xnor"]:
            if (isinstance(left_type, TypeVariant) or left_type == TypeVariant) or \
               (isinstance(right_type, TypeVariant) or right_type == TypeVariant):
                return TypeVariant()

            # Logical operators expect Boolean
            if operator in ["and", "or", "xor", "nor", "nand", "xnor"]:
                self.unify(left_type, TypeBoolean(), expression)
                self.unify(right_type, TypeBoolean(), expression)
                expression.resolved_type = TypeBoolean()
                return TypeBoolean()

            # Bitwise operators expect Integer
            if operator in ["&&", "||", "^^", "!&", "!|", "!^", "<<", ">>", "%%"]:
                self.unify(left_type, TypeInteger(), expression)
                self.unify(right_type, TypeInteger(), expression)
                expression.resolved_type = TypeInteger()
                return TypeInteger()

            result: Type = self.unify(left_type, right_type, expression)

            # Check if result is Numeric (Integer or Decimal) or String (concatenation)
            if isinstance(result, (TypeInteger, TypeDecimal, TypeVariant, TypeString)) or \
               result in (TypeInteger, TypeDecimal, TypeVariant, TypeString):
                expression.type = result
                expression.resolved_type = result
                return result

            # Allow String + Rune -> String
            if (isinstance(left_type, TypeString) or left_type == TypeString) and \
               (isinstance(right_type, TypeRune) or right_type == TypeRune) and \
               operator == "+":
               expression.type = TypeString()
               expression.resolved_type = TypeString()
               return TypeString()

            raise self.logger.error_type_unification(left_type, right_type, expression)

        if operator in COMPARATORS.keys():
            if (isinstance(left_type, TypeVariant) or left_type == TypeVariant) or \
               (isinstance(right_type, TypeVariant) or right_type == TypeVariant):
                return TypeBoolean()

            try:
                result: Type = self.unify(left_type, right_type, expression)

                if result:
                    expression.type = TypeBoolean()
                    expression.resolved_type = TypeBoolean()
                    return TypeBoolean()

            except Exception as error:
                raise error

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
            if a.bound is not None:
                return self.unify(a.bound, b, attachment)

            if self.occurs_check(a, b):
                raise self.logger.error_type_unification(a, b, attachment)

            a.bound = b
            return b

        if isinstance(b, TypeVariable):
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

        # Optional lenient fallback
        if variant_fallback:
            # self.logger.debug(
            #     f"Unify fallback: incompatible types {a} and {b}, returning Variant"
            # )
            return TypeVariant()

        # TODO: add FunctionType/StructType structural checks here

        raise self.logger.error_type_unification(a, b, attachment)
    def check_vector_literal(self, expression: VectorLiteral) -> Type:
        self.logger.debug("check_vector_literal", expression)
        # Infer element type from first element or Variant
        element_types = [self.check_expression(el.value) for el in expression.elements]
        if not element_types:
            expression.resolved_type = TypeVector(None, TypeVariant(), 0)
            return expression.resolved_type
            
        common_type = element_types[0]
        for t in element_types[1:]:
            common_type = self.unify(common_type, t, expression)
            
        expression.resolved_type = TypeVector(None, common_type, len(expression.elements))
        return expression.resolved_type

    def check_dictionary_literal(self, expression: DictionaryLiteral) -> Type:
        self.logger.debug("check_dictionary_literal", expression)
        # Infer key and value types
        if not expression.elements:
            expression.resolved_type = TypeMap(None, TypeVariant(), TypeVariant())
            return expression.resolved_type
            
        key_types = [self.check_expression(el.name) for el in expression.elements]
        value_types = [self.check_expression(el.value) for el in expression.elements]
        
        common_key_type = key_types[0]
        for t in key_types[1:]:
            common_key_type = self.unify(common_key_type, t, expression)
            
        common_value_type = value_types[0]
        for t in value_types[1:]:
            common_value_type = self.unify(common_value_type, t, expression)
            
        expression.resolved_type = TypeMap(None, common_key_type, common_value_type)
        return expression.resolved_type

    def check_set_literal(self, expression: SetLiteral) -> Type:
        self.logger.debug("check_set_literal", expression)
        element_types = [self.check_expression(el.value) for el in expression.elements]
        if not element_types:
            expression.resolved_type = TypeSet(None, TypeVariant())
            return expression.resolved_type
            
        common_type = element_types[0]
        for t in element_types[1:]:
            common_type = self.unify(common_type, t, expression)
            
        expression.resolved_type = TypeSet(None, common_type)
        return expression.resolved_type

    def check_tuple_literal(self, expression: TupleLiteral) -> Type:
        self.logger.debug("check_tuple_literal", expression)
        element_types = [TypeElement(getattr(el, "name") if hasattr(el, "name") else None, self.check_expression(el.value)) for el in expression.elements]
        expression.resolved_type = TypeTuple(None, element_types)
        return expression.resolved_type

    def check_export_statement(self, statement: ExportStatement) -> Type:
        self.logger.debug("check_export_statement", statement)
        return self.check_statement(statement.statement)
