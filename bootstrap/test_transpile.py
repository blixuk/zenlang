import sys
from Parser.Parser import Parser
from Lexer.Lexer import Lexer
from Transpiler.SMIRGenerator import SMIRGenerator
from Transpiler.SMIRAnalyzer import SMIRAnalyzer
from Checker.TypeChecker import TypeChecker

lexer = Lexer("import zen.text.text as text\nlet quiet -> text.Word { text -> \"test\" }\nlet capitalized -> text.Word.capitalize(quiet)")
tokens = lexer.tokenize()
parser = Parser(tokens, "tests/lib/test_text.zl")
ast = parser.parse()

checker = TypeChecker(ast, "tests/lib/test_text.zl")
checker.check_program()

gen = SMIRGenerator(
    filename="tests/lib/test_text.zl",
    main_file="tests/lib/test_text.zl",
    module_aliases={"text": "text"}
)
mir = gen.generate(ast)

analyzer = SMIRAnalyzer(mir, ast)
analyzer.analyze()

print("\n--- EMITTED MIR ---")
for instr in mir:
    if "Call" in str(type(instr)):
        print(f"Call: callee={instr.callee}")
