#include "zen_vm.h"
#include "zen_ops.h"
#include "zen_closure.h"
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
    if (chunk->constants) free(chunk->constants);
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
    ZenVM_reset(vm);
    return vm;
}

void ZenVM_free(ZenVM* vm) {
    if (!vm) return;
    free(vm);
}

void ZenVM_reset(ZenVM* vm) {
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

ZenValue ZenVM_run_chunk(ZenVM* vm, ZenChunk* chunk) {
    if (!vm || !chunk) return ZEN_NOTHING_VAL;

    ZenCallFrame* frame = &vm->frames[vm->frame_count++];
    frame->chunk = chunk;
    frame->ip = chunk->code;
    frame->slots = vm->stack_top;

    // Reserve slots for locals
    for (int i = 0; i < chunk->num_locals; i++) {
        push(vm, ZEN_NOTHING_VAL);
    }

    while (1) {
        uint8_t instruction = READ_BYTE(frame);
        switch (instruction) {
            case OP_NOP:
                break;
                
            case OP_CONST: {
                ZenValue constant = READ_CONST(frame);
                push(vm, constant);
                break;
            }
            
            case OP_NOTHING:
                push(vm, ZEN_NOTHING_VAL);
                break;
                
            case OP_DEFAULT: {
                uint16_t type_id = READ_U16(frame);
                switch (type_id) {
                    case ZEN_INTEGER: push(vm, ZenValue_make_integer(0)); break;
                    case ZEN_DECIMAL: push(vm, ZenValue_make_decimal(0.0)); break;
                    case ZEN_BOOLEAN: push(vm, ZenValue_make_boolean(false)); break;
                    case ZEN_STRING: push(vm, ZenValue_make_string("")); break;
                    case ZEN_LIST: push(vm, ZenValue_from_list(ZenList_new())); break;
                    case ZEN_MAP: push(vm, ZenValue_from_map(ZenMap_new())); break;
                    default: push(vm, ZEN_NOTHING_VAL); break;
                }
                break;
            }
            
            case OP_TRUE:
                push(vm, ZenValue_make_boolean(true));
                break;
                
            case OP_FALSE:
                push(vm, ZenValue_make_boolean(false));
                break;
                
            case OP_INT_SMALL: {
                int16_t val = READ_I16(frame);
                push(vm, ZenValue_make_integer(val));
                break;
            }
            
            case OP_POP:
                pop(vm);
                break;
                
            case OP_DUP:
                push(vm, peek(vm, 0));
                break;
                
            case OP_SWAP: {
                ZenValue a = pop(vm);
                ZenValue b = pop(vm);
                push(vm, a);
                push(vm, b);
                break;
            }
            
            case OP_LOAD_LOCAL: {
                uint16_t slot = READ_U16(frame);
                push(vm, frame->slots[slot]);
                break;
            }
            
            case OP_STORE_LOCAL: {
                uint16_t slot = READ_U16(frame);
                frame->slots[slot] = pop(vm);
                break;
            }
            
            case OP_LOAD_GLOBAL: {
                ZenValue name = READ_CONST(frame);
                ZenValue val = ZenMap_get_value_at_key(ZenValue_from_map(vm->globals), name);
                push(vm, val);
                break;
            }
            
            case OP_STORE_GLOBAL: {
                ZenValue name = READ_CONST(frame);
                ZenValue val = pop(vm);
                ZenMap_set_value_at_key(ZenValue_from_map(vm->globals), name, val);
                break;
            }
            
            case OP_ADD: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_add(a, b));
                break;
            }
            
            case OP_SUB: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_subtract(a, b));
                break;
            }
            
            case OP_MUL: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_multiply(a, b));
                break;
            }
            
            case OP_DIV: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_divide(a, b));
                break;
            }
            
            case OP_MOD: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_modulo(a, b));
                break;
            }
            
            case OP_NEG: {
                ZenValue a = pop(vm);
                push(vm, ZenValue_negate(a));
                break;
            }
            
            case OP_NOT: {
                ZenValue a = pop(vm);
                push(vm, ZenValue_not(a));
                break;
            }
            
            case OP_EQ: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_equal(a, b));
                break;
            }
            
            case OP_NEQ: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_not_equal(a, b));
                break;
            }
            
            case OP_LT: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_less_than(a, b));
                break;
            }
            
            case OP_LTE: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_less_than_or_equal(a, b));
                break;
            }
            
            case OP_GT: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_greater_than(a, b));
                break;
            }
            
            case OP_GTE: {
                ZenValue b = pop(vm);
                ZenValue a = pop(vm);
                push(vm, ZenValue_greater_than_or_equal(a, b));
                break;
            }
            
            case OP_MAKE_LIST: {
                uint16_t count = READ_U16(frame);
                ZenList* list = ZenList_new();
                ZenValue lval = ZenValue_from_list(list);
                // Stack contains items in push order: item0, item1, ...
                ZenValue* start = vm->stack_top - count;
                for (int i = 0; i < count; i++) {
                    ZenList_append_value(lval, start[i]);
                }
                vm->stack_top = start;
                push(vm, lval);
                break;
            }
            
            case OP_MAKE_MAP: {
                uint16_t count = READ_U16(frame);
                ZenMap* map = ZenMap_new();
                ZenValue mval = ZenValue_from_map(map);
                // Stack contains k0, v0, k1, v1, ...
                ZenValue* start = vm->stack_top - (count * 2);
                for (int i = 0; i < count * 2; i += 2) {
                    ZenMap_set_value_at_key(mval, start[i], start[i + 1]);
                }
                vm->stack_top = start;
                push(vm, mval);
                break;
            }
            
            case OP_GET_INDEX: {
                ZenValue key = pop(vm);
                ZenValue target = pop(vm);
                push(vm, ZenValue_get_at(target, key));
                break;
            }
            
            case OP_SET_INDEX: {
                ZenValue val = pop(vm);
                ZenValue key = pop(vm);
                ZenValue target = pop(vm);
                ZenValue_set_at(target, key, val);
                push(vm, val);
                break;
            }
            
            case OP_GET_PROP: {
                ZenValue key = READ_CONST(frame);
                ZenValue target = pop(vm);
                if (target.type == ZEN_MAP) {
                    push(vm, ZenMap_get_value_at_key(target, key));
                } else {
                    push(vm, ZEN_NOTHING_VAL);
                }
                break;
            }
            
            case OP_SET_PROP: {
                ZenValue key = READ_CONST(frame);
                ZenValue val = pop(vm);
                ZenValue target = pop(vm);
                if (target.type == ZEN_MAP) {
                    ZenMap_set_value_at_key(target, key, val);
                }
                push(vm, val);
                break;
            }
            
            case OP_JUMP: {
                int16_t offset = READ_I16(frame);
                frame->ip += offset;
                break;
            }
            
            case OP_JUMP_IF_FALSE: {
                int16_t offset = READ_I16(frame);
                if (!is_truthy(peek(vm, 0))) {
                    frame->ip += offset;
                }
                break;
            }
            
            case OP_JUMP_IF_TRUE: {
                int16_t offset = READ_I16(frame);
                if (is_truthy(peek(vm, 0))) {
                    frame->ip += offset;
                }
                break;
            }
            
            case OP_POP_JUMP_IF_FALSE: {
                int16_t offset = READ_I16(frame);
                ZenValue val = pop(vm);
                if (!is_truthy(val)) {
                    frame->ip += offset;
                }
                break;
            }
            
            case OP_CALL: {
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
                    vm->stack_top -= (argc + 1);
                    push(vm, res);
                } else {
                    fprintf(stderr, "VM Error: Callee is not callable (type %d)\n", callee.type);
                    vm->stack_top -= (argc + 1);
                    push(vm, ZEN_NOTHING_VAL);
                }
                break;
            }
            
            case OP_RETURN: {
                ZenValue result = pop(vm);
                vm->frame_count--;
                if (vm->frame_count == 0) {
                    return result;
                }
                vm->stack_top = frame->slots - 1; /* Discard frame & callee */
                push(vm, result);
                frame = &vm->frames[vm->frame_count - 1];
                break;
            }
            
            case OP_PRINT: {
                uint8_t argc = (uint8_t)READ_U16(frame);
                for (int i = argc - 1; i >= 0; i--) {
                    ZenValue val = pop(vm);
                    if (val.type == ZEN_STRING) printf("%s", val.as.string);
                    else if (val.type == ZEN_INTEGER) printf("%lld", val.as.integer);
                    else if (val.type == ZEN_DECIMAL) printf("%g", val.as.decimal);
                    else if (val.type == ZEN_BOOLEAN) printf("%s", val.as.boolean ? "True" : "False");
                    else if (val.type == ZEN_NOTHING) printf("Nothing");
                    else printf("[object %p]", val.as.object);
                    if (i > 0) printf(" ");
                }
                printf("\n");
                push(vm, ZEN_NOTHING_VAL);
                break;
            }
            
            case OP_HALT:
                return pop(vm);
                
            default:
                fprintf(stderr, "VM Error: Unknown opcode 0x%02X at %s:%d\n",
                        instruction, frame->chunk->name, (int)(frame->ip - frame->chunk->code - 1));
                return ZEN_NOTHING_VAL;
        }
    }
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
