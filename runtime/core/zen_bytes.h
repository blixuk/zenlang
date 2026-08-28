#ifndef ZEN_BYTES_H
#define ZEN_BYTES_H

#include "zen_value.h"

/* Byte arrays are represented as ZenValue lists of integer bytes (0–255). */

ZenValue ZenBytes_create_size(ZenValue size);
ZenValue ZenBytes_create_list(ZenValue list);
ZenValue ZenBytes_string_to_bytes(ZenValue s);
ZenValue ZenBytes_bytes_to_string(ZenValue bytes);
ZenValue ZenBytes_pack_binary(ZenValue spec, ZenValue data);
ZenValue ZenBytes_unpack_binary(ZenValue spec, ZenValue bytes);
/* Returns a Bytes class instance (struct with _data list field). */
ZenValue ZenBytes_from_string(ZenValue s);

#endif /* ZEN_BYTES_H */
