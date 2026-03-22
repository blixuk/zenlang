set -e
cd "$(dirname "$0")"

# Compile all .c files to .o
gcc -c memory/allocator_default.c -o memory/allocator_default.o
gcc -c object/list.c -o object/list.o
gcc -c object/string.c -o object/string.o
gcc -c io/io_default.c -o io/io_default.o

# Archive into libzenrt.a
ar rcs libzenrt.a memory/allocator_default.o object/list.o object/string.o io/io_default.o

echo "Built libzenrt.a"
