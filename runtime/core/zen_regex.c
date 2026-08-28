#include "zen_regex.h"
#include "collections/zen_string.h"
#include "collections/zen_list.h"
#include <regex.h>
#include <stdlib.h>
#include <string.h>

static const char* zen_str(ZenValue v) {
    if (v.type == ZEN_STRING) return ZenString_get_pointer(v);
    return NULL;
}

/* Convert common Python-style escapes to POSIX ERE. */
static char* zen_regex_posixify(const char* pat) {
    if (!pat) return NULL;
    size_t n = strlen(pat);
    /* worst case: each \x expands to ~12 chars */
    size_t cap = n * 12 + 1;
    char* out = malloc(cap);
    if (!out) return NULL;
    size_t j = 0;
    for (size_t i = 0; pat[i]; i++) {
        if (pat[i] == '\\' && pat[i + 1]) {
            char nch = pat[i + 1];
            const char* rep = NULL;
            if (nch == 's') rep = "[[:space:]]";
            else if (nch == 'd') rep = "[0-9]";
            else if (nch == 'w') rep = "[A-Za-z0-9_]";
            if (rep) {
                size_t rl = strlen(rep);
                if (j + rl + 1 > cap) {
                    cap = (j + rl + 1) * 2;
                    char* nb = realloc(out, cap);
                    if (!nb) { free(out); return NULL; }
                    out = nb;
                }
                memcpy(out + j, rep, rl);
                j += rl;
                i++;
                continue;
            }
        }
        if (j + 2 > cap) {
            cap *= 2;
            char* nb = realloc(out, cap);
            if (!nb) { free(out); return NULL; }
            out = nb;
        }
        out[j++] = pat[i];
    }
    out[j] = '\0';
    return out;
}

static int zen_regcomp(regex_t* re, const char* pat, int cflags) {
    char* p = zen_regex_posixify(pat);
    if (!p) return -1;
    int rc = regcomp(re, p, cflags);
    free(p);
    return rc;
}

ZenValue ZenRegex_match(ZenValue pattern, ZenValue s) {
    const char* pat = zen_str(pattern);
    const char* str = zen_str(s);
    if (!pat || !str) return ZenValue_make_boolean(false);
    regex_t re;
    if (zen_regcomp(&re, pat, REG_EXTENDED) != 0) {
        return ZenValue_make_boolean(false);
    }
    regmatch_t m;
    int rc = regexec(&re, str, 1, &m, 0);
    int ok = (rc == 0 && m.rm_so == 0);
    regfree(&re);
    return ZenValue_make_boolean(ok);
}

ZenValue ZenRegex_search(ZenValue pattern, ZenValue s) {
    const char* pat = zen_str(pattern);
    const char* str = zen_str(s);
    if (!pat || !str) return ZenValue_make_boolean(false);
    regex_t re;
    if (zen_regcomp(&re, pat, REG_EXTENDED | REG_NOSUB) != 0) {
        return ZenValue_make_boolean(false);
    }
    int ok = (regexec(&re, str, 0, NULL, 0) == 0);
    regfree(&re);
    return ZenValue_make_boolean(ok);
}

ZenValue ZenRegex_replace(ZenValue pattern, ZenValue repl, ZenValue s) {
    const char* pat = zen_str(pattern);
    const char* rep = zen_str(repl);
    const char* str = zen_str(s);
    if (!pat || !rep || !str) return ZenValue_make_string(str ? str : "");

    regex_t re;
    if (zen_regcomp(&re, pat, REG_EXTENDED) != 0) {
        return ZenValue_make_string(str);
    }

    size_t cap = strlen(str) + 64;
    char* out = malloc(cap);
    if (!out) {
        regfree(&re);
        return ZenValue_make_string(str);
    }
    size_t out_len = 0;
    const char* cursor = str;
    size_t rep_len = strlen(rep);

    while (*cursor) {
        regmatch_t m;
        if (regexec(&re, cursor, 1, &m, 0) != 0) {
            size_t rem = strlen(cursor);
            if (out_len + rem + 1 > cap) {
                cap = out_len + rem + 64;
                char* n = realloc(out, cap);
                if (!n) break;
                out = n;
            }
            memcpy(out + out_len, cursor, rem);
            out_len += rem;
            break;
        }
        if (m.rm_so < 0) break;
        size_t pre = (size_t)m.rm_so;
        size_t match_len = (size_t)(m.rm_eo - m.rm_so);
        if (out_len + pre + rep_len + 1 > cap) {
            cap = out_len + pre + rep_len + 64;
            char* n = realloc(out, cap);
            if (!n) break;
            out = n;
        }
        if (pre) {
            memcpy(out + out_len, cursor, pre);
            out_len += pre;
        }
        memcpy(out + out_len, rep, rep_len);
        out_len += rep_len;
        cursor += m.rm_eo;
        if (match_len == 0) {
            if (*cursor) {
                if (out_len + 2 > cap) {
                    cap += 16;
                    char* n = realloc(out, cap);
                    if (!n) break;
                    out = n;
                }
                out[out_len++] = *cursor++;
            } else break;
        }
    }
    out[out_len] = '\0';
    regfree(&re);
    ZenValue v = ZenValue_make_string(out);
    free(out);
    return v;
}

