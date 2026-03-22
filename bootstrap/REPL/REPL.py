
from argparse import ArgumentParser

from Lexer.Lexer import Lexer
from Parser.Parser import Parser
from Parser.AST import ASTNode
from Checker.TypeChecker import TypeChecker
from Checker.Scope import ScopeManager
from Checker.SemanticChecker import SemanticChecker
from Interpreter.Interpreter import Interpreter
from Interpreter.Runtime import Environment

SOURCE_PATH: str = 'REPL'

class REPL:

    def __init__(self, arguments: list = [], strict: bool = False, debug: bool = False):
        self.debug: bool = debug
        self.strict: bool = strict

        self.arguments: list = arguments

        self.lexer: Lexer = Lexer("", SOURCE_PATH, self.strict, self.debug)
        self.tokens: list = []
        self.parser: Parser = Parser([], SOURCE_PATH, self.strict, self.debug)
        self.AST: ASTNode = None

        self.global_scope: ScopeManager = None
        self.typechecker: TypeChecker = TypeChecker(None, SOURCE_PATH, self.strict, self.debug)
        self.global_scope = self.typechecker.scope

        self.global_environment: Environment = None
        self.interpreter: Interpreter = Interpreter(None, SOURCE_PATH, self.strict, self.debug)
        self.global_environment = self.interpreter.global_environment

    def process(self, input: str):
        self.tokens: list = self.lexer.tokenize(input)

        self.AST = self.parser.parse(self.tokens)

        self.typechecker.scope = self.global_scope
        self.AST = self.typechecker.check_program(self.AST)
        self.global_scope = self.typechecker.scope

        # semanticchecker: SemanticChecker = SemanticChecker(AST, SOURCE_PATH, self.strict, self.debug)
        # AST = semanticchecker.check_program()

        self.interpreter.global_environment = self.global_environment
        result: any = self.interpreter.evaluate_repl(self.AST, self.global_environment)
        self.global_environment = self.interpreter.global_environment

        if result is None:
            result = ''

        return result

    def run(self):
        result: any = None

        while result != 'exit':
            line: str = input('> ')
            
            if line == 'exit':
                break
            elif line == '':
                continue
            elif line == '$lexer.logs':
                self.lexer.logger.print_debugs()
                continue
            elif line == '$lexer.errors':
                self.lexer.logger.print_errors()
                continue
            elif line == '$lexer.tokens':
                self.lexer.print_tokens()
                continue
            elif line == '$parser.logs':
                self.parser.logger.print_logs()
                continue
            elif line == '$parser.errors':
                self.parser.logger.print_errors()
                continue
            elif line == '$parser.ast':
                self.parser.print_ast()
                continue
            elif line == '$typechecker.logs':
                self.typechecker.logger.print_logs()
                continue
            elif line == '$typechecker.errors':
                self.typechecker.logger.print_errors()
                continue
            elif line == '$typechecker.ast':
                self.typechecker.print_ast()
                continue
            elif line == '$interpreter.logs':
                self.interpreter.logger.print_logs()
                continue
            elif line == '$interpreter.errors':
                self.interpreter.logger.print_errors()
                continue
            elif line == '$interpreter.ast':
                self.interpreter.print_ast()
                continue
            elif line == '$scope':
                print(self.scope.symbols)
                continue
            elif line == '$environment':
                print(self.global_environment.values)
            else:
                result = self.process(line)
                #print(result)
        
        print('Exiting...')
        exit()
