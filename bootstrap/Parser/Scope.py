SCOPES: list = ["global", "block", "loop", "when", "structure", "function", "class"]


class Scope:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.level: int = 0

    def enter(self) -> int:
        self.level += 1
        return self.level

    def exit(self) -> int:
        self.level -= 1
        return self.level


class ScopeManager:
    def __init__(self) -> None:
        self.scopes: dict = {}

        self._create_scopes()

    def create_scope(self, name: str) -> Scope:
        self.scopes[name] = Scope(name)
        return self.scopes[name]

    def _create_scopes(self) -> None:
        for name in SCOPES:
            self.scopes[name] = Scope(name)

    def is_scope(self, name: str) -> bool:
        return name in SCOPES

    def get_scope(self, name: str) -> Scope:
        return self.scopes[name]

    def set_scope(self, name: str, scope: Scope) -> None:
        self.scopes[name] = scope

    def get_scope_level(self, name: str) -> int:
        return self.scopes[name].level

    def get_current_scope_level(self) -> int:
        return self.scopes["global"].level

    def enter(self, name: str) -> int:
        self.scopes["global"].enter()
        self.scopes[name].enter()
        return self.scopes[name].level

    def exit(self, name: str) -> int:
        self.scopes["global"].exit()
        self.scopes[name].exit()
        return self.scopes[name].level
