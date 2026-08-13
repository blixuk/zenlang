# from Logging.SemanticCheckerLogger import SemanticCheckerLogger

from Logging import Printer
from Parser.AST import (
    ASTNode,
    CallExpression,
    ExpressionStatement,
    FunctionStatement,
    Identifier,
    Program,
    Script,
    Statements,
)


class SemanticChecker:
    def __init__(
        self,
        AST: Statements,
        source_path: str,
        strict: bool = False,
        debug: bool = False,
    ) -> None:
        self.debugging: bool = debug
        self.strict: bool = strict

        self.source_path: str = source_path
        self.AST: Statements | Program | Script = AST

        self.entry_point: bool = False

        # self.logger: SemanticCheckerLogger = SemanticCheckerLogger(source_path)

    def print_ast(self, as_json: bool = False) -> None:
        Printer.print_data(self.AST, as_json, "SEMANTIC CHECKER AST")

    def check_program(self) -> ASTNode:
        self.resolve_entry_point()

        return self.AST

    def resolve_entry_point(self) -> None:
        main_function: FunctionStatement | None = None

        for statement in self.AST.statements:
            if type(statement) is FunctionStatement and statement.name == "main":
                # print("main function found")
                main_function = statement
                break

        if main_function:
            self.entry_point = True

            # Insert a call node at the end of the program
            call_node: CallExpression = CallExpression(
                main_function.line,
                main_function.column,
                main_function.scope_level,
                callee=Identifier(
                    main_function.line,
                    main_function.column,
                    main_function.scope_level,
                    main_function.name,
                    "Function",
                ),
                arguments=[],
            )

            self.AST.statements.append(ExpressionStatement(
                call_node.line,
                call_node.column,
                call_node
            ))

            program: Program = Program(self.AST.statements)

            self.AST = program
        else:
            script: Script = Script(self.AST.statements)

            self.AST = script
