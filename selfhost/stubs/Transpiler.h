#ifndef TRANSPILER_H
#define TRANSPILER_H

#include "zen_object.h"

typedef struct Transpiler Transpiler;

Transpiler* Transpiler_Transpiler(ZenList* statements);
ZenString Transpiler_transpile(Transpiler* self);

#endif
