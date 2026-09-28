#include "zen_vm.h"
#include "zen_ops.h"
#include "zen_dispatch.h"
#include "zen_sys.h"
#include "zen_closure.h"
#include "../concurrency/zen_task.h"
#include "../concurrency/zen_channel.h"
#include "../collections/zen_list.h"
#include "../collections/zen_map.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

#define READ_BYTE(frame) (*(frame)->ip++)
#define READ_U16(frame) ((frame)->ip += 2, (uint16_t)(((frame)->ip[-2] << 8) | (frame)->ip[-1]))
#define READ_I16(frame) ((frame)->ip += 2, (int16_t)(((frame)->ip[-2] << 8) | (frame)->ip[-1]))
#define READ_CONST(frame) ((frame)->chunk->constants[READ_U16(frame)])

/* --- Chunk Implementation --- */

ZenChunk* ZenChunk_new(const char* name) {
    ZenChunk* chunk = (ZenChunk*)malloc(sizeof(ZenChunk));
    if (!chunk) return NULL;
    chunk->code = NULL;
    chunk->count = 0;
    chunk->capacity = 0;
    chunk->constants = NULL;
    chunk->const_count = 0;
    chunk->const_capacity = 0;
    chunk->lines = NULL;
    chunk->num_locals = 0;
    chunk->name = name ? strdup(name) : strdup("<script>");
    return chunk;
}

void ZenChunk_free(ZenChunk* chunk) {
    if (!chunk) return;
    if (chunk->code) free(chunk->code);
    if (chunk->constants) {
        for (int i = 0; i < chunk->const_count; i++) {
            if (chunk->constants[i].type == ZEN_FUNCTION && chunk->constants[i].as.object) {
                ZenChunk_free((ZenChunk*)chunk->constants[i].as.object);
            }
        }
        free(chunk->constants);
    }
    if (chunk->lines) free(chunk->lines);
    if (chunk->name) free(chunk->name);
    free(chunk);
}

void ZenChunk_emit_byte(ZenChunk* chunk, uint8_t byte, int line) {
    if (chunk->count >= chunk->capacity) {
        int new_cap = chunk->capacity < 8 ? 8 : chunk->capacity * 2;
        chunk->code = (uint8_t*)realloc(chunk->code, new_cap * sizeof(uint8_t));
        chunk->lines = (int*)realloc(chunk->lines, new_cap * sizeof(int));
        chunk->capacity = new_cap;
    }
    chunk->code[chunk->count] = byte;
    chunk->lines[chunk->count] = line;
    chunk->count++;
}

void ZenChunk_emit_u16(ZenChunk* chunk, uint16_t val, int line) {
    ZenChunk_emit_byte(chunk, (uint8_t)((val >> 8) & 0xFF), line);
    ZenChunk_emit_byte(chunk, (uint8_t)(val & 0xFF), line);
}

void ZenChunk_emit_i16(ZenChunk* chunk, int16_t val, int line) {
    ZenChunk_emit_u16(chunk, (uint16_t)val, line);
}

int ZenChunk_add_constant(ZenChunk* chunk, ZenValue val) {
    if (chunk->const_count >= chunk->const_capacity) {
        int new_cap = chunk->const_capacity < 8 ? 8 : chunk->const_capacity * 2;
        chunk->constants = (ZenValue*)realloc(chunk->constants, new_cap * sizeof(ZenValue));
        chunk->const_capacity = new_cap;
    }
    
    /* ---------------------------------------------------------
     * PHASE 3: Constant Pool Freezing
     * Heap objects residing in the Bytecode chunk's constant 
     * pool are permanently frozen to elide ARC churn.
     * --------------------------------------------------------- */
    if (ZenValue_is_heap_pointer(val)) {
        ZenHeapHeader* h = (ZenHeapHeader*)val.as.object;
        if (h) {
            h->ref_count = ZEN_REF_FROZEN;
            h->flags |= ZEN_FLAG_FROZEN;
        }
    }

    chunk->constants[chunk->const_count] = val;
    return chunk->const_count++;
}

void ZenChunk_patch_i16(ZenChunk* chunk, int offset, int16_t val) {
    if (offset + 1 < chunk->count) {
        chunk->code[offset] = (uint8_t)((val >> 8) & 0xFF);
        chunk->code[offset + 1] = (uint8_t)(val & 0xFF);
    }
}

/* ZenValue object wrapper for chunk */
ZenValue ZenValue_from_chunk(ZenChunk* chunk) {
    return ZenValue_from_object((void*)chunk);
}

ZenChunk* ZenValue_to_chunk(ZenValue val) {
    return (ZenChunk*)ZenValue_to_object(val);
}

/* --- Disassembler --- */

void ZenChunk_disassemble(ZenChunk* chunk, const char* label) {
    printf("== %s (%s) ==\n", label ? label : "chunk", chunk->name ? chunk->name : "");
    for (int offset = 0; offset < chunk->count;) {
        offset = ZenChunk_disassemble_instruction(chunk, offset);
    }
}

static int simple_instruction(const char* name, int offset) {
    printf("%-20s\n", name);
    return offset + 1;
}

static int u16_instruction(const char* name, ZenChunk* chunk, int offset) {
    uint16_t val = (uint16_t)((chunk->code[offset + 1] << 8) | chunk->code[offset + 2]);
    printf("%-20s %4d\n", name, val);
    return offset + 3;
}

static int i16_instruction(const char* name, ZenChunk* chunk, int offset) {
    int16_t val = (int16_t)((chunk->code[offset + 1] << 8) | chunk->code[offset + 2]);
    printf("%-20s %+4d (dest %d)\n", name, val, offset + 3 + val);
    return offset + 3;
}

static int const_instruction(const char* name, ZenChunk* chunk, int offset) {
    uint16_t idx = (uint16_t)((chunk->code[offset + 1] << 8) | chunk->code[offset + 2]);
    printf("%-20s %4d '", name, idx);
    if (idx < chunk->const_count) {
        ZenValue v = chunk->constants[idx];
        if (v.type == ZEN_STRING) printf("%s", v.as.string);
        else if (v.type == ZEN_INTEGER) printf("%lld", v.as.integer);
        else if (v.type == ZEN_DECIMAL) printf("%g", v.as.decimal);
        else if (v.type == ZEN_BOOLEAN) printf("%s", v.as.boolean ? "True" : "False");
        else if (v.type == ZEN_NOTHING) printf("Nothing");
        else if (v.type == ZEN_DEFAULT) printf("Default");
        else printf("[type %d]", v.type);
    }
    printf("'\n");
    return offset + 3;
}

