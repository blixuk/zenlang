#ifndef ZEN_NET_H
#define ZEN_NET_H

#include "zen_value.h"

/*
 * Thin HTTP client for zen.net.http (__builtin_net.http_request).
 * Native implementation shells out to curl when available.
 * Returns map: { status: Integer, body: String, headers: Map }.
 * On failure status is -1 and body holds an error message.
 */

ZenValue ZenNet_http_request(ZenValue url, ZenValue method, ZenValue body, ZenValue headers);

/* Unix Domain Sockets & Poll Multiplexing for Compiler Daemon */
ZenValue ZenNet_unix_listen(ZenValue path);
ZenValue ZenNet_unix_connect(ZenValue path);
ZenValue ZenNet_unix_accept(ZenValue fd);
ZenValue ZenNet_socket_read(ZenValue fd, ZenValue max_bytes);
ZenValue ZenNet_socket_write(ZenValue fd, ZenValue content);
ZenValue ZenNet_socket_close(ZenValue fd);
ZenValue ZenNet_poll(ZenValue fds_list, ZenValue timeout_ms);

#endif /* ZEN_NET_H */