ZenValue ZenRegex_split(ZenValue pattern, ZenValue s) {
    const char* pat = zen_str(pattern);
    const char* str = zen_str(s);
    ZenValue list = ZenList_make_from_arguments(0);
    if (!pat || !str) {
        if (str) ZenList_append_value(list, ZenValue_make_string(str));
        return list;
    }
    regex_t re;
    if (zen_regcomp(&re, pat, REG_EXTENDED) != 0) {
        ZenList_append_value(list, ZenValue_make_string(str));
        return list;
    }
    const char* cursor = str;
    int any = 0;
    while (*cursor) {
        regmatch_t m;
        if (regexec(&re, cursor, 1, &m, 0) != 0) {
            ZenList_append_value(list, ZenValue_make_string(cursor));
            any = 1;
            break;
        }
        if (m.rm_so < 0) {
            ZenList_append_value(list, ZenValue_make_string(cursor));
            any = 1;
            break;
        }
        size_t pre = (size_t)m.rm_so;
        char* part = malloc(pre + 1);
        if (part) {
            memcpy(part, cursor, pre);
            part[pre] = '\0';
            ZenList_append_value(list, ZenValue_make_string(part));
            free(part);
        }
        any = 1;
        size_t match_len = (size_t)(m.rm_eo - m.rm_so);
        cursor += m.rm_eo;
        if (match_len == 0) {
            if (*cursor) {
                char one[2] = { *cursor, 0 };
                ZenList_append_value(list, ZenValue_make_string(one));
                cursor++;
            } else break;
        }
        if (!*cursor) break;
    }
    if (!any && str) {
        ZenList_append_value(list, ZenValue_make_string(str));
    }
    regfree(&re);
    return list;
}

ZenValue ZenRegex_find_all(ZenValue pattern, ZenValue s) {
    /* Python re.findall semantics:
     * - no groups: list of full match strings
     * - groups: list of group tuples (as lists of strings) */
    const char* pat = zen_str(pattern);
    const char* str = zen_str(s);
    ZenValue list = ZenList_make_from_arguments(0);
    if (!pat || !str) return list;

    char* pfix = zen_regex_posixify(pat);
    if (!pfix) return list;
    regex_t re;
    if (regcomp(&re, pfix, REG_EXTENDED) != 0) {
        free(pfix);
        return list;
    }
    free(pfix);

    /* Count capturing groups via re.re_nsub */
    size_t nsub = re.re_nsub;
    size_t nmatch = nsub + 1;
    regmatch_t* ms = calloc(nmatch, sizeof(regmatch_t));
    if (!ms) {
        regfree(&re);
        return list;
    }

    const char* cursor = str;
    while (*cursor) {
        if (regexec(&re, cursor, nmatch, ms, 0) != 0) break;
        if (ms[0].rm_so < 0) break;

        if (nsub == 0) {
            size_t match_len = (size_t)(ms[0].rm_eo - ms[0].rm_so);
            char* part = malloc(match_len + 1);
            if (part) {
                memcpy(part, cursor + ms[0].rm_so, match_len);
                part[match_len] = '\0';
                ZenList_append_value(list, ZenValue_make_string(part));
                free(part);
            }
        } else {
            ZenValue groups = ZenList_make_from_arguments(0);
            for (size_t g = 1; g <= nsub; g++) {
                if (ms[g].rm_so < 0) {
                    ZenList_append_value(groups, ZenValue_make_string(""));
                    continue;
                }
                size_t gl = (size_t)(ms[g].rm_eo - ms[g].rm_so);
                char* part = malloc(gl + 1);
                if (part) {
                    memcpy(part, cursor + ms[g].rm_so, gl);
                    part[gl] = '\0';
                    ZenList_append_value(groups, ZenValue_make_string(part));
                    free(part);
                }
            }
            ZenList_append_value(list, groups);
        }

        size_t match_len = (size_t)(ms[0].rm_eo - ms[0].rm_so);
        cursor += ms[0].rm_eo;
        if (match_len == 0) {
            if (*cursor) cursor++;
            else break;
        }
    }
    free(ms);
    regfree(&re);
    return list;
}