int ZenChunk_disassemble_instruction(ZenChunk* chunk, int offset) {
    printf("%04d ", offset);
    if (offset > 0 && chunk->lines[offset] == chunk->lines[offset - 1]) {
        printf("   | ");
    } else {
        printf("%4d ", chunk->lines[offset]);
    }

    uint8_t instruction = chunk->code[offset];
    switch (instruction) {
        case OP_NOP: return simple_instruction("OP_NOP", offset);
        case OP_CONST: return const_instruction("OP_CONST", chunk, offset);
        case OP_NOTHING: return simple_instruction("OP_NOTHING", offset);
        case OP_DEFAULT: return u16_instruction("OP_DEFAULT", chunk, offset);
        case OP_TRUE: return simple_instruction("OP_TRUE", offset);
        case OP_FALSE: return simple_instruction("OP_FALSE", offset);
        case OP_INT_SMALL: return i16_instruction("OP_INT_SMALL", chunk, offset);
        case OP_POP: return simple_instruction("OP_POP", offset);
        case OP_DUP: return simple_instruction("OP_DUP", offset);
        case OP_SWAP: return simple_instruction("OP_SWAP", offset);
        case OP_LOAD_LOCAL: return u16_instruction("OP_LOAD_LOCAL", chunk, offset);
        case OP_STORE_LOCAL: return u16_instruction("OP_STORE_LOCAL", chunk, offset);
        case OP_LOAD_GLOBAL: return const_instruction("OP_LOAD_GLOBAL", chunk, offset);
        case OP_STORE_GLOBAL: return const_instruction("OP_STORE_GLOBAL", chunk, offset);
        case OP_ADD: return simple_instruction("OP_ADD", offset);
        case OP_SUB: return simple_instruction("OP_SUB", offset);
        case OP_MUL: return simple_instruction("OP_MUL", offset);
        case OP_DIV: return simple_instruction("OP_DIV", offset);
        case OP_MOD: return simple_instruction("OP_MOD", offset);
        case OP_NEG: return simple_instruction("OP_NEG", offset);
        case OP_NOT: return simple_instruction("OP_NOT", offset);
        case OP_EQ: return simple_instruction("OP_EQ", offset);
        case OP_NEQ: return simple_instruction("OP_NEQ", offset);
        case OP_LT: return simple_instruction("OP_LT", offset);
        case OP_LTE: return simple_instruction("OP_LTE", offset);
        case OP_GT: return simple_instruction("OP_GT", offset);
        case OP_GTE: return simple_instruction("OP_GTE", offset);
        case OP_MAKE_LIST: return u16_instruction("OP_MAKE_LIST", chunk, offset);
        case OP_MAKE_MAP: return u16_instruction("OP_MAKE_MAP", chunk, offset);
        case OP_GET_INDEX: return simple_instruction("OP_GET_INDEX", offset);
        case OP_SET_INDEX: return simple_instruction("OP_SET_INDEX", offset);
        case OP_GET_PROP: return const_instruction("OP_GET_PROP", chunk, offset);
        case OP_SET_PROP: return const_instruction("OP_SET_PROP", chunk, offset);
        case OP_CAST: return const_instruction("OP_CAST", chunk, offset);
        case OP_RANGE_EXCL: return simple_instruction("OP_RANGE_EXCL", offset);
        case OP_RANGE_INCL: return simple_instruction("OP_RANGE_INCL", offset);
        case OP_CONCAT_APPEND: return simple_instruction("OP_CONCAT_APPEND", offset);
        case OP_DROP: return simple_instruction("OP_DROP", offset);
        case OP_CHECK_UNWRAP: return simple_instruction("OP_CHECK_UNWRAP", offset);
        case OP_RANGE_INCL_END: return simple_instruction("OP_RANGE_INCL_END", offset);
        case OP_RANGE_BETWEEN: return simple_instruction("OP_RANGE_BETWEEN", offset);
        case OP_IN: return simple_instruction("OP_IN", offset);
        case OP_COALESCE: return simple_instruction("OP_COALESCE", offset);
        case OP_SLICE: return simple_instruction("OP_SLICE", offset);
        case OP_JUMP: return i16_instruction("OP_JUMP", chunk, offset);
        case OP_JUMP_IF_FALSE: return i16_instruction("OP_JUMP_IF_FALSE", chunk, offset);
        case OP_JUMP_IF_TRUE: return i16_instruction("OP_JUMP_IF_TRUE", chunk, offset);
        case OP_POP_JUMP_IF_FALSE: return i16_instruction("OP_POP_JUMP_IF_FALSE", chunk, offset);
        case OP_CALL: return u16_instruction("OP_CALL", chunk, offset);
        case OP_RETURN: return simple_instruction("OP_RETURN", offset);
        case OP_MAKE_CLOSURE: return u16_instruction("OP_MAKE_CLOSURE", chunk, offset);
        case OP_PRINT: return u16_instruction("OP_PRINT", chunk, offset);
        case OP_HALT: return simple_instruction("OP_HALT", offset);
        default:
            printf("Unknown opcode 0x%02X\n", instruction);
            return offset + 1;
    }
}

/* --- Virtual Machine Implementation --- */

ZenVM* ZenVM_new(void) {
    ZenVM* vm = (ZenVM*)malloc(sizeof(ZenVM));
    if (!vm) return NULL;
    vm->globals = ZenMap_new();
    ZenVM_register_native_func(vm, "channel", (void*)ZenChannel_make);
    ZenVM_register_native_func(vm, "spawn", (void*)ZenTask_spawn_val);
    vm->stack_top = vm->stack;
    vm->frame_count = 0;
    vm->has_error = false;
    vm->error_val = ZEN_NOTHING_VAL;
    return vm;
}

void ZenVM_free(ZenVM* vm) {
    if (!vm) return;
    ZenVM_reset(vm);
    free(vm);
}

void ZenVM_reset(ZenVM* vm) {
    if (!vm) return;
    // Abnormal Unwind: Safely release all active stack slots to prevent 
    // memory leaks during exception propagation or fatal panics.
    while (vm->stack_top > vm->stack) {
        vm->stack_top--;
        ZenValue_release(*vm->stack_top);
    }
    ZenGC_collect_cycles();
    
    vm->frame_count = 0;
    vm->stack_top = vm->stack;
    vm->has_error = false;
    vm->error_val = ZEN_NOTHING_VAL;
}

static inline void push(ZenVM* vm, ZenValue val) {
    *vm->stack_top++ = val;
}

static inline ZenValue pop(ZenVM* vm) {
    return *(--vm->stack_top);
}

static inline ZenValue peek(ZenVM* vm, int distance) {
    return vm->stack_top[-1 - distance];
}

static inline bool is_truthy(ZenValue v) {
    if (v.type == ZEN_NOTHING) return false;
    if (v.type == ZEN_BOOLEAN) return v.as.boolean;
    if (v.type == ZEN_INTEGER) return v.as.integer != 0;
    if (v.type == ZEN_DECIMAL) return v.as.decimal != 0.0;
    if (v.type == ZEN_STRING) return v.as.string && v.as.string[0] != '\0';
    return true;
}

static ZenValue zen_invoke_native_fn(void* fn, int total, ZenValue* args) {
    if (!fn) return ZEN_NOTHING_VAL;
    switch (total) {
        case 0:
            return ((ZenValue (*)(void))fn)();
        case 1:
            return ((ZenValue (*)(ZenValue))fn)(args[0]);
        case 2:
            return ((ZenValue (*)(ZenValue, ZenValue))fn)(args[0], args[1]);
        case 3:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue))fn)(args[0], args[1], args[2]);
        case 4:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3]);
        case 5:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4]);
        case 6:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5]);
        case 7:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6]);
        case 8:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7]);
        default:
            fprintf(stderr, "VM Error: Native function apply arity %d exceeds limit\n", total);
            return ZEN_NOTHING_VAL;
    }
}

