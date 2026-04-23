from typing import List, Optional, Any
from Parser.AST import *
from Transpiler.MIR import *

class SMIRGenerator:
    def __init__(self, filename: Optional[str] = None):
        self.instructions: List[MIRInstruction] = []
        self.label_counter = 0
        self.filename = filename
        self.current_region: Optional[str] = "global"
        self.region_stack: List[str] = ["global"]

    def new_label(self, prefix="L") -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _emit(self, instr: MIRInstruction, node: ASTNode):
        instr.line = getattr(node, 'line', 0)
        instr.column = getattr(node, 'column', 0)
        instr.filename = self.filename
        self.instructions.append(instr)

    def _alloc_temp(self, name: str, node: ASTNode, type: Any = None, region: Optional[str] = None):
        r = region if region else self.current_region
        self._emit(Alloc(target=name, region=r, type=type), node)
        return name

    def generate(self, node: ASTNode, pre_allocated_symbols: List[str] = None) -> List[MIRInstruction]:
        self.instructions = []
        # Note: Parameters are now handled in _visit_function
        self._visit(node)
        return self.instructions

    def _visit(self, node: ASTNode):
        if isinstance(node, Program) or isinstance(node, Statements):
            for stmt in node.statements:
                self._visit(stmt)
        elif isinstance(node, FunctionStatement):
            self._visit_function(node)
        elif isinstance(node, BlockStatement):
            self._visit_block(node)
        elif isinstance(node, AssignmentStatement):
            self._visit_assignment(node)
        elif isinstance(node, ReassignmentStatement):
            self._visit_reassignment(node)
        elif isinstance(node, ExpressionStatement):
            self._visit_expression(node.expression)
        elif isinstance(node, ReturnStatement):
            self._visit_return(node)
        elif isinstance(node, DoStatement):
            self._visit_do(node)
        elif isinstance(node, WhenStatement):
            self._visit_when(node)
        elif isinstance(node, EnumeratorStatement):
            self._visit_enumerator(node)
        elif isinstance(node, MemberReassignmentStatement):
            self._visit_member_reassignment(node)
        elif isinstance(node, AssertStatement):
            self._visit_assert(node)
        elif isinstance(node, WithStatement):
            self._visit_with(node)
        elif isinstance(node, DeferStatement):
            self._visit_defer(node)
        elif isinstance(node, CheckStatement):
            self._visit_check_statement(node)
        elif isinstance(node, CheckExpression):
            return self._visit_check_expression(node, target_region=self.current_region)
        elif isinstance(node, RaiseStatement):
            self._visit_raise_statement(node)
        elif isinstance(node, IndexReassignmentStatement):
            self._visit_index_reassignment(node)
        elif isinstance(node, BlockExpression):
            for stmt in node.statements:
                self._visit(stmt)

    def _visit_return(self, node: ReturnStatement):
        res = self._visit_expression(node.value) if node.value else None
        
        # Emit RegionExit for all regions entered in this function
        # We walk back the stack until we hit a 'func_' region or global.
        for i in range(len(self.region_stack) - 1, 0, -1):
            rid = self.region_stack[i]
            self._emit(RegionExit(id=rid), node)
            if rid.startswith("func_"):
                 break

        self._emit(Return(value=res), node)

    def _visit_do(self, node: DoStatement):
        start_label = self.new_label("loop_start")
        end_label = self.new_label("loop_end")
        
        self._emit(Label(name=start_label), node)
        
        if node.condition:
            cond = self._visit_expression(node.condition)
            self._emit(Branch(condition=cond, true_label=None, false_label=end_label), node) 
            # (Simplified branch: if false, jump to end)
        
        self._visit(node.block)
        self._emit(Jump(target=start_label), node)
        self._emit(Label(name=end_label), node)

    def _visit_when(self, node: WhenStatement):
        exit_label = self.new_label("when_exit")
        
        # New: Structural pattern match branches (match-like)
        if hasattr(node, "branches") and node.branches is not None:
             subject = self._visit_expression(node.condition)
             for branch in node.branches:
                 next_case_label = self.new_label("case_next")
                 match_tmp = self._visit_pattern_match(subject, branch.pattern, node)
                 self._emit(Branch(condition=match_tmp, true_label=None, false_label=next_case_label), node)
                 
                 # Case block
                 self._visit(branch.block)
                 self._emit(Jump(target=exit_label), node)
                 self._emit(Label(name=next_case_label), node)
             
             if node.or_block:
                 self._visit(node.or_block)
             
             self._emit(Label(name=exit_label), node)
             return

        # Traditional conditional when-block
        next_branch_label = self.new_label("when_next")
        cond = self._visit_expression(node.condition)
        self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
        self._visit(node.when_block)
        self._emit(Jump(target=exit_label), node)
        self._emit(Label(name=next_branch_label), node)
        
        # or when
        for branch in node.conditional_blocks:
            next_branch_label = self.new_label("when_next")
            cond = self._visit_expression(branch["condition"])
            self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
            self._visit(branch["block"])
            self._emit(Jump(target=exit_label), node)
            self._emit(Label(name=next_branch_label), node)
        
        # else
        if node.or_block:
            self._visit(node.or_block)
        
        self._emit(Label(name=exit_label), node)

    def _visit_reassignment(self, node: ReassignmentStatement):
        # Move new value to existing target or attribute
        expr_result = self._visit_expression(node.value)
        if hasattr(node, "name") and isinstance(node.name, MemberExpression):
            obj = self._visit_expression(node.name.object)
            prop = node.name.property
            self._emit(SetAttr(obj=obj, prop=prop, value=expr_result), node)
        else:
            self._emit(Move(dest=node.name, src=expr_result), node)

    def _visit_member_reassignment(self, node: MemberReassignmentStatement):
        expr_result = self._visit_expression(node.value)
        
        # In the new parser version, node.callee is the full MemberExpression LHS
        lhs = node.callee
        if not isinstance(lhs, MemberExpression):
             # Fallback for old/simple cases
             obj = self._visit_expression(node.callee)
             path = node.expression # This might be the property name string
             if hasattr(node.callee, "resolved_type") and node.callee.resolved_type:
                  obj_type = node.callee.resolved_type
                  path = self._resolve_member_path(obj_type, path)
                  if path.startswith("."): path = path[1:]
        else:
             obj = self._visit_expression(lhs.object)
             prop = lhs.property
             # Inheritance resolution
             obj_type = getattr(lhs.object, "resolved_type", None)
             if not obj_type and hasattr(lhs, "resolved_type"):
                  # Use the property's parent type if available? No, we need the object's type.
                  pass
             
             path = prop
             if obj_type:
                  path = self._resolve_member_path(obj_type, prop)
                  if path.startswith("."): path = path[1:]
             
        self._emit(SetAttr(obj=obj, prop=path, value=expr_result), node)

    def _visit_index_reassignment(self, node: IndexReassignmentStatement):
        val = self._visit_expression(node.value)
        obj = self._visit_expression(node.object)
        idx = self._visit_expression(node.index)
        # Use a special call that CodeGenerator will map to ZenValue_set_index
        self._emit(Call(target=None, callee="Value_set_index", args=[obj, idx, val], region=self.current_region), node)

    def _visit_assignment(self, node: AssignmentStatement):
        # 1. Allocate space on current region
        all_type = node.declared_type
        if not all_type and hasattr(node, "resolved_type"):
             all_type = node.resolved_type
        
        self._emit(Alloc(target=node.name, region=self.current_region, type=all_type), node)
        
        # 2. Evaluate expression and move to target
        expr_result = self._visit_expression(node.value)
        self._emit(Move(dest=node.name, src=expr_result), node)

    def _visit_expression(self, node: ASTNode, target_region: Optional[str] = None) -> str:
        if isinstance(node, CheckExpression):
            return self._visit_check_expression(node, target_region)
        
        if isinstance(node, IsExpression):
            return self._visit_is_expression(node, target_region)

        current_reg = target_region if target_region else self.current_region
        
        if isinstance(node, InExpression):
            # The 'in' expression specifies a target region for its inner expression
            return self._visit_expression(node.expression, target_region=node.arena)

        if isinstance(node, IntegerLiteral):
            tmp = self._alloc_temp(self.new_label("tmp"), node, "int", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value), type="int"), node)
            return tmp
        elif isinstance(node, StringLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_str"), node, "string", region=current_reg)
            self._emit(Load(target=tmp, source=f"`{node.value}`", type="string"), node)
            return tmp
        elif isinstance(node, DecimalLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_dec"), node, "decimal", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value), type="decimal"), node)
            return tmp
        elif isinstance(node, RuneLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_rune"), node, "rune", region=current_reg)
            # Convert to integer code point for this runtime
            v = ord(node.value)
            self._emit(Load(target=tmp, source=str(v), type="rune"), node)
            return tmp
        elif isinstance(node, BooleanLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_bool"), node, "bool", region=current_reg)
            self._emit(Load(target=tmp, source=str(node.value).lower(), type="bool"), node)
            return tmp
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinaryOperation):
            left = self._visit_expression(node.left, target_region=target_region)
            right = self._visit_expression(node.right, target_region=target_region)
            res_type = getattr(node, "resolved_type", None)
            tmp = self._alloc_temp(self.new_label("tmp_bin"), node, region=current_reg)
            self._emit(Alloc(target=tmp, region=current_reg, type=res_type), node)
            op = node.operator.value if hasattr(node.operator, "value") else str(node.operator)
            self._emit(Compute(target=tmp, op=op, left=left, right=right), node)
            return tmp
        elif isinstance(node, UnaryOperation):
            right = self._visit_expression(node.right, target_region=target_region)
            tmp = self._alloc_temp(self.new_label("tmp_unary"), node, region=current_reg)
            op = node.operator.value if hasattr(node.operator, "value") else str(node.operator)
            # Use empty string for left operand in unary operations
            self._emit(Compute(target=tmp, op=op, left="", right=right), node)
            return tmp
        elif isinstance(node, CallExpression):
            args = [self._visit_expression(arg, target_region=target_region) for arg in node.arguments]
            if isinstance(node.callee, MemberExpression):
                # Don't visit it to avoid GetAttr. Instead, reconstruct the dotted name.
                obj = self._visit_expression(node.callee.object, target_region=target_region)
                prop = node.callee.property
                callee = f"{obj}.{prop}"
            else:
                callee = self._visit_expression(node.callee, target_region=target_region)
            res_type = getattr(node, "resolved_type", None)
            if res_type:
                 pass # print(f"DEBUG [SMIR]: Call {node.callee} has result type {res_type}")
            tmp = self._alloc_temp(self.new_label("tmp_call"), node, region=current_reg)
            self._emit(Alloc(target=tmp, region=current_reg, type=res_type), node)
            self._emit(Call(target=tmp, callee=callee, args=args, region=current_reg), node)
            return tmp
        elif isinstance(node, MemberExpression):
            obj = self._visit_expression(node.object, target_region=target_region)
            prop = node.property
            if hasattr(prop, "value"): prop = prop.value
            
            # Inheritance resolution
            obj_type = getattr(node.object, "resolved_type", None)
            path = str(prop)
            if obj_type:
                 path = self._resolve_member_path(obj_type, str(prop))
                 if path.startswith("."): path = path[1:]

            # Get the type of the property itself if possible
            prop_type = getattr(node, "resolved_type", None)
            
            tmp = self._alloc_temp(self.new_label("tmp_attr"), node, region=current_reg)
            self._emit(Alloc(target=tmp, region=current_reg, type=prop_type), node)
            self._emit(GetAttr(target=tmp, obj=obj, prop=path), node)
            return tmp
        elif isinstance(node, NothingLiteral):
            tmp = self._alloc_temp(self.new_label("tmp_none"), node, region=current_reg)
            self._emit(Nullify(target=tmp), node)
            return tmp
        elif isinstance(node, (ListLiteral, VectorLiteral, SetLiteral, TupleLiteral)):
            elements = [
                self._visit_expression(el.value if isinstance(el, ElementLiteral) else el, target_region=target_region)
                for el in node.elements
            ]
            
            prefix = "list"
            if isinstance(node, VectorLiteral):
                prefix = "vector"
            elif isinstance(node, SetLiteral):
                prefix = "set"
            elif isinstance(node, TupleLiteral):
                prefix = "tuple"

            tmp = self._alloc_temp(
                self.new_label(f"tmp_{prefix}"), node, region=current_reg
            )
            # Reconstruct as a call to ZenList_from_args
            args = [str(len(elements))] + elements
            # We use a special callee name that CodeGenerator will map to ZenList_from_args
            self._emit(
                Call(
                    target=tmp,
                    callee="List_from_args",
                    args=args,
                    region=current_reg,
                ),
                node,
            )
            return tmp
        elif isinstance(node, MapLiteral):
             elements = []
             for entry in node.elements:
                 elements.append(self._visit_expression(entry.name, target_region=target_region))
                 elements.append(self._visit_expression(entry.value, target_region=target_region))
             
             tmp = self._alloc_temp(self.new_label("tmp_map"), node, region=current_reg)
             args = [str(len(node.elements))] + elements
             self._emit(Call(target=tmp, callee="Map_from_args", args=args, region=current_reg), node)
             return tmp
        elif isinstance(node, ElementLiteral):
            return self._visit_expression(node.value, target_region=target_region)
        elif isinstance(node, ArgumentLiteral):
            return self._visit_expression(node.value, target_region=target_region)
        elif isinstance(node, IndexExpression):
            obj = self._visit_expression(node.object, target_region=target_region)
            index = self._visit_expression(node.index, target_region=target_region)
            tmp = self._alloc_temp(self.new_label("tmp_idx"), node, region=current_reg)
            self._emit(Call(target=tmp, callee="Value_get_index", args=[obj, index], region=current_reg), node)
            return tmp
        elif isinstance(node, BlockExpression):
            for stmt in node.statements:
                if isinstance(stmt, ExpressionStatement):
                    sym = self._visit_expression(stmt.expression, target_region=target_region)
                else:
                    self._visit(stmt)
                    sym = None
            
            if sym is None:
                tmp = self._alloc_temp(self.new_label("tmp_none"), node, region=current_reg)
                self._emit(Nullify(target=tmp), node)
                return tmp
            return sym

        import sys
        raise Exception(f"SMIRGenerator: unhandled expression node type: {type(node)}")

    def _visit_enumerator(self, node: EnumeratorStatement):
        # We emit an Enumerator instruction that CodeGenerator will use to define
        # constant variants or constructor functions.
        self._emit(Enumerator(name=node.name, variants=node.members), node)

    def _visit_function(self, node: FunctionStatement):
        region_id = f"func_{node.name}"
        old_region = self.current_region
        self.current_region = region_id
        self.region_stack.append(region_id)
        
        self._emit(Label(name=node.name), node)
        self._emit(RegionEnter(id=region_id), node)
        
        # Emit Alloc for parameters with their types
        for param in node.parameters:
             ptype = getattr(param, "resolved_type", None)
             self._emit(Alloc(target=param.name, region=self.current_region, type=ptype), param)

        self._visit(node.block)
        
        # Only emit if not already emitted by return
        self._emit(RegionExit(id=region_id), node)
        
        self.region_stack.pop()
        self.current_region = old_region

    def _visit_block(self, node: BlockStatement):
        region_id = f"block_{node.line}"
        old_region = self.current_region
        self.current_region = region_id
        self.region_stack.append(region_id)
        
        self._emit(RegionEnter(id=region_id), node)
        for stmt in node.statements:
            self._visit(stmt)
        self._emit(RegionExit(id=region_id), node)
        
        self.region_stack.pop()
        self.current_region = old_region

    def _visit_with(self, node: WithStatement):
        # 1. Evaluate the region/resource expression
        expr_result = self._visit_expression(node.expression)
        
        region_id = node.alias if node.alias else self.new_label("with_region")
        
        # 2. If there's an alias, allocate it and move the result to it
        if node.alias:
            self._emit(Alloc(target=node.alias, region=self.current_region, type=None), node)
            self._emit(Move(dest=node.alias, src=expr_result), node)

        # 2. Enter Region
        self._emit(RegionEnter(id=region_id, is_explicit=True), node)
        
        # 3. Block execution
        old_region = self.current_region
        self.current_region = region_id
        for stmt in node.block.statements:
            self._visit(stmt)
        self.current_region = old_region
        
        # 4. Exit Region
        self._emit(RegionExit(id=region_id, is_explicit=True), node)
        
        self.region_stack.pop()
        self.current_region = old_region

    def _visit_defer(self, node: DeferStatement):
        # We need a Release or similar instruction in MIR.
        # For now, let's just visit the block (which is usually a Call).
        # We'll need to update MIR and CodeGenerator to handle 'defer' correctly.
        # In this simplistic version, we'll just emit the instructions.
        # REAL DEFER requires emitting at scope boundaries (Return, RegionExit).
        self._visit(node.block)

    def _visit_assert(self, node: AssertStatement):
        cond = self._visit_expression(node.condition)
        raise_val = self._visit_expression(node.raise_expression) if node.raise_expression else None
        self._emit(Assert(condition=cond, message=raise_val), node)

    def _visit_check_statement(self, node: CheckStatement):
        exit_label = self.new_label("check_exit")
        # 1. Try block
        catch_label = self.new_label("check_catch")
        self._emit(Try(catch_label=catch_label), node)
        
        subject = self._visit_expression(node.expression)
        
        # 2. Handle cases
        if node.cases:
            for case in node.cases:
                next_case_label = self.new_label("case_next")
                match_tmp = self._visit_pattern_match(subject, case.pattern, node)
                self._emit(Branch(condition=match_tmp, true_label=None, false_label=next_case_label), node)
                
                # Case block
                self._visit(case.block)
                self._emit(Jump(target=exit_label), node)
                self._emit(Label(name=next_case_label), node)
        
        # 3. Handle default/or/raise
        # If we reached here without jumping to exit, it depends on whether we had cases.
        # If we had cases and none matched, we fall through to 'or' if it exists.
        if node.cases:
             self._emit(Jump(target=catch_label), node)

        self._emit(Jump(target=exit_label), node)

        # 4. Catch block
        self._emit(Catch(), node)
        self._emit(Label(name=catch_label), node)
        
        if node.or_block:
            self._visit(node.or_block)
        elif node.raise_expression:
            res = self._visit_expression(node.raise_expression)
            self._emit(Raise(value=res), node)
        
        self._emit(EndTry(), node)
        self._emit(Label(name=exit_label), node)

    def _visit_check_expression(self, node: CheckExpression, target_region: Optional[str] = None) -> str:
        current_reg = target_region if target_region else self.current_region
        exit_label = self.new_label("check_expr_exit")
        else_label = self.new_label("check_else")
        
        res_tmp = self._alloc_temp(self.new_label("check_res"), node, region=current_reg)
        
        # 1. Try block
        catch_label = self.new_label("check_expr_catch")
        self._emit(Try(catch_label=catch_label), node)
        
        val_tmp = self._visit_expression(node.expression)
        
        # Check if it's an error (Go-style return)
        is_err = self._alloc_temp(self.new_label("is_err"), node, region=current_reg)
        self._emit(Call(target=is_err, callee="ZenValue_is_type_name", args=[val_tmp, '"Error"'], region=current_reg), node)
        
        err_jump_label = self.new_label("check_expr_err_jump")
        self._emit(Branch(condition=is_err, true_label=err_jump_label, false_label=None), node)
        
        self._emit(Move(dest=res_tmp, src=val_tmp), node)
        self._emit(Jump(target=exit_label), node)
        
        self._emit(Label(name=err_jump_label), node)
        # If it was a return-style error, we still want to go to catch/else logic
        self._emit(Jump(target=catch_label), node)
        
        # 2. Catch block
        self._emit(Catch(), node)
        self._emit(Label(name=catch_label), node)
        
        if node.or_value:
            fb = self._visit_expression(node.or_value)
            self._emit(Move(dest=res_tmp, src=fb), node)
        elif node.raise_expression:
            msg = self._visit_expression(node.raise_expression)
            self._emit(Raise(value=msg), node)
        
        self._emit(EndTry(), node)
        self._emit(Label(name=exit_label), node)
        return res_tmp
        
        self._emit(Label(name=exit_label), node)
        return res_tmp

    def _visit_is_expression(self, node: IsExpression, target_region: Optional[str] = None) -> str:
        subject = self._visit_expression(node.left, target_region=target_region)
        return self._visit_pattern_match(subject, node.right, node)

    def _visit_pattern_match(self, subject: str, pattern: Any, node: ASTNode) -> str:
        current_reg = self.current_region
        tmp_match = self._alloc_temp(self.new_label("tmp_match"), node, region=current_reg)
        
        if isinstance(pattern, WildcardPattern):
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            return tmp_match
            
        if isinstance(pattern, IdentifierPattern):
            # Bind: Alloc and Move
            self._emit(Alloc(target=pattern.name, region=current_reg, type=None), node)
            self._emit(Move(dest=pattern.name, src=subject), node)
            self._emit(Load(target=tmp_match, source="true", type="bool"), node)
            return tmp_match

        if isinstance(pattern, IsMatchPattern):
            self._emit(Call(target=tmp_match, callee="ZenValue_is_type_name", args=[subject, f'"{pattern.type_name}"'], region=current_reg), node)
            return tmp_match

        if isinstance(pattern, ListPattern):
            # 1. Check if subject is a list
            is_list = self._alloc_temp(self.new_label("is_list"), node, region=current_reg)
            self._emit(Call(target=is_list, callee="ZenValue_is_type_name", args=[subject, '"List"'], region=current_reg), node)
            self._emit(Move(dest=tmp_match, src=is_list), node)
            
            for i, elem_pattern in enumerate(pattern.elements):
                elem_val = self._alloc_temp(self.new_label("elem_val"), node, region=current_reg)
                # Box the index i
                idx_tmp = self._alloc_temp(self.new_label("idx"), node, "int", region=current_reg)
                self._emit(Load(target=idx_tmp, source=str(i), type="int"), node)
                self._emit(Call(target=elem_val, callee="Value_get_index", args=[subject, idx_tmp], region=current_reg), node)
                elem_match = self._visit_pattern_match(elem_val, elem_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=elem_match), node)
            return tmp_match

        if isinstance(pattern, MapPattern):
            # 1. Check if subject is a Map
            is_map = self._alloc_temp(self.new_label("is_map"), node, region=current_reg)
            self._emit(Call(target=is_map, callee="ZenValue_is_type_name", args=[subject, '"Map"'], region=current_reg), node)
            self._emit(Move(dest=tmp_match, src=is_map), node)
            
            for key_node, val_pattern in pattern.pairs:
                key_val = self._visit_expression(key_node)
                val_val = self._alloc_temp(self.new_label("val_val"), node, region=current_reg)
                self._emit(Call(target=val_val, callee="Value_get_index", args=[subject, key_val], region=current_reg), node)
                val_match = self._visit_pattern_match(val_val, val_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=val_match), node)
            return tmp_match

        if isinstance(pattern, LiteralPattern):
            val = self._visit_expression(pattern.value)
            self._emit(Compute(target=tmp_match, op="==", left=subject, right=val), node)
            return tmp_match

        if isinstance(pattern, VariantPattern):
            # Use the 3-argument ZenValue_is_variant(val, enum, variant)
            zen_enum = self._alloc_temp(self.new_label("zen_enum"), node, "string", region=current_reg)
            self._emit(Load(target=zen_enum, source=f"`{pattern.enum_name}`", type="string"), node)
            
            zen_variant = self._alloc_temp(self.new_label("zen_variant"), node, "string", region=current_reg)
            self._emit(Load(target=zen_variant, source=f"`{pattern.name}`", type="string"), node)
            
            self._emit(Call(target=tmp_match, callee="ZenValue_is_variant", args=[subject, zen_enum, zen_variant], region=current_reg), node)
            
            # 3. Destructure params
            for i, param_pattern in enumerate(pattern.params):
                param_val = self._alloc_temp(self.new_label("param_val"), node, region=current_reg)
                idx_tmp = self._alloc_temp(self.new_label("idx"), node, "int", region=current_reg)
                self._emit(Load(target=idx_tmp, source=str(i), type="int"), node)
                # Value_get_index can be used for variant data as well if the runtime supports it,
                # or we use a specific ZenValue_get_variant_data. Let's use get_variant_data.
                self._emit(Call(target=param_val, callee="ZenValue_get_variant_data", args=[subject, idx_tmp], region=current_reg), node)
                
                param_match = self._visit_pattern_match(param_val, param_pattern, node)
                self._emit(Compute(target=tmp_match, op="and", left=tmp_match, right=param_match), node)
            
            return tmp_match
            
    def _resolve_member_path(self, obj_type: Any, member_name: str) -> str:
        current = obj_type
        prefix = ""
        while current:
            # Check members
            members = getattr(current, "members", {})
            if isinstance(members, list):
                 if any(m.name == member_name for m in members if hasattr(m, "name")):
                      return prefix + "." + member_name
            elif member_name in members:
                 return prefix + "." + member_name
            
            # Move to parent
            parent = getattr(current, "parent", None)
            if parent:
                 prefix += ".base"
                 if isinstance(parent, str): 
                      # Try to find the parent structure if it's just a string
                      # For now, if it's a string we might be stuck unless mapped
                      break
                 current = parent
            else:
                 break
        return "." + member_name # Fallback
