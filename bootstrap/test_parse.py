import sys
from Parser.Parser import Parser
from Lexer.Lexer import Lexer
from Parser.AST import CallExpression, MemberExpression

lexer = Lexer("let x -> text.Word.capitalize(quiet)")
tokens = lexer.tokenize()
parser = Parser(tokens, "dummy.zl")
ast = parser.parse()
stmt = ast.statements[0]
call = stmt.value
print("callee type:", type(call.callee))
if isinstance(call.callee, MemberExpression):
    print("callee obj type:", type(call.callee.object))
    print("callee prop:", call.callee.property)