#if defined(__GNUC__) || defined(__clang__)
#define ZEN_VM_DIRECT_THREADED 1
#endif

ZenValue ZenVM_run_chunk(ZenVM* vm, ZenChunk* chunk) {
    if (!vm || !chunk) return ZEN_NOTHING_VAL;

    ZenCallFrame* frame = &vm->frames[vm->frame_count++];
    frame->chunk = chunk;
    frame->ip = chunk->code;
    frame->slots = vm->stack_top;
    frame->argc = 0;

    // Reserve slots for locals
    for (int i = 0; i < chunk->num_locals; i++) {
        push(vm, ZEN_NOTHING_VAL);
    }

#if ZEN_VM_DIRECT_THREADED
    static const void* const dispatch_table[256] = {
        [0 ... 255] = &&do_OP_UNKNOWN,
        [OP_NOP] = &&do_OP_NOP,
        [OP_CONST] = &&do_OP_CONST,
        [OP_NOTHING] = &&do_OP_NOTHING,
        [OP_DEFAULT] = &&do_OP_DEFAULT,
        [OP_TRUE] = &&do_OP_TRUE,
        [OP_FALSE] = &&do_OP_FALSE,
        [OP_INT_SMALL] = &&do_OP_INT_SMALL,
        [OP_POP] = &&do_OP_POP,
        [OP_DUP] = &&do_OP_DUP,
        [OP_SWAP] = &&do_OP_SWAP,
        [OP_LOAD_LOCAL] = &&do_OP_LOAD_LOCAL,
        [OP_STORE_LOCAL] = &&do_OP_STORE_LOCAL,
        [OP_LOAD_GLOBAL] = &&do_OP_LOAD_GLOBAL,
        [OP_STORE_GLOBAL] = &&do_OP_STORE_GLOBAL,
        [OP_END_SCOPE] = &&do_OP_END_SCOPE,
        [OP_ADD] = &&do_OP_ADD,
        [OP_SUB] = &&do_OP_SUB,
        [OP_MUL] = &&do_OP_MUL,
        [OP_DIV] = &&do_OP_DIV,
        [OP_MOD] = &&do_OP_MOD,
        [OP_NEG] = &&do_OP_NEG,
        [OP_NOT] = &&do_OP_NOT,
        [OP_EQ] = &&do_OP_EQ,
        [OP_NEQ] = &&do_OP_NEQ,
        [OP_LT] = &&do_OP_LT,
        [OP_LTE] = &&do_OP_LTE,
        [OP_GT] = &&do_OP_GT,
        [OP_GTE] = &&do_OP_GTE,
        [OP_MAKE_LIST] = &&do_OP_MAKE_LIST,
        [OP_MAKE_MAP] = &&do_OP_MAKE_MAP,
        [OP_GET_INDEX] = &&do_OP_GET_INDEX,
        [OP_SET_INDEX] = &&do_OP_SET_INDEX,
        [OP_GET_PROP] = &&do_OP_GET_PROP,
        [OP_SET_PROP] = &&do_OP_SET_PROP,
        [OP_CAST] = &&do_OP_CAST,
        [OP_RANGE_EXCL] = &&do_OP_RANGE_EXCL,
        [OP_RANGE_INCL] = &&do_OP_RANGE_INCL,
        [OP_CONCAT_APPEND] = &&do_OP_CONCAT_APPEND,
        [OP_DROP] = &&do_OP_DROP,
        [OP_CHECK_UNWRAP] = &&do_OP_CHECK_UNWRAP,
        [OP_RANGE_INCL_END] = &&do_OP_RANGE_INCL_END,
        [OP_RANGE_BETWEEN] = &&do_OP_RANGE_BETWEEN,
        [OP_IN] = &&do_OP_IN,
        [OP_COALESCE] = &&do_OP_COALESCE,
        [OP_SLICE] = &&do_OP_SLICE,
        [OP_JUMP] = &&do_OP_JUMP,
        [OP_JUMP_IF_FALSE] = &&do_OP_JUMP_IF_FALSE,
        [OP_JUMP_IF_TRUE] = &&do_OP_JUMP_IF_TRUE,
        [OP_POP_JUMP_IF_FALSE] = &&do_OP_POP_JUMP_IF_FALSE,
        [OP_CALL] = &&do_OP_CALL,
        [OP_RETURN] = &&do_OP_RETURN,
        [OP_MAKE_CLOSURE] = &&do_OP_MAKE_CLOSURE,
        [OP_PRINT] = &&do_OP_PRINT,
        [OP_HALT] = &&do_OP_HALT,
    };
    #define DISPATCH() goto *dispatch_table[READ_BYTE(frame)]
    #define TARGET(op) do_##op:
    #define NEXT() DISPATCH()
    
    DISPATCH();
#else
    #define TARGET(op) case op:
    #define NEXT() break

    while (1) {
        uint8_t instruction = READ_BYTE(frame);
        switch (instruction) {
#endif
            TARGET(OP_NOP)
                NEXT();
                
            TARGET(OP_CONST) {
                ZenValue constant = READ_CONST(frame);
                push(vm, constant);
                NEXT();
            }
            
            TARGET(OP_NOTHING) {
                push(vm, ZEN_NOTHING_VAL);
                NEXT();
            }
            
            TARGET(OP_DEFAULT) {
                uint16_t type_id = READ_U16(frame);
                switch (type_id) {
                    case ZEN_INTEGER: push(vm, ZenValue_make_integer(0)); break;
                    case ZEN_DECIMAL: push(vm, ZenValue_make_decimal(0.0)); break;
                    case ZEN_BOOLEAN: push(vm, ZenValue_make_boolean(false)); break;
                    case ZEN_STRING: push(vm, ZenValue_make_string("")); break;
                    case ZEN_LIST: push(vm, ZenValue_from_list(ZenList_new())); break;
                    case ZEN_MAP: push(vm, ZenValue_from_map(ZenMap_new())); break;
                    default: push(vm, ZEN_DEFAULT_VAL); break;
                }
                NEXT();
            }
            
            TARGET(OP_TRUE) {
                push(vm, ZenValue_make_boolean(true));
                NEXT();
            }
            
            TARGET(OP_FALSE) {
                push(vm, ZenValue_make_boolean(false));
                NEXT();
            }
            
            TARGET(OP_INT_SMALL) {
                int16_t val = READ_I16(frame);
                push(vm, ZenValue_make_integer(val));
                NEXT();
            }
            
            TARGET(OP_POP) {
                ZenValue discarded = pop(vm);
                ZenValue_release(discarded);
                NEXT();
            }
            
            TARGET(OP_DUP) {
                ZenValue val = peek(vm, 0);
                ZenValue_retain(val);
                push(vm, val);
                NEXT();
            }
            
            TARGET(OP_SWAP) {
                ZenValue a = pop(vm);
                ZenValue b = pop(vm);
                push(vm, a);
                push(vm, b);
                NEXT();
            }
            
            TARGET(OP_LOAD_LOCAL) {
                uint16_t slot = READ_U16(frame);
                ZenValue val = frame->slots[slot];
                ZenValue_retain(val);
                push(vm, val);
                NEXT();
            }
            
            TARGET(OP_STORE_LOCAL) {
                uint16_t slot = READ_U16(frame);
                ZenValue new_val = pop(vm);
                ZenValue old_val = frame->slots[slot];
                frame->slots[slot] = new_val;
                ZenValue_release(old_val);
                NEXT();
            }
            
            TARGET(OP_LOAD_GLOBAL) {
                ZenValue name = READ_CONST(frame);
                ZenValue val = ZenMap_get_value_at_key(ZenValue_from_map(vm->globals), name);
                if (val.type == ZEN_NOTHING && name.type == ZEN_STRING && name.as.string) {
                    val = ZenFFI_resolve_symbol(name.as.string);
                    if (val.type != ZEN_NOTHING) {
                        ZenMap_set_value_at_key(ZenValue_from_map(vm->globals), name, val);
                    }
                }
                push(vm, val);
                NEXT();
            }
            
            TARGET(OP_STORE_GLOBAL) {
                ZenValue name = READ_CONST(frame);
                ZenValue val = pop(vm);
                ZenMap_set_value_at_key(ZenValue_from_map(vm->globals), name, val);
                NEXT();
            }
            
            TARGET(OP_END_SCOPE) {
                uint8_t count = READ_BYTE(frame);
                for (int i = 0; i < count; i++) {
                    ZenValue_release(pop(vm));
                }
                NEXT();
            }
            
            TARGET(OP_ADD) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_integer(a.as.integer + b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_decimal(a.as.decimal + b.as.decimal));
                } else {
                    push(vm, ZenValue_add(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_SUB) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_integer(a.as.integer - b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_decimal(a.as.decimal - b.as.decimal));
                } else {
                    push(vm, ZenValue_subtract(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_MUL) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_integer(a.as.integer * b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_decimal(a.as.decimal * b.as.decimal));
                } else {
                    push(vm, ZenValue_multiply(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_DIV) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER && b.as.integer != 0 && (a.as.integer % b.as.integer == 0)) {
                    push(vm, ZenValue_make_integer(a.as.integer / b.as.integer));
                } else {
                    push(vm, ZenValue_divide(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_MOD) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER && b.as.integer != 0) {
                    push(vm, ZenValue_make_integer(a.as.integer % b.as.integer));
                } else {
                    push(vm, ZenValue_modulo(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_NEG) {
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_integer(-a.as.integer));
                } else if (a.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_decimal(-a.as.decimal));
                } else {
                    push(vm, ZenValue_negate(a));
                }
                NEXT();
            }
            
            TARGET(OP_NOT) {
                ZenValue a = pop(vm);
                if (a.type == ZEN_BOOLEAN) {
                    push(vm, ZenValue_make_boolean(!a.as.boolean));
                } else {
                    push(vm, ZenValue_not(a));
                }
                NEXT();
            }
            
            TARGET(OP_EQ) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer == b.as.integer));
                } else if (a.type == ZEN_BOOLEAN && b.type == ZEN_BOOLEAN) {
                    push(vm, ZenValue_make_boolean(a.as.boolean == b.as.boolean));
                } else {
                    push(vm, ZenValue_equal(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_NEQ) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer != b.as.integer));
                } else if (a.type == ZEN_BOOLEAN && b.type == ZEN_BOOLEAN) {
                    push(vm, ZenValue_make_boolean(a.as.boolean != b.as.boolean));
                } else {
                    push(vm, ZenValue_not_equal(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_LT) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer < b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_boolean(a.as.decimal < b.as.decimal));
                } else {
                    push(vm, ZenValue_less_than(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_LTE) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer <= b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_boolean(a.as.decimal <= b.as.decimal));
                } else {
                    push(vm, ZenValue_less_than_or_equal(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_GT) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer > b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_boolean(a.as.decimal > b.as.decimal));
                } else {
                    push(vm, ZenValue_greater_than(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_GTE) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
                    push(vm, ZenValue_make_boolean(a.as.integer >= b.as.integer));
                } else if (a.type == ZEN_DECIMAL && b.type == ZEN_DECIMAL) {
                    push(vm, ZenValue_make_boolean(a.as.decimal >= b.as.decimal));
                } else {
                    push(vm, ZenValue_greater_than_or_equal(a, b));
                }
                NEXT();
            }
            
            TARGET(OP_MAKE_LIST) {
                uint16_t count = READ_U16(frame);
                ZenList* list = ZenList_new();
                ZenValue lval = ZenValue_from_list(list);
                ZenValue* start = vm->stack_top - count;
                for (int i = 0; i < count; i++) {
                    ZenList_append_value(lval, start[i]);
                }
                vm->stack_top = start;
                push(vm, lval);
                NEXT();
            }
            
            TARGET(OP_MAKE_MAP) {
                uint16_t count = READ_U16(frame);
                ZenMap* map = ZenMap_new();
                ZenValue mval = ZenValue_from_map(map);
                ZenValue* start = vm->stack_top - (count * 2);
                for (int i = 0; i < count * 2; i += 2) {
                    ZenMap_set_value_at_key(mval, start[i], start[i + 1]);
                }
                vm->stack_top = start;
                push(vm, mval);
                NEXT();
            }
            
            TARGET(OP_GET_INDEX) {
                ZenValue key = pop(vm);
                ZenValue target = pop(vm);
                if (target.type == ZEN_LIST && key.type == ZEN_INTEGER) {
                    push(vm, ZenList_get_value_at_index(target, key));
                } else if (target.type == ZEN_MAP) {
                    push(vm, ZenMap_get_value_at_key(target, key));
                } else {
                    push(vm, ZenValue_get_at(target, key));
                }
                NEXT();
            }
            
            TARGET(OP_SET_INDEX) {
                ZenValue val = pop(vm);
                ZenValue key = pop(vm);
                ZenValue target = pop(vm);
                if (target.type == ZEN_LIST && key.type == ZEN_INTEGER) {
                    ZenList_set_value_at_index(target, key, val);
                } else if (target.type == ZEN_MAP) {
                    ZenMap_set_value_at_key(target, key, val);
                } else {
                    ZenValue_set_at(target, key, val);
                }
                push(vm, val);
                NEXT();
            }
            
            TARGET(OP_GET_PROP) {
                ZenValue key = READ_CONST(frame);
                ZenValue target = pop(vm);
                if (target.type == ZEN_MAP) {
                    ZenValue val = ZenMap_get_value_at_key(target, key);
                    if (val.type == ZEN_NOTHING && key.type == ZEN_STRING && key.as.string) {
                        ZenValue is_ext = ZenMap_get_value_at_key(target, ZenValue_make_string("__is_extern_module"));
                        if (is_ext.type == ZEN_BOOLEAN && is_ext.as.boolean) {
                            ZenValue h_val = ZenMap_get_value_at_key(target, ZenValue_make_string("__handle"));
                            void* handle = (h_val.type == ZEN_OBJECT) ? h_val.as.object : NULL;
                            void* sym = ZenFFI_dlsym(handle, key.as.string);
                            if (sym) {
                                val = ZenFFI_make_callable(sym, key.as.string, NULL, -1);
                                ZenMap_set_value_at_key(target, key, val);
                            }
                        }
                    }
                    push(vm, val);
                } else if (key.type == ZEN_STRING && key.as.string) {
                    push(vm, ZenValue_get_field(target, key.as.string));
                } else {
                    push(vm, ZEN_NOTHING_VAL);
                }
                NEXT();
            }
            
            TARGET(OP_SET_PROP) {
                ZenValue key = READ_CONST(frame);
                ZenValue val = pop(vm);
                ZenValue target = pop(vm);
                if (target.type == ZEN_MAP) {
                    ZenMap_set_value_at_key(target, key, val);
                }
                push(vm, val);
                NEXT();
            }
            
            TARGET(OP_CAST) {
                ZenValue target_type = READ_CONST(frame);
                ZenValue val = pop(vm);
                const char* type_str = (target_type.type == ZEN_STRING && target_type.as.string) ? target_type.as.string : "";
                push(vm, ZenValue_cast(val, type_str));
                NEXT();
            }
            
            TARGET(OP_RANGE_EXCL) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_range_exclusive_end(a, b));
                NEXT();
            }
            
            TARGET(OP_RANGE_INCL) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_range_full_inclusive(a, b));
                NEXT();
            }
            
            TARGET(OP_CONCAT_APPEND) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_op_append(a, b));
                NEXT();
            }
            
            TARGET(OP_DROP) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_op_remove(a, b));
                NEXT();
            }
            
            TARGET(OP_CHECK_UNWRAP) {
                ZenValue top = pop(vm);
                if (top.type == ZEN_ERROR) {
                    push(vm, ZEN_NOTHING_VAL);
                } else {
                    push(vm, top);
                }
                NEXT();
            }
            
            TARGET(OP_RANGE_INCL_END) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_range_open_start_inclusive(a, b));
                NEXT();
            }
            
            TARGET(OP_RANGE_BETWEEN) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_range_between(a, b));
                NEXT();
            }
            
            TARGET(OP_IN) {
                ZenValue container = pop(vm);
                ZenValue elem = pop(vm);
                push(vm, ZenValue_in(elem, container));
                NEXT();
            }
            
            TARGET(OP_COALESCE) {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_coalesce(a, b));
                NEXT();
            }
            
            TARGET(OP_SLICE) {
                ZenValue step = pop(vm);
                ZenValue end = pop(vm);
                ZenValue start = pop(vm);
                ZenValue obj = pop(vm);
                push(vm, ZenValue_slice(obj, start, end, step));
                NEXT();
            }
            
            TARGET(OP_JUMP) {
                int16_t offset = READ_I16(frame);
                frame->ip += offset;
                NEXT();
            }
            
            TARGET(OP_JUMP_IF_FALSE) {
                int16_t offset = READ_I16(frame);
                if (!is_truthy(peek(vm, 0))) {
                    frame->ip += offset;
                }
                NEXT();
            }
            
            TARGET(OP_JUMP_IF_TRUE) {
                int16_t offset = READ_I16(frame);
                if (is_truthy(peek(vm, 0))) {
                    frame->ip += offset;
                }
                NEXT();
            }
            
            TARGET(OP_POP_JUMP_IF_FALSE) {
                int16_t offset = READ_I16(frame);
                ZenValue val = pop(vm);
                if (!is_truthy(val)) {
                    frame->ip += offset;
                }
                NEXT();
            }
            
            TARGET(OP_CALL) {
                uint8_t argc = (uint8_t)READ_U16(frame);
                ZenValue callee = peek(vm, argc);
                
                // 1. If callee is a ZenChunk / bytecode function
                if (callee.type == ZEN_OBJECT && callee.as.object != NULL) {
                    ZenChunk* callee_chunk = (ZenChunk*)callee.as.object;
                    if (vm->frame_count >= ZEN_VM_MAX_FRAMES) {
                        fprintf(stderr, "VM Error: Stack overflow (max call frames %d)\n", ZEN_VM_MAX_FRAMES);
                        return ZEN_NOTHING_VAL;
                    }
                    ZenCallFrame* next_frame = &vm->frames[vm->frame_count++];
                    next_frame->chunk = callee_chunk;
                    next_frame->ip = callee_chunk->code;
                    next_frame->slots = vm->stack_top - argc;
                    next_frame->argc = argc;
                    
                    // Allocate additional locals
                    for (int i = argc; i < callee_chunk->num_locals; i++) {
                        push(vm, ZEN_NOTHING_VAL);
                    }
                    frame = next_frame;
                } else if (callee.type == ZEN_FUNCTION) {
                    // 2. Native C function or closure
                    ZenValue args[ZEN_MAX_APPLY_ARGS];
                    int n = argc < ZEN_MAX_APPLY_ARGS ? argc : ZEN_MAX_APPLY_ARGS;
                    for (int i = 0; i < n; i++) {
                        args[i] = vm->stack_top[-argc + i];
                    }
                    ZenValue res = ZEN_NOTHING_VAL;
                    if (callee.as.object != NULL) {
                        ZenClosureData* c = (ZenClosureData*)callee.as.object;
                        ZenValue all[ZEN_MAX_APPLY_ARGS];
                        int n_caps = c->n_caps;
                        if (n_caps < 0) n_caps = 0;
                        if (n_caps > ZEN_MAX_CAPTURES) n_caps = ZEN_MAX_CAPTURES;
                        for (int i = 0; i < n_caps; i++) {
                            all[i] = c->caps[i];
                        }
                        int n_user = n;
                        if (n_caps + n_user > ZEN_MAX_APPLY_ARGS) {
                            n_user = ZEN_MAX_APPLY_ARGS - n_caps;
                        }
                        for (int i = 0; i < n_user; i++) {
                            all[n_caps + i] = args[i];
                        }
                        res = zen_invoke_native_fn(c->fn, n_caps + n_user, all);
                    } else if (callee.as.func != NULL) {
                        res = zen_invoke_native_fn((void*)callee.as.func, n, args);
                    }
                    for (int i = 0; i < argc; i++) {
                        ZenValue_release(vm->stack_top[-argc + i]);
                    }
                    ZenValue_release(callee);
                    vm->stack_top -= (argc + 1);
                    push(vm, res);
                } else {
                    fprintf(stderr, "VM Error: Callee is not callable (type %d)\n", callee.type);
                    for (int i = 0; i < argc; i++) {
                        ZenValue_release(vm->stack_top[-argc + i]);
                    }
                    ZenValue_release(callee);
                    vm->stack_top -= (argc + 1);
                    push(vm, ZEN_NOTHING_VAL);
                }
                NEXT();
            }
            
            TARGET(OP_RETURN) {
                ZenValue result = pop(vm);
                
                // 1. Release locally allocated function variables & temporaries
                // Boundary: (argc .. stack_top - 1)
                for (ZenValue* slot = frame->slots + frame->argc; slot < vm->stack_top; slot++) {
                    ZenValue_release(*slot);
                }
                
                // 2. Cleanly release the call arguments pushed by the caller
                // Boundary: (0 .. argc - 1)
                for (int i = 0; i < frame->argc; i++) {
                    ZenValue_release(frame->slots[i]);
                }
                
                // 3. For inner frames, release the callee closure (residing at frame->slots - 1)
                if (vm->frame_count > 1) {
                    ZenValue_release(*(frame->slots - 1));
                    vm->stack_top = frame->slots - 1; /* Discard frame & callee */
                } else {
                    vm->stack_top = frame->slots;
                }
                
                vm->frame_count--;
                if (vm->frame_count == 0) {
                    return result; // Program execution finished
                }
                
                push(vm, result);
                frame = &vm->frames[vm->frame_count - 1];
                NEXT();
            }

            TARGET(OP_MAKE_CLOSURE) {
                uint16_t proto_idx = READ_U16(frame);
                uint8_t n_caps = READ_BYTE(frame);
                ZenValue proto_val = frame->chunk->constants[proto_idx];
                ZenChunk* proto_chunk = (ZenChunk*)proto_val.as.object;
                ZenClosureData* c = (ZenClosureData*)calloc(1, sizeof(ZenClosureData));
                if (!c) {
                    push(vm, ZEN_NOTHING_VAL);
                } else {
                    ZenHeapHeader_init(&c->header, ZEN_FUNCTION, ZEN_FLAG_CONTAINER);
                    c->fn = (void*)proto_chunk;
                    c->n_caps = n_caps;
                    c->arity = proto_chunk ? proto_chunk->num_locals : 0;
                    for (int i = n_caps - 1; i >= 0; i--) {
                        c->caps[i] = pop(vm);
                    }
                    ZenValue z;
                    z.type = ZEN_FUNCTION;
                    z.as.object = c;
                    push(vm, z);
                }
                NEXT();
            }
            
            TARGET(OP_PRINT) {
                uint8_t argc = (uint8_t)READ_U16(frame);
                for (int i = argc - 1; i >= 0; i--) {
                    ZenValue val = pop(vm);
                    if (val.type == ZEN_STRING) printf("%s", val.as.string);
                    else if (val.type == ZEN_INTEGER) printf("%lld", val.as.integer);
                    else if (val.type == ZEN_DECIMAL) printf("%g", val.as.decimal);
                    else if (val.type == ZEN_BOOLEAN) printf("%s", val.as.boolean ? "True" : "False");
                    else if (val.type == ZEN_NOTHING) printf("Nothing");
                    else if (val.type == ZEN_DEFAULT) printf("Default");
                    else printf("[object %p]", val.as.object);
                    if (i > 0) printf(" ");
                }
                printf("\n");
                push(vm, ZEN_NOTHING_VAL);
                NEXT();
            }
            
            TARGET(OP_HALT)
                return pop(vm);
                
