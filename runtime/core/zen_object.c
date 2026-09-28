#include "zen_object.h"
#include <stdlib.h>

void ZenObject_destroy(ZenObject* obj) {
    if (!obj) return;
    if (obj->header.ref_count != ZEN_REF_PINNED) {
        free(obj);
    }
}
