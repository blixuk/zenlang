import os
from typing import List, Optional, Any, Union
from Checker.Type import SymbolKind
from Parser.AST import *
from Transpiler.MIR import *

from Transpiler.Handlers.MangleHandler import MangleHandler
from Transpiler.Handlers.ExpressionHandler import ExpressionHandler
from Transpiler.Handlers.StatementHandler import StatementHandler
from Transpiler.Handlers.PatternHandler import PatternHandler

class SMIRGenerator(StatementHandler, ExpressionHandler, PatternHandler, MangleHandler):
    _global_label_counter = 0

    def __init__(
        self,
        filename: Optional[str] = None,
        main_file: Optional[str] = None,
        global_variable_names: set = None,
        pending_lambdas: list = None,
        module_aliases: dict = None,
        current_scope: Optional[str] = None,
        imported_modules: set = None,
    ):
        self.instructions: List[MIRInstruction] = []
        self.filename = filename
        self.main_file = main_file
        self.global_variable_names = global_variable_names if global_variable_names is not None else set()
        self.pending_lambdas = pending_lambdas if pending_lambdas is not None else []
        self.module_aliases = module_aliases if module_aliases is not None else {}
        self.imported_modules = imported_modules if imported_modules is not None else set()
        self.locals = set()
        self.allocated_vars = set()
        # Inherit enclosing named-scope prefix (e.g. Sentence) so sibling calls
        # like to_words mangle to text_Sentence_to_words, matching definitions.
        self.current_scope = current_scope
        self.scope_stack = []
        self.current_function = None
        self.current_region: Optional[str] = "global"
        self.region_stack: List[str] = ["global"]
        self.loop_stack: List[dict] = []

    def new_label(self, prefix="L") -> str:
        label = f"{prefix}_{SMIRGenerator._global_label_counter}"
        SMIRGenerator._global_label_counter += 1
        return label

    def _emit(self, instr: MIRInstruction, node: ASTNode):
        if isinstance(instr, Alloc):
            if instr.target in self.allocated_vars:
                # print(f"DEBUG [SMIR]: Skipping duplicate Alloc for {instr.target}")
                return
            self.allocated_vars.add(instr.target)
        
        instr.line = getattr(node, 'line', 0)
        instr.column = getattr(node, 'column', 0)
        instr.filename = getattr(node, 'filename', None) or self.filename
        self.instructions.append(instr)

    def _alloc_temp(self, name: str, node: ASTNode, type: Any = None, region: Optional[str] = None):
        r = region if region else self.current_region
        self._emit(Alloc(target=name, region=r, type=type), node)
        return name

    def generate(self, node: ASTNode, pre_allocated_symbols: List[str] = None) -> List[MIRInstruction]:
        self.instructions = []
        self._visit(node)
        return self.instructions

    def _visit(self, node: ASTNode):
        if isinstance(node, Program) or isinstance(node, Statements):
            for stmt in node.statements:
                self._visit(stmt)
        elif isinstance(node, FunctionStatement):
            self._visit_function(node)
        elif isinstance(node, TaskStatement):
            self._visit_task(node)
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
        elif isinstance(node, ScopeStatement):
            self._visit_scope(node)
        elif isinstance(node, IndexReassignmentStatement):
            self._visit_index_reassignment(node)
        elif isinstance(node, BreakStatement):
            self._visit_break(node)
        elif isinstance(node, ContinueStatement):
            self._visit_continue(node)
        elif isinstance(node, BlockExpression):
            for stmt in node.statements:
                self._visit(stmt)
        elif isinstance(node, AwaitExpression):
            return self._visit_await(node, target_region=self.current_region)
