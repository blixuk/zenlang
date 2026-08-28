#ifndef ZEN_SYS_H
#define ZEN_SYS_H

#include <zen_object.h>

ZenList* Sys_get_args();
ZenString Sys_get_env(ZenString key);
void Sys_exit(long long code);
long long ZenSys_exec(ZenString cmd);
ZenString Sys_get_cwd();


// Globals to be set by the real main
extern int zen_argc;
extern char** zen_argv;

#endif
