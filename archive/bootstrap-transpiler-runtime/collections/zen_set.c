#include "collections/zen_set.h"
#include "collections/zen_list.h"
#include "core/zen_object.h"
#include "core/zen_dispatch.h"
#include <stdlib.h>

ZenValue ZenSet_new(void) {
    ZenSet* set = malloc(sizeof(ZenSet));
    set->list = ZenList_make_from_arguments(0);
    ZenValue v;
    v.type = ZEN_SET;
    v.as.set = set;
    return v;
}

ZenValue ZenSet_contains_value(ZenValue set, ZenValue value) {
    if (set.type != ZEN_SET) return ZenValue_make_boolean(false);
    ZenSet* s = set.as.set;
    if (!s) return ZenValue_make_boolean(false);
    return ZenList_contains_value(s->list, value);
}

ZenValue ZenSet_add_value(ZenValue set, ZenValue value) {
    if (set.type != ZEN_SET) return set;
    ZenSet* s = set.as.set;
    if (!s) return set;
    if (!ZenList_contains_value(s->list, value).as.boolean) {
        ZenList_append_value(s->list, value);
    }
    return set;
}

ZenValue ZenSet_from_list(ZenValue list) {
    ZenValue set = ZenSet_new();
    if (list.type != ZEN_LIST) return set;
    ZenList* l = list.as.list;
    if (!l) return set;
    for (int i = 0; i < l->count; i++) {
        ZenSet_add_value(set, l->items[i]);
    }
    return set;
}

ZenValue ZenSet_to_list(ZenValue set) {
    if (set.type != ZEN_SET) return ZenValue_make_nothing();
    ZenSet* s = set.as.set;
    if (!s) return ZenValue_make_nothing();
    return s->list;
}

int ZenSet_get_count(ZenValue set) {
    if (set.type != ZEN_SET) return 0;
    ZenSet* s = set.as.set;
    if (!s) return 0;
    return (int)ZenList_get_length(s->list).as.integer;
}

ZenValue ZenSet_remove_value(ZenValue set, ZenValue value) {
    if (set.type != ZEN_SET) return set;
    ZenSet* s = set.as.set;
    if (!s) return set;
    ZenList_remove(s->list, value);
    return set;
}
