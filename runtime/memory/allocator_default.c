#include <stdlib.h>
#include "zen_allocator.h"

__attribute__((weak))
void* zen_alloc(size_t size) {
    return malloc(size);
}

__attribute__((weak))
void* zen_realloc(void* ptr, size_t size) {
    return realloc(ptr, size);
}

__attribute__((weak))
void zen_free(void* ptr) {
    free(ptr);
}
