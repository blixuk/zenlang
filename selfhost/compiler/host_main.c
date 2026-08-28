#include "bootstrap_runtime.h"
#include "Token.h"
#include "Lexer.h"
#include "Parser.h"
#include "AST.h"
#include "CTranspiler.h"
#include "Resolver.h"
#include "DependencyGraph.h"

// The transpiled src/zen.zl exposes zen_main as the entry
extern ZenValue zen_main();

int main(int argc, char** argv) {
    // Initialize runtime with command line arguments (use the symbol provided by the runtime)
    ZenSystem_initialize_arguments(argc, argv);
    
    // Call the transpiled Zen self-host entry point
    zen_main();
    
    return 0;
}
