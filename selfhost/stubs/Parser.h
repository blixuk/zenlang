#ifndef PARSER_H
#define PARSER_H

#include "zen_object.h"

typedef struct Parser Parser;

Parser* Parser_Parser(ZenList* tokens);
ZenList* Parser_parse(Parser* self);

#endif
