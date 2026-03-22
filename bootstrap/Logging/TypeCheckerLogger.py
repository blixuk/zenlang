
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
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
        if self.attachment:
            return f"""[{self.name}] [{RED}Error{RESET}]
{YELLOW}{self.message}{RESET}
    {WHITE}'{getattr(self.attachment, 'name', str(self.attachment))}': {getattr(self.attachment, 'line', '?')}, {getattr(self.attachment, 'column', '?')}{RESET}
{WHITE}{self.source_path}:{getattr(self.attachment, 'line', '?')}:{getattr(self.attachment, 'column', '?')}{RESET}"""
        else:
            return f"[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"

class VariableUndefinedError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"""[{self.name}] [{RED}VariableUndefinedError{RESET}]
{YELLOW}Variable '{self.attachment.name}' has not been defined{RESET}   
    '{self.attachment.name}' : {WHITE}{self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}VariableUndefinedError{RESET}] {YELLOW}Variable '{self.attachment.name}' has not been defined{RESET}"

class VariableImmutableError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"""[{self.name}] [{RED}VariableImmutableError{RESET}]
{YELLOW}'{self.attachment.name}' is Immutable and can not be reassigned{RESET}
    '{self.attachment.name}' : {WHITE}{self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}VariableImmutableError{RESET}] {YELLOW}Unification Type Mismatch for '{self.attachment.name}'{RESET}"

class VariableTypeError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None, declared_type: str = None, value_type: str = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment

        self.value_type: str = value_type
        self.declared_type: str = declared_type

        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"""[{self.name}] [{RED}VariableTypeError{RESET}]
{YELLOW}Variable Type Mismatch for '{self.attachment.name}'
Variable with Declared Type: {WHITE}'{self.declared_type.name}' {YELLOW}Can not be reassigned to Value Type: {WHITE}'{self.value_type.name}'
    '{self.attachment.name}' : {WHITE}{self.attachment.line}, {self.attachment.column}{RESET}
{WHITE}{self.source_path}:{self.attachment.line}:{self.attachment.column}{RESET}"""
        else:
            return f"[{self.name}] [{RED}VariableTypeError{RESET}] {YELLOW}Variable Type Mismatch for '{self.attachment.name}'{RESET}"

class TypeUnificationError(Exception):
    def __init__(self, name: str, source_path: str, attachment: any = None, a_type: str = None, b_type: str = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment

        self.a_type: str = a_type
    def __init__(self, name: str, source_path: str, attachment: any = None, expected_type: str = None, recieved_type: str = None):
        self.name: str = name
        self.source_path: str = source_path
        self.attachment: any = attachment

        self.expected_type: str = expected_type
        self.recieved_type: str = recieved_type

        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"""[{self.name}] [{RED}TypeUnificationError{RESET}]
{YELLOW}Unification Type Mismatch for '{getattr(self.attachment, 'name', str(self.attachment))}'
Expected: {self.expected_type}
Got: {self.recieved_type}{RESET}
    '{getattr(self.attachment, 'name', str(self.attachment))}' : {WHITE}{getattr(self.attachment, 'line', '?')}, {getattr(self.attachment, 'column', '?')}{RESET}
{WHITE}{self.source_path}:{getattr(self.attachment, 'line', '?')}:{getattr(self.attachment, 'column', '?')}{RESET}"""
        else:
            return f"[{self.name}] [{RED}TypeUnificationError{RESET}] {YELLOW}Unification Type Mismatch for '{getattr(self.attachment, 'name', str(self.attachment))}'{RESET}"

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
        for error in self.errors:
            print(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

