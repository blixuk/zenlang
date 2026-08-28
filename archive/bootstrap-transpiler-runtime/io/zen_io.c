#include "../bootstrap_runtime.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

// Built-in objects definitions
ZenValue __builtin_output;
ZenValue __builtin_input;
ZenValue __builtin_file;
ZenValue __builtin_sys;
ZenValue __builtin_string;
ZenValue __builtin_math;
ZenValue __builtin_list;
ZenValue __builtin_map;
ZenValue __builtin_set;
ZenValue __builtin_range;
ZenValue __builtin_time;
ZenValue __builtin_term;

typedef struct ZenFileHandle {
    FILE* fp;
} ZenFileHandle;

// Internal Print helpers
void ZenIO_internal_print_value(ZenValue value) {
    switch (value.type) {
        case ZEN_INTEGER: printf("%lld", value.as.integer); break;
        case ZEN_DECIMAL: printf("%g", value.as.decimal); break;
        case ZEN_BOOLEAN: printf("%s", value.as.boolean ? "true" : "false"); break;
        case ZEN_STRING: printf("%s", value.as.string ? value.as.string : ""); break;
        case ZEN_NOTHING: printf("nothing"); break;
        case ZEN_ERROR: printf("Error(%s)", value.as.string ? value.as.string : ""); break;
        case ZEN_LIST:
        case ZEN_MAP:
        case ZEN_VARIANT:
        case ZEN_SET: {
            ZenValue s = ZenValue_to_string(value);
            if (s.type == ZEN_STRING && s.as.string) {
                printf("%s", s.as.string);
            } else {
                printf("<value>");
            }
            break;
        }
        default: printf("<object %p>", value.as.object); break;
    }
}

