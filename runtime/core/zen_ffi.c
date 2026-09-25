#define _GNU_SOURCE
#include "zen_ffi.h"
#include "zen_value.h"
#include "zen_closure.h"
#include "../collections/zen_map.h"
#include "../collections/zen_list.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

static char g_last_ffi_error[256] = {0};

static void set_ffi_error(const char* err) {
    if (err) {
        strncpy(g_last_ffi_error, err, sizeof(g_last_ffi_error) - 1);
        g_last_ffi_error[sizeof(g_last_ffi_error) - 1] = '\0';
    } else {
        g_last_ffi_error[0] = '\0';
    }
}

const char* ZenFFI_dlerror(void) {
    return g_last_ffi_error;
}

void* ZenFFI_dlopen(const char* path) {
    void* handle = NULL;
    if (!path || path[0] == '\0') {
        handle = dlopen(NULL, RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) set_ffi_error(dlerror());
        return handle;
    }

    // Header notation: <math.h>, <unistd.h>, etc.
    if (path[0] == '<' || strstr(path, ".h") != NULL) {
        if (strstr(path, "math") != NULL) {
            handle = dlopen("libm.so.6", RTLD_LAZY | RTLD_GLOBAL);
            if (!handle) handle = dlopen("libm.so", RTLD_LAZY | RTLD_GLOBAL);
        }
        if (!handle) {
            handle = dlopen(NULL, RTLD_LAZY | RTLD_GLOBAL);
        }
        if (!handle) set_ffi_error(dlerror());
        return handle;
    }

    // Canonical short names
    if (strcmp(path, "m") == 0 || strcmp(path, "libm") == 0) {
        handle = dlopen("libm.so.6", RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) handle = dlopen("libm.so", RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) set_ffi_error(dlerror());
        return handle;
    }
    if (strcmp(path, "c") == 0 || strcmp(path, "libc") == 0) {
        handle = dlopen("libc.so.6", RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) handle = dlopen("libc.so", RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) set_ffi_error(dlerror());
        return handle;
    }

    handle = dlopen(path, RTLD_LAZY | RTLD_GLOBAL);
    if (!handle) {
        // Fallback to process symbols (e.g. for standard C library / system symbols)
        handle = dlopen(NULL, RTLD_LAZY | RTLD_GLOBAL);
    }
    if (!handle) {
        set_ffi_error(dlerror());
    }
    return handle;
}

void* ZenFFI_dlsym(void* handle, const char* symbol_name) {
    if (!symbol_name) return NULL;
    void* sym = dlsym(handle ? handle : RTLD_DEFAULT, symbol_name);
    if (!sym) {
        // Try fallback to process symbols
        sym = dlsym(RTLD_DEFAULT, symbol_name);
    }
    if (!sym) {
        set_ffi_error(dlerror());
    }
    return sym;
}

int ZenFFI_dlclose(void* handle) {
    if (!handle) return 0;
    return dlclose(handle);
}

static inline intptr_t unbox_int_or_ptr(ZenValue v) {
    switch (v.type) {
        case ZEN_INTEGER: return (intptr_t)v.as.integer;
        case ZEN_BOOLEAN: return (intptr_t)(v.as.boolean ? 1 : 0);
        case ZEN_STRING:  return (intptr_t)(v.as.string ? v.as.string : "");
        case ZEN_OBJECT:  return (intptr_t)v.as.object;
        case ZEN_DECIMAL: return (intptr_t)v.as.decimal;
        default: return 0;
    }
}

static inline double unbox_double(ZenValue v) {
    switch (v.type) {
        case ZEN_DECIMAL: return v.as.decimal;
        case ZEN_INTEGER: return (double)v.as.integer;
        case ZEN_BOOLEAN: return v.as.boolean ? 1.0 : 0.0;
        default: return 0.0;
    }
}

