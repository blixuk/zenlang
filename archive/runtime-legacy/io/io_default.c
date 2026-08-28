#include "zen_io.h"
#include <stdio.h>
#include "../memory/zen_allocator.h"
#include <unistd.h>
#include <dirent.h>
#include <string.h>
void IO_write(ZenString value) {
    if (value) printf("%s", value);
}

void zl_write(ZenString value) {
    IO_write(value);
}

void out_write(ZenString value, void* data) {
    IO_write(value);
}

void IO_write_int(long long value) {
    printf("%lld", value);
}

void IO_error(ZenString value) {
    if (value) fprintf(stderr, "%s", value);
}

ZenString IO_read_file(ZenString path) {
    FILE* f = fopen(path, "rb");
    if (!f) return NULL;
    
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    char* string = (char*)zen_alloc(fsize + 1);
    fread(string, fsize, 1, f);
    fclose(f);
    
    string[fsize] = 0;
    return string;
}

void IO_write_file(ZenString path, ZenString content) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    if (content) fputs(content, f);
    fclose(f);
}

long long IO_file_exists(ZenString path) {
    if (access(path, F_OK) != -1) return 1;
    return 0;
}

ZenList* ZenIO_list_dir(ZenString path) {
    ZenList* list = ZenList_create();
    DIR* d;
    struct dirent* dir;
    d = opendir(path);
    if (d) {
        while ((dir = readdir(d)) != NULL) {
            if (strcmp(dir->d_name, ".") != 0 && strcmp(dir->d_name, "..") != 0) {
                ZenString element = ZenString_create(dir->d_name);
                ZenList_append(list, zen_str(element));
            }
        }
        closedir(d);
    }
    return list;
}
