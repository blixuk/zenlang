from Lexer.Lexer import Lexer
import os

with open("src/compiler/Lexer.zl", "r") as f:
    source = f.read()

lexer = Lexer(source, "src/compiler/Lexer.zl")
try:
    tokens = lexer.tokenize()
    print(f"Token count: {len(tokens)}")
    for t in tokens:
        if t.line > 1: # Just show some tokens around the class start
            print(t)
        if t.line > 10: break
except Exception as e:
    print(f"Lexer failed: {e}")
    lexer.logger.print_errors()
