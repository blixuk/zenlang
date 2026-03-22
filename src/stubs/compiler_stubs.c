#include "Lexer.h"
#include "Parser.h"
#include "Transpiler.h"
#include <stdio.h>
#include <string.h>

// Dummy structs
struct Lexer { int x; };
struct Parser { int x; };
struct Transpiler { int x; };

Lexer* Lexer_Lexer(ZenString source) {
    if (source) {
        printf("[Stub] Lexer created with source of length: %d\n", ZenString_length(source));
    } else {
        printf("[Stub] Lexer created with NULL source\n");
    }
    return (Lexer*)zen_alloc(sizeof(Lexer));
}

ZenList* Lexer_tokenize(Lexer* self) {
    printf("[Stub] Lexer tokenized\n");
    return ZenList_create();
}

Parser* Parser_Parser(ZenList* tokens) {
    printf("[Stub] Parser created\n");
    return (Parser*)zen_alloc(sizeof(Parser));
}

ZenList* Parser_parse(Parser* self) {
    printf("[Stub] Parser parsed\n");
    return ZenList_create();
}

Transpiler* Transpiler_Transpiler(ZenList* statements) {
    printf("[Stub] Transpiler created\n");
    return (Transpiler*)zen_alloc(sizeof(Transpiler));
}

ZenString Transpiler_transpile(Transpiler* self) {
    printf("[Stub] Transpiler transpiled\n");
    return ZenString_create("// Generated C Code by Stub\nvoid main() {}");
}
