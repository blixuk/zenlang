#ifndef ZEN_AST_H
#define ZEN_AST_H

#include "zen_value.h"

#define ZEN_AST_MAX_SLOTS 6

typedef struct ZenToken {
    int16_t kind;
    int16_t flags;
    int32_t start;
    int32_t length;
    int32_t line;
    int32_t col;
    int32_t end_line;
    int32_t end_col;
} ZenToken;

typedef struct ZenAstNode {
    int16_t kind;
    int16_t slot_count;
    int32_t line;
    int32_t col;
    ZenValue slots[ZEN_AST_MAX_SLOTS];
} ZenAstNode;

// Value Constructors
ZenValue ZenValue_from_token(ZenToken* tok);
ZenValue ZenValue_from_ast_node(ZenAstNode* node);

ZenValue ZenToken_make(ZenValue kind, ZenValue start, ZenValue length,
                       ZenValue line, ZenValue col,
                       ZenValue end_line, ZenValue end_col);

ZenValue ZenAst_node_create0(ZenValue kind, ZenValue line, ZenValue col);
ZenValue ZenAst_node_create1(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0);
ZenValue ZenAst_node_create2(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1);
ZenValue ZenAst_node_create3(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2);
ZenValue ZenAst_node_create4(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2, ZenValue s3);
ZenValue ZenAst_node_create5(ZenValue kind, ZenValue line, ZenValue col, ZenValue s0, ZenValue s1, ZenValue s2, ZenValue s3, ZenValue s4);
ZenValue ZenAst_node_create(ZenValue kind, ZenValue line, ZenValue col,
                            ZenValue s0, ZenValue s1, ZenValue s2,
                            ZenValue s3, ZenValue s4, ZenValue s5);

// Indexing and Length
ZenValue ZenToken_get_at(ZenValue self, ZenValue index);
ZenValue ZenToken_set_at(ZenValue self, ZenValue index, ZenValue val);
ZenValue ZenAst_node_get_at(ZenValue self, ZenValue index);
ZenValue ZenAst_node_set_at(ZenValue self, ZenValue index, ZenValue val);
int ZenAst_node_length(ZenValue self);

// Direct Field Accessors
int ZenAst_node_kind(ZenValue self);
int ZenAst_node_line(ZenValue self);
int ZenAst_node_col(ZenValue self);
ZenValue ZenAst_node_get_slot(ZenValue self, int slot_idx);
void ZenAst_node_set_slot(ZenValue self, int slot_idx, ZenValue val);

int ZenToken_kind(ZenValue self);
int ZenToken_start(ZenValue self);
int ZenToken_length(ZenValue self);
int ZenToken_line(ZenValue self);
int ZenToken_col(ZenValue self);
int ZenToken_end_line(ZenValue self);
int ZenToken_end_col(ZenValue self);

#endif // ZEN_AST_H
