#include "zen_object.h"
#include "zen_object.h"
#include <stdlib.h> // for NULL if needed
#include <stdarg.h>
#include <stdarg.h>
ZenList* ZenList_create() {
    ZenList* list = (ZenList*)zen_alloc(sizeof(ZenList));
    list->capacity = 8;
    list->count = 0;
    list->items = (ZenVariant*)zen_alloc(sizeof(ZenVariant) * list->capacity);
    return list;
}

void ZenList_append(ZenList* list, ZenVariant item) {
    if (list->count >= list->capacity) {
        list->capacity *= 2;
        list->items = (ZenVariant*)zen_realloc(list->items, sizeof(ZenVariant) * list->capacity);
    }
    list->items[list->count++] = item;
}

ZenVariant ZenList_get(ZenList* list, int index) {
    if (index < 0 || index >= list->count) return Zen_nothing;
    return list->items[index];
}

int ZenList_length(ZenList* list) {
    return list->count;
}

ZenList* ZenList_from_args(int count, ...) {
    ZenList* list = ZenList_create();
    va_list args;
    va_start(args, count);
    for (int i = 0; i < count; i++) {
        ZenVariant item = va_arg(args, ZenVariant);
        ZenList_append(list, item);
    }
    va_end(args);
    return list;
}
