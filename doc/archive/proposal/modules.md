# Modules System

## Include

Include is a simple way to include a file into another file. 
It will include all contents of the file into the current file.
Includes are resolved in LIFO order, meaning the last include will be the first to be resolved.


```
include `path/to/file.zl`
```

## Import

Module importing system for zenlang

```
// import module
import module

module.name
module.name()

// import package
import package

package.module.name
package.module.name()

// import package with alias
import package as alias

alias.module.name
alias.module.name()

// import selected from package
from package import module

module.name
module.name()

// from package.module import selected
from package.module import name

name
name()

// from package.module import name with alias
from package.module import name as alias

alias
alias()

// import selected from package with alias
from package import module as alias

alias.name
alias.name()

// import selected from module
from module import name

name
name()

// import selected from module with alias
from module import name as alias

alias
alias()

// import all from module
from module import *

name
name()

```

Package -> Module -> Function

Structure:
```
Package (Folder)
├── Module (File)
│   ├── Function
│   ├── Structure
│   ├── Variable
│   └── Constant

Path: zen/io.zl
Path: libs/zen/io.zl
Path: runtime/zen/io.zl

import zen.io
io.write(`Hello World!`)

from zen.io import write
write(`Hello World!`) 
```

Id like a system can import from zen standard library or user defined packages or files

```
Project (Folder)
├── libs (Folder)
│   ├── zen (Folder)
│   │   └── io.zl (File)
│   └── mylib (Folder)
│       └── mymodule.zl (File)
├── tools (Folder)
│   └── tool.zl (File)
├── other.zl (File)
└── main.zl (File)    
```

Id like a system that can manage its dependencies, rather than just including all the code form that file, only include the code that is needed.

so if a user imports a function, only include that function and what that function requires.

Id also like to be able to use runtime stuff in the standard library. for like io (Reading and writing to the terminal and files) or zen.memory (allocating and freeing memory)

I think we need Tree Shaking (Dead Code Elimination) combined with a hierarchical Module Resolution System.
To achieve "only include code that is needed," the compiler cannot simply paste files together (like C #include). Instead, it must build a Dependency Graph starting from main.zl and verify which functions, structures, and variables are actually reachable. either in the parser stage or the semantic analysis stage with a resolver.

Dependency Manager

Runtime Integration (The Bridge)
We want the Standard Library (zen.io) to access Runtime capabilities (C functions). We could  handle this via a 'native' or 'extern' keyword in the standard library files that maps to symbols in your C Runtime?

The runtime must export these symbols so the linker can find them.
This would be handled differently based on Interpreter or Compiler.

Shared Standard Library between Interpreter and Compiler
Interpreter Runtime and Compiler Runtime should both be accessible by the standard library.
This means having parity between the interpreter and compiler runtime.

