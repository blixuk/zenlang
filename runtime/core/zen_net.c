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
#include <sys/socket.h>
#include <sys/un.h>
#include <poll.h>
#include <fcntl.h>
#include <errno.h>

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

/* Unix Domain Sockets & Poll Multiplexing for Compiler Daemon */

ZenValue ZenNet_unix_listen(ZenValue path_v) {
    const char* path = ZenString_get_pointer(path_v);
    if (!path || !*path) return ZenValue_make_integer(-1);

    unlink(path);

    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return ZenValue_make_integer(-1);

    int flags = fcntl(fd, F_GETFL, 0);
    if (flags >= 0) fcntl(fd, F_SETFL, flags | O_NONBLOCK);
    fcntl(fd, F_SETFD, FD_CLOEXEC);

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(fd);
        return ZenValue_make_integer(-1);
    }

    if (listen(fd, 32) < 0) {
        close(fd);
        return ZenValue_make_integer(-1);
    }

    return ZenValue_make_integer(fd);
}

ZenValue ZenNet_unix_connect(ZenValue path_v) {
    const char* path = ZenString_get_pointer(path_v);
    if (!path || !*path) return ZenValue_make_integer(-1);

    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return ZenValue_make_integer(-1);

    fcntl(fd, F_SETFD, FD_CLOEXEC);

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(fd);
        return ZenValue_make_integer(-1);
    }

    return ZenValue_make_integer(fd);
}

ZenValue ZenNet_unix_accept(ZenValue fd_v) {
    if (fd_v.type != ZEN_INTEGER) return ZenValue_make_integer(-1);
    int fd = (int)fd_v.as.integer;
    if (fd < 0) return ZenValue_make_integer(-1);

    int client_fd = accept(fd, NULL, NULL);
    if (client_fd < 0) {
        return ZenValue_make_integer(-1);
    }

    int flags = fcntl(client_fd, F_GETFL, 0);
    if (flags >= 0) fcntl(client_fd, F_SETFL, flags | O_NONBLOCK);
    fcntl(client_fd, F_SETFD, FD_CLOEXEC);

    return ZenValue_make_integer(client_fd);
}

ZenValue ZenNet_socket_read(ZenValue fd_v, ZenValue max_bytes_v) {
    if (fd_v.type != ZEN_INTEGER) return ZenValue_make_nothing();
    int fd = (int)fd_v.as.integer;
    if (fd < 0) return ZenValue_make_nothing();

    int max_bytes = 65536;
    if (max_bytes_v.type == ZEN_INTEGER && max_bytes_v.as.integer > 0) {
        max_bytes = (int)max_bytes_v.as.integer;
        if (max_bytes > 10 * 1024 * 1024) max_bytes = 10 * 1024 * 1024;
    }

    char* buf = (char*)malloc(max_bytes + 1);
    if (!buf) return ZenValue_make_nothing();

    ssize_t n = read(fd, buf, max_bytes);
    if (n < 0) {
        free(buf);
        return ZenValue_make_nothing();
    }
    if (n == 0) {
        free(buf);
        return ZenValue_make_string("");
    }
    buf[n] = '\0';
    ZenValue res = ZenValue_make_string(buf);
    free(buf);
    return res;
}

ZenValue ZenNet_socket_write(ZenValue fd_v, ZenValue content_v) {
    if (fd_v.type != ZEN_INTEGER) return ZenValue_make_integer(-1);
    int fd = (int)fd_v.as.integer;
    if (fd < 0) return ZenValue_make_integer(-1);

    const char* str = ZenString_get_pointer(content_v);
    if (!str) return ZenValue_make_integer(0);

    size_t len = strlen(str);
    size_t written = 0;
    while (written < len) {
        ssize_t n = write(fd, str + written, len - written);
        if (n < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                struct pollfd pfd;
                pfd.fd = fd;
                pfd.events = POLLOUT;
                pfd.revents = 0;
                if (poll(&pfd, 1, 1000) > 0) continue;
            }
            break;
        }
        written += (size_t)n;
    }
    return ZenValue_make_integer((long long)written);
}

ZenValue ZenNet_socket_close(ZenValue fd_v) {
    if (fd_v.type == ZEN_INTEGER) {
        int fd = (int)fd_v.as.integer;
        if (fd >= 0) {
            close(fd);
        }
    }
    return ZenValue_make_nothing();
}

ZenValue ZenNet_poll(ZenValue fds_list_v, ZenValue timeout_ms_v) {
    int timeout = 0;
    if (timeout_ms_v.type == ZEN_INTEGER) {
        timeout = (int)timeout_ms_v.as.integer;
    }

    if (fds_list_v.type != ZEN_LIST) {
        return ZenList_make_from_arguments(0);
    }
    ZenList* l = fds_list_v.as.list;
    if (!l || l->count == 0) {
        if (timeout > 0) usleep((useconds_t)timeout * 1000);
        return ZenList_make_from_arguments(0);
    }

    int count = l->count > 64 ? 64 : l->count;
    struct pollfd pfds[64];
    for (int i = 0; i < count; i++) {
        pfds[i].fd = (l->items[i].type == ZEN_INTEGER) ? (int)l->items[i].as.integer : -1;
        pfds[i].events = POLLIN | POLLPRI;
        pfds[i].revents = 0;
    }

    int r = poll(pfds, (nfds_t)count, timeout);
    struct ZenList* ready = ZenList_new();
    if (r > 0) {
        for (int i = 0; i < count; i++) {
            if (pfds[i].revents & (POLLIN | POLLPRI | POLLHUP | POLLERR)) {
                ZenList_append_value(ZenValue_from_list(ready), ZenValue_make_integer(pfds[i].fd));
            }
        }
    }
    return ZenValue_from_list(ready);
}