static bool is_math_float_sym(const char* name) {
    if (!name) return false;
    return (strcmp(name, "sqrt") == 0 ||
            strcmp(name, "pow") == 0 ||
            strcmp(name, "sin") == 0 ||
            strcmp(name, "cos") == 0 ||
            strcmp(name, "tan") == 0 ||
            strcmp(name, "asin") == 0 ||
            strcmp(name, "acos") == 0 ||
            strcmp(name, "atan") == 0 ||
            strcmp(name, "atan2") == 0 ||
            strcmp(name, "sinh") == 0 ||
            strcmp(name, "cosh") == 0 ||
            strcmp(name, "tanh") == 0 ||
            strcmp(name, "exp") == 0 ||
            strcmp(name, "log") == 0 ||
            strcmp(name, "log10") == 0 ||
            strcmp(name, "log2") == 0 ||
            strcmp(name, "ceil") == 0 ||
            strcmp(name, "floor") == 0 ||
            strcmp(name, "fabs") == 0 ||
            strcmp(name, "round") == 0 ||
            strcmp(name, "cbrt") == 0 ||
            strcmp(name, "hypot") == 0);
}

static bool is_string_ret_sym(const char* name) {
    if (!name) return false;
    return (strcmp(name, "getenv") == 0 ||
            strcmp(name, "strerror") == 0 ||
            strcmp(name, "strdup") == 0);
}

ZenValue ZenFFI_call(void* fn_ptr, int argc, ZenValue* args, const char* ret_type_hint) {
    if (!fn_ptr) return ZEN_NOTHING_VAL;

    bool is_float = false;
    if (ret_type_hint) {
        if (strcmp(ret_type_hint, "double") == 0 ||
            strcmp(ret_type_hint, "decimal") == 0 ||
            strcmp(ret_type_hint, "float") == 0) {
            is_float = true;
        }
    } else {
        for (int i = 0; i < argc; i++) {
            if (args[i].type == ZEN_DECIMAL) {
                is_float = true;
                break;
            }
        }
    }

    if (is_float) {
        double d[6] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
        for (int i = 0; i < argc && i < 6; i++) {
            d[i] = unbox_double(args[i]);
        }
        double res = 0.0;
        switch (argc) {
            case 0: res = ((double (*)(void))fn_ptr)(); break;
            case 1: res = ((double (*)(double))fn_ptr)(d[0]); break;
            case 2: res = ((double (*)(double, double))fn_ptr)(d[0], d[1]); break;
            case 3: res = ((double (*)(double, double, double))fn_ptr)(d[0], d[1], d[2]); break;
            case 4: res = ((double (*)(double, double, double, double))fn_ptr)(d[0], d[1], d[2], d[3]); break;
            case 5: res = ((double (*)(double, double, double, double, double))fn_ptr)(d[0], d[1], d[2], d[3], d[4]); break;
            case 6: res = ((double (*)(double, double, double, double, double, double))fn_ptr)(d[0], d[1], d[2], d[3], d[4], d[5]); break;
            default: res = ((double (*)(double, double, double, double, double, double))fn_ptr)(d[0], d[1], d[2], d[3], d[4], d[5]); break;
        }
        return ZenValue_make_decimal(res);
    }

    // Integer / Pointer call
    intptr_t a[6] = {0, 0, 0, 0, 0, 0};
    for (int i = 0; i < argc && i < 6; i++) {
        a[i] = unbox_int_or_ptr(args[i]);
    }
    intptr_t res = 0;
    switch (argc) {
        case 0: res = ((intptr_t (*)(void))fn_ptr)(); break;
        case 1: res = ((intptr_t (*)(intptr_t))fn_ptr)(a[0]); break;
        case 2: res = ((intptr_t (*)(intptr_t, intptr_t))fn_ptr)(a[0], a[1]); break;
        case 3: res = ((intptr_t (*)(intptr_t, intptr_t, intptr_t))fn_ptr)(a[0], a[1], a[2]); break;
        case 4: res = ((intptr_t (*)(intptr_t, intptr_t, intptr_t, intptr_t))fn_ptr)(a[0], a[1], a[2], a[3]); break;
        case 5: res = ((intptr_t (*)(intptr_t, intptr_t, intptr_t, intptr_t, intptr_t))fn_ptr)(a[0], a[1], a[2], a[3], a[4]); break;
        case 6: res = ((intptr_t (*)(intptr_t, intptr_t, intptr_t, intptr_t, intptr_t, intptr_t))fn_ptr)(a[0], a[1], a[2], a[3], a[4], a[5]); break;
        default: res = ((intptr_t (*)(intptr_t, intptr_t, intptr_t, intptr_t, intptr_t, intptr_t))fn_ptr)(a[0], a[1], a[2], a[3], a[4], a[5]); break;
    }

    if (ret_type_hint) {
        if (strcmp(ret_type_hint, "string") == 0 ||
            strcmp(ret_type_hint, "str") == 0 ||
            strcmp(ret_type_hint, "char*") == 0) {
            return ZenValue_make_string(res ? (const char*)res : "");
        }
        if (strcmp(ret_type_hint, "bool") == 0 ||
            strcmp(ret_type_hint, "boolean") == 0) {
            return ZenValue_make_boolean(res != 0);
        }
        if (strcmp(ret_type_hint, "void") == 0) {
            return ZEN_NOTHING_VAL;
        }
    }

    return ZenValue_make_integer((long long)res);
}