#if ZEN_VM_DIRECT_THREADED
        do_OP_UNKNOWN:
            fprintf(stderr, "VM Error: Unknown opcode at %s:%d\n",
                    frame->chunk->name, (int)(frame->ip - frame->chunk->code - 1));
            return ZEN_NOTHING_VAL;
#else
            default:
                fprintf(stderr, "VM Error: Unknown opcode 0x%02X at %s:%d\n",
                        instruction, frame->chunk->name, (int)(frame->ip - frame->chunk->code - 1));
                return ZEN_NOTHING_VAL;
        }
    }
#endif
}

/* Mixed Execution ABI & Embed API (Phase 4) */

void ZenVM_register_global(ZenVM* vm, const char* name, ZenValue val) {
    if (!vm || !name) return;
    if (!vm->globals) {
        vm->globals = ZenMap_new();
    }
    ZenMap_set_value_at_key(ZenValue_from_map(vm->globals), ZenValue_make_string(name), val);
}

void ZenVM_register_native_func(ZenVM* vm, const char* name, void* fn) {
    if (!vm || !name || !fn) return;
    ZenValue fn_val = ZenValue_from_closure(fn, -1, 0);
    ZenVM_register_global(vm, name, fn_val);
}

ZenValue ZenVM_load_native_module(ZenVM* vm, const char* path) {
    if (!vm || !path) return ZEN_NOTHING_VAL;
    void* handle = dlopen(path, RTLD_LAZY | RTLD_GLOBAL);
    if (!handle) {
        fprintf(stderr, "VM Error: dlopen failed for %s: %s\n", path, dlerror());
        return ZEN_NOTHING_VAL;
    }
    
    // Look for standard Zen module init symbols
    typedef ZenValue (*ZenModInitFn)(void);
    ZenModInitFn init_fn = (ZenModInitFn)dlsym(handle, "zen_module_init");
    if (!init_fn) {
        init_fn = (ZenModInitFn)dlsym(handle, "zen_init_module");
    }
    if (!init_fn) {
        char sym_buf[256];
        const char* base = strrchr(path, '/');
        base = base ? base + 1 : path;
        char mod_name[128] = {0};
        strncpy(mod_name, base, sizeof(mod_name) - 1);
        char* dot = strrchr(mod_name, '.');
        if (dot) *dot = '\0';
        snprintf(sym_buf, sizeof(sym_buf), "zen_mod_init_%s", mod_name);
        init_fn = (ZenModInitFn)dlsym(handle, sym_buf);
    }
    
    if (!init_fn) {
        fprintf(stderr, "VM Error: No module init symbol found in %s\n", path);
        return ZEN_NOTHING_VAL;
    }
    
    ZenValue mod_exports = init_fn();
    return mod_exports;
}

