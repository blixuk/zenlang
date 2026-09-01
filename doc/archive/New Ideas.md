Yeah, lets add some of the tool to zen to improve the usage and experience.
- Project Manager, Create a new project, set up environment..ect
- Build System, '.zbuild'
- Test System
- App Template, Terminal App Template with Command line aruments, command, help...ect
- Todo / Fixme system
- Version Control
- Documentation Generator
- Package Manager

A way to have these systems and tooling and have them work together cleanly. Project direcotry with everything contained inside, directories for outpus, building the program in the directory and placing the compiled output in the project directory, a project clean up also. A full language suit with great user experience.

----

Zen compiler plugin/extension system, allowing users to create custom plugins/extensions for the compiler.
These could incluse things like code analysis, issue/bug trackkers, comment viewers and much more.

Allow the compiler devs and the compiler users to create custom plugins/extensions for the compiler that can improve and extend the compilers tools and features.

---

Compiler (AOT)
Interpreter / Virtual Machine (JIT)

Zenlang should be able to compile and interpert code.
Compile to an execuatable.
Interpret code on the fly.

Zenlang should have an option for storing cached bytecode to speed up interpreting.
Zenlang should have an option to store JIT along with bytecode to create an intimediate between compiling and Interpreting.
Zenlang should be able to package bytecode to run a script without having the source code.

----

Coloured brackets, different colours for different nesting levels, maybe even a slight transpaent highlight on the elements inside that nesting level?

----

Handle empty files gracefully. The compiler should produce an error telling you what you need for a minimum compilable zen program.
The compiler shouldn't produce anything or dump an empty binary or object files.

The zen compiler should place output into a build directory and keep the project directory clean. 

The zen compiler should be able to staticly link and dynamically link.

Zen should have built in documentation, like man pages, on the command line. 
zen documents that can be queried for information about any keyword or symbol in the language.

---
Zen should have a keyword for every symbol.

Keyword: assign, Symbol: -> 
Keyword: assignin, Symbol: :>
Keyword: type, Symbol: :
Keyword: cast, Symbol: <:
Keyword: return, Symbol: <- 
Keyword: check, Symbol: ?
Keyword: assert, Symbol: !
Keyword: raise, Symbol: ^

Keyword: defer, Symbol: ~
Keyword: yeild, Symbol: <~

Keyword: , Symbol: 