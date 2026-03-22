# AST

AST Components system:

Each AST component stores it's children within itself.
Each node has a parent property that points to it's parent node, this should avoid cycles and conflicts, allowing for easy navigation and traversal.
Each node should have a line and column property that points to it's location in the source code.

Include and Import statements are not AST components, they are handled by the parser, they should have a unique id and parent, and reference the file they include or import. 

NodeProgram { 
    id: "00000" ,
    parent: null,
    path: "main.zl",
    type: "program",
    line: 0,
    column: 0
}
    - statements

        - NodeStatement { 
            id: "00001",
            parent: "00000",
            line: 1,
            column: 1,
            type: "function"
        }
            - statement
                - NodeFunction { 
                    id: "00001", 
                    parent: "00001",
                    name: "x" 
                }
                    - statements
                        - NodeLet { 
                            id: "00002", 
                            parent: "00001",
                            name: "a" 
                        }
                            - value
                                - NodeNumber { 
                                    id: "00003", 
                                    parent: "00002",
                                    value: 1 
                                }
