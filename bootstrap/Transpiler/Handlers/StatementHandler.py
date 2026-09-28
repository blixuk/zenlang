from typing import Optional
from Parser.AST import *
from Transpiler.MIR import *

class StatementHandler:
    def _visit_return(self, node: ReturnStatement):
        res = self._visit_expression(node.value) if node.value else None
        
        # Emit RegionExit for all regions entered in this function
        for i in range(len(self.region_stack) - 1, 0, -1):
            rid = self.region_stack[i]
            self._emit(RegionExit(id=rid), node)
            if rid.startswith("func_"):
                 break

        self._emit(Return(value=res), node)

    def _visit_do(self, node: DoStatement):
        start_label = self.new_label("loop_start")
        end_label = self.new_label("loop_end")
        
        self.loop_stack.append({"start": start_label, "end": end_label})
        
        if node.iterator and node.iterable:
            # do for iterator in iterable
            iterable = self._visit_expression(node.iterable)
            
            # Temporary for the iterator object and index
            iter_obj = self._alloc_temp(self.new_label("iter_obj"), node)
            self._emit(Move(dest=iter_obj, src=iterable), node)
            
            index = self._alloc_temp(self.new_label("iter_idx"), node)
            self._emit(Load(target=index, source="0", type="int"), node)
            
            self._emit(Label(name=start_label), node)
            
            # Condition: index < iter_obj.length()
            length = self._alloc_temp(self.new_label("iter_len"), node)
            self._emit(Call(target=length, callee="ZenValue_get_length", args=[iter_obj]), node)
            
            cond = self._alloc_temp(self.new_label("iter_cond"), node)
            self._emit(Compute(target=cond, op="<", left=index, right=length), node)
            self._emit(Branch(condition=cond, true_label=None, false_label=end_label), node)
            
            # Load current item into iterator variable
            iterator_name = self.get_mangled_name(node.iterator)
            iterator_type = getattr(node.iterator, "resolved_type", None)
            # Declared in the current region
            self._emit(Alloc(target=iterator_name, region=self.current_region, type=iterator_type), node)
            self._emit(Call(target=iterator_name, callee="ZenValue_get_at", args=[iter_obj, index]), node)
            
            self._visit(node.body)
            
            # Increment index
            one = self._alloc_temp(self.new_label("tmp_one"), node)
            self._emit(Load(target=one, source="1", type="int"), node)
            self._emit(Compute(target=index, op="+", left=index, right=one), node)
            
            self._emit(Jump(target=start_label), node)
            self._emit(Label(name=end_label), node)
            self.loop_stack.pop()
            return

        # do { body } while cond  — body first, repeat while cond is true
        if node.do_type == "while_post":
             self._emit(Label(name=start_label), node)
             self._visit(node.body)
             cond = self._visit_expression(node.condition)
             self._emit(Branch(condition=cond, true_label=start_label, false_label=None), node)
             self._emit(Label(name=end_label), node)
             self.loop_stack.pop()
             return

        # do { body } until cond  — body first, stop when cond is true
        if node.do_type == "until_post":
             self._emit(Label(name=start_label), node)
             self._visit(node.body)
             cond = self._visit_expression(node.condition)
             self._emit(Branch(condition=cond, true_label=end_label, false_label=None), node)
             self._emit(Jump(target=start_label), node)
             self._emit(Label(name=end_label), node)
             self.loop_stack.pop()
             return

        # do until cond { body }  — pre-test: loop while NOT cond
        if node.do_type == "until":
             self._emit(Label(name=start_label), node)
             if node.condition:
                 cond = self._visit_expression(node.condition)
                 # exit when condition becomes true
                 self._emit(Branch(condition=cond, true_label=end_label, false_label=None), node)
             self._visit(node.body)
             self._emit(Jump(target=start_label), node)
             self._emit(Label(name=end_label), node)
             self.loop_stack.pop()
             return

        # do while cond { body }  — pre-test while
        self._emit(Label(name=start_label), node)
        if node.condition:
            cond = self._visit_expression(node.condition)
            self._emit(Branch(condition=cond, true_label=None, false_label=end_label), node) 
        
        self._visit(node.body)
        self._emit(Jump(target=start_label), node)
        self._emit(Label(name=end_label), node)
        self.loop_stack.pop()

    def _visit_when(self, node: WhenStatement):
        exit_label = self.new_label("when_exit")
        
        if hasattr(node, "branches") and node.branches is not None:
             subject = self._visit_expression(node.condition)
             for branch in node.branches:
                 next_case_label = self.new_label("case_next")
                 match_tmp = self._visit_pattern_match(subject, branch.pattern, node)
                 self._emit(Branch(condition=match_tmp, true_label=None, false_label=next_case_label), node)
                 
                 self._visit(branch.body)
                 self._emit(Jump(target=exit_label), node)
                 self._emit(Label(name=next_case_label), node)
             
             if node.or_block:
                 self._visit(node.or_block)
             
             self._emit(Label(name=exit_label), node)
             return

        next_branch_label = self.new_label("when_next")
        cond = self._visit_expression(node.condition)
        self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
        self._visit(node.when_block)
        self._emit(Jump(target=exit_label), node)
        self._emit(Label(name=next_branch_label), node)
        
        for branch in node.conditional_blocks:
            next_branch_label = self.new_label("when_next")
            cond = self._visit_expression(branch["condition"])
            self._emit(Branch(condition=cond, true_label=None, false_label=next_branch_label), node)
            self._visit(branch["block"])
            self._emit(Jump(target=exit_label), node)
            self._emit(Label(name=next_branch_label), node)
        
        if node.or_block:
            self._visit(node.or_block)
        
        self._emit(Label(name=exit_label), node)

    def _visit_reassignment(self, node: ReassignmentStatement):
        expr_result = self._visit_expression(node.value)
        if hasattr(node, "name") and isinstance(node.name, MemberExpression):
            obj = self._visit_expression(node.name.object)
            prop = node.name.property
            self._emit(SetAttr(obj=obj, prop=prop, value=expr_result), node)
        else:
            target_name = self.get_mangled_name(node)
            self._emit(Move(dest=target_name, src=expr_result), node)

    def _visit_member_reassignment(self, node: MemberReassignmentStatement):
        expr_result = self._visit_expression(node.value)
        obj = self._visit_expression(node.callee)
        prop = node.property
        
        obj_type = getattr(node.callee, "resolved_type", None)
        path = prop
        if obj_type:
             path = self._resolve_member_path(obj_type, prop)
             if path.startswith("."): path = path[1:]
        
        tname = self.get_mangled_type_name(obj_type) if obj_type else None
        self._emit(SetAttr(obj=obj, prop=path, value=expr_result, type=tname), node)

    def _visit_index_reassignment(self, node: IndexReassignmentStatement):
        val = self._visit_expression(node.value)
        obj = self._visit_expression(node.callee)
        idx = self._visit_expression(node.index)
        self._emit(Call(target=None, callee="Value_set_index", args=[obj, idx, val], region=self.current_region), node)

    def _visit_assignment(self, node: AssignmentStatement):
        all_type = getattr(node, "resolved_type", None)
        target_name = self.get_mangled_name(node)
        self._emit(Alloc(target=target_name, region=self.current_region, type=all_type), node)
        
        expr_result = self._visit_expression(node.value)
        self._emit(Move(dest=target_name, src=expr_result), node)

    def _visit_enumerator(self, node: EnumeratorStatement):
        self._emit(Enumerator(name=node.name, variants=node.members), node)

    def _visit_function(self, node: FunctionStatement):
        region_id = f"func_{node.name}"
        old_region = self.current_region
        self.current_region = region_id
        self.region_stack.append(region_id)
        
        self._emit(Label(name=node.name), node)
        self._emit(RegionEnter(id=region_id), node)
        
        for param in node.parameters:
             ptype = getattr(param, "resolved_type", None)
             target_name = self.get_mangled_name(param)
             self._emit(Alloc(target=target_name, region=self.current_region, type=ptype), param)

        self._visit(node.body)
        self._emit(RegionExit(id=region_id), node)
        
        self.region_stack.pop()
        self.current_region = old_region

    def _visit_task(self, node: TaskStatement):
        region_id = f"task_{node.name}"
        old_region = self.current_region
        self.current_region = region_id
        self.region_stack.append(region_id)
        
        self._emit(Label(name=node.name), node)
        self._emit(RegionEnter(id=region_id), node)
        
        for param in node.parameters:
             ptype = getattr(param, "resolved_type", None)
             target_name = self.get_mangled_name(param)
             self._emit(Alloc(target=target_name, region=self.current_region, type=ptype), param)

        self._visit(node.body)
        self._emit(RegionExit(id=region_id), node)
        
        self.region_stack.pop()
        self.current_region = old_region

    def _visit_block(self, node: BlockStatement):
        if not hasattr(self.__class__, "_global_block_counter"):
            self.__class__._global_block_counter = 0
        self.__class__._global_block_counter += 1
        region_id = f"block_{node.line}_{self.__class__._global_block_counter}"
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
        expr_result = self._visit_expression(node.expression)
        region_id = node.alias if node.alias else self.new_label("with_region")
        
        if node.alias:
            self._emit(Alloc(target=node.alias, region=self.current_region, type=None), node)
            self._emit(Move(dest=node.alias, src=expr_result), node)

        self._emit(RegionEnter(id=region_id, is_explicit=True), node)
        
        old_region = self.current_region
        self.current_region = region_id
        # AST WithStatement uses `body` (BlockStatement); older drafts used `block`.
        body = getattr(node, "body", None) or getattr(node, "block", None)
        if body is not None:
            stmts = getattr(body, "statements", None)
            if stmts is not None:
                for stmt in stmts:
                    self._visit(stmt)
            else:
                self._visit(body)
        self.current_region = old_region
        
        self._emit(RegionExit(id=region_id, is_explicit=True), node)

    def _visit_defer(self, node: DeferStatement):
        self._visit(node.body)

    def _visit_raise_statement(self, node: RaiseStatement):
        val = self._visit_expression(node.value) if node.value else None
        self._emit(Raise(value=val), node)

    def _visit_assert(self, node: AssertStatement):
        cond = self._visit_expression(node.condition)
        raise_val = self._visit_expression(node.raise_expression) if node.raise_expression else None
        self._emit(Assert(condition=cond, message=raise_val), node)

    def _visit_check_statement(self, node: CheckStatement):
        exit_label = self.new_label("check_exit")
        catch_label = self.new_label("check_catch")
        self._emit(Try(catch_label=catch_label), node)
        
        subject = self._visit_expression(node.expression)
        
        if node.cases:
            for case in node.cases:
                next_case_label = self.new_label("case_next")
                match_tmp = self._visit_pattern_match(subject, case.pattern, node)
                # Optional guard: case n when n >= 10
                guard_expr = getattr(case, "guard", None)
                if guard_expr is not None:
                    guard_tmp = self._visit_expression(guard_expr)
                    self._emit(Compute(target=match_tmp, op="and", left=match_tmp, right=guard_tmp), node)
                self._emit(Branch(condition=match_tmp, true_label=None, false_label=next_case_label), node)
                
                self._visit(case.body)
                self._emit(Jump(target=exit_label), node)
                self._emit(Label(name=next_case_label), node)
        
        if node.cases:
             self._emit(Jump(target=catch_label), node)

        self._emit(Jump(target=exit_label), node)

        self._emit(Catch(error_alias=getattr(node, "error_alias", None)), node)
        self._emit(Label(name=catch_label), node)
        
        if node.or_block:
            self._visit(node.or_block)
        elif node.raise_expression:
            res = self._visit_expression(node.raise_expression)
            self._emit(Raise(value=res), node)
        
        self._emit(EndTry(), node)
        self._emit(Label(name=exit_label), node)

    def _visit_scope(self, node: ScopeStatement):
        old_scope = self.current_scope
        self.scope_stack.append(node.name)
        self.current_scope = "_".join(self.scope_stack)
        self._visit(node.body)
        self.scope_stack.pop()
        self.current_scope = old_scope

    def _visit_break(self, node: BreakStatement):
        if self.loop_stack:
            self._emit(Jump(target=self.loop_stack[-1]["end"]), node)

    def _visit_continue(self, node: ContinueStatement):
        if self.loop_stack:
            self._emit(Jump(target=self.loop_stack[-1]["start"]), node)