/* Multi-arity trampoline wrappers: closures pass cap[0] (ZenFFISymbol*) as first arg */
static ZenValue zen_ffi_tramp_0(ZenValue cap) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    return ZenFFI_call(sym->fn_ptr, 0, NULL, rhint);
}

static ZenValue zen_ffi_tramp_1(ZenValue cap, ZenValue a0) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[1] = { a0 };
    return ZenFFI_call(sym->fn_ptr, 1, args, rhint);
}

static ZenValue zen_ffi_tramp_2(ZenValue cap, ZenValue a0, ZenValue a1) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[2] = { a0, a1 };
    return ZenFFI_call(sym->fn_ptr, 2, args, rhint);
}

static ZenValue zen_ffi_tramp_3(ZenValue cap, ZenValue a0, ZenValue a1, ZenValue a2) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[3] = { a0, a1, a2 };
    return ZenFFI_call(sym->fn_ptr, 3, args, rhint);
}

static ZenValue zen_ffi_tramp_4(ZenValue cap, ZenValue a0, ZenValue a1, ZenValue a2, ZenValue a3) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[4] = { a0, a1, a2, a3 };
    return ZenFFI_call(sym->fn_ptr, 4, args, rhint);
}

static ZenValue zen_ffi_tramp_5(ZenValue cap, ZenValue a0, ZenValue a1, ZenValue a2, ZenValue a3, ZenValue a4) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[5] = { a0, a1, a2, a3, a4 };
    return ZenFFI_call(sym->fn_ptr, 5, args, rhint);
}

static ZenValue zen_ffi_tramp_6(ZenValue cap, ZenValue a0, ZenValue a1, ZenValue a2, ZenValue a3, ZenValue a4, ZenValue a5) {
    ZenFFISymbol* sym = (ZenFFISymbol*)cap.as.object;
    if (!sym) return ZEN_NOTHING_VAL;
    const char* rhint = sym->ret_type[0] ? sym->ret_type : (is_math_float_sym(sym->name) ? "double" : (is_string_ret_sym(sym->name) ? "string" : NULL));
    ZenValue args[6] = { a0, a1, a2, a3, a4, a5 };
    return ZenFFI_call(sym->fn_ptr, 6, args, rhint);
}

ZenValue ZenFFI_make_callable(void* fn_ptr, const char* name, const char* ret_type_hint, int arity) {
    if (!fn_ptr) return ZEN_NOTHING_VAL;
    ZenFFISymbol* sym = (ZenFFISymbol*)malloc(sizeof(ZenFFISymbol));
    if (!sym) return ZEN_NOTHING_VAL;
    sym->fn_ptr = fn_ptr;
    sym->name[0] = '\0';
    if (name) {
        strncpy(sym->name, name, sizeof(sym->name) - 1);
        sym->name[sizeof(sym->name) - 1] = '\0';
    }
    sym->ret_type[0] = '\0';
    if (ret_type_hint) {
        strncpy(sym->ret_type, ret_type_hint, sizeof(sym->ret_type) - 1);
        sym->ret_type[sizeof(sym->ret_type) - 1] = '\0';
    }
    sym->arity = arity;

    void* tramp = (void*)zen_ffi_tramp_0;
    switch (arity) {
        case 0: tramp = (void*)zen_ffi_tramp_0; break;
        case 1: tramp = (void*)zen_ffi_tramp_1; break;
        case 2: tramp = (void*)zen_ffi_tramp_2; break;
        case 3: tramp = (void*)zen_ffi_tramp_3; break;
        case 4: tramp = (void*)zen_ffi_tramp_4; break;
        case 5: tramp = (void*)zen_ffi_tramp_5; break;
        case 6: tramp = (void*)zen_ffi_tramp_6; break;
        default:
            // Flexible arity: use 6-param tramp which reads args safely
            tramp = (void*)zen_ffi_tramp_6;
            break;
    }

    ZenValue cap = ZenValue_from_object((void*)sym);
    return ZenValue_from_closure(tramp, arity, 1, cap);
}

