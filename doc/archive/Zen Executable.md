# ZenLang Executable

## Commands

- `-p <path>` - Path to the project root
- `-o <path>` - Path to the output file
- `-t` - Transpile
- `-c` - Compile
- `-b` - Build
- `-r` - Reload
- `-i` - Interpret
- `-C` - Clean
- `-R` - Run
- `-v` - Verbose output
- `-d` - Debug output
- `-D` - Dump Tokens, AST, C Code
- `-h` - Help


### Compile
Compile will compile a Zen C Code to an executable.

### Transpile
Transpile will transpile a Zen file to Zen C Code.

### Interpret
Interpret will interpret a Zen file.

### Reload
Reload will only transpile and compile a files that have been modified.

### Run
Run will launch the executable after a compile or build.

### Build
Build will look in the current directory for a `.zbuild` file. If it finds one, it will build the project.

### Clean
Clean will remove the build directory.


## Examples

```bash
# Transpile a Zen file to C
zen -t src/main.zl -o build/main.c

# Compile a Zen file to an executable
zen -c src/main.zl -o build/main

# Run a Zen file
zen -r src/main.zl

# Interpret a Zen file
zen -i src/main.zl

# Clean the build directory
zen -C

# Dump tokens, AST, and C code
zen -D src/main.zl
```
