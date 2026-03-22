from typing import List, Optional, Any
from Parser.AST import *
from Transpiler.MIR import *

class SMIRGenerator:
    def __init__(self):
        self.instructions: List[MIRInstruction] = []
        self.label_counter = 0
        self.current_region: Optional[str] = "global"

    def new_label(self, prefix="L") -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def generate(self, node: ASTNode) -> List[MIRInstruction]:
        self.instructions = []
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
        # TODO: Add more node types

    def _visit_return(self, node: ReturnStatement):
        res = self._visit_expression(node.value) if node.value else None
        self.instructions.append(Return(value=res))

    def _visit_do(self, node: DoStatement):
        start_label = self.new_label("loop_start")
        end_label = self.new_label("loop_end")
        
        self.instructions.append(Label(start_label))
        
        if node.condition:
            cond = self._visit_expression(node.condition)
            self.instructions.append(Branch(condition=cond, true_label=None, false_label=end_label)) 
            # (Simplified branch: if false, jump to end)
        
        self._visit(node.block)
        self.instructions.append(Jump(target=start_label))
        self.instructions.append(Label(end_label))

    def _visit_when(self, node: WhenStatement):
        exit_label = self.new_label("when_exit")
        
        # Primary when
        next_branch_label = self.new_label("when_next")
        cond = self._visit_expression(node.condition)
        self.instructions.append(Branch(condition=cond, true_label=None, false_label=next_branch_label))
        self._visit(node.when_block)
        self.instructions.append(Jump(target=exit_label))
        self.instructions.append(Label(next_branch_label))
        
        # or when
        for branch in node.conditional_blocks:
            next_branch_label = self.new_label("when_next")
            cond = self._visit_expression(branch["condition"])
            self.instructions.append(Branch(condition=cond, true_label=None, false_label=next_branch_label))
            self._visit(branch["block"])
            self.instructions.append(Jump(target=exit_label))
            self.instructions.append(Label(next_branch_label))
        
        # else
        if node.or_block:
            self._visit(node.or_block)
        
        self.instructions.append(Label(exit_label))

    def _visit_reassignment(self, node: ReassignmentStatement):
        # Move new value to existing target
        expr_result = self._visit_expression(node.value)
        self.instructions.append(Move(dest=node.name, src=expr_result))

    def _visit_assignment(self, node: AssignmentStatement):
        # 1. Allocate space on current region
        self.instructions.append(Alloc(target=node.name, region=self.current_region, type=getattr(node, 'resolved_type', None)))
        
        # 2. Evaluate expression and move to target
        expr_result = self._visit_expression(node.value)
        self.instructions.append(Move(dest=node.name, src=expr_result))

    def _visit_expression(self, node: ASTNode) -> str:
        if isinstance(node, IntegerLiteral):
            tmp = self.new_label("tmp")
            self.instructions.append(Load(target=tmp, source=str(node.value)))
            return tmp
        elif isinstance(node, StringLiteral):
            tmp = self.new_label("tmp_str")
            self.instructions.append(Load(target=tmp, source=f"`{node.value}`"))
            return tmp
        elif isinstance(node, BooleanLiteral):
            tmp = self.new_label("tmp_bool")
            self.instructions.append(Load(target=tmp, source=str(node.value)))
            return tmp
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinaryOperation):
            left = self._visit_expression(node.left)
            right = self._visit_expression(node.right)
            tmp = self.new_label("tmp_bin")
            # We treat BinaryOp as a load for now in S-MIR or a special instruction
            # For S-MIR we'll just use a generic 'Compute' or similar?
            # Let's add 'Compute' to MIR.py
            self.instructions.append(Load(target=tmp, source=f"{left} {node.operator} {right}"))
            return tmp
        elif isinstance(node, CallExpression):
            args = [self._visit_expression(arg) for arg in node.arguments]
            callee = self._visit_expression(node.callee)
            tmp = self.new_label("tmp_call")
            self.instructions.append(Call(target=tmp, callee=callee, args=args))
            return tmp
        return "tmp_none"

    def _visit_function(self, node: FunctionStatement):
        region_id = f"func_{node.name}"
        old_region = self.current_region
        self.current_region = region_id
        
        self.instructions.append(Label(node.name))
        self.instructions.append(RegionEnter(region_id))
        self._visit(node.block)
        self.instructions.append(RegionExit(region_id))
        
        self.current_region = old_region

    def _visit_block(self, node: BlockStatement):
        region_id = f"block_{node.line}"
        old_region = self.current_region
        self.current_region = region_id
        
        self.instructions.append(RegionEnter(region_id))
        for stmt in node.statements:
            self._visit(stmt)
        self.instructions.append(RegionExit(region_id))
        
        self.current_region = old_region
