#ifndef ZEN_REGEX_H
#define ZEN_REGEX_H

#include "zen_value.h"

/* POSIX-regex backed helpers for zen.text.regex / __builtin_regex. */
ZenValue ZenRegex_match(ZenValue pattern, ZenValue s);
ZenValue ZenRegex_search(ZenValue pattern, ZenValue s);
ZenValue ZenRegex_replace(ZenValue pattern, ZenValue repl, ZenValue s);
ZenValue ZenRegex_split(ZenValue pattern, ZenValue s);
ZenValue ZenRegex_find_all(ZenValue pattern, ZenValue s);

#endif /* ZEN_REGEX_H */
