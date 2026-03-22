from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class RegionNode:
    id: str
    parent: Optional['RegionNode'] = None
    children: List['RegionNode'] = field(default_factory=list)

    def outlives(self, other: 'RegionNode') -> bool:
        """Returns True if this region outlives (is a parent of) the other region."""
        curr = other
        while curr:
            if curr == self:
                return True
            curr = curr.parent
        return False

class Scope:
    def __init__(self, parent=None, region: Optional[RegionNode] = None) -> None:
        self.parent: Scope | None = parent
        self.symbols: dict = {}
        self.region: RegionNode | None = region

    def define(self, symbol: 'Symbol'):
        if symbol.name in self.symbols:
            raise Exception(f"redeclaration: {symbol.name}")

        self.symbols[symbol.name] = symbol

    def lookup(self, name: str, current_scope_only: bool = False):
        if current_scope_only:
            return self.symbols.get(name)

        scope: Scope | None = self

        while scope:
            if name in scope.symbols:
                return scope.symbols[name]

            scope = scope.parent

        return None


from Checker.Type import Symbol

class ScopeManager:
    def __init__(self) -> None:
        self.global_region: RegionNode = RegionNode(id="global")
        self.global_scope: Scope = Scope(region=self.global_region)
        self.current_scope: Scope = self.global_scope
        self.current_region: RegionNode = self.global_region
        self.level: int = 0

    def push(self, region_id: Optional[str] = None) -> None:
        region = self.current_region
        if region_id:
            region = RegionNode(id=region_id, parent=self.current_region)
            self.current_region.children.append(region)
            self.current_region = region
            
        self.current_scope = Scope(self.current_scope, region=self.current_region)
        self.level += 1

    def pop(self) -> None:
        if self.current_scope.parent is None:
            raise Exception("cannot pop global scope")

        # If the current scope is the start of a new region, pop the region too
        if self.current_scope.region != self.current_scope.parent.region:
            self.current_region = self.current_region.parent

        self.current_scope = self.current_scope.parent
        self.level -= 1

    def define(self, symbol: 'Symbol'):
        self.current_scope.define(symbol)

    def lookup(self, name: str, current_scope_only: bool = False):
        return self.current_scope.lookup(name, current_scope_only)

    def get_parent(self):
        return self.current_scope.parent

    def get_symbols(self):
        return self.current_scope.symbols

    def get_global_symbols(self):
        return self.global_scope.symbols

    def get_global_scope(self):
        return self.global_scope

    def get_current_scope(self):
        return self.current_scope

    def get_current_level(self) -> int:
        return self.level
