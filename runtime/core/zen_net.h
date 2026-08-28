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

#endif /* ZEN_NET_H */
