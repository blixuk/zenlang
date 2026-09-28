#include "zen_gc.h"
#include "../core/zen_value.h"
#include "../collections/zen_list.h"
#include "../collections/zen_map.h"
#include "../collections/zen_set.h"
#include "../core/zen_variant.h"
#include "../core/zen_closure.h"
#include "../core/zen_object.h"
#include "../concurrency/zen_channel.h"
#include "../concurrency/zen_task.h"
#include <stdlib.h>
#include <stdbool.h>

#define GC_COLOR_BLACK 0  /* In use / Alive */
#define GC_COLOR_GRAY  1  /* Trial deletion tracing */
#define GC_COLOR_WHITE 2  /* Confirmed dead cycle */

#define MAX_SUSPECTS 8192

static ZenHeapHeader* suspects[MAX_SUSPECTS];
static int suspect_count = 0;
static bool in_collection = false;

int ZenGC_suspect_count(void) {
    return suspect_count;
}

void ZenGC_add_suspect(ZenHeapHeader* h) {
    if (in_collection) return;
    if (!h || h->ref_count <= 0 || h->ref_count == ZEN_REF_PINNED || h->ref_count == ZEN_REF_FROZEN) return;
    if (h->extra != 0) return; // Already in suspect buffer

    if (suspect_count >= MAX_SUSPECTS) {
        ZenGC_collect_cycles();
        if (suspect_count >= MAX_SUSPECTS) return;
    }

    int idx = suspect_count++;
    suspects[idx] = h;
    h->extra = (uint16_t)(idx + 1);
}

void ZenGC_remove_suspect(ZenHeapHeader* h) {
    if (!h || h->extra == 0 || in_collection) return;
    int idx = (int)h->extra - 1;
    if (idx >= 0 && idx < suspect_count && suspects[idx] == h) {
        int last = --suspect_count;
        if (idx != last) {
            ZenHeapHeader* moved = suspects[last];
            suspects[idx] = moved;
            if (moved) {
                moved->extra = (uint16_t)(idx + 1);
            }
        }
        suspects[last] = NULL;
    }
    h->extra = 0;
}

/* =========================================================================
 * Phase 1: Mark Gray (Trial Decrement)
 * ========================================================================= */
static void mark_gray(ZenHeapHeader* h);
static void mark_gray_visitor(ZenValue child, void* context) {
    (void)context;
    ZenHeapHeader* h = ZenValue_get_header(child);
    if (h && h->ref_count > 0 && h->ref_count != ZEN_REF_PINNED && h->ref_count != ZEN_REF_FROZEN) {
        h->ref_count--;
        mark_gray(h);
    }
}

static void mark_gray(ZenHeapHeader* h) {
    if (h->extra != GC_COLOR_GRAY) {
        h->extra = GC_COLOR_GRAY;
        ZenValue_visit_children(h, mark_gray_visitor, NULL);
    }
}

/* =========================================================================
 * Phase 2: Scan (Detect External Edges vs Isolated Cycles)
 * ========================================================================= */
static void scan_black(ZenHeapHeader* h);
static void scan_black_visitor(ZenValue child, void* context) {
    (void)context;
    ZenHeapHeader* h = ZenValue_get_header(child);
    if (h && h->ref_count >= 0 && h->ref_count != ZEN_REF_PINNED && h->ref_count != ZEN_REF_FROZEN) {
        h->ref_count++;
        if (h->extra != GC_COLOR_BLACK) {
            scan_black(h);
        }
    }
}

static void scan_black(ZenHeapHeader* h) {
    if (!h) return;
    h->extra = GC_COLOR_BLACK;
    ZenValue_visit_children(h, scan_black_visitor, NULL);
}

static void scan(ZenHeapHeader* h);
static void scan_visitor(ZenValue child, void* context) {
    (void)context;
    ZenHeapHeader* h = ZenValue_get_header(child);
    if (h && h->ref_count >= 0 && h->ref_count != ZEN_REF_PINNED && h->ref_count != ZEN_REF_FROZEN) {
        scan(h);
    }
}

static void scan(ZenHeapHeader* h) {
    if (!h) return;
    if (h->extra == GC_COLOR_GRAY) {
        if (h->ref_count > 0) {
            scan_black(h); // Found external reference, graph is alive
        } else {
            h->extra = GC_COLOR_WHITE; // No external refs, conditionally dead
            ZenValue_visit_children(h, scan_visitor, NULL);
        }
    }
}

