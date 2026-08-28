#ifndef ZEN_IO_H
#define ZEN_IO_H

#include <stdio.h>
#include "../core/zen_value.h"

// Internal Print helpers
void ZenIO_internal_print_begin(void);
void ZenIO_internal_print_separator(void);
void ZenIO_internal_print_end(void);
void ZenIO_internal_print_value(ZenValue value);
void ZenIO_internal_print_integer(long long value);
void ZenIO_internal_print_decimal(double value);
void ZenIO_internal_print_string(const char* value);
void ZenIO_internal_print_boolean(bool value);

// Built-in objects
extern ZenValue __builtin_output;
extern ZenValue __builtin_input;
extern ZenValue __builtin_file;
extern ZenValue __builtin_sys;
extern ZenValue __builtin_string;
extern ZenValue __builtin_math;
extern ZenValue __builtin_list;
extern ZenValue __builtin_map;
extern ZenValue __builtin_set;
extern ZenValue __builtin_range;
extern ZenValue __builtin_time;
extern ZenValue __builtin_term;

// Zenlang IO API
ZenValue ZenIO_write_value(ZenValue value);
ZenValue ZenIO_write_line(ZenValue value);
ZenValue ZenIO_read_value(ZenValue prompt);
ZenValue ZenIO_write_info(ZenValue value);
ZenValue ZenIO_write_warning(ZenValue value);
ZenValue ZenIO_write_debug(ZenValue value);
ZenValue ZenIO_write_error(ZenValue value);
ZenValue ZenIO_flush(void);

// File IO
ZenValue ZenIO_file_exists(ZenValue path);
ZenValue ZenIO_read_file(ZenValue path);
ZenValue ZenIO_write_file(ZenValue path, ZenValue content);
ZenValue ZenIO_list_dir(ZenValue path);
ZenValue ZenIO_append(ZenValue path, ZenValue content);
ZenValue ZenIO_write_bytes(ZenValue path, ZenValue bytes);
ZenValue ZenIO_remove(ZenValue path);
ZenValue ZenIO_is_file(ZenValue path);
ZenValue ZenIO_is_dir(ZenValue path);
ZenValue ZenIO_open(ZenValue path, ZenValue mode);

// Open file handle methods (generated code may pass ZenObject* or ZenValue)
ZenValue ZenObject_read(void* self);
ZenValue ZenObject_write(void* self, ZenValue content);
ZenValue ZenObject_close(void* self);

#endif // ZEN_IO_H
