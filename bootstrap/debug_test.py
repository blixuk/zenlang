import sys
from Parser.Parser import Parser
from Lexer.Lexer import Lexer
from Parser.AST import ASTNode

with open("../tests/lib/test_text.zl", "r") as f:
    source = f.read()

lexer = Lexer(source)
tokens = lexer.tokenize()
parser = Parser(tokens, "../tests/lib/test_text.zl")
ast = parser.parse()

import os
os.environ["ZEN_PATH"] = "../lib"

from Checker.TypeChecker import TypeChecker
checker = TypeChecker(ast, "../tests/lib/test_text.zl")
checker.check_program()

def traverse(node):
    if not isinstance(node, ASTNode):
        if isinstance(node, list):
            for n in node:
                traverse(n)
        return
    
    if hasattr(node, "callee"):
        if hasattr(node.callee, "property") and node.callee.property == "capitalize":
            print(f"FOUND capitalize!")
            print(f"callee type: {getattr(node.callee, 'resolved_type', None)}")
            print(f"callee symbol: {getattr(node.callee, 'symbol', None)}")
            if hasattr(node.callee, 'symbol') and node.callee.symbol:
                print(f"symbol kind: {node.callee.symbol.kind}")
    
    for k, v in vars(node).items():
        if isinstance(v, ASTNode) or isinstance(v, list):
            traverse(v)

traverse(ast)