// Zenlang IO API
ZenValue ZenIO_write_value(ZenValue value) {
    ZenIO_internal_print_value(value);
    fflush(stdout);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_line(ZenValue value) {
    ZenIO_internal_print_value(value);
    printf("\n");
    fflush(stdout);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_read_value(ZenValue prompt) {
    if (prompt.type == ZEN_STRING) {
        printf("%s", prompt.as.string);
    }
    char buffer[1024];
    if (fgets(buffer, sizeof(buffer), stdin)) {
        buffer[strcspn(buffer, "\n")] = 0;
        return ZenValue_make_string(buffer);
    }
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_info(ZenValue value) {
    printf("[INFO] ");
    ZenIO_internal_print_value(value);
    printf("\n");
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_warning(ZenValue value) {
    printf("[WARN] ");
    ZenIO_internal_print_value(value);
    printf("\n");
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_error(ZenValue value) {
    printf("[ERROR] ");
    ZenIO_internal_print_value(value);
    printf("\n");
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_debug(ZenValue value) {
    printf("[DEBUG] ");
    ZenIO_internal_print_value(value);
    printf("\n");
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_flush(void) {
    fflush(stdout);
    return ZEN_NOTHING_VAL;
}

/* File IO */
ZenValue ZenIO_file_exists(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_boolean(false);
    FILE* f = fopen(path, "r");
    if (f) {
        fclose(f);
        return ZenValue_make_boolean(true);
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenIO_read_file(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_error(ZenValue_make_string("Invalid path"));
    FILE* f = fopen(path, "r");
    if (!f) return ZenValue_make_error(ZenValue_make_string("File not found"));
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = malloc(len + 1);
    if (fread(buf, 1, len, f) != (size_t)len) { /* ignore */ }
    buf[len] = '\0';
    fclose(f);
    ZenValue z = ZenValue_make_string(buf);
    free(buf);
    return z;
}

ZenValue ZenIO_write_file(ZenValue path_val, ZenValue content_val) {
    const char* path = ZenString_get_pointer(path_val);
    const char* content = ZenString_get_pointer(content_val);
    if (!path || !content) return ZenValue_make_nothing();
    FILE* f = fopen(path, "w");
    if (f) { fprintf(f, "%s", content); fclose(f); }
    return ZenValue_make_nothing();
}

ZenValue ZenIO_list_dir(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_nothing();
    DIR* d = opendir(path);
    if (!d) return ZenValue_make_nothing();
    struct ZenList* list = ZenList_new();
    struct dirent* dir;
    while ((dir = readdir(d)) != NULL) {
        if (strcmp(dir->d_name, ".") != 0 && strcmp(dir->d_name, "..") != 0) {
            ZenList_append_value(ZenValue_from_list(list), ZenValue_make_string(dir->d_name));
        }
    }
    closedir(d);
    return ZenValue_from_list(list);
}

ZenValue ZenIO_append(ZenValue path_val, ZenValue content_val) {
    const char* path = ZenString_get_pointer(path_val);
    const char* content = ZenString_get_pointer(content_val);
    if (!path || !content) return ZenValue_make_nothing();
    FILE* f = fopen(path, "a");
    if (f) { fprintf(f, "%s", content); fclose(f); }
    return ZenValue_make_nothing();
}

ZenValue ZenIO_write_bytes(ZenValue path_val, ZenValue bytes_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path || bytes_val.type != ZEN_LIST || !bytes_val.as.list) {
        return ZenValue_make_nothing();
    }
    FILE* f = fopen(path, "wb");
    if (!f) return ZenValue_make_nothing();
    ZenValue list_v = bytes_val;
    long long n = ZenValue_to_integer(ZenList_get_length(list_v));
    for (long long i = 0; i < n; i++) {
        ZenValue b = ZenList_get_value_at_index(list_v, ZenValue_make_integer(i));
        unsigned char byte = 0;
        if (b.type == ZEN_INTEGER) byte = (unsigned char)(b.as.integer & 0xFF);
        fputc(byte, f);
    }
    fclose(f);
    return ZenValue_make_nothing();
}

ZenValue ZenIO_remove(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_boolean(false);
    if (unlink(path) == 0) return ZenValue_make_boolean(true);
    if (rmdir(path) == 0) return ZenValue_make_boolean(true);
    return ZenValue_make_boolean(false);
}

ZenValue ZenIO_is_file(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_boolean(false);
    struct stat st;
    if (stat(path, &st) != 0) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(S_ISREG(st.st_mode));
}

ZenValue ZenIO_is_dir(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_boolean(false);
    struct stat st;
    if (stat(path, &st) != 0) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(S_ISDIR(st.st_mode));
}

ZenValue ZenIO_open(ZenValue path_val, ZenValue mode_val) {
    const char* path = ZenString_get_pointer(path_val);
    const char* mode = ZenString_get_pointer(mode_val);
    if (!path) return ZenValue_make_nothing();
    if (!mode || mode[0] == '\0') mode = "r";
    FILE* fp = fopen(path, mode);
    if (!fp) return ZenValue_make_nothing();
    ZenFileHandle* h = (ZenFileHandle*)malloc(sizeof(ZenFileHandle));
    if (!h) { fclose(fp); return ZenValue_make_nothing(); }
    h->fp = fp;
    return ZenValue_from_object(h);
}

static ZenFileHandle* zen_file_handle_from_ptr(void* self) {
    if (!self) return NULL;
    /* Generated code may pass a ZenValue* (boxed handle) or raw ZenFileHandle*. */
    ZenValue* as_val = (ZenValue*)self;
    if (as_val->type == ZEN_OBJECT && as_val->as.object) {
        return (ZenFileHandle*)as_val->as.object;
    }
    return (ZenFileHandle*)self;
}

ZenValue ZenObject_read(void* self) {
    ZenFileHandle* h = zen_file_handle_from_ptr(self);
    if (!h || !h->fp) return ZenValue_make_error(ZenValue_make_string("FileNotOpen"));
    FILE* f = h->fp;
    long pos = ftell(f);
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)len + 1);
    if (!buf) { fseek(f, pos, SEEK_SET); return ZenValue_make_string(""); }
    size_t n = fread(buf, 1, (size_t)len, f);
    buf[n] = '\0';
    ZenValue z = ZenValue_make_string(buf);
    free(buf);
    return z;
}

ZenValue ZenObject_write(void* self, ZenValue content) {
    ZenFileHandle* h = zen_file_handle_from_ptr(self);
    if (!h || !h->fp) return ZenValue_make_error(ZenValue_make_string("FileNotOpen"));
    const char* s = ZenString_get_pointer(content);
    if (s) fputs(s, h->fp);
    fflush(h->fp);
    return ZenValue_make_nothing();
}

ZenValue ZenObject_close(void* self) {
    ZenFileHandle* h = zen_file_handle_from_ptr(self);
    if (!h) return ZenValue_make_nothing();
    if (h->fp) {
        fclose(h->fp);
        h->fp = NULL;
    }
    return ZenValue_make_nothing();
}
