#include "zen_sys.h"

extern long long zen_entry();

int main(int argc, char** argv) {
    zen_argc = argc;
    zen_argv = argv;
    return (int)zen_entry();
}
