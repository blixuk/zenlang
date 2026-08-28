from typing import Optional, Dict, Any
from Checker.Type import (
    Type,
    TypeVoid,
    TypeBoolean,
    TypeFunction,
    TypeTask,
    TypeTaskHandle,
    TypeClass,
    TypeStructure,
    TypeEnum,
    TypeEnumVariant,
    TypeVariant,
    Symbol,
    SymbolKind,
    PRIMITIVE_TYPES,
    TypePrimitive,
)
from Parser.AST import (
    ASTNode,
    AssignmentStatement,
    ReassignmentStatement,
    FunctionStatement,
    TaskStatement,
    MemberReassignmentStatement,
    IndexReassignmentStatement,
    DereferenceReassignmentStatement,
    BlockStatement,
    ReturnStatement,
    StructureStatement,
    EnumeratorStatement,
    ScopeStatement,
    WhenStatement,
    DoStatement,
    ImportStatement,
    FromImportStatement,
    ClassStatement,
    WithStatement,
    ObjectStatement,
    DeferStatement,
    RaiseStatement,
    AssertStatement,
    CheckStatement,
    BreakStatement,
    ContinueStatement,
    ExportStatement,
    MemberExpression,
    ReturnStatement,
    IdentifierPattern,
    VariantPattern,
    ListPattern,
    MapPattern,
)

