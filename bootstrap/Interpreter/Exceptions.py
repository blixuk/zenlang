from dataclasses import dataclass
from typing import Any, Optional

class ReturnException(Exception):
    def __init__(self, value: Any):
        self.value = value

@dataclass
class RaiseException(Exception):
    value: Any
    with_value: Optional[Any] = None

class RuntimeBreak(Exception):
    pass

class RuntimeContinue(Exception):
    pass
