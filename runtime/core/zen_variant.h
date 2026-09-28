#ifndef ZEN_VARIANT_H
#define ZEN_VARIANT_H

#include "zen_value.h"

typedef struct ZenVariantObject {
    ZenHeapHeader header;     /* 8 bytes: intrusive ARC / Sentinel header */
    ZenValue enum_name;
    ZenValue variant_name;
    ZenValue data; // ZenList* of ZenValue
} ZenVariantObject;

ZenValue ZenValue_make_variant(ZenValue enum_name, ZenValue variant_name, int n_params, ...);
void ZenVariantObject_destroy(ZenVariantObject* v);
ZenVariantObject* ZenVariantObject_deep_clone(ZenVariantObject* v);

static inline ZenValue ZenValue_from_variant(ZenVariantObject* v) {
    ZenValue res;
    res.type = ZEN_VARIANT;
    res.as.variant = v;
    return res;
}
ZenValue ZenValue_is_variant(ZenValue val, ZenValue expected_enum, ZenValue expected_variant);
ZenValue ZenValue_is_error(ZenValue v);
ZenValue ZenValue_is_type_name(ZenValue val, const char* expected_type);
ZenValue ZenValue_get_variant_name(ZenValue val);
ZenValue ZenValue_get_variant_data(ZenValue val, ZenValue index);

#endif // ZEN_VARIANT_H
