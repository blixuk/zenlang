#ifndef ZEN_VM_H
#define ZEN_VM_H

#include "zen_value.h"
#include <stdint.h>
#include <stdbool.h>

#define ZEN_VM_STACK_MAX 4096
#define ZEN_VM_MAX_FRAMES 512

typedef enum {
    OP_NOP = 0x00,
    OP_CONST = 0x01,        /* u16 const_idx */
    OP_NOTHING = 0x02,
    OP_DEFAULT = 0x03,      /* u16 type_id */
    OP_TRUE = 0x04,
    OP_FALSE = 0x05,
    OP_INT_SMALL = 0x06,    /* i16 val */
    
    OP_POP = 0x10,
    OP_DUP = 0x11,
    OP_SWAP = 0x12,
    
    OP_LOAD_LOCAL = 0x20,   /* u16 slot */
    OP_STORE_LOCAL = 0x21,  /* u16 slot */
    OP_LOAD_GLOBAL = 0x22,  /* u16 name_const_idx */
    OP_STORE_GLOBAL = 0x23, /* u16 name_const_idx */
    
    OP_ADD = 0x30,
    OP_SUB = 0x31,
    OP_MUL = 0x32,
    OP_DIV = 0x33,
    OP_MOD = 0x34,
    OP_NEG = 0x35,
    OP_NOT = 0x36,
    
    OP_EQ = 0x40,
    OP_NEQ = 0x41,
    OP_LT = 0x42,
    OP_LTE = 0x43,
    OP_GT = 0x44,
    OP_GTE = 0x45,
    
    OP_MAKE_LIST = 0x50,    /* u16 count */
    OP_MAKE_MAP = 0x51,     /* u16 count */
    OP_GET_INDEX = 0x52,
    OP_SET_INDEX = 0x53,
    OP_GET_PROP = 0x54,     /* u16 name_const_idx */
    OP_SET_PROP = 0x55,     /* u16 name_const_idx */
    OP_CAST = 0x56,         /* u16 type_name_const_idx */
    
    OP_JUMP = 0x60,         /* i16 offset */
    OP_JUMP_IF_FALSE = 0x61,/* i16 offset */
    OP_JUMP_IF_TRUE = 0x62, /* i16 offset */
    OP_POP_JUMP_IF_FALSE = 0x63, /* i16 offset */
    
    OP_CALL = 0x70,         /* u8 argc */
    OP_RETURN = 0x71,
    OP_MAKE_CLOSURE = 0x72, /* u16 proto_idx, u8 n_caps */
    OP_CALL_BUILTIN = 0x73, /* u16 builtin_id, u8 argc */
    OP_PRINT = 0x74,        /* u8 argc */
    
    OP_HALT = 0xFF
} ZenOpCode;

typedef struct ZenChunk {
    uint8_t* code;
    int count;
    int capacity;
    ZenValue* constants;
    int const_count;
    int const_capacity;
    int* lines;
    int num_locals;
    char* name;
} ZenChunk;

typedef struct ZenCallFrame {
    ZenChunk* chunk;
    uint8_t* ip;
    ZenValue* slots;
} ZenCallFrame;

typedef struct ZenVM {
    ZenCallFrame frames[ZEN_VM_MAX_FRAMES];
    int frame_count;
    ZenValue stack[ZEN_VM_STACK_MAX];
    ZenValue* stack_top;
    struct ZenMap* globals;
    bool has_error;
    ZenValue error_val;
} ZenVM;

/* Chunk Lifecycle */
ZenChunk* ZenChunk_new(const char* name);
void ZenChunk_free(ZenChunk* chunk);
void ZenChunk_emit_byte(ZenChunk* chunk, uint8_t byte, int line);
void ZenChunk_emit_u16(ZenChunk* chunk, uint16_t val, int line);
void ZenChunk_emit_i16(ZenChunk* chunk, int16_t val, int line);
int ZenChunk_add_constant(ZenChunk* chunk, ZenValue val);
void ZenChunk_patch_i16(ZenChunk* chunk, int offset, int16_t val);

/* VM Execution */
ZenVM* ZenVM_new(void);
void ZenVM_free(ZenVM* vm);
void ZenVM_reset(ZenVM* vm);
ZenValue ZenVM_run_chunk(ZenVM* vm, ZenChunk* chunk);

/* Disassembly / Debug */
void ZenChunk_disassemble(ZenChunk* chunk, const char* label);
int ZenChunk_disassemble_instruction(ZenChunk* chunk, int offset);

/* ZenValue Object Wrapper for Chunk (allows Zen programs to hold ZenChunk as ZenValue) */
ZenValue ZenValue_from_chunk(ZenChunk* chunk);
ZenChunk* ZenValue_to_chunk(ZenValue val);

/* Mixed Execution ABI & Embed API (Phase 4) */
void ZenVM_register_global(ZenVM* vm, const char* name, ZenValue val);
void ZenVM_register_native_func(ZenVM* vm, const char* name, void* fn);
ZenValue ZenVM_load_native_module(ZenVM* vm, const char* path);
ZenValue ZenVM_call_named(ZenVM* vm, const char* func_name, int argc, ZenValue* args);

/* Bytecode Binary Serialization & Packaging (.zbc) */
int ZenChunk_save_file(ZenChunk* chunk, const char* path, uint64_t src_hash);
ZenChunk* ZenChunk_load_file(const char* path, uint64_t* out_src_hash);
ZenValue ZenVM_run_bytecode_file(ZenVM* vm, const char* path);

#endif /* ZEN_VM_H */