ZenValue ZenFFI_make_module(const char* header_or_lib, const char* alias) {
    ZenValue mod = ZenValue_from_map(ZenMap_new());
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__is_extern_module"), ZenValue_make_boolean(true));
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__header"), ZenValue_make_string(header_or_lib ? header_or_lib : ""));
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__alias"), ZenValue_make_string(alias ? alias : ""));
    return mod;
}

ZenValue ZenFFI_resolve_symbol(const char* name) {
    if (!name || name[0] == '\0') return ZEN_NOTHING_VAL;

    // Check for alias_symbol pattern, e.g. "unistd_getpid" or "u_getpid" or "sysinfo_get_nprocs"
    const char* underscore = strchr(name, '_');
    if (underscore) {
        const char* subname = underscore + 1;
        void* sym = dlsym(RTLD_DEFAULT, subname);
        if (sym) {
            int arity = -1;
            if (strcmp(subname, "getpid") == 0 || strcmp(subname, "getppid") == 0 ||
                strcmp(subname, "getuid") == 0 || strcmp(subname, "getgid") == 0 ||
                strcmp(subname, "get_nprocs") == 0 || strcmp(subname, "get_nprocs_conf") == 0 ||
                strcmp(subname, "sync") == 0) {
                arity = 0;
            } else if (strcmp(subname, "abs") == 0 || strcmp(subname, "sqrt") == 0 ||
                       strcmp(subname, "strlen") == 0 || strcmp(subname, "isatty") == 0 ||
                       strcmp(subname, "sleep") == 0 || strcmp(subname, "usleep") == 0 ||
                       strcmp(subname, "unlink") == 0 || strcmp(subname, "rmdir") == 0 ||
                       strcmp(subname, "sysconf") == 0) {
                arity = 1;
            } else if (strcmp(subname, "pow") == 0 || strcmp(subname, "kill") == 0 ||
                       strcmp(subname, "rename") == 0) {
                arity = 2;
            }
            return ZenFFI_make_callable(sym, subname, NULL, arity);
        }
    }

    // Direct symbol lookup, e.g. "get_nprocs", "getuid", "abs", "sqrt"
    void* direct_sym = dlsym(RTLD_DEFAULT, name);
    if (direct_sym) {
        int arity = -1;
        if (strcmp(name, "getpid") == 0 || strcmp(name, "getppid") == 0 ||
            strcmp(name, "getuid") == 0 || strcmp(name, "getgid") == 0 ||
            strcmp(name, "get_nprocs") == 0 || strcmp(name, "get_nprocs_conf") == 0 ||
            strcmp(name, "sync") == 0) {
            arity = 0;
        } else if (strcmp(name, "abs") == 0 || strcmp(name, "sqrt") == 0 ||
                   strcmp(name, "strlen") == 0 || strcmp(name, "isatty") == 0 ||
                   strcmp(name, "sleep") == 0 || strcmp(name, "usleep") == 0 ||
                   strcmp(name, "unlink") == 0 || strcmp(name, "rmdir") == 0 ||
                   strcmp(name, "sysconf") == 0) {
            arity = 1;
        } else if (strcmp(name, "pow") == 0 || strcmp(name, "kill") == 0 ||
                   strcmp(name, "rename") == 0) {
            arity = 2;
        }
        return ZenFFI_make_callable(direct_sym, name, NULL, arity);
    }

    // Check if name is a known C module/header alias
    if (strcmp(name, "unistd") == 0 || strcmp(name, "u") == 0 ||
        strcmp(name, "sysinfo") == 0 || strcmp(name, "math") == 0 ||
        strcmp(name, "stdlib") == 0 || strcmp(name, "string") == 0 ||
        strcmp(name, "c") == 0 || strcmp(name, "libc") == 0 ||
        strcmp(name, "termios") == 0 || strcmp(name, "signal") == 0 ||
        strcmp(name, "stdio") == 0) {
        return ZenFFI_make_module(name, name);
    }

    return ZEN_NOTHING_VAL;
}

