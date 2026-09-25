#ifndef ZEN_FFI_H
#define ZEN_FFI_H

#include "zen_value.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ZenFFISymbol {
    void* fn_ptr;
    char name[64];
    char ret_type[16];
    int arity;
} ZenFFISymbol;

/* Library Lifecycle */
void* ZenFFI_dlopen(const char* path);
void* ZenFFI_dlsym(void* handle, const char* symbol_name);
int   ZenFFI_dlclose(void* handle);
const char* ZenFFI_dlerror(void);

/* Call Dispatch & Value Boxing */
ZenValue ZenFFI_call(void* fn_ptr, int argc, ZenValue* args, const char* ret_type_hint);
ZenValue ZenFFI_make_callable(void* fn_ptr, const char* name, const char* ret_type_hint, int arity);
ZenValue ZenFFI_resolve_symbol(const char* name);
ZenValue ZenFFI_make_module(const char* header_or_lib, const char* alias);

/* Builtin API Bindings (__builtin_ffi) */
ZenValue ZenFFI_builtin_load(ZenValue path_val);
ZenValue ZenFFI_builtin_symbol(ZenValue handle_val, ZenValue name_val, ZenValue ret_type_val);
ZenValue ZenFFI_builtin_call(ZenValue fn_val, ZenValue args_val, ZenValue ret_type_val);
ZenValue ZenFFI_builtin_close(ZenValue handle_val);
ZenValue ZenFFI_builtin_error(void);
ZenValue ZenFFI_builtin_resolve(ZenValue name_val);

#ifdef __cplusplus
}
#endif

#endif /* ZEN_FFI_H */