ZenValue ZenVM_call_named(ZenVM* vm, const char* func_name, int argc, ZenValue* args) {
    if (!vm || !func_name) return ZEN_NOTHING_VAL;
    if (!vm->globals) return ZEN_NOTHING_VAL;
    ZenValue fn = ZenMap_get_value_at_key(ZenValue_from_map(vm->globals), ZenValue_make_string(func_name));
    if (fn.type == ZEN_NOTHING) {
        fprintf(stderr, "VM Error: Global function '%s' not found\n", func_name);
        return ZEN_NOTHING_VAL;
    }
    
    if (fn.type == ZEN_OBJECT && fn.as.object != NULL) {
        // Push callee and arguments for VM chunk call
        push(vm, fn);
        for (int i = 0; i < argc; i++) {
            push(vm, args[i]);
        }
        ZenChunk* chunk = (ZenChunk*)fn.as.object;
        return ZenVM_run_chunk(vm, chunk);
    } else if (fn.type == ZEN_FUNCTION) {
        if (fn.as.object != NULL) {
            ZenClosureData* c = (ZenClosureData*)fn.as.object;
            ZenValue all[ZEN_MAX_APPLY_ARGS];
            int n_caps = c->n_caps;
            if (n_caps < 0) n_caps = 0;
            if (n_caps > ZEN_MAX_CAPTURES) n_caps = ZEN_MAX_CAPTURES;
            for (int i = 0; i < n_caps; i++) {
                all[i] = c->caps[i];
            }
            int n_user = argc < ZEN_MAX_APPLY_ARGS - n_caps ? argc : ZEN_MAX_APPLY_ARGS - n_caps;
            for (int i = 0; i < n_user; i++) {
                all[n_caps + i] = args[i];
            }
            return zen_invoke_native_fn(c->fn, n_caps + n_user, all);
        } else if (fn.as.func != NULL) {
            return zen_invoke_native_fn((void*)fn.as.func, argc, args);
        }
    }
    
    return ZEN_NOTHING_VAL;
}

