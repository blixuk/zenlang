from typing import List, Any
from .MIR import *

class SMIRLowerer:
    """
    Translates analyzed S-MIR into explicit memory management instructions (L-MIR).
    """
    def __init__(self, instructions: List[MIRInstruction]):
        self.instructions = instructions
        self.output: List[MIRInstruction] = []

    def lower(self) -> List[MIRInstruction]:
        for instr in self.instructions:
            self._lower_instruction(instr)
        return self.output

    def _lower_instruction(self, instr: MIRInstruction):
        if isinstance(instr, Alloc):
            # Resolve to ArenaAlloc or HeapAlloc based on region
            if instr.region == "global" or instr.region == "heap":
                self.output.append(HeapAlloc(
                    target=instr.target, 
                    type=instr.type, 
                    line=instr.line, 
                    column=instr.column,
                    filename=instr.filename
                ))
            else:
                self.output.append(ArenaAlloc(
                    target=instr.target, 
                    arena_id=instr.region, 
                    type=instr.type, 
                    line=instr.line, 
                    column=instr.column,
                    filename=instr.filename
                ))
        
        elif isinstance(instr, Move):
            # A move is a pointer copy followed by nullifying the source
            self.output.append(PointerCopy(
                dest=instr.dest, 
                src=instr.src, 
                line=instr.line, 
                column=instr.column,
                filename=instr.filename
            ))
            self.output.append(Nullify(
                target=instr.src, 
                line=instr.line, 
                column=instr.column,
                filename=instr.filename
            ))
            
        elif isinstance(instr, RegionEnter):
            if instr.is_explicit:
                self.output.append(instr)
            else:
                self.output.append(ArenaCreate(
                    arena_id=instr.id, 
                    line=instr.line, 
                    column=instr.column,
                    filename=instr.filename
                ))
            
        elif isinstance(instr, RegionExit):
            if instr.is_explicit:
                self.output.append(instr)
            elif instr.id.startswith("loop_"):
                self.output.append(ArenaReset(
                    arena_id=instr.id, 
                    line=instr.line, 
                    column=instr.column,
                    filename=instr.filename
                ))
            else:
                self.output.append(ArenaFree(
                    arena_id=instr.id, 
                    line=instr.line, 
                    column=instr.column,
                    filename=instr.filename
                ))
            
        else:
            # Pass through control flow, calls, loads, etc.
            self.output.append(instr)
