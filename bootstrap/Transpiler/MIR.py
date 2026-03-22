from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class MIRInstruction:
    pass

# Memory Operations
@dataclass
class Alloc(MIRInstruction):
    target: str
    region: str
    type: Any

@dataclass
class Move(MIRInstruction):
    dest: str
    src: str

@dataclass
class Borrow(MIRInstruction):
    dest: str
    src: str
    mutable: bool = False

@dataclass
class Promote(MIRInstruction):
    target: str
    new_region: str

# Scope Operations
@dataclass
class RegionEnter(MIRInstruction):
    id: str

@dataclass
class RegionExit(MIRInstruction):
    id: str

# Control Flow Operations
@dataclass
class Label(MIRInstruction):
    name: str

@dataclass
class Jump(MIRInstruction):
    target: str

@dataclass
class Branch(MIRInstruction):
    condition: Any # S-MIR operand
    true_label: str
    false_label: str

@dataclass
class Call(MIRInstruction):
    target: str
    callee: str
    args: List[str]

@dataclass
class Return(MIRInstruction):
    value: Optional[Any] = None

# Intermediate Values / Operands
@dataclass
class Load(MIRInstruction):
    target: str
    source: str # Literal or Symbol name
