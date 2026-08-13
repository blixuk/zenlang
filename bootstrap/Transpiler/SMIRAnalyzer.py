from typing import List, Dict, Optional, Set
from Transpiler.MIR import *
from Checker.Scope import RegionNode
from dataclasses import dataclass, field

@dataclass
class BasicBlock:
    id: int
    instructions: List[MIRInstruction] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)
    predecessors: List['BasicBlock'] = field(default_factory=list)
    
    # Dataflow sets
    gen_moved: Set[str] = field(default_factory=set)
    kill_moved: Set[str] = field(default_factory=set)
    in_moved: Set[str] = field(default_factory=set)
    out_moved: Set[str] = field(default_factory=set)

class SMIRAnalyzer:
    def __init__(self, instructions: List[MIRInstruction], region_root: RegionNode):
        self.instructions = instructions
        self.region_root = region_root
        self.symbol_allocs: Dict[str, Alloc] = {}
        self.blocks: List[BasicBlock] = []
        self.label_to_block: Dict[str, BasicBlock] = {}
        
    def analyze(self):
        self._build_region_tree()
        self._find_allocs()
        self._promotion_pass()
        self._build_cfg()
        
        # print("DEBUG [Analyzer] CFG:")
        # for block in self.blocks:
        #     print(f"  Block {block.id}: {[str(i) for i in block.instructions]}")
        #     print(f"    Preds: {[p.id for p in block.predecessors]}")
        #     print(f"    Succs: {[s.id for s in block.successors]}")
            
        self._move_validation_pass()
        
    def _build_region_tree(self):
        # We start with the passed region_root (usually just 'global')
        stack = [self.region_root]
        for instr in self.instructions:
            instr.region = stack[-1].id
            if isinstance(instr, RegionEnter):
                # New child region
                child = RegionNode(id=instr.id, parent=stack[-1])
                stack[-1].children.append(child)
                stack.append(child)
            elif isinstance(instr, RegionExit):
                if len(stack) > 1:
                    stack.pop()
    
    def _find_allocs(self):
        for instr in self.instructions:
            if isinstance(instr, Alloc):
                self.symbol_allocs[instr.target] = instr

    def _build_cfg(self):
        if not self.instructions: return

        current_block = BasicBlock(id=0)
        self.blocks.append(current_block)
        
        for instr in self.instructions:
            if isinstance(instr, Label):
                if current_block.instructions:
                    # New block for the label
                    new_block = BasicBlock(id=len(self.blocks))
                    # Link sequential blocks
                    current_block.successors.append(new_block)
                    new_block.predecessors.append(current_block)
                    current_block = new_block
                    self.blocks.append(current_block)
                
                self.label_to_block[instr.name] = current_block
                current_block.instructions.append(instr)
            
            elif isinstance(instr, (Jump, Branch, Return)):
                current_block.instructions.append(instr)
                # Next instruction (if any) starts a new block
                current_block = BasicBlock(id=len(self.blocks))
                self.blocks.append(current_block)
            
            else:
                current_block.instructions.append(instr)

        # Remove empty blocks
        self.blocks = [b for b in self.blocks if b.instructions]

        # Second pass: Connect edges
        for i, block in enumerate(self.blocks):
            last_instr = block.instructions[-1]
            
            if isinstance(last_instr, Jump):
                target = self.label_to_block.get(last_instr.target)
                if target and target not in block.successors:
                    block.successors.append(target)
                    target.predecessors.append(block)
            elif isinstance(last_instr, Branch):
                if last_instr.true_label:
                    target = self.label_to_block.get(last_instr.true_label)
                    if target and target not in block.successors:
                        block.successors.append(target)
                        target.predecessors.append(block)
                else:
                    # Fallthrough
                    if i + 1 < len(self.blocks):
                        target = self.blocks[i+1]
                        if target not in block.successors:
                            block.successors.append(target)
                            target.predecessors.append(block)

                if last_instr.false_label:
                    target = self.label_to_block.get(last_instr.false_label)
                    if target and target not in block.successors:
                        block.successors.append(target)
                        target.predecessors.append(block)
                else:
                     # Fallthrough (though usually Branch has both or one is None for fallthrough)
                     if i + 1 < len(self.blocks):
                        target = self.blocks[i+1]
                        if target not in block.successors:
                            block.successors.append(target)
                            target.predecessors.append(block)

            elif not isinstance(last_instr, Return):
                # Fallthrough
                if i + 1 < len(self.blocks):
                    target = self.blocks[i+1]
                    if target not in block.successors:
                        block.successors.append(target)
                        target.predecessors.append(block)
                
    def _move_validation_pass(self):
        # 1. Compute Gen/Kill for each block
        for block in self.blocks:
            for instr in block.instructions:
                if isinstance(instr, Move):
                    # Destination becomes valid, source becomes moved
                    if instr.src in self.symbol_allocs:
                        block.gen_moved.add(instr.src)
                        if instr.src in block.kill_moved:
                             block.kill_moved.remove(instr.src)
                    
                    if instr.dest in self.symbol_allocs:
                        block.kill_moved.add(instr.dest)
                        if instr.dest in block.gen_moved:
                            block.gen_moved.remove(instr.dest)
                            
                elif isinstance(instr, Alloc):
                    block.kill_moved.add(instr.target)
                    if instr.target in block.gen_moved:
                        block.gen_moved.remove(instr.target)
        
        # 2. Fixed-point iteration
        changed = True
        while changed:
            changed = False
            for block in self.blocks:
                new_in = set()
                for pred in block.predecessors:
                    new_in.update(pred.out_moved)
                
                if new_in != block.in_moved:
                    block.in_moved = new_in
                    changed = True
                
                new_out = block.gen_moved.union(block.in_moved - block.kill_moved)
                if new_out != block.out_moved:
                    block.out_moved = new_out
                    changed = True

        # 3. Check for violations
        for block in self.blocks:
            current_moved = set(block.in_moved)
            for instr in block.instructions:
                # Check for use of moved variable
                used_vars = self._get_used_vars(instr)
                for var in used_vars:
                    if var in current_moved:
                        self._report_use_after_move(var, instr)
                
                # Update state within block
                if isinstance(instr, Move):
                    if instr.src in self.symbol_allocs:
                        current_moved.add(instr.src)
                    if instr.dest in current_moved:
                        current_moved.remove(instr.dest)
                elif isinstance(instr, Alloc):
                    if instr.target in current_moved:
                        current_moved.remove(instr.target)

    def _get_used_vars(self, instr: MIRInstruction) -> Set[str]:
        import re
        vars = set()
        if isinstance(instr, Move):
            if instr.src in self.symbol_allocs:
                vars.add(instr.src)
        elif isinstance(instr, Borrow):
            if instr.src in self.symbol_allocs:
                vars.add(instr.src)
        elif isinstance(instr, Call):
            for arg in instr.args:
                if arg in self.symbol_allocs:
                    vars.add(arg)
        elif isinstance(instr, Return):
            if instr.value and instr.value in self.symbol_allocs:
                vars.add(instr.value)
        elif isinstance(instr, Load):
             # Extract variables from source string (e.g. "x + y")
             found = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', instr.source)
             for f in found:
                 if f in self.symbol_allocs:
                     vars.add(f)
        elif isinstance(instr, Compute):
            if instr.left in self.symbol_allocs:
                vars.add(instr.left)
            if instr.right in self.symbol_allocs:
                vars.add(instr.right)
        elif isinstance(instr, GetAttr):
            if instr.obj in self.symbol_allocs:
                vars.add(instr.obj)
        elif isinstance(instr, SetAttr):
            if instr.obj in self.symbol_allocs:
                vars.add(instr.obj)
            if instr.value in self.symbol_allocs:
                vars.add(instr.value)
        elif isinstance(instr, Branch):
            if instr.condition in self.symbol_allocs:
                vars.add(instr.condition)
        elif isinstance(instr, Assert):
            if instr.condition in self.symbol_allocs:
                vars.add(instr.condition)
            if instr.message in self.symbol_allocs:
                vars.add(instr.message)
        elif isinstance(instr, Raise):
            if instr.value in self.symbol_allocs:
                vars.add(instr.value)
        return vars

    def _report_use_after_move(self, var: str, instr: MIRInstruction):
        # Print warning/error, but do not raise an exception to allow compiling.
        print(f"[SMIRAnalyzer] Use-After-Move Error: Variable '{var}' used at {instr.line}:{instr.column} after being moved. Instruction: {instr}")

    def _promotion_pass(self):
        # Run multiple passes to converge (promotion can propagate through moves)
        for _ in range(5):
            # Process in reverse to catch Return -> Move chains
            for instr in reversed(self.instructions):
                if isinstance(instr, Move):
                    self._check_move_promotion(instr)
                elif isinstance(instr, Return):
                    self._check_return_promotion(instr)

    def _check_move_promotion(self, instr: Move):
        # Find src and dest allocs
        src_alloc = self.symbol_allocs.get(instr.src)
        dest_alloc = self.symbol_allocs.get(instr.dest)
        
        if src_alloc and dest_alloc:
            # If dest region outlives src region, src must be promoted to dest region
            src_node = self.region_root.find(src_alloc.region)
            dest_node = self.region_root.find(dest_alloc.region)
            
            if src_node and dest_node and dest_node.outlives(src_node):
                # Promote src
                src_alloc.region = dest_alloc.region
        else:
             pass

    def _check_return_promotion(self, instr: Return):
        if not instr.value: return
        
        src_alloc = self.symbol_allocs.get(instr.value)
        if src_alloc:
            src_node = self.region_root.find(src_alloc.region)
            if not src_node:
                 return

            func_node = src_node
            while func_node and not func_node.id.startswith("func_"):
                func_node = func_node.parent
            
            if func_node and func_node.parent:
                src_alloc.region = func_node.parent.id
