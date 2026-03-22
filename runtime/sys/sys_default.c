#include "zen_sys.h"
#include <stdlib.h>
#include <zen_object.h>
#include <string.h>

int zen_argc = 0;
char** zen_argv = NULL;

ZenList* Sys_get_args() {
    ZenList* list = ZenList_create();
    for (int i = 0; i < zen_argc; i++) {
        ZenList_append(list, ZenString_create(zen_argv[i]));
    }
    return list;
}

ZenString Sys_get_env(ZenString key) {
    char* val = getenv(key);
    if (!val) return NULL;
    return ZenString_create(val);
}

void Sys_exit(long long code) {
    exit((int)code);
}
