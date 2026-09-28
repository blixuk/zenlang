#ifndef ZEN_GC_H
#define ZEN_GC_H

#include "../core/zen_value.h"

void ZenGC_add_suspect(ZenHeapHeader* h);
void ZenGC_remove_suspect(ZenHeapHeader* h);
void ZenGC_collect_cycles(void);
int ZenGC_suspect_count(void);

#endif // ZEN_GC_H