/* =========================================================================
 * Phase 3: Sever Container Edges (UAF Protection)
 * ========================================================================= */
static void clear_container_safely(ZenHeapHeader* h) {
    if (!h) return;
    switch (h->type) {
        case ZEN_LIST: {
            ZenList* list = (ZenList*)h;
            list->count = 0;
            break;
        }
        case ZEN_MAP: {
            ZenMap* map = (ZenMap*)h;
            map->count = 0;
            break;
        }
        case ZEN_SET: {
            ZenSet* set = (ZenSet*)h;
            set->list = (ZenValue){ZEN_NOTHING, {0}};
            break;
        }
        case ZEN_VARIANT: {
            ZenVariantObject* var = (ZenVariantObject*)h;
            ZenValue n = { .type = ZEN_NOTHING, .as.integer = 0 };
            var->enum_name = n;
            var->variant_name = n;
            var->data = n;
            break;
        }
        case ZEN_FUNCTION: {
            ZenClosureData* closure = (ZenClosureData*)h;
            closure->n_caps = 0;
            break;
        }
        case ZEN_OBJECT: {
            break;
        }
        case ZEN_CHANNEL: {
            ZenChannel* ch = (ZenChannel*)h;
            pthread_mutex_lock(&ch->lock);
            ch->count = 0;
            ch->head = 0;
            ch->tail = 0;
            pthread_mutex_unlock(&ch->lock);
            break;
        }
        case ZEN_TASK: {
            ZenTaskHandle* task = (ZenTaskHandle*)h;
            pthread_mutex_lock(&task->lock);
            task->callable = (ZenValue){ZEN_NOTHING, {0}};
            task->argument = (ZenValue){ZEN_NOTHING, {0}};
            task->result = (ZenValue){ZEN_NOTHING, {0}};
            pthread_mutex_unlock(&task->lock);
            break;
        }
        default:
            break;
    }
}

/* =========================================================================
 * Cycle Collection Execution
 * ========================================================================= */
void ZenGC_collect_cycles(void) {
    if (in_collection || suspect_count == 0) return;
    in_collection = true;

    // 1. Trial decrement (Mark Gray)
    for (int i = 0; i < suspect_count; i++) {
        if (suspects[i]) {
            mark_gray(suspects[i]);
        }
    }

    // 2. Scan and color
    for (int i = 0; i < suspect_count; i++) {
        if (suspects[i]) {
            scan(suspects[i]);
        }
    }

    // 3. Sever cycle edges to prevent Use-After-Free during destruction
    for (int i = 0; i < suspect_count; i++) {
        if (suspects[i] && suspects[i]->extra == GC_COLOR_WHITE) {
            clear_container_safely(suspects[i]);
        }
    }

    // 4. Safely free isolated white nodes
    for (int i = 0; i < suspect_count; i++) {
        ZenHeapHeader* h = suspects[i];
        if (!h) continue;
        if (h->extra == GC_COLOR_WHITE) {
            h->extra = GC_COLOR_BLACK; 
            h->ref_count = ZEN_REF_DEAD; // Safety lock
            
            switch (h->type) {
                case ZEN_LIST: ZenList_destroy((ZenList*)h); break;
                case ZEN_MAP: ZenMap_destroy((ZenMap*)h); break;
                case ZEN_SET: ZenSet_destroy((ZenSet*)h); break;
                case ZEN_VARIANT: ZenVariantObject_destroy((ZenVariantObject*)h); break;
                case ZEN_FUNCTION: ZenClosure_destroy((ZenClosureData*)h); break;
                case ZEN_OBJECT: ZenObject_destroy((ZenObject*)h); break;
                case ZEN_CHANNEL: ZenChannel_destroy((ZenChannel*)h); break;
                case ZEN_TASK: ZenTask_destroy((ZenTaskHandle*)h); break;
                default: break;
            }
        } else {
            h->extra = GC_COLOR_BLACK; // Reset surviving active nodes
        }
        suspects[i] = NULL;
    }

    suspect_count = 0; // Clear buffer
    in_collection = false;
}