class StatementHandler:
    def check_break_statement(self, statement: BreakStatement) -> Type:
        return PRIMITIVE_TYPES["Void"]()

    def check_continue_statement(self, statement: ContinueStatement) -> Type:
        return PRIMITIVE_TYPES["Void"]()

    def resolve_type_node(self, node: Any) -> Type:
        if node is None:
            return self.new_typevariable()
        if isinstance(node, str):
            name = node
            subtypes = []
        else:
            name = getattr(node, "name", None)
            subtypes = getattr(node, "subtypes", []) or []

        if not name:
            return self.new_typevariable()

        if name in ["Pointer", "Reference", "borrowed", "owned"]:
            # Handle pointer/reference types recursively
            inner_type = TypeVariant()
            if subtypes:
                inner_type = self.resolve_type_node(subtypes[0])
            elif not isinstance(node, str) and hasattr(node, "type") and node.type:
                inner_type = self.resolve_type_node(node.type)
                
            from Checker.Type import TypePointer, TypeReference
            if name in ["Pointer", "owned"]:
                return TypePointer(inner_type)
            else:
                return TypeReference(inner_type)

        if name in PRIMITIVE_TYPES:
            return PRIMITIVE_TYPES[name]()

        if name == "List":
            from Checker.Type import TypeList
            return TypeList(None, [])
        if name == "Map":
            from Checker.Type import TypeMap, TypeVariant
            return TypeMap(None, TypeVariant(), TypeVariant())

        symbol = self.scope.lookup(name)
        if symbol:
            return symbol.type

        return self.new_typevariable()

    def check_assignment_statement(self, statement: AssignmentStatement):
        self.logger.debug("check_assignment_statement", statement)
        
        declared_type: Type | None = None
        
        if statement.declared_type:
            declared_type = self.resolve_type_node(statement.declared_type)
        
        value_type: Type = (
            self.check_expression(statement.value)
            if statement.value is not None
            else self.new_typevariable()
        )

        if declared_type is None:
            declared_type = value_type

        resolved_type: Type = self.unify(declared_type, value_type, statement)

        kind: SymbolKind = (
            SymbolKind.VARIABLE if statement.mutable else SymbolKind.CONSTANT
        )

        from Checker.Type import TypeInteger, TypeBoolean, TypeDecimal, TypeRune, TypeString, TypeNothing, TypeVoid, SymbolState, TypeReference

        symbol: Symbol = Symbol(
            statement.name,
            resolved_type,
            statement.value,
            statement.mutable,
            kind,
            statement.scope_level,
            filename=getattr(statement, "filename", self.source_path)
        )

        # Ownership: move is opt-in via MemoryKind.UNIQUE (owned bindings).
        # Default structures/classes/collections share or copy — auto-moving every
        # non-primitive broke the self-host sources (ASTNode rebinding).
        from Parser.AST import Identifier as IdentifierAST
        from Checker.Type import MemoryKind
        if isinstance(statement.value, IdentifierAST):
            source_symbol = self.scope.lookup(statement.value.name)
            if (
                source_symbol
                and source_symbol.kind != SymbolKind.CONSTANT
                and source_symbol.memory_kind == MemoryKind.UNIQUE
            ):
                source_symbol.state = SymbolState.MOVED
                self.logger.debug(f"Moved ownership of '{statement.value.name}' to '{statement.name}'")
                
                # Invalidate any references in active scopes that borrow this symbol
                from Checker.Type import TypeReference
                curr_scope = self.scope.current_scope
                while curr_scope:
                    for sym_name, sym in curr_scope.symbols.items():
                        sym_type = sym.type
                        if hasattr(sym_type, "resolve"):
                            sym_type = sym_type.resolve()
                        if isinstance(sym_type, TypeReference) and sym_type.borrowed_name == source_symbol.name:
                            sym.state = SymbolState.EXPIRED
                            self.logger.debug(f"Expired reference '{sym_name}' because '{source_symbol.name}' was moved")
                    curr_scope = curr_scope.parent

        self.scope.define(symbol)

        statement.resolved_type = resolved_type
        statement.symbol = symbol

        return resolved_type

    def check_dereference_reassignment_statement(self, statement: DereferenceReassignmentStatement):
        self.logger.debug("check_dereference_reassignment_statement", statement)
        ptr_type = self.check_expression(statement.pointer_expression)
        value_type = self.check_expression(statement.value)
        
        from Checker.Type import TypeReference, TypePointer
        if isinstance(ptr_type, (TypeReference, TypePointer)):
            self.unify(ptr_type.inner_type, value_type, statement)
        else:
            self.unify(ptr_type, value_type, statement)

    def check_reassignment_statement(self, statement: ReassignmentStatement):

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
            statement.symbol = symbol

    def check_function_statement(self, statement: FunctionStatement):
        
        return_type = self.resolve_type_node(statement.return_type)

        symbol: Symbol = Symbol(
            statement.name,
            TypeFunction(statement.name, statement.parameters, return_type),
            None,
            True,
            SymbolKind.FUNCTION,
            statement.scope_level,
            filename=getattr(statement, "filename", self.source_path)
        )

        try:
            self.scope.define(symbol)
            statement.symbol = symbol
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
            parameter_type = self.resolve_type_node(parameter.declared_type if hasattr(parameter, 'declared_type') else None)
            
            level = self.scope.get_current_level()
            symbol_parameter: Symbol = Symbol(
                parameter.name,
                parameter_type,
                parameter.value,
                True,
                SymbolKind.PARAMETER,
                level,
            )

            self.scope.define(symbol_parameter)
            
            # Update AST node
            parameter.declared_type = parameter_type
            parameter.scope_level = level

        if getattr(self, "defer_function_bodies", False):
            if not hasattr(self, "deferred_functions"):
                self.deferred_functions = []
            
            # Enclosing scope is the parent of the temporary function scope we pushed.
            # Restore it when typechecking deferred bodies so siblings in named
            # scopes (e.g. scope Sentence { to_words; count_words }) resolve.
            enclosing_scope = self.scope.current_scope.parent
            enclosing_level = max(0, self.scope.level - 1)
            enclosing_region = self.scope.current_region
            if (
                self.scope.current_scope.parent is not None
                and self.scope.current_scope.parent.region is not None
            ):
                enclosing_region = self.scope.current_scope.parent.region

            self.deferred_functions.append(
                (
                    statement,
                    self.source_path,
                    self.current_class,
                    symbol,
                    enclosing_scope,
                    enclosing_level,
                    enclosing_region,
                )
            )
            self.scope.pop()
            return return_type

        result_type: Type = self.check_block_statement(statement.body)
        self.scope.pop()

        symbol.resolved_type = result_type
        
        # Create new TypeFunction with updated return type
        new_func_type = TypeFunction(
             symbol.type.name,
             symbol.type.parameters,
             result_type
        )
        symbol.type = new_func_type

        statement.resolved_type = new_func_type
        return new_func_type

    def check_task_statement(self, statement: TaskStatement):
        return_type = statement.return_type
        if hasattr(return_type, "name"):
            rt_name = return_type.name
            if rt_name in PRIMITIVE_TYPES:
                return_type = PRIMITIVE_TYPES[rt_name]()
            else:
                sym = self.scope.lookup(rt_name)
                if sym:
                    return_type = sym.type

        from Checker.Type import TypeTask
        symbol: Symbol = Symbol(
            statement.name,
            TypeTask(statement.name, statement.parameters, return_type),
            None,
            True,
            SymbolKind.FUNCTION,
            statement.scope_level,
            filename=getattr(statement, "filename", self.source_path)
        )

        try:
            self.scope.define(symbol)
            statement.symbol = symbol
        except Exception as e:
            if "redeclaration" in str(e) and statement.scope_level == 0:
                 pass 
            else:
                 raise e

        self.scope.push(region_id=f"task_{statement.name}")
    
        for parameter in statement.parameters:
            p_type_name = parameter.declared_type if hasattr(parameter, 'declared_type') else None
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
            
            level = self.scope.get_current_level()
            symbol_parameter: Symbol = Symbol(
                parameter.name,
                parameter_type,
                parameter.value,
                True,
                SymbolKind.PARAMETER,
                level,
            )

            self.scope.define(symbol_parameter)
            parameter.declared_type = parameter_type
            parameter.scope_level = level

        if getattr(self, "defer_function_bodies", False):
            if not hasattr(self, "deferred_functions"):
                self.deferred_functions = []
            
            enclosing_scope = self.scope.current_scope.parent
            enclosing_level = max(0, self.scope.level - 1)
            enclosing_region = self.scope.current_region
            if (
                self.scope.current_scope.parent is not None
                and self.scope.current_scope.parent.region is not None
            ):
                enclosing_region = self.scope.current_scope.parent.region

            self.deferred_functions.append(
                (
                    statement,
                    self.source_path,
                    self.current_class,
                    symbol,
                    enclosing_scope,
                    enclosing_level,
                    enclosing_region,
                )
            )
            self.scope.pop()
            return return_type

        result_type: Type = self.check_block_statement(statement.body)
        self.scope.pop()

        symbol.resolved_type = result_type
        
        new_task_type = TypeTask(
             symbol.type.name,
             symbol.type.parameters,
             result_type
        )
        symbol.type = new_task_type

        statement.resolved_type = new_task_type
        return new_task_type

    def check_member_reassignment_statement(self, statement: MemberReassignmentStatement):
        
        obj_type = self.check_expression(statement.callee)
        prop = statement.property
        member_type = self._resolve_member_type(obj_type, prop, statement)
        
        value_type = self.check_expression(statement.value)
        resolved_type = self.unify(member_type, value_type, statement)
        
        statement.resolved_type = resolved_type
        return resolved_type

    def check_index_reassignment_statement(self, statement: IndexReassignmentStatement):
        
        obj_type = self.check_expression(statement.callee)
        index_type = self.check_expression(statement.index)
        value_type = self.check_expression(statement.value)
        
        resolved_type = self.unify(obj_type, value_type, statement)
        statement.resolved_type = value_type
        return value_type

    def check_block_statement(self, statement: BlockStatement, region_id: Optional[str] = None):

        line = getattr(statement, "line", "unknown")
        self.scope.push(region_id=region_id or f"block_{line}")

        result_type: Type = TypeVoid()

        for _statement in statement.statements:
            if self.recover:
                try:
                    _type: Type = self.check_statement(_statement)
                    if not isinstance(_type, TypeVoid):
                        result_type = _type
                    if isinstance(_statement, ReturnStatement):
                        self.scope.pop()
                        return result_type
                except Exception as error:
                    if self.debugging:
                        import traceback
                        traceback.print_exc()
                    if self.strict:
                        self.scope.pop()
                        raise
                    # Log bare exceptions that weren't already recorded by the logger
                    if not self.logger.has_errors:
                        self.logger.error(str(error))
            else:
                _type: Type = self.check_statement(_statement)
                if not isinstance(_type, TypeVoid):
                    result_type = _type
                if isinstance(_statement, ReturnStatement):
                    self.scope.pop()
                    return result_type

        statement.return_type = result_type

        self.scope.pop()
        return result_type

    def check_return_statement(self, statement: ReturnStatement):

        if statement.value:
            value_type: Type = self.check_expression(statement.value)
            statement.resolved_type = value_type
            return value_type
        else:
            statement.resolved_type = TypeVoid()
            return TypeVoid()

    def check_structure_statement(self, statement: StructureStatement):
        self.scope.push()

        parent_type = None
        if statement.parent:
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol:
                parent_type = parent_symbol.type
            else:
                pass

        member_types: dict = {}
        if parent_type and hasattr(parent_type, "members"):
            member_types.update(parent_type.members)

        for member in statement.members:
            m_type_name = member.declared_type
            if hasattr(m_type_name, 'name'):
                m_type_name = m_type_name.name
            
            declared_type = None
            if m_type_name:
                if m_type_name in PRIMITIVE_TYPES:
                    declared_type = PRIMITIVE_TYPES[m_type_name]()
                else:
                    symbol = self.scope.lookup(m_type_name)
                    if symbol:
                        declared_type = symbol.type
            
            if declared_type is None:
                 declared_type = self.new_typevariable()

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
                filename=getattr(statement, "filename", self.source_path)
            )
            self.scope.define(symbol)

        self.scope.pop()

        existing = self.scope.lookup(statement.name, current_scope_only=True)
        if existing and isinstance(existing.type, (TypeStructure, TypeVariant)):
            existing.type.__class__ = TypeStructure
            struct_type = existing.type
            struct_type.name = statement.name
            struct_type.members = member_types
            struct_type.parent = parent_type
            struct_type.filename = self.source_path
            symbol = existing
        else:
            struct_type = TypeStructure(statement.name, member_types, parent_type, filename=getattr(statement, "filename", self.source_path))
            symbol = Symbol(statement.name, struct_type, None, True, SymbolKind.STRUCTURE, statement.scope_level, filename=getattr(statement, "filename", self.source_path))
            self.scope.define(symbol)

        statement.resolved_type = struct_type
        return struct_type

    def check_enumerator_statement(self, statement: EnumeratorStatement):
        
        variants: Dict[str, TypeEnumVariant] = {}
        for variant in statement.members:
            param_types = [TypeVariant() for _ in variant.params]
            v_type = TypeEnumVariant(variant.name, param_types, statement.name)
            variants[variant.name] = v_type
            
            if not variant.params:
                symbol = Symbol(
                    variant.name,
                    v_type,
                    None,
                    False,
                    SymbolKind.VARIANT,
                    statement.scope_level
                )
            else:
                symbol = Symbol(
                    variant.name,
                    TypeFunction(variant.name, param_types, v_type),
                    None,
                    False,
                    SymbolKind.VARIANT,
                    statement.scope_level
                )
            self.scope.define(symbol)
                
        enum_type = TypeEnum(statement.name, variants, filename=getattr(statement, "filename", self.source_path))
        existing = self.scope.lookup(statement.name, current_scope_only=True)
        if existing:
            # Replace placeholder / prior type; never mutate frozen TypeEnum in place.
            existing.type = enum_type
            existing.kind = SymbolKind.TYPE
            existing.filename = self.source_path
            symbol = existing
        else:
            symbol = Symbol(
                statement.name,
                enum_type,
                None,
                False,
                SymbolKind.TYPE,
                statement.scope_level,
                filename=getattr(statement, "filename", self.source_path)
            )
            self.scope.define(symbol)
        statement.resolved_type = enum_type
        return enum_type

    def _bind_pattern(self, pattern, value_type: Type):
        from Parser.AST import (
            IdentifierPattern,
            VariantPattern,
            ListPattern,
            MapPattern,
            WildcardPattern,
            LiteralPattern,
            IsMatchPattern,
        )

        if isinstance(pattern, IdentifierPattern):
            # Bind the identifier to the value type
            level = self.scope.get_current_level()
            pattern.scope_level = level
            symbol = Symbol(
                pattern.name,
                value_type,
                None,
                False,
                SymbolKind.VARIABLE,
                level,
            )
            self.scope.define(symbol)
            pattern.symbol = symbol
        elif isinstance(pattern, VariantPattern):
            # For Option.Something(v), we try to bind parameters
            # For now, we use TypeVariant() for parameters unless we can resolve the enum
            for p in pattern.params:
                self._bind_pattern(p, TypeVariant())
        elif isinstance(pattern, ListPattern):
            for p in pattern.elements:
                self._bind_pattern(p, TypeVariant())
        elif isinstance(pattern, MapPattern):
            for k, p in pattern.pairs:
                self._bind_pattern(p, TypeVariant())
        # WildcardPattern, LiteralPattern, IsMatchPattern do not bind names

    def check_scope_statement(self, statement: ScopeStatement):
        existing_symbol = self.scope.lookup(statement.name, current_scope_only=True)
        target_type = existing_symbol.type if existing_symbol else TypeVariant()
        
        self.scope.push(region_id=f"scope_{statement.name}")
        
        for _statement in statement.body.statements:
            self.check_statement(_statement)
            if hasattr(_statement, "name") and hasattr(_statement, "resolved_type"):
                if isinstance(target_type, (TypeStructure, TypeClass)):
                    if not hasattr(target_type, "methods") or target_type.methods is None:
                        target_type.methods = {}
                    target_type.methods[_statement.name] = _statement.resolved_type
        
        self.scope.pop()
        
        if existing_symbol is None:
            symbol = Symbol(statement.name, target_type, None, False, SymbolKind.NAMESPACE, self.scope.get_current_level(), filename=getattr(statement, "filename", self.source_path))
            target_type.symbol = symbol
            self.scope.define(symbol)
        
        statement.resolved_type = target_type
        return target_type

    def check_when_statement(self, statement: WhenStatement):

        if hasattr(statement, "branches") and statement.branches is not None:
            condition_type = self.check_expression(statement.condition)
            
            for branch in statement.branches:
                self.scope.push(region_id=f"case_{branch.line}")
                self._bind_pattern(branch.pattern, condition_type)
                if branch.guard:
                    guard_type = self.check_expression(branch.guard)
                    self.unify(guard_type, TypeBoolean(), branch.guard)
                self.check_block_statement(branch.body)
                self.scope.pop()
            
            if statement.or_block:
                self.check_block_statement(statement.or_block)
            return TypeVoid()

        ret_type = None
        if statement.when_block:
            self.scope.push(region_id=f"when_{statement.line}_main")
            condition_type: Type = self.check_expression(statement.condition)
            self.unify(condition_type, TypeBoolean(), statement.condition)
            b_type = self.check_block_statement(statement.when_block)
            if b_type and not isinstance(b_type, TypeVoid):
                ret_type = b_type
            self.scope.pop()

        for conditional_block in statement.conditional_blocks:
            self.scope.push(region_id=f"when_or_{conditional_block['condition'].line}")
            condition_type: Type = self.check_expression(conditional_block["condition"])
            self.unify(condition_type, TypeBoolean(), conditional_block["condition"])
            cb_type = self.check_block_statement(conditional_block["block"])
            if cb_type and not isinstance(cb_type, TypeVoid):
                ret_type = cb_type
            self.scope.pop()

        if statement.or_block:
            self.scope.push(region_id=f"when_else_{statement.line}")
            ob_type = self.check_block_statement(statement.or_block)
            if ob_type and not isinstance(ob_type, TypeVoid):
                ret_type = ob_type
            self.scope.pop()

        return ret_type if ret_type is not None else TypeVoid()

    def check_do_statement(self, statement: DoStatement):
        
        if statement.condition:
            condition_type: Type = self.check_expression(statement.condition)
            resolved_type: Type = self.unify(
                condition_type, TypeBoolean(), statement.condition
            )

        if statement.iterator and statement.iterable:
            iterable_type = self.check_expression(statement.iterable)
            element_type = PRIMITIVE_TYPES["Variant"]()
            
            self.scope.push(region_id=f"loop_{statement.line}")
            
            # Sync iterator node scope level
            if hasattr(statement.iterator, "scope_level"):
                statement.iterator.scope_level = self.scope.level

            iter_name = statement.iterator.name if hasattr(statement.iterator, "name") else statement.iterator
            if self.debugging:
                print(f"DEBUG [TC]: Iterator is {type(statement.iterator)} name={iter_name}")
            
            # Infer element type
            element_type = PRIMITIVE_TYPES["Variant"]()
            
            # Check for explicit type hint first
            if hasattr(statement.iterator, "type") and statement.iterator.type not in ("Variable", "Variant"):
                if self.debugging:
                    print(f"DEBUG [TC]: Found type hint {statement.iterator.type} for iterator")
                hint_sym = self.scope.lookup(statement.iterator.type)
                if hint_sym:
                    element_type = hint_sym.type
                    if self.debugging:
                        print(f"DEBUG [TC]: Resolved hint type: {element_type}")
                else:
                    if self.debugging:
                        print(f"DEBUG [TC]: Hint type {statement.iterator.type} NOT FOUND")
                    # Maybe it's a primitive?
                    if statement.iterator.type in PRIMITIVE_TYPES:
                        element_type = PRIMITIVE_TYPES[statement.iterator.type]()
            
            if isinstance(element_type, PRIMITIVE_TYPES["Variant"]) and \
               hasattr(iterable_type, "elements") and iterable_type.elements:
                # For List, Vector, etc.
                if hasattr(iterable_type.elements[0], "type"):
                     element_type = iterable_type.elements[0].type
                else:
                     element_type = iterable_type.elements[0]
            elif isinstance(element_type, PRIMITIVE_TYPES["Variant"]) and \
                 hasattr(iterable_type, "value_type"):
                # For Map
                element_type = iterable_type.value_type

            statement.iterator.resolved_type = element_type
            symbol = Symbol(
                iter_name,
                element_type,
                None,
                False, 
                SymbolKind.VARIABLE,
                self.scope.level
            )
            # Attach symbol to iterator node for easier access during transpilation
            if hasattr(statement.iterator, "symbol"):
                statement.iterator.symbol = symbol

            self.scope.define(symbol)
            if hasattr(statement.iterator, "resolved_type"):
                statement.iterator.resolved_type = element_type
            
            self.check_block_statement(statement.body)
            self.scope.pop()
        else:
            self.check_block_statement(statement.body)
        
        if statement.or_block:
            self.check_block_statement(statement.or_block)

        statement.resolved_type = TypeVoid()
        return TypeVoid()

    def check_import_statement(self, statement: ImportStatement):
        
        symbol_name = statement.alias if statement.alias else statement.name
        symbol_path = getattr(statement, "resolved_path", None)
        if not symbol_path:
            symbol_path = statement.path
        symbol = Symbol(
            symbol_name,
            TypeVariant(), # Use instance
            None,
            False,
            SymbolKind.MODULE,
            0, # scope_level
            filename=symbol_path
        )
        # Always install a fresh MODULE binding. Never mutate an existing
        # non-module symbol in place (e.g. function `error` from zen.io) —
        # that would corrupt that symbol's filename/kind and break native
        # mangling (`error_error`) and call sites (`error.new`).
        existing = self.scope.lookup(symbol_name, current_scope_only=True)
        if existing and existing.kind == SymbolKind.MODULE:
            existing.filename = symbol_path
            existing.type = symbol.type
        else:
            # Overwrite bare name collisions (functions from other modules)
            # with the import alias so `import zen.error as error` wins.
            self.scope.current_scope.symbols[symbol_name] = symbol

        statement.resolved_type = TypeVariant()
        return TypeVariant()

    def check_from_import_statement(self, statement: FromImportStatement):
        for symbol_info in statement.symbols:
            name = symbol_info["name"]
            alias = symbol_info["alias"]
            symbol_name = alias if alias else name

            existing = self.scope.lookup(name)
            resolved_path = getattr(statement, "resolved_path", None)
            
            if existing:
                symbol = Symbol(
                    symbol_name,
                    existing.type,
                    existing.value,
                    existing.mutable,
                    existing.kind,
                    0,
                    filename=resolved_path
                )
            else:
                symbol = Symbol(
                    symbol_name,
                    TypeStructure(symbol_name, {}, filename=resolved_path),
                    None,
                    False,
                    SymbolKind.VARIABLE,
                    0,
                    filename=resolved_path
                )
            self.scope.current_scope.symbols[symbol_name] = symbol

        statement.resolved_type = TypeVariant()
        return TypeVariant()

    def check_class_statement(self, statement: ClassStatement):
        
        parent_type = None
        if statement.parent:
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol and isinstance(parent_symbol.type, TypeClass):
                parent_type = parent_symbol.type
            else:
                pass

        member_types: dict = {}
        method_types: dict = {}
        
        existing = self.scope.lookup(statement.name, current_scope_only=True)
        if existing and isinstance(existing.type, (TypeClass, TypeStructure, TypeVariant)):
            existing.type.__class__ = TypeClass
            class_type = existing.type
            class_type.name = statement.name
            class_type.members = member_types
            class_type.methods = method_types
            class_type.parent = parent_type
            class_type.filename = self.source_path
            symbol = existing
        else:
            class_type = TypeClass(
                name=statement.name,
                members=member_types,
                methods=method_types,
                parent=parent_type,
                filename=getattr(statement, "filename", self.source_path)
            )
            # Define symbol in parent scope so it can be looked up by methods
            symbol = Symbol(statement.name, class_type, None, False, SymbolKind.CLASS, self.scope.get_current_level(), filename=getattr(statement, "filename", self.source_path))
            class_type.symbol = symbol
            self.scope.define(symbol)

        self.scope.push()

        previous_class = self.current_class
        self.current_class = class_type

        for member in statement.members:
             member_type = self.check_statement(member)
             member_types[member.name] = member_type

        for method in statement.methods:
             method_type = self.check_statement(method)
             method_types[method.name] = method_type

        self.current_class = previous_class
        statement.resolved_type = class_type
        self.scope.pop()
        
        return class_type

    def check_with_statement(self, statement: WithStatement):
        resource_type = self.check_expression(statement.expression)
        self.scope.push(region_id=statement.alias if statement.alias else f"with_{statement.line}")
        
        if statement.alias:
            symbol = Symbol(
                statement.alias,
                resource_type,
                None,
                False,
                SymbolKind.VARIABLE,
                self.scope.level
            )
            self.scope.define(symbol)

        # AST uses `body` (not `block`) — see Parser.AST.WithStatement
        body = getattr(statement, "body", None) or getattr(statement, "block", None)
        if body is None:
            result_type = None
        else:
            result_type = self.check_block_statement(body)
        self.scope.pop()
        
        statement.resolved_type = result_type
        return result_type

    def check_object_statement(self, statement: ObjectStatement):
        self.scope.push()
        parent_type = None
        if statement.parent:
            parent_symbol = self.scope.lookup(statement.parent)
            if parent_symbol:
                parent_type = parent_symbol.type
            else:
                 pass

        member_types: dict = {}
        if parent_type and hasattr(parent_type, "members"):
             member_types.update(parent_type.members)

        for member in statement.members:
            m_type_name = member.declared_type
            if hasattr(m_type_name, 'name'):
                m_type_name = m_type_name.name
            
            declared_type = None
            if m_type_name:
                if m_type_name in PRIMITIVE_TYPES:
                    declared_type = PRIMITIVE_TYPES[m_type_name]()
                else:
                    symbol = self.scope.lookup(m_type_name)
                    if symbol:
                        declared_type = symbol.type
            
            if declared_type is None:
                 declared_type = self.new_typevariable()

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

        obj_type = TypeStructure(statement.name, member_types, parent_type, filename=getattr(statement, "filename", self.source_path))
        type_symbol = Symbol(statement.name, obj_type, None, True, SymbolKind.STRUCTURE, statement.scope_level)
        self.scope.define(type_symbol)
        
        instance_symbol = Symbol(statement.name, obj_type, None, False, SymbolKind.VARIABLE, statement.scope_level)
        existing = self.scope.lookup(statement.name, current_scope_only=True)
        if not existing:
             self.scope.define(instance_symbol)

        statement.resolved_type = obj_type
        return obj_type

    def check_defer_statement(self, statement: DeferStatement):
        return self.check_statement(statement.body)

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
        matched_type = self.check_expression(statement.expression)
        
        for case in statement.cases:
            self.scope.push(region_id=f"case_{case.line}")
            self.check_pattern(case.pattern, matched_type)
            if case.guard:
                guard_type = self.check_expression(case.guard)
                self.unify(guard_type, TypeBoolean(), case.guard)
            self.check_statement(case.body)
            self.scope.pop()
        
        if statement.or_block:
             self.check_statement(statement.or_block)
             
        return TypeVoid()

    def check_export_statement(self, statement: ExportStatement) -> Type:
        self.logger.debug("check_export_statement", statement)
        return self.check_statement(statement.statement)