/* --- Bytecode Binary Serialization & Packaging (.zbc) --- */

#define ZEN_BYTECODE_MAGIC 0x424E455A /* 'Z' 'E' 'N' 'B' in little endian */
#define ZEN_BYTECODE_VERSION 1

int ZenChunk_save_file(ZenChunk* chunk, const char* path, uint64_t src_hash) {
    if (!chunk || !path) return 0;
    FILE* fp = fopen(path, "wb");
    if (!fp) return 0;

    uint32_t magic = ZEN_BYTECODE_MAGIC;
    uint16_t version = ZEN_BYTECODE_VERSION;
    fwrite(&magic, sizeof(uint32_t), 1, fp);
    fwrite(&version, sizeof(uint16_t), 1, fp);
    fwrite(&src_hash, sizeof(uint64_t), 1, fp);

    uint16_t num_locals = (uint16_t)chunk->num_locals;
    uint16_t const_count = (uint16_t)chunk->const_count;
    fwrite(&num_locals, sizeof(uint16_t), 1, fp);
    fwrite(&const_count, sizeof(uint16_t), 1, fp);

    // Write Constants Pool
    for (int i = 0; i < chunk->const_count; i++) {
        ZenValue cv = chunk->constants[i];
        uint8_t tag = (uint8_t)cv.type;
        fwrite(&tag, sizeof(uint8_t), 1, fp);
        switch (cv.type) {
            case ZEN_BOOLEAN: {
                uint8_t b = cv.as.boolean ? 1 : 0;
                fwrite(&b, sizeof(uint8_t), 1, fp);
                break;
            }
            case ZEN_INTEGER: {
                int64_t iv = (int64_t)cv.as.integer;
                fwrite(&iv, sizeof(int64_t), 1, fp);
                break;
            }
            case ZEN_DECIMAL: {
                double dv = cv.as.decimal;
                fwrite(&dv, sizeof(double), 1, fp);
                break;
            }
            case ZEN_STRING: {
                const char* str = cv.as.string ? cv.as.string : "";
                uint16_t slen = (uint16_t)strlen(str);
                fwrite(&slen, sizeof(uint16_t), 1, fp);
                if (slen > 0) fwrite(str, 1, slen, fp);
                break;
            }
            default:
                break;
        }
    }

    // Write Code
    uint32_t code_count = (uint32_t)chunk->count;
    fwrite(&code_count, sizeof(uint32_t), 1, fp);
    if (code_count > 0) {
        fwrite(chunk->code, sizeof(uint8_t), code_count, fp);
    }

    // Write Debug Lines
    if (code_count > 0 && chunk->lines) {
        for (uint32_t i = 0; i < code_count; i++) {
            int32_t line = (int32_t)chunk->lines[i];
            fwrite(&line, sizeof(int32_t), 1, fp);
        }
    }

    // Write Chunk Name
    const char* cname = chunk->name ? chunk->name : "<script>";
    uint16_t nlen = (uint16_t)strlen(cname);
    fwrite(&nlen, sizeof(uint16_t), 1, fp);
    if (nlen > 0) fwrite(cname, 1, nlen, fp);

    fclose(fp);
    return 1;
}

