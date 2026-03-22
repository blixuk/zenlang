#ifndef ZEN_ALLOCATOR_H
#define ZEN_ALLOCATOR_H

#include <stddef.h>

void* zen_alloc(size_t size);
void* zen_realloc(void* ptr, size_t size);
void zen_free(void* ptr);

#endif
