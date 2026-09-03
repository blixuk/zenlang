from Checker.Type import (
    Type,
    TypeVariable,
    TypeVariant,
    TypeFunction,
    TypeTask,
    TypeTaskHandle,
    TypeClass,
    TypeStructure,
    TypeInteger,
    TypeString,
    TypeBoolean,
    TypeDecimal,
    TypeRune,
    TypeVoid,
    TypeList,
    TypeElement,
    Symbol,
    SymbolKind,
)
from Parser.AST import (
    ASTNode,
    InExpression,
    WhenExpression,
    WhenInlineExpression,
    FunctionExpression,
    BlockExpression,
    CallExpression,
    MemberExpression,
    IndexExpression,
    SliceExpression,
    StructureExpression,
    ReturnStatement,
    IntegerLiteral,
    DecimalLiteral,
    StringLiteral,
    RuneLiteral,
    NothingLiteral,
    VoidLiteral,
    BooleanLiteral,
    VariantLiteral,
    ListLiteral,
    StructureStatement,
    UnaryOperation,
    BinaryOperation,
    CheckExpression,
    IsExpression,
    AwaitExpression,
    Identifier,
)
from Lexer.Token import OPERATORS, COMPARATORS

class ExpressionHandler:
    def check_call_expression(self, expression: CallExpression) -> Type:
        self.logger.debug("check_call_expression", expression)

        callee_type = self.check_expression(expression.callee)

        # Check arguments first so their types are resolved
        for i, argument in enumerate(expression.arguments):
            argument_type = self.check_expression(argument)
            argument.resolved_type = argument_type

        # Allow calls on Variants (e.g. io.write)
        if isinstance(callee_type, TypeVariant) or callee_type == TypeVariant:
             # Variant call returns Variant (dynamic)
             expression.resolved_type = TypeVariant()
             return TypeVariant()
        elif isinstance(callee_type, TypeFunction):
             expression.resolved_type = callee_type.return_type
        elif isinstance(callee_type, TypeTask):
             expression.resolved_type = TypeTaskHandle(callee_type.return_type)
             return expression.resolved_type
        elif isinstance(callee_type, TypeClass) or isinstance(callee_type, TypeStructure):
             # Constructor call returns instance of the class/structure
             expression.resolved_type = callee_type
             return callee_type
        else:
             # Fallback
             expression.resolved_type = TypeVariant()

        return expression.resolved_type

    def check_member_expression(self, expression: MemberExpression) -> Type:
        self.logger.debug("check_member_expression", expression)

        object_type = self.check_expression(expression.object)
        
        if isinstance(object_type, TypeVariant) or object_type == TypeVariant:
            # Module access hack for bootstrap
            if hasattr(expression.object, "symbol") and expression.object.symbol and expression.object.symbol.kind == SymbolKind.MODULE:
                # Try to find the actual symbol in scope (class, struct, namespace, or function)
                sym = self.scope.lookup(expression.property)
                if sym:
                    if isinstance(sym.type, (TypeClass, TypeStructure, TypeFunction)) or sym.kind in (SymbolKind.CLASS, SymbolKind.STRUCTURE, SymbolKind.NAMESPACE, SymbolKind.FUNCTION):
                        expression.resolved_type = sym.type
                        expression.symbol = sym
                        return sym.type

                if expression.property[0].isupper():
                    # Likely a class access from a module (fallback to hollow)
                    module_path = expression.object.symbol.filename
                    t = TypeClass(expression.property, {}, {}, filename=module_path)
                    sym = Symbol(expression.property, t, None, False, SymbolKind.CLASS, 0, filename=module_path)
                    t.symbol = sym
                    expression.resolved_type = t
                    return t

            # If it's a variant, we allow dynamic access. 
            expression.resolved_type = TypeVariant()
            return TypeVariant()
            
        # Resolve member type (with Inheritance)
        member_name = expression.property
        t = self._resolve_member_type(object_type, member_name, expression)
        expression.resolved_type = t
        return t

    def _resolve_member_type(self, object_type: Type, member_name: str, node: ASTNode) -> Type:
        from Checker.Type import TypeReference
        if isinstance(object_type, TypeReference):
             object_type = object_type.inner_type

        # Structure Member Access
        if isinstance(object_type, TypeStructure):
            if member_name in object_type.members:
                return object_type.members[member_name]
            if hasattr(object_type, "methods") and object_type.methods and member_name in object_type.methods:
                return object_type.methods[member_name]
            else:
                print(f"[TypeChecker] Error: Member '{member_name}' not found in Structure '{object_type.name}'")
                return TypeVariant()

        # Class Member Access (with Inheritance)
        if isinstance(object_type, TypeClass):
            # 1. Check current class members/methods
            if member_name in object_type.members:
                return object_type.members[member_name]
            
            if member_name in object_type.methods:
                return object_type.methods[member_name]
            
            # 2. Check Parent Hierarchy
            current_type = object_type.parent
            while current_type:
                if member_name in current_type.members:
                    return current_type.members[member_name]
                
                if member_name in current_type.methods:
                    return current_type.methods[member_name]

                current_type = current_type.parent
        
        from Checker.Type import TypeEnum
        if isinstance(object_type, TypeEnum):
            if member_name in object_type.variants:
                v_type = object_type.variants[member_name]
                # Look up the symbol for this variant to attach it
                # The symbol name is usually just the member_name or Enum_member_name
                # In StatementHandler it was defined as variant.name
                v_symbol = self.scope.lookup(member_name)
                if v_symbol:
                    node.symbol = v_symbol
                return v_type
        
        # Fallback
        return TypeVariant()

    def check_index_expression(self, expression: IndexExpression) -> Type:
        self.logger.debug("check_index_expression", expression)
        
        object_type = self.check_expression(expression.object)
        index_type = self.check_expression(expression.index)
        
        if not isinstance(index_type, (TypeInteger, TypeVariant)) and self.debugging:
             print(f"[TypeChecker] Error: Index must be Integer, got {index_type}")
        
        from Checker.Type import TypeList
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
            
        if self.debugging:
            print(f"[TypeChecker] Error: Indexing not supported on {object_type}")
        expression.resolved_type = TypeVariant()
        return TypeVariant()

    def check_slice_expression(self, expression: SliceExpression) -> Type:
        self.logger.debug("check_slice_expression", expression)
        object_type = self.check_expression(expression.object)
        if expression.start is not None:
            self.check_expression(expression.start)
        if expression.end is not None:
            self.check_expression(expression.end)
        if expression.step is not None:
            self.check_expression(expression.step)
        expression.resolved_type = object_type
        return object_type

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

        if expression.operator in ["&", "source"]:
            from Checker.Type import TypeReference
            borrowed_name = None
            if isinstance(expression.right, Identifier):
                borrowed_name = expression.right.name
            expression.resolved_type = TypeReference(right_type, borrowed_name=borrowed_name)
            return expression.resolved_type
            
        if expression.operator in ["*", "target"]:
            from Checker.Type import TypeReference, TypePointer
            if isinstance(right_type, (TypeReference, TypePointer)):
                expression.resolved_type = right_type.inner_type
            else:
                expression.resolved_type = right_type
            return expression.resolved_type

        return right_type

    def check_await_expression(self, expression: AwaitExpression) -> Type:
        self.logger.debug("check_await_expression", expression)
        expr_type = self.check_expression(expression.expression)
        
        if isinstance(expr_type, TypeTaskHandle):
             expression.resolved_type = expr_type.inner_type
             return expr_type.inner_type
        
        # If it's a variant, we allow it (runtime check)
        if isinstance(expr_type, TypeVariant) or expr_type == TypeVariant:
             expression.resolved_type = TypeVariant()
             return TypeVariant()
             
        # Otherwise it's an error
        print(f"[TypeChecker] Error: Cannot await non-task type {expr_type}")
        expression.resolved_type = TypeVariant()
        return TypeVariant()

    def map_type_from_str(self, name: str) -> Type:
        if name in ("Integer", "Int", "Int64", "Int32", "Int16", "Int8", "Byte"):
            return TypeInteger()
        if name in ("Decimal", "Float", "Double"):
            return TypeDecimal()
        if name in ("String", "Str"):
            return TypeString()
        if name in ("Boolean", "Bool"):
            return TypeBoolean()
        if name in ("Rune", "Char", "Glyph"):
            return TypeRune()
        if name in ("Bytes", "Buffer"):
            return TypeList(None, [TypeElement(None, TypeInteger())])
        if name in ("List", "Set"):
            return TypeList(None, [TypeElement(None, TypeVariant())])
        if name == "Map":
            return TypeMap(None, TypeVariant(), TypeVariant())
        return TypeVariant()

    def check_binary_operation(self, expression: BinaryOperation) -> Type:
        self.logger.debug("check_binary_operation", expression)

        operator: str = expression.operator
        if operator == "<:":
            left_type = self.check_expression(expression.left)
            target_type_str = getattr(expression.right, "name", str(expression.right))
            res = self.map_type_from_str(target_type_str)
            expression.type = res
            expression.resolved_type = res
            return res

        left_type: Type = self.check_expression(expression.left)
        right_type: Type = self.check_expression(expression.right)

        # Range operators produce a List (of integers or single-character strings).
        if operator in ("..", "..+", "..-", "..."):
            expression.resolved_type = TypeList(None, [TypeElement(None, TypeVariant())])
            return expression.resolved_type

        if operator == "in":
            expression.type = TypeBoolean()
            expression.resolved_type = TypeBoolean()
            return expression.resolved_type

        if operator == "??":
            from Checker.Type import TypeNothing
            if isinstance(left_type, TypeNothing) or left_type == TypeNothing:
                res = right_type
            else:
                res = left_type
            expression.type = res
            expression.resolved_type = res
            return res

        # Extended '++' (append/prepend/concat) and '--' (drop start/end/decrement)
        if operator == "++":
            if isinstance(left_type, TypeString) or left_type == TypeString or \
               isinstance(right_type, TypeString) or right_type == TypeString:
                expression.type = TypeString()
                expression.resolved_type = TypeString()
                return TypeString()
            if isinstance(left_type, TypeList) or left_type == TypeList or \
               isinstance(right_type, TypeList) or right_type == TypeList:
                res = TypeList(None, [TypeElement(None, TypeVariant())])
                expression.type = res
                expression.resolved_type = res
                return res
            if (isinstance(left_type, TypeVariant) or left_type == TypeVariant) or \
               (isinstance(right_type, TypeVariant) or right_type == TypeVariant):
                return TypeVariant()
            # Numeric addition fallback
            result: Type = self.unify(left_type, right_type, expression)
            expression.type = result
            expression.resolved_type = result
            return result

        if operator == "--":
            if isinstance(left_type, TypeString) or left_type == TypeString or \
               isinstance(right_type, TypeString) or right_type == TypeString:
                expression.type = TypeString()
                expression.resolved_type = TypeString()
                return TypeString()
            if isinstance(left_type, TypeList) or left_type == TypeList or \
               isinstance(right_type, TypeList) or right_type == TypeList:
                res = TypeList(None, [TypeElement(None, TypeVariant())])
                expression.type = res
                expression.resolved_type = res
                return res
            if (isinstance(left_type, TypeVariant) or left_type == TypeVariant) or \
               (isinstance(right_type, TypeVariant) or right_type == TypeVariant):
                return TypeVariant()
            # Numeric subtraction fallback
            result: Type = self.unify(left_type, right_type, expression)
            expression.type = result
            expression.resolved_type = result
            return result

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

            # Check if result is Numeric (Integer or Decimal), String, or unbound TypeVariable
            if isinstance(result, (TypeInteger, TypeDecimal, TypeVariant, TypeString, TypeVariable)) or \
               result in (TypeInteger, TypeDecimal, TypeVariant, TypeString, TypeVariable):
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

    def check_in_expression(self, expression: InExpression) -> Type:
        self.logger.debug("check_in_expression", expression)
        # Verify the arena exists in scope
        self.scope.lookup(expression.arena)
        
        inner_type = self.check_expression(expression.expression)
        expression.resolved_type = inner_type
        return inner_type

    def check_is_expression(self, expression: IsExpression) -> Type:
        left_type = self.check_expression(expression.left)
        # Patterns can bind variables in the current scope.
        self.check_pattern(expression.right, left_type)
        expression.resolved_type = TypeBoolean()
        return expression.resolved_type

    def check_check_expression(self, expression: CheckExpression) -> Type:
        self.logger.debug("check_check_expression", expression)
        # Check the primary expression
        matched_type = self.check_expression(expression.expression)
        
        # If it's an Option<T> or Result<T, E>, unwrap to T
        inner_type = matched_type
        from Checker.Type import TypeOption, TypeResult
        if isinstance(matched_type, TypeOption):
            inner_type = matched_type.inner_type
        elif isinstance(matched_type, TypeResult):
            inner_type = matched_type.inner_type
            
        # Check fallback value or raise expression
        if expression.or_value:
            fallback_type = self.check_expression(expression.or_value)
            # Unify unwrapped type and fallback type
            res = self.unify(inner_type, fallback_type, expression)
            expression.resolved_type = res
            return res
        
        if expression.raise_expression:
            self.check_expression(expression.raise_expression)
            
        expression.resolved_type = inner_type
        return inner_type

    def check_structure_expression(self, expression: StructureExpression) -> Type:
        self.logger.debug("check_structure_expression", expression)
        # Check structure name
        symbol = self.scope.lookup(expression.name)
        if not symbol:
             # If not found, maybe it's a dynamic variant?
             expression.resolved_type = TypeVariant()
             return TypeVariant()
             
        struct_type = symbol.type
            
        for member in expression.members:
             self.check_expression(member.value)
             
        expression.resolved_type = struct_type
        return struct_type

    def check_function_expression(self, expression: FunctionExpression):
        self.logger.debug("check_function_expression", expression)
        # Lambda/Inline function
        self.scope.push(region_id=f"func_expr_{expression.line}")
        for param in expression.parameters:
            self.scope.define(Symbol(param.name, TypeVariant(), None, True, SymbolKind.PARAMETER, self.scope.level))
            
        result_type = self.check_block_expression(expression.body)
        self.scope.pop()
        
        # Create function type
        func_type = TypeFunction(None, expression.parameters, result_type)
        expression.resolved_type = func_type
        return func_type

    def check_block_expression(self, expression: BlockExpression) -> Type:
        self.logger.debug("check_block_expression", expression)

        self.scope.push()

        result_type: Type = TypeVoid()

        for statement in expression.statements:
            _type: Type = self.check_statement(statement)

            if isinstance(statement, ReturnStatement):
                result_type = _type
                break

            result_type = _type if _type is not None else TypeVoid()
            statement.return_type = result_type

        self.scope.pop()
        expression.resolved_type = result_type
        return result_type

    def check_when_expression(self, expression: WhenExpression) -> Type:
        self.logger.debug("check_when_expression", expression)

        branch_types: list[Type] = []

        # Main branch
        self.scope.push(region_id=f"when_expr_{expression.line}_main")
        condition_type: Type = self.check_expression(expression.condition)
        self.unify(condition_type, TypeBoolean(), expression.condition)
        
        when_type = self.check_block_expression(expression.when_block)
        if when_type:
            branch_types.append(when_type)
        self.scope.pop()

        for conditional_block in getattr(expression, "conditional_blocks", []):
            self.scope.push(region_id=f"when_expr_or_{conditional_block['condition'].line}")
            condition_type: Type = self.check_expression(conditional_block["condition"])
            self.unify(condition_type, TypeBoolean(), conditional_block["condition"])

            conditional_type = self.check_block_expression(conditional_block["block"])
            if conditional_type:
                branch_types.append(conditional_type)
            self.scope.pop()

        if expression.or_block:
            or_type = self.check_block_expression(expression.or_block)
            if or_type:
                branch_types.append(or_type)

        if not branch_types:
            return TypeVoid()

        result_type = branch_types[0]
        for t in branch_types[1:]:
            result_type = self.unify(result_type, t, expression)

        expression.return_type = result_type
        expression.resolved_type = result_type

        return result_type

    def check_when_inline_expression(self, expression: WhenInlineExpression) -> Type:
        self.logger.debug("check_when_inline_expression", expression)

        self.scope.push(region_id=f"when_inline_{expression.line}")
        condition_type: Type = self.check_expression(expression.condition)
        self.unify(condition_type, TypeBoolean(), expression.condition)

        when_type: Type = (
            self.check_expression(expression.when_value)
            if expression.when_value
            else TypeVoid()
        )
        self.scope.pop()
        
        or_type: Type = (
            self.check_expression(expression.or_value)
            if expression.or_value
            else TypeVoid()
        )

        result_type: Type = self.unify(when_type, or_type, expression)
        expression.return_type = result_type
        expression.resolved_type = result_type

        return result_type

    def check_identifier(self, expression: Identifier) -> Type:
        self.logger.debug("check_identifier", expression)

        symbol = self.scope.lookup(expression.name)

        if not symbol:
            if expression.name in ("Integer", "String", "Decimal", "Boolean", "Rune", "Bytes", "Set", "List", "Map", "Int", "Str", "Float", "Bool", "Char"):
                t = self.map_type_from_str(expression.name)
                expression.resolved_type = t
                return t
            raise self.logger.error_variable_undefined(expression)

        from Checker.Type import SymbolState
        if symbol.state == SymbolState.MOVED:
            raise self.logger.error(
                f"Use of moved value '{expression.name}'",
                expression,
            )
        elif symbol.state == SymbolState.EXPIRED:
            raise self.logger.error(
                f"Use of expired reference '{expression.name}'",
                expression,
            )

        expression.symbol = symbol
        expression.resolved_type = symbol.type

        return symbol.type
