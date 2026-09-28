from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class MIRInstruction:
    line: int = 0
    column: int = 0
    filename: Optional[str] = None
    region: Optional[str] = None

# Memory Operations
@dataclass
class Alloc(MIRInstruction):
    target: str = ""
    region: str = ""
    type: Any = None

@dataclass
class Move(MIRInstruction):
    dest: str = ""
    src: str = ""

@dataclass
class Borrow(MIRInstruction):
    dest: str = ""
    src: str = ""
    mutable: bool = False

@dataclass
class Promote(MIRInstruction):
    target: str = ""
    new_region: str = ""

# Scope Operations
@dataclass
class RegionEnter(MIRInstruction):
    id: str = ""
    is_explicit: bool = False

@dataclass
class RegionExit(MIRInstruction):
    id: str = ""
    is_explicit: bool = False

# Control Flow Operations
@dataclass
class Label(MIRInstruction):
    name: str = ""

@dataclass
class Jump(MIRInstruction):
    target: str = ""

@dataclass
class Branch(MIRInstruction):
    condition: Any = None
    true_label: Optional[str] = None
    false_label: Optional[str] = None

@dataclass
class Call(MIRInstruction):
    target: Optional[str] = None
    callee: str = ""
    args: List[str] = field(default_factory=list)

@dataclass
class Return(MIRInstruction):
    value: Optional[Any] = None

@dataclass
class Assert(MIRInstruction):
    condition: Any = None
    message: Optional[str] = None

@dataclass
class Load(MIRInstruction):
    target: str = ""
    source: str = ""
    type: Optional[str] = None

# --- Lowered MIR (L-MIR) ---
@dataclass
class ArenaAlloc(MIRInstruction):
    target: str = ""
    arena_id: str = ""
    type: Any = None

@dataclass
class HeapAlloc(MIRInstruction):
    target: str = ""
    type: Any = None

@dataclass
class ArenaCreate(MIRInstruction):
    arena_id: str = ""

@dataclass
class ArenaReset(MIRInstruction):
    arena_id: str = ""

@dataclass
class ArenaFree(MIRInstruction):
    arena_id: str = ""

@dataclass
class PointerCopy(MIRInstruction):
    dest: str = ""
    src: str = ""

@dataclass
class Nullify(MIRInstruction):
    target: str = ""

@dataclass
class Compute(MIRInstruction):
    target: str = ""
    op: str = ""
    left: str = ""
    right: str = ""

@dataclass
class GetAttr(MIRInstruction):
    target: str = ""
    obj: str = ""
    prop: str = ""
    type: Optional[str] = None

@dataclass
class SetAttr(MIRInstruction):
    obj: str = ""
    prop: str = ""
    value: str = ""
    type: Optional[str] = None

@dataclass
class Enumerator(MIRInstruction):
    name: str = ""
    variants: List[Any] = field(default_factory=list)

@dataclass
class Task(MIRInstruction):
    name: str = ""
    parameters: List[Any] = field(default_factory=list)
    body: Any = None

@dataclass
class Spawn(MIRInstruction):
    target: str = ""
    callee: str = ""
    args: List[str] = field(default_factory=list)

@dataclass
class Await(MIRInstruction):
    target: str = ""
    handle: str = ""

@dataclass
class Try(MIRInstruction):
    catch_label: str = ""

@dataclass
class Catch(MIRInstruction):
    error_alias: Optional[str] = None

@dataclass
class EndTry(MIRInstruction):
    pass

@dataclass
class Raise(MIRInstruction):
    value: str = ""
