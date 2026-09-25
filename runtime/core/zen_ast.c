#include "zen_ast.h"
#include "../memory/zen_memory.h"
#include <stdlib.h>
#include <string.h>

ZenValue ZenValue_from_token(ZenToken* tok) {
    ZenValue v;
    v.type = ZEN_TOKEN;
    v.as.token = tok;
    return v;
}

ZenValue ZenValue_from_ast_node(ZenAstNode* node) {
    ZenValue v;
    v.type = ZEN_AST_NODE;
    v.as.ast_node = node;
    return v;
}

ZenValue ZenToken_make(ZenValue kind, ZenValue start, ZenValue length,
                       ZenValue line, ZenValue col,
                       ZenValue end_line, ZenValue end_col) {
    ZenToken* t = (ZenToken*)ZenRuntime_allocate(sizeof(ZenToken));
    if (!t) return ZEN_NOTHING_VAL;
    t->kind = (int16_t)(kind.type == ZEN_INTEGER ? kind.as.integer : 0);
    t->flags = 0;
    t->start = (int32_t)(start.type == ZEN_INTEGER ? start.as.integer : 0);
    t->length = (int32_t)(length.type == ZEN_INTEGER ? length.as.integer : 0);
    t->line = (int32_t)(line.type == ZEN_INTEGER ? line.as.integer : 0);
    t->col = (int32_t)(col.type == ZEN_INTEGER ? col.as.integer : 0);
    t->end_line = (int32_t)(end_line.type == ZEN_INTEGER ? end_line.as.integer : 0);
    t->end_col = (int32_t)(end_col.type == ZEN_INTEGER ? end_col.as.integer : 0);
    return ZenValue_from_token(t);
}

static ZenAstNode* alloc_ast_node(int kind, int line, int col, int slot_count) {
    ZenAstNode* n = (ZenAstNode*)ZenRuntime_allocate(sizeof(ZenAstNode));
    if (!n) return NULL;
    n->kind = (int16_t)kind;
    n->slot_count = (int16_t)slot_count;
    n->line = (int32_t)line;
    n->col = (int32_t)col;
    for (int i = 0; i < ZEN_AST_MAX_SLOTS; i++) {
        n->slots[i] = ZEN_NOTHING_VAL;
    }
    return n;
}

static inline int to_int(ZenValue v) {
    return v.type == ZEN_INTEGER ? (int)v.as.integer : 0;
}

ZenValue ZenAst_node_create0(ZenValue kind, ZenValue line, ZenValue col) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 0);
    if (!n) return ZEN_NOTHING_VAL;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create1(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 1);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create2(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 2);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    n->slots[1] = s1;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create3(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 3);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    n->slots[1] = s1;
    n->slots[2] = s2;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create4(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2, ZenValue s3) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 4);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    n->slots[1] = s1;
    n->slots[2] = s2;
    n->slots[3] = s3;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create5(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2, ZenValue s3, ZenValue s4) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 5);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    n->slots[1] = s1;
    n->slots[2] = s2;
    n->slots[3] = s3;
    n->slots[4] = s4;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenAst_node_create(ZenValue kind, ZenValue line, ZenValue col,
                            ZenValue s0, ZenValue s1, ZenValue s2,
                            ZenValue s3, ZenValue s4, ZenValue s5) {
    ZenAstNode* n = alloc_ast_node(to_int(kind), to_int(line), to_int(col), 6);
    if (!n) return ZEN_NOTHING_VAL;
    n->slots[0] = s0;
    n->slots[1] = s1;
    n->slots[2] = s2;
    n->slots[3] = s3;
    n->slots[4] = s4;
    n->slots[5] = s5;
    return ZenValue_from_ast_node(n);
}

ZenValue ZenToken_get_at(ZenValue self, ZenValue index) {
    if (self.type != ZEN_TOKEN || !self.as.token || index.type != ZEN_INTEGER) {
        return ZEN_NOTHING_VAL;
    }
    ZenToken* t = self.as.token;
    switch (index.as.integer) {
        case 0: return ZenValue_make_integer(t->kind);
        case 1: return ZenValue_make_integer(t->start);
        case 2: return ZenValue_make_integer(t->length);
        case 3: return ZenValue_make_integer(t->line);
        case 4: return ZenValue_make_integer(t->col);
        case 5: return ZenValue_make_integer(t->end_line);
        case 6: return ZenValue_make_integer(t->end_col);
        default: return ZEN_NOTHING_VAL;
    }
}

ZenValue ZenToken_set_at(ZenValue self, ZenValue index, ZenValue val) {
    if (self.type != ZEN_TOKEN || !self.as.token || index.type != ZEN_INTEGER) {
        return self;
    }
    ZenToken* t = self.as.token;
    long long v = val.type == ZEN_INTEGER ? val.as.integer : 0;
    switch (index.as.integer) {
        case 0: t->kind = (int16_t)v; break;
        case 1: t->start = (int32_t)v; break;
        case 2: t->length = (int32_t)v; break;
        case 3: t->line = (int32_t)v; break;
        case 4: t->col = (int32_t)v; break;
        case 5: t->end_line = (int32_t)v; break;
        case 6: t->end_col = (int32_t)v; break;
        default: break;
    }
    return self;
}

