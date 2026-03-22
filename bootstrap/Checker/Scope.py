from Checker.Type import Symbol


class Scope:
    def __init__(self, parent=None) -> None:
        self.parent: Scope | None = parent
        self.symbols: dict = {}

    def define(self, symbol: Symbol):
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


class ScopeManager:
    def __init__(self) -> None:
        self.global_scope: Scope = Scope()
        self.current_scope: Scope = self.global_scope
        self.level: int = 0

    def push(self) -> None:
        self.current_scope = Scope(self.current_scope)
        self.level += 1

    def pop(self) -> None:
        if self.current_scope.parent is None:
            raise Exception("cannot pop global scope")

        self.current_scope = self.current_scope.parent
        self.level -= 1

    def define(self, symbol: Symbol):
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
