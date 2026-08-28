#ifndef ZEN_OBJECT_H
#define ZEN_OBJECT_H

#include "zen_value.h"

// Generic object base
typedef struct ZenObject {
    ZenValue __none; 
} ZenObject;

struct ZenObject_struct {
    ZenValue kind;
    ZenValue value;
    ZenValue name;
    ZenValue path;
    ZenValue line;
    ZenValue column;
    ZenValue statements;
    ZenValue expression;
    ZenValue arguments;
};

#endif // ZEN_OBJECT_H
