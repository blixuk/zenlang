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
void ZenIO_internal_print_value_to(FILE* f, ZenValue value) {
    if (!f) f = stdout;
    switch (value.type) {
        case ZEN_INTEGER: fprintf(f, "%lld", value.as.integer); break;
        case ZEN_DECIMAL: fprintf(f, "%g", value.as.decimal); break;
        case ZEN_BOOLEAN: fprintf(f, "%s", value.as.boolean ? "true" : "false"); break;
        case ZEN_STRING: fprintf(f, "%s", value.as.string ? value.as.string : ""); break;
        case ZEN_NOTHING: fprintf(f, "nothing"); break;
        case ZEN_ERROR: fprintf(f, "Error(%s)", value.as.string ? value.as.string : ""); break;
        case ZEN_LIST:
        case ZEN_MAP:
        case ZEN_VARIANT:
        case ZEN_SET:
        case ZEN_AST_NODE:
        case ZEN_TOKEN: {
            ZenValue s = ZenValue_to_string(value);
            if (s.type == ZEN_STRING && s.as.string) {
                fprintf(f, "%s", s.as.string);
            } else {
                fprintf(f, "<value>");
            }
            break;
        }
        default: fprintf(f, "<object %p>", value.as.object); break;
    }
}

void ZenIO_internal_print_value(ZenValue value) {
    ZenIO_internal_print_value_to(stdout, value);
}

// Zenlang IO API
ZenValue ZenIO_write_value(ZenValue value) {
    ZenIO_internal_print_value_to(stdout, value);
    fflush(stdout);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_line(ZenValue value) {
    ZenIO_internal_print_value_to(stdout, value);
    fprintf(stdout, "\n");
    fflush(stdout);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_stderr(ZenValue value) {
    ZenIO_internal_print_value_to(stderr, value);
    fflush(stderr);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_write_line_stderr(ZenValue value) {
    ZenIO_internal_print_value_to(stderr, value);
    fprintf(stderr, "\n");
    fflush(stderr);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_flush_stderr(void) {
    fflush(stderr);
    return ZEN_NOTHING_VAL;
}

ZenValue ZenIO_stdin_lines(void) {
    ZenValue list_val = ZenValue_from_list(ZenList_new());
    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), stdin)) {
        buffer[strcspn(buffer, "\r\n")] = 0;
        ZenList_append_value(list_val, ZenValue_make_string(buffer));
    }
    return list_val;
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

ZenValue ZenIO_read(ZenValue prompt) {
    return ZenIO_read_value(prompt);
}

ZenValue ZenIO_read_line(void) {
    size_t cap = 256;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) return ZEN_NOTHING_VAL;
    
    int c;
    while ((c = fgetc(stdin)) != EOF) {
        if (c == '\r') {
            int next_c = fgetc(stdin);
            if (next_c != '\n' && next_c != EOF) {
                ungetc(next_c, stdin);
            }
            break;
        }
        if (c == '\n') {
            break;
        }
        if (len + 1 >= cap) {
            cap *= 2;
            char* new_buf = (char*)realloc(buf, cap);
            if (!new_buf) {
                free(buf);
                return ZEN_NOTHING_VAL;
            }
            buf = new_buf;
        }
        buf[len++] = (char)c;
    }
    if (len == 0 && c == EOF) {
        free(buf);
        return ZEN_NOTHING_VAL;
    }
    buf[len] = '\0';
    ZenValue result = ZenValue_make_string(buf);
    free(buf);
    return result;
}

ZenValue ZenIO_read_exact(ZenValue count_val) {
    if (count_val.type != ZEN_INTEGER || count_val.as.integer <= 0) {
        return ZenValue_make_string("");
    }
    size_t count = (size_t)count_val.as.integer;
    char* buf = (char*)malloc(count + 1);
    if (!buf) return ZEN_NOTHING_VAL;
    
    size_t total_read = 0;
    while (total_read < count) {
        size_t n = fread(buf + total_read, 1, count - total_read, stdin);
        if (n == 0) {
            if (feof(stdin) || ferror(stdin)) break;
        }
        total_read += n;
    }
    buf[total_read] = '\0';
    ZenValue result = ZenValue_make_string(buf);
    free(buf);
    return result;
}

ZenValue ZenIO_write_raw(ZenValue str) {
    if (str.type == ZEN_STRING && str.as.string) {
        fputs(str.as.string, stdout);
        fflush(stdout);
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
    struct stat st;
    if (stat(path, &st) != 0) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(true);
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
    /* Always return a list (empty on failure) for dual-path friendliness. */
    if (!path) return ZenList_make_from_arguments(0);
    DIR* d = opendir(path);
    if (!d) return ZenList_make_from_arguments(0);
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

ZenValue ZenIO_mkdir(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path || path[0] == '\0') return ZenValue_make_boolean(false);
    struct stat st;
    if (stat(path, &st) == 0) {
        return ZenValue_make_boolean(S_ISDIR(st.st_mode));
    }
    if (mkdir(path, 0755) == 0) return ZenValue_make_boolean(true);
    return ZenValue_make_boolean(false);
}

/* Recursive mkdir -p (mutates a writable copy of path). */
static int zen_mkdir_p_cstr(char* path) {
    if (!path || path[0] == '\0') return -1;
    struct stat st;
    if (stat(path, &st) == 0) {
        return S_ISDIR(st.st_mode) ? 0 : -1;
    }
    size_t len = strlen(path);
    /* Walk path components */
    for (size_t i = 1; i < len; i++) {
        if (path[i] != '/') continue;
        path[i] = '\0';
        if (path[0] != '\0' && stat(path, &st) != 0) {
            if (mkdir(path, 0755) != 0) {
                path[i] = '/';
                return -1;
            }
        } else if (path[0] != '\0' && !S_ISDIR(st.st_mode)) {
            path[i] = '/';
            return -1;
        }
        path[i] = '/';
    }
    if (stat(path, &st) == 0) {
        return S_ISDIR(st.st_mode) ? 0 : -1;
    }
    return mkdir(path, 0755);
}

ZenValue ZenIO_mkdir_p(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path || path[0] == '\0') return ZenValue_make_boolean(false);
    size_t n = strlen(path);
    char* buf = (char*)malloc(n + 1);
    if (!buf) return ZenValue_make_boolean(false);
    memcpy(buf, path, n + 1);
    /* Strip trailing slashes (keep root "/") */
    while (n > 1 && buf[n - 1] == '/') {
        buf[n - 1] = '\0';
        n--;
    }
    int rc = zen_mkdir_p_cstr(buf);
    free(buf);
    return ZenValue_make_boolean(rc == 0);
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
