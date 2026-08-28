#include "zen_net.h"
#include "../collections/zen_map.h"
#include "../collections/zen_string.h"
#include "../collections/zen_list.h"
#include "zen_ops.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

static ZenValue http_error(const char* msg) {
    ZenValue m = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(m, ZenValue_make_string("status"), ZenValue_make_integer(-1));
    ZenMap_set_value_at_key(m, ZenValue_make_string("body"),
                            ZenValue_make_string(msg ? msg : "http error"));
    ZenMap_set_value_at_key(m, ZenValue_make_string("headers"),
                            ZenMap_make_from_arguments(0));
    return m;
}

static void append_escaped(char** buf, size_t* len, size_t* cap, const char* s) {
    if (!s) return;
    for (const char* p = s; *p; p++) {
        if (*len + 4 >= *cap) {
            *cap = (*cap == 0) ? 256 : (*cap * 2);
            char* nb = (char*)realloc(*buf, *cap);
            if (!nb) return;
            *buf = nb;
        }
        /* Single-quote shell escape: 'foo'\''bar' */
        if (*p == '\'') {
            (*buf)[(*len)++] = '\'';
            (*buf)[(*len)++] = '\\';
            (*buf)[(*len)++] = '\'';
            (*buf)[(*len)++] = '\'';
        } else {
            (*buf)[(*len)++] = *p;
        }
    }
}

static void append_lit(char** buf, size_t* len, size_t* cap, const char* s) {
    if (!s) return;
    size_t n = strlen(s);
    if (*len + n + 1 >= *cap) {
        size_t need = *len + n + 64;
        *cap = need > (*cap * 2) ? need : (*cap == 0 ? need : *cap * 2);
        char* nb = (char*)realloc(*buf, *cap);
        if (!nb) return;
        *buf = nb;
    }
    memcpy(*buf + *len, s, n);
    *len += n;
    (*buf)[*len] = '\0';
}

/* Build: curl -sS -L -X METHOD [-H ...] [-d body] -o bodyfile -w '%{http_code}' URL */
static char* build_curl_cmd(const char* url, const char* method, const char* body,
                            ZenValue headers, const char* body_path) {
    size_t cap = 512, len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) return NULL;
    buf[0] = '\0';

    /* -sS silent but show errors; 2>/dev/null keeps refused-connection tests quiet */
    append_lit(&buf, &len, &cap, "curl -sS -L --max-time 30 2>/dev/null ");
    if (method && method[0]) {
        append_lit(&buf, &len, &cap, "-X '");
        append_escaped(&buf, &len, &cap, method);
        append_lit(&buf, &len, &cap, "' ");
    }
    if (headers.type == ZEN_MAP && headers.as.map) {
        struct ZenMap* m = headers.as.map;
        for (int i = 0; i < m->count; i++) {
            const char* k = ZenString_get_pointer(m->entries[i].key);
            const char* v = ZenString_get_pointer(m->entries[i].value);
            if (!k) continue;
            append_lit(&buf, &len, &cap, "-H '");
            append_escaped(&buf, &len, &cap, k);
            append_lit(&buf, &len, &cap, ": ");
            if (v) append_escaped(&buf, &len, &cap, v);
            append_lit(&buf, &len, &cap, "' ");
        }
    }
    if (body && body[0] != '\0') {
        append_lit(&buf, &len, &cap, "-d '");
        append_escaped(&buf, &len, &cap, body);
        append_lit(&buf, &len, &cap, "' ");
    }
    append_lit(&buf, &len, &cap, "-o '");
    append_escaped(&buf, &len, &cap, body_path);
    append_lit(&buf, &len, &cap, "' -w '%{http_code}' '");
    append_escaped(&buf, &len, &cap, url ? url : "");
    append_lit(&buf, &len, &cap, "'");
    return buf;
}

static char* read_file_cstr(const char* path, size_t* out_len) {
    FILE* f = fopen(path, "rb");
    if (!f) {
        if (out_len) *out_len = 0;
        return NULL;
    }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (n < 0) n = 0;
    char* buf = (char*)malloc((size_t)n + 1);
    if (!buf) {
        fclose(f);
        if (out_len) *out_len = 0;
        return NULL;
    }
    size_t got = fread(buf, 1, (size_t)n, f);
    buf[got] = '\0';
    fclose(f);
    if (out_len) *out_len = got;
    return buf;
}

ZenValue ZenNet_http_request(ZenValue url_v, ZenValue method_v, ZenValue body_v, ZenValue headers_v) {
    const char* url = ZenString_get_pointer(url_v);
    if (!url || url[0] == '\0') return http_error("missing url");

    const char* method = "GET";
    if (method_v.type == ZEN_STRING) {
        const char* m = ZenString_get_pointer(method_v);
        if (m && m[0]) method = m;
    }

    const char* body = NULL;
    if (body_v.type == ZEN_STRING) {
        body = ZenString_get_pointer(body_v);
    }

    /* Require curl on PATH */
    if (access("/usr/bin/curl", X_OK) != 0 && access("/bin/curl", X_OK) != 0) {
        /* Still try PATH via shell */
    }

    char body_path[] = "/tmp/zen_http_body_XXXXXX";
    int fd = mkstemp(body_path);
    if (fd < 0) return http_error("mkstemp failed");
    close(fd);

    char* cmd = build_curl_cmd(url, method, body, headers_v, body_path);
    if (!cmd) {
        unlink(body_path);
        return http_error("oom building curl command");
    }

    FILE* pipe = popen(cmd, "r");
    free(cmd);
    if (!pipe) {
        unlink(body_path);
        return http_error("failed to run curl (is it installed?)");
    }

    char code_buf[32];
    size_t n = fread(code_buf, 1, sizeof(code_buf) - 1, pipe);
    code_buf[n] = '\0';
    int st = pclose(pipe);

    size_t body_len = 0;
    char* body_data = read_file_cstr(body_path, &body_len);
    unlink(body_path);

    long long status = -1;
    if (n > 0) {
        status = atoll(code_buf);
    }
    /* file:// often reports 000 from curl; treat readable body as 200 */
    if (status == 0 && body_data && strncmp(url, "file:", 5) == 0) {
        status = 200;
    }
    if (status == 0 && st != 0 && !body_data) {
        status = -1;
    }

    ZenValue result = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(result, ZenValue_make_string("status"),
                            ZenValue_make_integer(status));
    ZenMap_set_value_at_key(result, ZenValue_make_string("body"),
                            ZenValue_make_string(body_data ? body_data : ""));
    ZenMap_set_value_at_key(result, ZenValue_make_string("headers"),
                            ZenMap_make_from_arguments(0));
    free(body_data);
    return result;
}
