#ifndef LEXER_H
#define LEXER_H

#include "zen_object.h"

typedef struct Lexer Lexer;

Lexer* Lexer_Lexer(ZenString source);
ZenList* Lexer_tokenize(Lexer* self);

#endif