static char* zen_unescape_str(const char* s) {
    if (!s) return strdup("");
    size_t len = strlen(s);
    char* out = (char*)malloc(len + 1);
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (s[i] == '\\' && i + 1 < len) {
            i++;
            if (s[i] == 'n') out[j++] = '\n';
            else if (s[i] == 't') out[j++] = '\t';
            else if (s[i] == 'r') out[j++] = '\r';
            else if (s[i] == '\\') out[j++] = '\\';
            else out[j++] = s[i];
        } else {
            out[j++] = s[i];
        }
    }
    out[j] = '\0';
    return out;
}

static ZenChunk* zen_chunk_from_text(char* text, uint64_t* out_src_hash) {
    if (!text) return NULL;
    char* saveptr = NULL;
    char* line = strtok_r(text, "\r\n", &saveptr);
    if (!line || strncmp(line, "ZENB:", 5) != 0) return NULL;

    // Line 0: ZENB:1:<src_hash>:<num_locals>:<name>
    char* p = line + 5;
    char* colon1 = strchr(p, ':'); // after version
    if (!colon1) return NULL;
    char* colon2 = strchr(colon1 + 1, ':'); // after src_hash
    if (!colon2) return NULL;
    char* colon3 = strchr(colon2 + 1, ':'); // after num_locals
    if (!colon3) return NULL;

    uint64_t src_hash = (uint64_t)strtoull(colon1 + 1, NULL, 10);
    if (out_src_hash) *out_src_hash = src_hash;
    int num_locals = atoi(colon2 + 1);
    char* cname = colon3 + 1;

    ZenChunk* chunk = ZenChunk_new(cname);
    chunk->num_locals = (uint16_t)num_locals;

    // Next line: CONSTANTS:<count>
    line = strtok_r(NULL, "\r\n", &saveptr);
    if (!line || strncmp(line, "CONSTANTS:", 10) != 0) {
        ZenChunk_free(chunk);
        return NULL;
    }
    int const_count = atoi(line + 10);

    for (int i = 0; i < const_count; i++) {
        line = strtok_r(NULL, "\r\n", &saveptr);
        if (!line) {
            ZenChunk_free(chunk);
            return NULL;
        }
        if (line[0] == 'N') {
            ZenChunk_add_constant(chunk, ZEN_NOTHING_VAL);
        } else if (line[0] == 'D') {
            ZenChunk_add_constant(chunk, ZEN_DEFAULT_VAL);
        } else if (line[0] == 'B') {
            int b = atoi(line + 2);
            ZenChunk_add_constant(chunk, ZenValue_make_boolean(b != 0));
        } else if (line[0] == 'I') {
            int64_t iv = (int64_t)atoll(line + 2);
            ZenChunk_add_constant(chunk, ZenValue_make_integer(iv));
        } else if (line[0] == 'S') {
            char* unesc = zen_unescape_str(line + 2);
            ZenChunk_add_constant(chunk, ZenValue_make_string(unesc));
            free(unesc);
        } else if (line[0] == 'F') {
            char* sub_raw = zen_unescape_str(line + 2);
            ZenChunk* sub_chunk = zen_chunk_from_text(sub_raw, NULL);
            free(sub_raw);
            ZenValue f_val;
            f_val.type = ZEN_FUNCTION;
            f_val.as.object = sub_chunk;
            ZenChunk_add_constant(chunk, f_val);
        } else {
            ZenChunk_add_constant(chunk, ZEN_NOTHING_VAL);
        }
    }

    // Next line: CODE:<len>
    line = strtok_r(NULL, "\r\n", &saveptr);
    if (!line || strncmp(line, "CODE:", 5) != 0) {
        ZenChunk_free(chunk);
        return NULL;
    }
    int code_len = atoi(line + 5);

    if (code_len > 0) {
        line = strtok_r(NULL, "\r\n", &saveptr);
        if (!line) {
            ZenChunk_free(chunk);
            return NULL;
        }
        char* byte_saveptr = NULL;
        char* byte_tok = strtok_r(line, ",", &byte_saveptr);
        while (byte_tok) {
            uint8_t b = (uint8_t)atoi(byte_tok);
            ZenChunk_emit_byte(chunk, b, 0);
            byte_tok = strtok_r(NULL, ",", &byte_saveptr);
        }
    }

    // Next line: LINES:<len>
    line = strtok_r(NULL, "\r\n", &saveptr);
    if (line && strncmp(line, "LINES:", 6) == 0) {
        int lines_len = atoi(line + 6);
        if (lines_len > 0) {
            line = strtok_r(NULL, "\r\n", &saveptr);
            if (line) {
                char* line_saveptr = NULL;
                char* line_tok = strtok_r(line, ",", &line_saveptr);
                int lidx = 0;
                while (line_tok && lidx < chunk->count) {
                    chunk->lines[lidx++] = atoi(line_tok);
                    line_tok = strtok_r(NULL, ",", &line_saveptr);
                }
            }
        }
    }

    return chunk;
}

