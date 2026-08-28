#ifndef ZEN_IO_H
#define ZEN_IO_H

#include "../object/zen_object.h"

void IO_write(ZenString value);
void zl_write(ZenString value);
void out_write(ZenString value, void* data);
void IO_write_int(long long value);
void IO_error(ZenString value);
ZenString IO_read_file(ZenString path);
void IO_write_file(ZenString path, ZenString content);
long long IO_file_exists(ZenString path);
ZenList* ZenIO_list_dir(ZenString path);

#endif