ZenValue ZenFFI_builtin_load(ZenValue path_val) {
    const char* path = (path_val.type == ZEN_STRING && path_val.as.string) ? path_val.as.string : "";
    void* handle = ZenFFI_dlopen(path);
    if (!handle) {
        return ZEN_NOTHING_VAL;
    }
    ZenValue mod = ZenValue_from_map(ZenMap_new());
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__is_extern_module"), ZenValue_make_boolean(true));
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__handle"), ZenValue_from_object(handle));
    ZenMap_set_value_at_key(mod, ZenValue_make_string("__path"), ZenValue_make_string(path));
    return mod;
}

ZenValue ZenFFI_builtin_symbol(ZenValue handle_val, ZenValue name_val, ZenValue ret_type_val) {
    void* handle = NULL;
    if (handle_val.type == ZEN_MAP) {
        ZenValue h_val = ZenMap_get_value_at_key(handle_val, ZenValue_make_string("__handle"));
        if (h_val.type == ZEN_OBJECT) handle = h_val.as.object;
    } else if (handle_val.type == ZEN_OBJECT) {
        handle = handle_val.as.object;
    }
    const char* name = (name_val.type == ZEN_STRING && name_val.as.string) ? name_val.as.string : "";
    const char* rtype = (ret_type_val.type == ZEN_STRING && ret_type_val.as.string) ? ret_type_val.as.string : NULL;
    void* sym = ZenFFI_dlsym(handle, name);
    if (!sym) return ZEN_NOTHING_VAL;
    return ZenFFI_make_callable(sym, name, rtype, -1);
}

ZenValue ZenFFI_builtin_call(ZenValue fn_val, ZenValue args_val, ZenValue ret_type_val) {
    void* fn_ptr = NULL;
    if (fn_val.type == ZEN_OBJECT) {
        fn_ptr = fn_val.as.object;
    } else if (fn_val.type == ZEN_FUNCTION && fn_val.as.object) {
        ZenClosureData* c = (ZenClosureData*)fn_val.as.object;
        if (c->n_caps > 0 && c->caps[0].type == ZEN_OBJECT && c->caps[0].as.object) {
            ZenFFISymbol* sym = (ZenFFISymbol*)c->caps[0].as.object;
            fn_ptr = sym->fn_ptr;
        }
    }
    if (!fn_ptr) return ZEN_NOTHING_VAL;

    const char* rtype = (ret_type_val.type == ZEN_STRING && ret_type_val.as.string) ? ret_type_val.as.string : NULL;
    int argc = 0;
    ZenValue args_buf[16];
    if (args_val.type == ZEN_LIST && args_val.as.list) {
        argc = args_val.as.list->count;
        if (argc > 16) argc = 16;
        for (int i = 0; i < argc; i++) {
            args_buf[i] = args_val.as.list->items[i];
        }
    }
    return ZenFFI_call(fn_ptr, argc, args_buf, rtype);
}

ZenValue ZenFFI_builtin_close(ZenValue handle_val) {
    void* handle = NULL;
    if (handle_val.type == ZEN_MAP) {
        ZenValue h_val = ZenMap_get_value_at_key(handle_val, ZenValue_make_string("__handle"));
        if (h_val.type == ZEN_OBJECT) handle = h_val.as.object;
    } else if (handle_val.type == ZEN_OBJECT) {
        handle = handle_val.as.object;
    }
    int res = ZenFFI_dlclose(handle);
    return ZenValue_make_integer(res);
}

ZenValue ZenFFI_builtin_error(void) {
    return ZenValue_make_string(g_last_ffi_error);
}

ZenValue ZenFFI_builtin_resolve(ZenValue name_val) {
    const char* name = (name_val.type == ZEN_STRING && name_val.as.string) ? name_val.as.string : "";
    return ZenFFI_resolve_symbol(name);
}
