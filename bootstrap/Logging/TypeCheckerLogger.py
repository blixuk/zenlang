
from Logging.Diagnostic import Diagnostic, Span, DiagnosticSeverity

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
BOLD = "\033[1m"
RESET = "\033[0m"

class Debug(Exception):
    def __init__(self, name: str, message: str, attachment: any = None):
        self.name: str = name
        self.message: str = message
        self.attachment: str = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"[{self.name}] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}\n    Attachment: {YELLOW}{self.attachment}{RESET}"
        else:
            return f"[{self.name}] [{BLUE}Debug{RESET}] {GREEN}{self.message}{RESET}"

class Error(Exception):
    def __init__(self, name: str, source_path: str, message: str, attachment: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.message: str = message
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        span = None
        if self.attachment:
            span = Span.from_node(self.attachment, self.source_path)
        diag = Diagnostic(DiagnosticSeverity.ERROR, self.message, code="TypeCheck", span=span)
        return diag.render()

class VariableUndefinedError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        var_name = getattr(self.attachment, 'name', str(self.attachment)) if self.attachment else "variable"
        span = Span.from_node(self.attachment, self.source_path, label=f"undefined variable `{var_name}`") if self.attachment else None
        diag = Diagnostic(
            DiagnosticSeverity.ERROR,
            f"Variable `{var_name}` is not defined",
            code="E0101: UndefinedVariable",
            span=span
        ).add_hint(f"Check spelling or declare `{var_name}` with `let {var_name} -> ...` before use.")
        return diag.render()

class VariableImmutableError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        var_name = getattr(self.attachment, 'name', str(self.attachment)) if self.attachment else "variable"
        span = Span.from_node(self.attachment, self.source_path, label=f"`{var_name}` cannot be reassigned") if self.attachment else None
        diag = Diagnostic(
            DiagnosticSeverity.ERROR,
            f"Cannot reassign immutable variable `{var_name}`",
            code="E0103: ImmutableVariable",
            span=span
        ).add_note(f"Variables declared without mutable annotations cannot be rebound in this scope.")
        return diag.render()

class VariableTypeError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None, declared_type: any = None, value_type: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        self.value_type = value_type
        self.declared_type = declared_type
        super().__init__(self.__str__())

    def __str__(self) -> str:
        var_name = getattr(self.attachment, 'name', str(self.attachment)) if self.attachment else "variable"
        decl_name = getattr(self.declared_type, 'name', str(self.declared_type)) if self.declared_type else "?"
        val_name = getattr(self.value_type, 'name', str(self.value_type)) if self.value_type else "?"
        span = Span.from_node(self.attachment, self.source_path, label=f"expected `{decl_name}`, found `{val_name}`") if self.attachment else None
        diag = Diagnostic(
            DiagnosticSeverity.ERROR,
            f"Type mismatch for variable `{var_name}`",
            code="E0102: TypeMismatch",
            span=span
        ).add_note(f"Variable was declared with type `{decl_name}`, but value has type `{val_name}`.")
        return diag.render()

class TypeUnificationError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None, expected_type: any = None, recieved_type: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        self.expected_type = expected_type
        self.recieved_type = recieved_type
        super().__init__(self.__str__())

    def __str__(self) -> str:
        target_name = getattr(self.attachment, 'name', str(self.attachment)) if self.attachment else "expression"
        exp_name = getattr(self.expected_type, 'name', str(self.expected_type)) if self.expected_type else str(self.expected_type)
        got_name = getattr(self.recieved_type, 'name', str(self.recieved_type)) if self.recieved_type else str(self.recieved_type)
        span = Span.from_node(self.attachment, self.source_path, label=f"expected `{exp_name}`, got `{got_name}`") if self.attachment else None
        diag = Diagnostic(
            DiagnosticSeverity.ERROR,
            f"Type unification failed for `{target_name}`",
            code="E0104: TypeUnification",
            span=span
        ).add_note(f"Expected type `{exp_name}`, but encountered `{got_name}`.")
        return diag.render()

class TypeCheckerLogger:

    def __init__(self, source_path: str = None):
        self.name: str = 'TypeChecker'
        self.source_path: str = source_path
        self.debugs: list[Debug] = []
        self.errors: list[Error] = []
    
    def debug(self, message: str, attachment: any = None):
            error: Debug = Debug(self.name, message, attachment)
            self.debugs.append(error)
            return error

    def print_debugs(self):
        for debug in self.debugs:
            print(debug)

    def error(self, message: str, attachment: any = None):
        error: Error = Error(self.name, self.source_path, message, attachment)
        self.errors.append(error)
        return error

    def error_variable_undefined(self, attachment: any = None):
        error: VariableUndefinedError = VariableUndefinedError(self.name, self.source_path, attachment)
        self.errors.append(error)
        return error

    def error_variable_immutable(self, attachment: any = None):
        error: VariableImmutableError = VariableImmutableError(self.name, self.source_path, attachment)
        self.errors.append(error)
        return error

    def error_variable_type(self, attachment: any = None, symbol_type: str = None, declared_type: str = None):
        error: VariableTypeError = VariableTypeError(self.name, self.source_path, attachment, symbol_type, declared_type)
        self.errors.append(error)
        return error

    def error_type_unification(self, a_type: str = None, b_type: str = None, attachment: any = None,):
        error: TypeUnificationError = TypeUnificationError(self.name, self.source_path, attachment, a_type, b_type)
        self.errors.append(error)
        return error

    def print_errors(self):
        seen: set = set()
        for error in self.errors:
            rendered = str(error)
            if rendered not in seen:
                print(rendered, file=__import__('sys').stderr)
                seen.add(rendered)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

