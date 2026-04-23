#include "bootstrap_runtime.h"
#include "compiler/Token.h" // Needed for some types if used
#include "zen.h"    // Zenlang main (zen_main)

extern ZenValue zen_main();

int main(int argc, char** argv) {
    // Initialize runtime with command line arguments
    _Sys_init_args(argc, argv);
    
    // Call Zenlang main (which is now zen_main)
    zen_main();
    
    // Cleanup/Shutdown if needed
    // zen_runtime_shutdown();
    
    return 0;
}
