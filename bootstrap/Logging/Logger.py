
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

class Logger:

    def __init__(self, name: str):
        self.name: str = name
        self.errors: list[Error] = []
        self.debugs: list[Debug] = []
    
    def error(self, message: str, attachment: any = None):
        self.errors.append(Error(self.name, message, attachment))
    
    def debug(self, message: str, attachment: any = None):
        self.debugs.append(Debug(self.name, message, attachment))
    
    def print_errors(self):
        for error in self.errors:
            print(error)
    
    def print_debugs(self):
        for debug in self.debugs:
            print(debug)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

class Error(Exception):
    def __init__(self, name: str, message: str, attachment: any = None):
        self.name: str = name
        self.message: str = message
        self.attachment: any = attachment
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.attachment:
            return f"[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}\n    {WHITE}Attachment: {self.attachment}{RESET}"
        else:
            return f"[{self.name}] [{RED}Error{RESET}] {YELLOW}{self.message}{RESET}"

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