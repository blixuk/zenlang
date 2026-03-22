from Lexer.Lexer import Lexer
from Lexer.Token import TokenType

source = "5 ^^ 3"
lexer = Lexer(source)
tokens = lexer.tokenize()
for t in tokens:
    print(f"Token: {t.type} '{t.value}'")