ZenValue ZenAst_node_get_at(ZenValue self, ZenValue index) {
    if (self.type != ZEN_AST_NODE || !self.as.ast_node || index.type != ZEN_INTEGER) {
        return ZEN_NOTHING_VAL;
    }
    ZenAstNode* n = self.as.ast_node;
    long long idx = index.as.integer;
    switch (idx) {
        case 0: return ZenValue_make_integer(n->kind);
        case 1: return ZenValue_make_integer(n->line);
        case 2: return ZenValue_make_integer(n->col);
        default: {
            int slot = (int)(idx - 3);
            if (slot >= 0 && slot < ZEN_AST_MAX_SLOTS) {
                return n->slots[slot];
            }
            return ZEN_NOTHING_VAL;
        }
    }
}

ZenValue ZenAst_node_set_at(ZenValue self, ZenValue index, ZenValue val) {
    if (self.type != ZEN_AST_NODE || !self.as.ast_node || index.type != ZEN_INTEGER) {
        return self;
    }
    ZenAstNode* n = self.as.ast_node;
    long long idx = index.as.integer;
    switch (idx) {
        case 0: n->kind = (int16_t)(val.type == ZEN_INTEGER ? val.as.integer : 0); break;
        case 1: n->line = (int32_t)(val.type == ZEN_INTEGER ? val.as.integer : 0); break;
        case 2: n->col = (int32_t)(val.type == ZEN_INTEGER ? val.as.integer : 0); break;
        default: {
            int slot = (int)(idx - 3);
            if (slot >= 0 && slot < ZEN_AST_MAX_SLOTS) {
                n->slots[slot] = val;
                if (slot + 1 > n->slot_count) {
                    n->slot_count = (int16_t)(slot + 1);
                }
            }
            break;
        }
    }
    return self;
}

int ZenAst_node_length(ZenValue self) {
    if (self.type != ZEN_AST_NODE || !self.as.ast_node) return 0;
    return 3 + self.as.ast_node->slot_count;
}

int ZenAst_node_kind(ZenValue self) {
    if (self.type == ZEN_AST_NODE && self.as.ast_node) return self.as.ast_node->kind;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 0) {
        ZenValue k = self.as.list->items[0];
        return k.type == ZEN_INTEGER ? (int)k.as.integer : -1;
    }
    return -1;
}

int ZenAst_node_line(ZenValue self) {
    if (self.type == ZEN_AST_NODE && self.as.ast_node) return self.as.ast_node->line;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 1) {
        ZenValue l = self.as.list->items[1];
        return l.type == ZEN_INTEGER ? (int)l.as.integer : 0;
    }
    return 0;
}

int ZenAst_node_col(ZenValue self) {
    if (self.type == ZEN_AST_NODE && self.as.ast_node) return self.as.ast_node->col;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 2) {
        ZenValue c = self.as.list->items[2];
        return c.type == ZEN_INTEGER ? (int)c.as.integer : 0;
    }
    return 0;
}

ZenValue ZenAst_node_get_slot(ZenValue self, int slot_idx) {
    if (self.type == ZEN_AST_NODE && self.as.ast_node) {
        if (slot_idx >= 0 && slot_idx < ZEN_AST_MAX_SLOTS) {
            return self.as.ast_node->slots[slot_idx];
        }
        return ZEN_NOTHING_VAL;
    }
    if (self.type == ZEN_LIST && self.as.list) {
        int idx = 3 + slot_idx;
        if (idx >= 0 && idx < self.as.list->count) {
            return self.as.list->items[idx];
        }
    }
    return ZEN_NOTHING_VAL;
}

void ZenAst_node_set_slot(ZenValue self, int slot_idx, ZenValue val) {
    if (self.type == ZEN_AST_NODE && self.as.ast_node) {
        if (slot_idx >= 0 && slot_idx < ZEN_AST_MAX_SLOTS) {
            self.as.ast_node->slots[slot_idx] = val;
            if (slot_idx + 1 > self.as.ast_node->slot_count) {
                self.as.ast_node->slot_count = (int16_t)(slot_idx + 1);
            }
        }
    } else if (self.type == ZEN_LIST && self.as.list) {
        int idx = 3 + slot_idx;
        if (idx >= 0 && idx < self.as.list->count) {
            self.as.list->items[idx] = val;
        }
    }
}

int ZenToken_kind(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->kind;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 0) {
        ZenValue k = self.as.list->items[0];
        return k.type == ZEN_INTEGER ? (int)k.as.integer : -1;
    }
    return -1;
}

int ZenToken_start(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->start;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 1) {
        ZenValue s = self.as.list->items[1];
        return s.type == ZEN_INTEGER ? (int)s.as.integer : 0;
    }
    return 0;
}

int ZenToken_length(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->length;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 2) {
        ZenValue l = self.as.list->items[2];
        return l.type == ZEN_INTEGER ? (int)l.as.integer : 0;
    }
    return 0;
}

int ZenToken_line(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->line;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 3) {
        ZenValue l = self.as.list->items[3];
        return l.type == ZEN_INTEGER ? (int)l.as.integer : 0;
    }
    return 0;
}

int ZenToken_col(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->col;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 4) {
        ZenValue c = self.as.list->items[4];
        return c.type == ZEN_INTEGER ? (int)c.as.integer : 0;
    }
    return 0;
}

int ZenToken_end_line(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->end_line;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 5) {
        ZenValue l = self.as.list->items[5];
        return l.type == ZEN_INTEGER ? (int)l.as.integer : 0;
    }
    return 0;
}

int ZenToken_end_col(ZenValue self) {
    if (self.type == ZEN_TOKEN && self.as.token) return self.as.token->end_col;
    if (self.type == ZEN_LIST && self.as.list && self.as.list->count > 6) {
        ZenValue c = self.as.list->items[6];
        return c.type == ZEN_INTEGER ? (int)c.as.integer : 0;
    }
    return 0;
}