ZenChunk* ZenChunk_load_file(const char* path, uint64_t* out_src_hash) {
    if (!path) return NULL;
    FILE* fp = fopen(path, "rb");
    if (!fp) return NULL;

    char header_prefix[6] = {0};
    if (fread(header_prefix, 1, 5, fp) == 5 && memcmp(header_prefix, "ZENB:", 5) == 0) {
        fseek(fp, 0, SEEK_END);
        long sz = ftell(fp);
        fseek(fp, 0, SEEK_SET);
        char* buf = (char*)malloc(sz + 1);
        if (!buf) {
            fclose(fp);
            return NULL;
        }
        size_t nread = fread(buf, 1, sz, fp);
        buf[nread] = '\0';
        fclose(fp);
        ZenChunk* chunk = zen_chunk_from_text(buf, out_src_hash);
        free(buf);
        return chunk;
    }

    // Binary format
    fseek(fp, 0, SEEK_SET);
    uint32_t magic = 0;
    uint16_t version = 0;
    if (fread(&magic, sizeof(uint32_t), 1, fp) != 1 || magic != ZEN_BYTECODE_MAGIC) {
        fclose(fp);
        return NULL;
    }
    if (fread(&version, sizeof(uint16_t), 1, fp) != 1 || version != ZEN_BYTECODE_VERSION) {
        fclose(fp);
        return NULL;
    }
    uint64_t src_hash = 0;
    if (fread(&src_hash, sizeof(uint64_t), 1, fp) != 1) {
        fclose(fp);
        return NULL;
    }
    if (out_src_hash) *out_src_hash = src_hash;

    uint16_t num_locals = 0;
    uint16_t const_count = 0;
    if (fread(&num_locals, sizeof(uint16_t), 1, fp) != 1 ||
        fread(&const_count, sizeof(uint16_t), 1, fp) != 1) {
        fclose(fp);
        return NULL;
    }

    ZenChunk* chunk = ZenChunk_new(NULL);
    chunk->num_locals = num_locals;

    // Read Constants Pool
    for (int i = 0; i < const_count; i++) {
        uint8_t tag = 0;
        if (fread(&tag, sizeof(uint8_t), 1, fp) != 1) {
            ZenChunk_free(chunk);
            fclose(fp);
            return NULL;
        }
        ZenValue cv = ZEN_NOTHING_VAL;
        switch (tag) {
            case ZEN_NOTHING:
                cv = ZEN_NOTHING_VAL;
                break;
            case ZEN_BOOLEAN: {
                uint8_t b = 0;
                if (fread(&b, sizeof(uint8_t), 1, fp) == 1) {
                    cv = ZenValue_make_boolean(b != 0);
                }
                break;
            }
            case ZEN_INTEGER: {
                int64_t iv = 0;
                if (fread(&iv, sizeof(int64_t), 1, fp) == 1) {
                    cv = ZenValue_make_integer(iv);
                }
                break;
            }
            case ZEN_DECIMAL: {
                double dv = 0.0;
                if (fread(&dv, sizeof(double), 1, fp) == 1) {
                    cv = ZenValue_make_decimal(dv);
                }
                break;
            }
            case ZEN_STRING: {
                uint16_t slen = 0;
                if (fread(&slen, sizeof(uint16_t), 1, fp) == 1) {
                    char* str_buf = (char*)malloc(slen + 1);
                    if (slen > 0) {
                        size_t read_bytes = fread(str_buf, 1, slen, fp);
                        (void)read_bytes;
                    }
                    str_buf[slen] = '\0';
                    cv = ZenValue_make_string(str_buf);
                    free(str_buf);
                }
                break;
            }
            default:
                cv = ZEN_NOTHING_VAL;
                break;
        }
        ZenChunk_add_constant(chunk, cv);
    }

    // Read Code
    uint32_t code_count = 0;
    if (fread(&code_count, sizeof(uint32_t), 1, fp) != 1) {
        ZenChunk_free(chunk);
        fclose(fp);
        return NULL;
    }
    for (uint32_t i = 0; i < code_count; i++) {
        uint8_t byte = 0;
        if (fread(&byte, sizeof(uint8_t), 1, fp) == 1) {
            ZenChunk_emit_byte(chunk, byte, 0);
        }
    }

    // Read Debug Lines
    for (uint32_t i = 0; i < code_count; i++) {
        int32_t line = 0;
        if (fread(&line, sizeof(int32_t), 1, fp) == 1) {
            chunk->lines[i] = (int)line;
        }
    }

    // Read Chunk Name
    uint16_t nlen = 0;
    if (fread(&nlen, sizeof(uint16_t), 1, fp) == 1) {
        char* name_buf = (char*)malloc(nlen + 1);
        if (nlen > 0) {
            size_t read_bytes = fread(name_buf, 1, nlen, fp);
            (void)read_bytes;
        }
        name_buf[nlen] = '\0';
        if (chunk->name) free(chunk->name);
        chunk->name = name_buf;
    }

    fclose(fp);
    return chunk;
}

ZenValue ZenVM_run_bytecode_file(ZenVM* vm, const char* path) {
    if (!path) return ZEN_NOTHING_VAL;
    ZenChunk* chunk = ZenChunk_load_file(path, NULL);
    if (!chunk) {
        fprintf(stderr, "VM Error: Failed to load bytecode file: %s\n", path);
        return ZEN_NOTHING_VAL;
    }
    bool free_vm = false;
    if (!vm) {
        vm = ZenVM_new();
        free_vm = true;
    }
    ZenValue result = ZenVM_run_chunk(vm, chunk);
    ZenChunk_free(chunk);
    if (free_vm) {
        ZenVM_free(vm);
    }
    return result;
}

