#ifndef ZEN_BOOTSTRAP_RUNTIME_H
#define ZEN_BOOTSTRAP_RUNTIME_H

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <setjmp.h>

// Core
#include "core/zen_value.h"
#include "core/zen_closure.h"
#include "core/zen_object.h"
#include "core/zen_ops.h"
#include "core/zen_variant.h"
#include "core/zen_dispatch.h"
#include "core/zen_sys.h"
#include "core/zen_math.h"

// Memory
#include "memory/zen_memory.h"

// Collections
#include "collections/zen_list.h"
#include "collections/zen_map.h"
#include "collections/zen_set.h"
#include "collections/zen_string.h"

// IO
#include "io/zen_io.h"

// Concurrency
#include "concurrency/zen_task.h"

// Compatibility helpers for the transpiler
static inline void* zen_get_body_ptr(void* obj) {
    if (!obj) return NULL;
    int kind = *(int*)obj;
    // ASTKind: FUNCTION_STATEMENT=16, FOR_STATEMENT=27, CASE_CLAUSE=34, CHECK_EXPRESSION=31
    if (kind == 16 || kind == 27 || kind == 31 || kind == 34) {
        return ((void**)obj)[3]; // 4th field
    }
    return ((void**)obj)[2]; // 3rd field (While/When/DoWhile)
}

// Compatibility macros for old builtin names
#define __builtin_map_has ZenMap_has_key
#define __builtin_map_keys ZenMap_get_keys
#define __builtin_map_values ZenMap_get_values
#define __builtin_set_has ZenSet_contains_value
#define __builtin_set_add ZenSet_add_value
#define __builtin_set_from_list ZenSet_from_list
#define __builtin_set_to_list ZenSet_to_list
#define __builtin_error ZenValue_make_error_message
#define __builtin_error_literal ZenValue_make_error_literal

#endif /* ZEN_BOOTSTRAP_RUNTIME_H */
